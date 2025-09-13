"""
Base AI Model Interface

Defines the abstract interface that all AI models must implement
for the R2 astromech droid system.
"""

from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Any
import logging

logger = logging.getLogger(__name__)


class BaseAIModel(ABC):
    """
    Abstract base class for all AI models in the R2 system.
    
    This interface ensures consistent behavior across different model implementations
    and provides common functionality for model management.
    """
    
    def __init__(self, model_name: str, config: Dict[str, Any]):
        """
        Initialize the base model.
        
        Args:
            model_name: Name identifier for this model
            config: Configuration dictionary for the model
        """
        self.model_name = model_name
        self.config = config
        self.is_loaded = False
        self._model = None
        
    @abstractmethod
    def load_model(self) -> bool:
        """
        Load the AI model into memory.
        
        Returns:
            bool: True if model loaded successfully, False otherwise
        """
        pass
    
    @abstractmethod
    def unload_model(self) -> bool:
        """
        Unload the AI model from memory.
        
        Returns:
            bool: True if model unloaded successfully, False otherwise
        """
        pass
    
    @abstractmethod
    def generate_response(self, input_text: str, **kwargs) -> str:
        """
        Generate a response based on input text.
        
        Args:
            input_text: The input text to process
            **kwargs: Additional parameters for generation
            
        Returns:
            str: Generated response text
        """
        pass
    
    @abstractmethod
    def translate_to_r2(self, human_text: str) -> str:
        """
        Translate human text to R2-style communication.
        
        Args:
            human_text: Human-readable text to translate
            
        Returns:
            str: R2-style beeps and sounds representation
        """
        pass
    
    @abstractmethod
    def translate_from_r2(self, r2_sounds: str) -> str:
        """
        Translate R2-style sounds to human-readable text.
        
        Args:
            r2_sounds: R2 sound pattern to interpret
            
        Returns:
            str: Human-readable interpretation
        """
        pass
    
    def get_model_info(self) -> Dict[str, Any]:
        """
        Get information about the current model.
        
        Returns:
            Dict containing model information
        """
        return {
            'name': self.model_name,
            'loaded': self.is_loaded,
            'config': self.config
        }
    
    def is_model_loaded(self) -> bool:
        """
        Check if the model is currently loaded.
        
        Returns:
            bool: True if model is loaded, False otherwise
        """
        return self.is_loaded
    
    def validate_config(self) -> bool:
        """
        Validate the model configuration.
        
        Returns:
            bool: True if configuration is valid, False otherwise
        """
        required_keys = ['model_path', 'device']
        return all(key in self.config for key in required_keys)
