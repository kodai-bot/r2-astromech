"""
Training Data Generation Module

This module provides training data generation capabilities for the R2 astromech unit,
converting network discovery and AI analysis data into formats suitable for machine
learning training and fine-tuning.
"""

from .interfaces import (
    IDataFormatter,
    ITrainingDataExporter,
    ITrainingDataGenerator,
    TrainingDataConfig,
    TrainingDataMetrics
)

from .data_formatter import NetworkDataFormatter
from .data_exporter import TrainingDataExporter
from .training_generator import ModularTrainingDataGenerator

__all__ = [
    "IDataFormatter",
    "ITrainingDataExporter", 
    "ITrainingDataGenerator",
    "TrainingDataConfig",
    "TrainingDataMetrics",
    "NetworkDataFormatter",
    "TrainingDataExporter",
    "ModularTrainingDataGenerator"
]
