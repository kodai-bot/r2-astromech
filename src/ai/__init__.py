"""
R2 Astromech AI Module

This module handles all AI-related functionality for the R2 astromech droid,
including model management, translation, and communication processing.
"""

from .model_manager import ModelManager
from .translator import R2Translator
from .models.base_model import BaseAIModel
from .models.phi3_model import Phi3Model

__all__ = [
    'ModelManager',
    'R2Translator', 
    'BaseAIModel',
    'Phi3Model'
]

__version__ = '1.0.0'
