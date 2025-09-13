"""
AI Models Module

Contains all AI model implementations for the R2 astromech droid.
"""

from .base_model import BaseAIModel
from .phi3_model import Phi3Model

__all__ = [
    'BaseAIModel',
    'Phi3Model'
]
