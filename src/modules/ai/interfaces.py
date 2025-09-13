"""
AI Module Interfaces

This module defines the interfaces for AI-related functionality
including model management, network analysis, and translation.
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, Union
from datetime import datetime

from ...core.interfaces import IModule


class IAIModelManager(IModule):
    """AI Model Manager interface"""
    
    @abstractmethod
    async def load_model(self, model_name: str, force_reload: bool = False) -> bool:
        """
        Load a specific AI model.
        
        Args:
            model_name: Name of the model to load
            force_reload: Whether to force reload if already loaded
            
        Returns:
            bool: True if model loaded successfully
        """
        pass
    
    @abstractmethod
    async def unload_current_model(self) -> bool:
        """
        Unload the currently loaded model.
        
        Returns:
            bool: True if unloaded successfully
        """
        pass
    
    @abstractmethod
    async def switch_model(self, model_name: str) -> bool:
        """
        Switch to a different AI model.
        
        Args:
            model_name: Name of the model to switch to
            
        Returns:
            bool: True if switch successful
        """
        pass
    
    @abstractmethod
    async def generate_response(self, input_text: str, **kwargs) -> str:
        """
        Generate a response using the current model.
        
        Args:
            input_text: Input text to process
            **kwargs: Additional parameters
            
        Returns:
            str: Generated response
        """
        pass
    
    @abstractmethod
    async def translate_to_r2(self, human_text: str) -> str:
        """
        Translate human text to R2 sounds.
        
        Args:
            human_text: Human text to translate
            
        Returns:
            str: R2-style sound representation
        """
        pass
    
    @abstractmethod
    async def translate_from_r2(self, r2_sounds: str) -> str:
        """
        Translate R2 sounds to human text.
        
        Args:
            r2_sounds: R2 sound pattern
            
        Returns:
            str: Human-readable interpretation
        """
        pass
    
    @abstractmethod
    async def get_available_models(self) -> List[str]:
        """
        Get list of available model names.
        
        Returns:
            List[str]: Available model names
        """
        pass
    
    @abstractmethod
    async def get_model_status(self) -> Dict[str, Any]:
        """
        Get status information about the current model.
        
        Returns:
            Dict[str, Any]: Model status information
        """
        pass
    
    @abstractmethod
    async def get_memory_usage(self) -> Dict[str, Any]:
        """
        Get current memory usage statistics.
        
        Returns:
            Dict[str, Any]: Memory usage information
        """
        pass


class INetworkAnalyzer(IModule):
    """Network Analysis interface"""
    
    @abstractmethod
    async def analyze_discovered_devices(self, devices: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Analyze discovered network devices.
        
        Args:
            devices: List of discovered devices
            
        Returns:
            Dict[str, Any]: Analysis results including R2 response
        """
        pass
    
    @abstractmethod
    async def analyze_network_issue(self, device_data: str, symptoms: str) -> Dict[str, Any]:
        """
        Diagnose a network issue.
        
        Args:
            device_data: Device information
            symptoms: Description of symptoms
            
        Returns:
            Dict[str, Any]: Diagnosis results
        """
        pass
    
    @abstractmethod
    async def assess_security_posture(self, devices: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Perform security assessment of network devices.
        
        Args:
            devices: List of devices to assess
            
        Returns:
            Dict[str, Any]: Security assessment results
        """
        pass
    
    @abstractmethod
    async def get_analysis_history(self, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Get recent analysis history.
        
        Args:
            limit: Maximum number of analyses to return
            
        Returns:
            List[Dict[str, Any]]: Recent analyses
        """
        pass


class ITranslator(IModule):
    """Translation service interface"""
    
    @abstractmethod
    async def translate_to_r2(self, human_text: str, context: Optional[str] = None) -> str:
        """
        Translate human text to R2 sounds.
        
        Args:
            human_text: Human text to translate
            context: Optional context for translation
            
        Returns:
            str: R2 sound representation
        """
        pass
    
    @abstractmethod
    async def translate_from_r2(self, r2_sounds: str) -> str:
        """
        Translate R2 sounds to human text.
        
        Args:
            r2_sounds: R2 sound pattern
            
        Returns:
            str: Human-readable interpretation
        """
        pass
    
    @abstractmethod
    async def generate_contextual_response(self, message: str) -> tuple[str, str]:
        """
        Generate contextual R2 response.
        
        Args:
            message: Input message
            
        Returns:
            tuple[str, str]: (R2 sounds, human interpretation)
        """
        pass
    
    @abstractmethod
    async def get_conversation_history(self) -> List[Dict[str, Any]]:
        """
        Get conversation history.
        
        Returns:
            List[Dict[str, Any]]: Conversation history
        """
        pass
    
    @abstractmethod
    async def clear_history(self) -> None:
        """Clear conversation history"""
        pass
    
    @abstractmethod
    async def get_available_emotions(self) -> List[str]:
        """
        Get available emotions for translation.
        
        Returns:
            List[str]: Available emotions
        """
        pass


class IAIModel(ABC):
    """Base interface for AI model implementations"""
    
    @property
    @abstractmethod
    def model_name(self) -> str:
        """Get model name"""
        pass
    
    @abstractmethod
    async def load_model(self) -> bool:
        """
        Load the model.
        
        Returns:
            bool: True if loaded successfully
        """
        pass
    
    @abstractmethod
    async def unload_model(self) -> bool:
        """
        Unload the model.
        
        Returns:
            bool: True if unloaded successfully
        """
        pass
    
    @abstractmethod
    async def generate_response(self, input_text: str, **kwargs) -> str:
        """
        Generate response from the model.
        
        Args:
            input_text: Input text
            **kwargs: Additional parameters
            
        Returns:
            str: Generated response
        """
        pass
    
    @abstractmethod
    async def translate_to_r2(self, human_text: str) -> str:
        """
        Translate human text to R2 sounds.
        
        Args:
            human_text: Human text
            
        Returns:
            str: R2 sound representation
        """
        pass
    
    @abstractmethod
    async def translate_from_r2(self, r2_sounds: str) -> str:
        """
        Translate R2 sounds to human text.
        
        Args:
            r2_sounds: R2 sound pattern
            
        Returns:
            str: Human interpretation
        """
        pass
    
    @abstractmethod
    async def get_model_info(self) -> Dict[str, Any]:
        """
        Get model information.
        
        Returns:
            Dict[str, Any]: Model information
        """
        pass