"""
AI Model Manager

Handles loading, switching, and managing different AI models
for the R2 astromech droid system.
"""

import logging
from typing import Dict, Any, Optional, Type
import torch
import yaml
import os

from .models.base_model import BaseAIModel
from .models.phi3_model import Phi3Model

logger = logging.getLogger(__name__)


class ModelManager:
    """
    Manages AI models for the R2 astromech system.
    
    Provides functionality to:
    - Load and switch between different AI models
    - Manage model configurations
    - Handle model lifecycle (load/unload)
    - Provide model health monitoring
    """
    
    def __init__(self, config_path: Optional[str] = None):
        """
        Initialize the model manager.
        
        Args:
            config_path: Path to configuration file (optional)
        """
        self.current_model: Optional[BaseAIModel] = None
        self.available_models: Dict[str, Type[BaseAIModel]] = {
            'phi-3': Phi3Model
        }
        self.config = {}
        self.config_path = config_path or self._get_default_config_path()
        
        # Load configuration
        self._load_config()
        
        # Auto-detect device capabilities
        self._detect_device_capabilities()
    
    def _get_default_config_path(self) -> str:
        """Get the default configuration file path."""
        # Assume we're in src/ai/ and config is in project root
        current_dir = os.path.dirname(os.path.abspath(__file__))
        project_root = os.path.dirname(os.path.dirname(current_dir))
        return os.path.join(project_root, 'config', 'ai_config.yaml')
    
    def _load_config(self):
        """Load configuration from file."""
        try:
            if os.path.exists(self.config_path):
                with open(self.config_path, 'r') as f:
                    self.config = yaml.safe_load(f) or {}
                logger.info(f"Loaded AI configuration from {self.config_path}")
            else:
                # Use default configuration
                self.config = self._get_default_config()
                logger.info("Using default AI configuration")
        except Exception as e:
            logger.error(f"Failed to load config: {e}. Using defaults.")
            self.config = self._get_default_config()
    
    def _get_default_config(self) -> Dict[str, Any]:
        """Get default configuration."""
        return {
            'models': {
                'phi-3': {
                    'model_path': 'microsoft/Phi-3-mini-4k-instruct',
                    'device': 'auto',
                    'max_length': 512,
                    'temperature': 0.7,
                    'personality_mode': 'helpful'
                }
            },
            'default_model': 'phi-3',
            'auto_load': True,
            'device_preferences': ['cuda', 'cpu']
        }
    
    def _detect_device_capabilities(self):
        """Detect and set optimal device configuration."""
        if torch.cuda.is_available():
            device = 'cuda'
            gpu_count = torch.cuda.device_count()
            gpu_name = torch.cuda.get_device_name(0) if gpu_count > 0 else "Unknown"
            logger.info(f"CUDA available: {gpu_count} GPU(s) - {gpu_name}")
        else:
            device = 'cpu'
            logger.info("CUDA not available, using CPU")
        
        # Update model configs with detected device if set to 'auto'
        for model_name, model_config in self.config.get('models', {}).items():
            if model_config.get('device') == 'auto':
                model_config['device'] = device
    
    def load_model(self, model_name: str, force_reload: bool = False) -> bool:
        """
        Load a specific AI model.
        
        Args:
            model_name: Name of the model to load
            force_reload: Whether to force reload if model is already loaded
            
        Returns:
            bool: True if model loaded successfully, False otherwise
        """
        try:
            # Check if model is already loaded
            if (self.current_model is not None and 
                self.current_model.model_name == model_name and 
                not force_reload):
                logger.info(f"Model {model_name} already loaded")
                return True
            
            # Unload current model if exists
            if self.current_model is not None:
                self.unload_current_model()
            
            # Check if model is available
            if model_name not in self.available_models:
                logger.error(f"Model {model_name} not available")
                return False
            
            # Get model configuration
            model_config = self.config.get('models', {}).get(model_name, {})
            if not model_config:
                logger.error(f"No configuration found for model {model_name}")
                return False
            
            # Create and load model
            model_class = self.available_models[model_name]
            model_instance = model_class(model_config)
            
            if model_instance.load_model():
                self.current_model = model_instance
                logger.info(f"Successfully loaded model: {model_name}")
                return True
            else:
                logger.error(f"Failed to load model: {model_name}")
                return False
                
        except Exception as e:
            logger.error(f"Error loading model {model_name}: {e}")
            return False
    
    def unload_current_model(self) -> bool:
        """
        Unload the currently loaded model.
        
        Returns:
            bool: True if unloaded successfully, False otherwise
        """
        if self.current_model is not None:
            try:
                model_name = self.current_model.model_name
                if self.current_model.unload_model():
                    self.current_model = None
                    logger.info(f"Successfully unloaded model: {model_name}")
                    return True
                else:
                    logger.error(f"Failed to unload model: {model_name}")
                    return False
            except Exception as e:
                logger.error(f"Error unloading model: {e}")
                return False
        else:
            logger.info("No model currently loaded")
            return True
    
    def switch_model(self, model_name: str) -> bool:
        """
        Switch to a different AI model.
        
        Args:
            model_name: Name of the model to switch to
            
        Returns:
            bool: True if switch successful, False otherwise
        """
        return self.load_model(model_name, force_reload=True)
    
    def get_current_model(self) -> Optional[BaseAIModel]:
        """
        Get the currently loaded model.
        
        Returns:
            BaseAIModel: Current model instance or None
        """
        return self.current_model
    
    def get_available_models(self) -> list:
        """
        Get list of available model names.
        
        Returns:
            list: List of available model names
        """
        return list(self.available_models.keys())
    
    def get_model_status(self) -> Dict[str, Any]:
        """
        Get status information about the current model.
        
        Returns:
            Dict: Model status information
        """
        if self.current_model is not None:
            return {
                'loaded': True,
                'model_info': self.current_model.get_model_info(),
                'available_models': self.get_available_models()
            }
        else:
            return {
                'loaded': False,
                'model_info': None,
                'available_models': self.get_available_models()
            }
    
    def generate_response(self, input_text: str, **kwargs) -> str:
        """
        Generate a response using the current model.
        
        Args:
            input_text: Input text to process
            **kwargs: Additional parameters
            
        Returns:
            str: Generated response or error message
        """
        if self.current_model is None:
            # Try to auto-load default model
            default_model = self.config.get('default_model', 'phi-3')
            if self.config.get('auto_load', True):
                logger.info(f"Auto-loading default model: {default_model}")
                if not self.load_model(default_model):
                    return "Error: No model loaded and failed to auto-load default model"
            else:
                return "Error: No model loaded"
        
        return self.current_model.generate_response(input_text, **kwargs)
    
    def translate_to_r2(self, human_text: str) -> str:
        """
        Translate human text to R2 sounds using current model.
        
        Args:
            human_text: Human text to translate
            
        Returns:
            str: R2-style sound representation
        """
        if self.current_model is None:
            return "beep-boop?"  # Default confused sound
        
        return self.current_model.translate_to_r2(human_text)
    
    def translate_from_r2(self, r2_sounds: str) -> str:
        """
        Translate R2 sounds to human text using current model.
        
        Args:
            r2_sounds: R2 sound pattern
            
        Returns:
            str: Human-readable interpretation
        """
        if self.current_model is None:
            return "Unable to interpret R2 communication (no model loaded)"
        
        return self.current_model.translate_from_r2(r2_sounds)
    
    def register_model(self, model_name: str, model_class: Type[BaseAIModel]):
        """
        Register a new model type.
        
        Args:
            model_name: Name for the model
            model_class: Model class that inherits from BaseAIModel
        """
        self.available_models[model_name] = model_class
        logger.info(f"Registered new model: {model_name}")
    
    def save_config(self):
        """Save current configuration to file."""
        try:
            os.makedirs(os.path.dirname(self.config_path), exist_ok=True)
            with open(self.config_path, 'w') as f:
                yaml.dump(self.config, f, default_flow_style=False)
            logger.info(f"Saved configuration to {self.config_path}")
        except Exception as e:
            logger.error(f"Failed to save configuration: {e}")
    
    def force_cleanup(self) -> bool:
        """
        Force cleanup of all models and clear memory caches.
        Use this for explicit cleanup when needed.
        
        Returns:
            bool: True if cleanup successful
        """
        try:
            # Unload current model
            self.unload_current_model()
            
            # Force garbage collection
            import gc
            gc.collect()
            
            # Clear PyTorch caches if available
            if torch.cuda.is_available():
                torch.cuda.empty_cache()
                torch.cuda.synchronize()
            
            logger.info("Force cleanup completed")
            return True
            
        except Exception as e:
            logger.error(f"Error during force cleanup: {e}")
            return False
    
    def get_memory_usage(self) -> Dict[str, Any]:
        """
        Get current memory usage statistics.
        
        Returns:
            Dict: Memory usage information
        """
        memory_info = {
            'system_memory': {},
            'gpu_memory': {},
            'model_loaded': self.current_model is not None
        }
        
        try:
            import psutil
            process = psutil.Process()
            memory_info['system_memory'] = {
                'rss_mb': process.memory_info().rss / 1024 / 1024,
                'vms_mb': process.memory_info().vms / 1024 / 1024,
                'percent': process.memory_percent()
            }
        except ImportError:
            memory_info['system_memory'] = {'error': 'psutil not available'}
        
        if torch.cuda.is_available():
            try:
                for i in range(torch.cuda.device_count()):
                    device = f"cuda:{i}"
                    allocated_gb = torch.cuda.memory_allocated(device) / 1024**3
                    reserved_gb = torch.cuda.memory_reserved(device) / 1024**3
                    total_gb = torch.cuda.get_device_properties(device).total_memory / 1024**3
                    
                    memory_info['gpu_memory'][device] = {
                        'allocated_gb': allocated_gb,
                        'reserved_gb': reserved_gb,
                        'total_gb': total_gb,
                        'utilization_percent': (allocated_gb / total_gb) * 100
                    }
            except Exception as e:
                memory_info['gpu_memory']['error'] = str(e)
        
        return memory_info
    
    def __del__(self):
        """Cleanup when manager is destroyed."""
        if self.current_model is not None:
            self.unload_current_model()
    
    def __enter__(self):
        """Context manager entry."""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit with cleanup."""
        self.force_cleanup()
