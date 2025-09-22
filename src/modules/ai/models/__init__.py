"""
AI Models Package

This package contains the modular AI model implementations for the R2 system.
"""

from .phi3_model import ModularPhi3Model
from .tinyllm_model import TinyLLMModel

__all__ = ['ModularPhi3Model', 'TinyLLMModel']