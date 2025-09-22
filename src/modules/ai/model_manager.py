"""
Modular AI Model Manager Implementation

This module implements the IAIModelManager interface for the new modular R2 system.
It provides event-driven AI model management with proper encapsulation.
"""

import asyncio
import logging
import torch
import gc
from typing import Dict, Any, Optional, List, Type
from datetime import datetime
import psutil
import os

from ...core.interfaces import IModule, ModuleStatus
from ...core.events import EventBus, create_event, R2Events
from ..ai.interfaces import IAIModelManager, IAIModel
from ...utils.exceptions import R2AIException, R2ModuleException
from ...utils.logging import get_module_logger
from .models.phi3_model import ModularPhi3Model
from .models.tinyllm_model import TinyLLMModel

logger = get_module_logger("ai.model_manager")


class ModularAIModelManager(IAIModelManager):
    """
    Modular AI Model Manager implementation
    
    This manager uses event-driven communication and follows the new
    modular architecture principles.
    """
    
    def __init__(self, event_bus: EventBus, config: Dict[str, Any]):
        """
        Initialize the modular AI model manager.
        
        Args:
            event_bus: Event bus for communication
            config: AI configuration
        """
        self.event_bus = event_bus
        self.config = config
        self.logger = logger
        
        # Manager state
        self.is_running = False
        self.current_model: Optional[IAIModel] = None
        self.model_loading = False
        
        # Available models - Only TinyLLM for resource-constrained devices
        self.available_models: Dict[str, Type[IAIModel]] = {
            'tinyllm': TinyLLMModel
            # 'phi-3': ModularPhi3Model,  # Disabled - too large for resource-constrained devices
        }
        
        # Model configurations
        self.model_configs = config.get('models', {})
        self.default_model = config.get('default_model', 'tinyllm')
        self.auto_load = config.get('auto_load', True)
        
        # Performance tracking
        self.stats = {
            'models_loaded': 0,
            'models_unloaded': 0,
            'responses_generated': 0,
            'translations_performed': 0,
            'errors': 0,
            'memory_peak_mb': 0
        }
        
        # Device capabilities
        self.device_capabilities = self._detect_device_capabilities()
        
        self.logger.info("Modular AI Model Manager initialized")
    
    @property
    def module_name(self) -> str:
        """Get the module name"""
        return "ai_model_manager"
    
    async def initialize(self) -> bool:
        """Initialize the AI model manager"""
        try:
            self.logger.info("Initializing AI model manager...")
            
            # Subscribe to relevant events
            await self.event_bus.subscribe(R2Events.SYSTEM_STARTUP, self._on_system_startup)
            await self.event_bus.subscribe(R2Events.SYSTEM_SHUTDOWN, self._on_system_shutdown)
            await self.event_bus.subscribe("ai.model_requested", self._on_model_requested)
            await self.event_bus.subscribe("ai.analysis_requested", self._on_analysis_requested)
            
            # Auto-load default model if configured
            if self.auto_load and self.default_model:
                self.logger.info(f"Auto-loading default model: {self.default_model}")
                await self.load_model(self.default_model)
            
            self.logger.info("AI model manager initialized successfully")
            return True
            
        except Exception as e:
            self.logger.error(f"AI model manager initialization failed: {e}")
            return False
    
    async def start(self) -> bool:
        """Start the AI model manager"""
        try:
            self.logger.info("Starting AI model manager...")
            
            # Publish module started event
            await self.event_bus.publish(create_event(
                R2Events.MODULE_STARTED,
                {
                    "module": self.module_name,
                    "capabilities": ["model_management", "text_generation", "r2_translation"],
                    "available_models": list(self.available_models.keys()),
                    "device_capabilities": self.device_capabilities
                },
                self.module_name
            ))
            
            self.is_running = True
            self.logger.info("AI model manager started successfully")
            return True
            
        except Exception as e:
            self.logger.error(f"AI model manager start failed: {e}")
            return False
    
    async def stop(self) -> bool:
        """Stop the AI model manager"""
        try:
            self.logger.info("Stopping AI model manager...")
            
            # Unload current model
            if self.current_model:
                await self.unload_current_model()
            
            # Publish module stopped event
            await self.event_bus.publish(create_event(
                R2Events.MODULE_STOPPED,
                {"module": self.module_name, "stats": self.stats},
                self.module_name
            ))
            
            self.is_running = False
            self.logger.info("AI model manager stopped successfully")
            return True
            
        except Exception as e:
            self.logger.error(f"AI model manager stop failed: {e}")
            return False
    
    async def get_status(self) -> ModuleStatus:
        """Get current module status"""
        current_model_info = None
        if self.current_model:
            try:
                current_model_info = await self.current_model.get_model_info()
            except Exception:
                current_model_info = {"name": "unknown", "status": "error"}
        
        return ModuleStatus(
            name=self.module_name,
            status='running' if self.is_running else 'stopped',
            health_score=1.0 if self.current_model else 0.5,
            last_heartbeat=datetime.now(),
            memory_usage_mb=self._get_memory_usage()
        )
    
    async def health_check(self) -> bool:
        """Perform health check"""
        try:
            # Check if manager is running
            if not self.is_running:
                return False
            
            # Check current model health
            if self.current_model:
                # Try to get model info as a health check
                await self.current_model.get_model_info()
            
            return True
            
        except Exception as e:
            self.logger.error(f"Health check failed: {e}")
            return False
    
    async def cleanup(self) -> bool:
        """Cleanup AI model manager resources"""
        try:
            self.logger.info("Cleaning up AI model manager...")
            
            # Unload current model
            if self.current_model:
                await self.unload_current_model()
            
            # Clear GPU memory
            if torch.cuda.is_available():
                torch.cuda.empty_cache()
                gc.collect()
            
            self.logger.info("AI model manager cleanup complete")
            return True
            
        except Exception as e:
            self.logger.error(f"AI model manager cleanup failed: {e}")
            return False
    
    async def load_model(self, model_name: str, force_reload: bool = False) -> bool:
        """
        Load a specific AI model.
        
        Args:
            model_name: Name of the model to load
            force_reload: Whether to force reload if already loaded
            
        Returns:
            bool: True if model loaded successfully
        """
        try:
            if self.model_loading:
                self.logger.warning("Model loading already in progress")
                return False
            
            # Check if model is already loaded
            if self.current_model and self.current_model.model_name == model_name and not force_reload:
                self.logger.info(f"Model {model_name} already loaded")
                return True
            
            # Check if model is available
            if model_name not in self.available_models:
                self.logger.error(f"Model {model_name} not available")
                return False
            
            self.model_loading = True
            
            # Publish model loading started event
            await self.event_bus.publish(create_event(
                R2Events.AI_MODEL_LOADED,
                {"model_name": model_name, "status": "loading_started"},
                self.module_name
            ))
            
            # Unload current model if different
            if self.current_model and self.current_model.model_name != model_name:
                await self.unload_current_model()
            
            # Get model configuration
            model_config = self.model_configs.get(model_name, {})
            model_config.update({
                'device_capabilities': self.device_capabilities,
                'event_bus': self.event_bus
            })
            
            # Create and load new model
            model_class = self.available_models[model_name]
            self.current_model = model_class(model_config)
            
            # Load the model
            success = await self.current_model.load_model()
            
            if success:
                self.stats['models_loaded'] += 1
                self.logger.info(f"Model {model_name} loaded successfully")
                
                # Publish model loaded event
                await self.event_bus.publish(create_event(
                    R2Events.AI_MODEL_LOADED,
                    {
                        "model_name": model_name,
                        "status": "loaded",
                        "model_info": await self.current_model.get_model_info()
                    },
                    self.module_name
                ))
            else:
                self.logger.error(f"Failed to load model {model_name}")
                self.current_model = None
            
            self.model_loading = False
            return success
            
        except Exception as e:
            self.logger.error(f"Error loading model {model_name}: {e}")
            self.stats['errors'] += 1
            self.model_loading = False
            return False
    
    async def unload_current_model(self) -> bool:
        """
        Unload the currently loaded model.
        
        Returns:
            bool: True if unloaded successfully
        """
        try:
            if not self.current_model:
                self.logger.info("No model currently loaded")
                return True
            
            model_name = self.current_model.model_name
            
            # Publish model unloading event
            await self.event_bus.publish(create_event(
                R2Events.AI_MODEL_UNLOADED,
                {"model_name": model_name, "status": "unloading"},
                self.module_name
            ))
            
            # Unload the model
            success = await self.current_model.unload_model()
            
            if success:
                self.stats['models_unloaded'] += 1
                self.logger.info(f"Model {model_name} unloaded successfully")
                
                # Publish model unloaded event
                await self.event_bus.publish(create_event(
                    R2Events.AI_MODEL_UNLOADED,
                    {"model_name": model_name, "status": "unloaded"},
                    self.module_name
                ))
            else:
                self.logger.error(f"Failed to unload model {model_name}")
            
            self.current_model = None
            
            # Clear GPU memory
            if torch.cuda.is_available():
                torch.cuda.empty_cache()
                gc.collect()
            
            return success
            
        except Exception as e:
            self.logger.error(f"Error unloading model: {e}")
            self.stats['errors'] += 1
            return False
    
    async def switch_model(self, model_name: str) -> bool:
        """
        Switch to a different AI model.
        
        Args:
            model_name: Name of the model to switch to
            
        Returns:
            bool: True if switch successful
        """
        return await self.load_model(model_name, force_reload=True)
    
    async def generate_response(self, input_text: str, **kwargs) -> str:
        """
        Generate a response using the current model.
        
        Args:
            input_text: Input text to process
            **kwargs: Additional parameters
            
        Returns:
            str: Generated response
        """
        try:
            if not self.current_model:
                raise R2AIException("No model currently loaded")
            
            # Publish analysis started event
            await self.event_bus.publish(create_event(
                R2Events.AI_ANALYSIS_STARTED,
                {"input_text": input_text[:100] + "..." if len(input_text) > 100 else input_text},
                self.module_name
            ))
            
            # Generate response
            response = await self.current_model.generate_response(input_text, **kwargs)
            
            self.stats['responses_generated'] += 1
            
            # Publish analysis completed event
            await self.event_bus.publish(create_event(
                R2Events.AI_ANALYSIS_COMPLETED,
                {
                    "input_length": len(input_text),
                    "response_length": len(response),
                    "model_name": self.current_model.model_name
                },
                self.module_name
            ))
            
            return response
            
        except Exception as e:
            self.logger.error(f"Error generating response: {e}")
            self.stats['errors'] += 1
            raise R2AIException(f"Failed to generate response: {e}")
    
    async def translate_to_r2(self, human_text: str) -> str:
        """
        Translate human text to R2 sounds.
        
        Args:
            human_text: Human text to translate
            
        Returns:
            str: R2-style sound representation
        """
        try:
            if not self.current_model:
                raise R2AIException("No model currently loaded")
            
            translation = await self.current_model.translate_to_r2(human_text)
            self.stats['translations_performed'] += 1
            
            return translation
            
        except Exception as e:
            self.logger.error(f"Error translating to R2: {e}")
            self.stats['errors'] += 1
            raise R2AIException(f"Failed to translate to R2: {e}")
    
    async def translate_from_r2(self, r2_sounds: str) -> str:
        """
        Translate R2 sounds to human text.
        
        Args:
            r2_sounds: R2 sound pattern
            
        Returns:
            str: Human-readable interpretation
        """
        try:
            if not self.current_model:
                raise R2AIException("No model currently loaded")
            
            translation = await self.current_model.translate_from_r2(r2_sounds)
            self.stats['translations_performed'] += 1
            
            return translation
            
        except Exception as e:
            self.logger.error(f"Error translating from R2: {e}")
            self.stats['errors'] += 1
            raise R2AIException(f"Failed to translate from R2: {e}")
    
    async def get_available_models(self) -> List[str]:
        """
        Get list of available model names.
        
        Returns:
            List[str]: Available model names
        """
        return list(self.available_models.keys())
    
    async def get_model_status(self) -> Dict[str, Any]:
        """
        Get status information about the current model.
        
        Returns:
            Dict[str, Any]: Model status information
        """
        if not self.current_model:
            return {
                "current_model": None,
                "status": "no_model_loaded",
                "available_models": await self.get_available_models()
            }
        
        try:
            model_info = await self.current_model.get_model_info()
            return {
                "current_model": self.current_model.model_name,
                "status": "loaded",
                "model_info": model_info,
                "available_models": await self.get_available_models()
            }
        except Exception as e:
            return {
                "current_model": self.current_model.model_name,
                "status": "error",
                "error": str(e),
                "available_models": await self.get_available_models()
            }
    
    async def get_memory_usage(self) -> Dict[str, Any]:
        """
        Get current memory usage statistics.
        
        Returns:
            Dict[str, Any]: Memory usage information
        """
        memory_info = {
            "system_memory": {
                "total_mb": psutil.virtual_memory().total // (1024 * 1024),
                "available_mb": psutil.virtual_memory().available // (1024 * 1024),
                "used_mb": psutil.virtual_memory().used // (1024 * 1024),
                "percent": psutil.virtual_memory().percent
            },
            "process_memory": {
                "rss_mb": psutil.Process().memory_info().rss // (1024 * 1024),
                "vms_mb": psutil.Process().memory_info().vms // (1024 * 1024)
            }
        }
        
        # GPU memory if available
        if torch.cuda.is_available():
            memory_info["gpu_memory"] = {
                "total_mb": torch.cuda.get_device_properties(0).total_memory // (1024 * 1024),
                "allocated_mb": torch.cuda.memory_allocated() // (1024 * 1024),
                "cached_mb": torch.cuda.memory_reserved() // (1024 * 1024),
                "free_mb": (torch.cuda.get_device_properties(0).total_memory - torch.cuda.memory_reserved()) // (1024 * 1024)
            }
        
        return memory_info
    
    def _detect_device_capabilities(self) -> Dict[str, Any]:
        """Detect device capabilities for model optimization"""
        capabilities = {
            "cpu_count": os.cpu_count(),
            "memory_gb": psutil.virtual_memory().total // (1024 * 1024 * 1024),
            "cuda_available": torch.cuda.is_available(),
            "cuda_device_count": torch.cuda.device_count() if torch.cuda.is_available() else 0
        }
        
        if torch.cuda.is_available():
            capabilities.update({
                "cuda_device_name": torch.cuda.get_device_name(0),
                "cuda_memory_gb": torch.cuda.get_device_properties(0).total_memory // (1024 * 1024 * 1024)
            })
        
        return capabilities
    
    def _get_memory_usage(self) -> Optional[float]:
        """Get current memory usage in MB"""
        try:
            return psutil.Process().memory_info().rss / (1024 * 1024)
        except Exception:
            return None
    
    async def _on_system_startup(self, event) -> None:
        """Handle system startup event"""
        self.logger.info("System startup detected")
    
    async def _on_system_shutdown(self, event) -> None:
        """Handle system shutdown event"""
        self.logger.info("System shutdown detected")
        if self.current_model:
            await self.unload_current_model()
    
    async def _on_model_requested(self, event) -> None:
        """Handle model request event"""
        model_name = event.data.get('model_name')
        if model_name:
            await self.load_model(model_name)
    
    async def _on_analysis_requested(self, event) -> None:
        """Handle analysis request event"""
        input_text = event.data.get('input_text')
        if input_text and self.current_model:
            try:
                response = await self.generate_response(input_text)
                await self.event_bus.publish(create_event(
                    R2Events.AI_RESPONSE_GENERATED,
                    {"response": response, "model_name": self.current_model.model_name},
                    self.module_name
                ))
            except Exception as e:
                self.logger.error(f"Analysis request failed: {e}")