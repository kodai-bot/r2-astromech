"""
Training Data Generation Interfaces

This module defines interfaces for the training data generation system
that produces JSON and GeoJSON training datasets from R2's discoveries.
"""

from abc import ABC, abstractmethod
from typing import Dict, List, Any, Optional, Union
from datetime import datetime
import json


class IDataFormatter(ABC):
    """Interface for data formatters that convert discovery data to training format"""
    
    @abstractmethod
    def format_device_data(self, device_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Format device discovery data for training.
        
        Args:
            device_data: Raw device discovery data
            
        Returns:
            Dict containing formatted training data
        """
        pass
    
    @abstractmethod
    def format_network_data(self, network_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Format network discovery data for training.
        
        Args:
            network_data: Raw network discovery data
            
        Returns:
            Dict containing formatted training data
        """
        pass
    
    @abstractmethod
    def validate_output(self, data: Dict[str, Any]) -> bool:
        """
        Validate that the formatted data meets training requirements.
        
        Args:
            data: Formatted training data
            
        Returns:
            bool: True if data is valid for training
        """
        pass


class ITrainingDataExporter(ABC):
    """Interface for exporting training data to different formats"""
    
    @abstractmethod
    async def export_json(self, data: Dict[str, Any], output_path: str) -> bool:
        """
        Export training data as JSON.
        
        Args:
            data: Training data to export
            output_path: Path to save the JSON file
            
        Returns:
            bool: True if export successful
        """
        pass
    
    @abstractmethod
    async def export_geojson(self, data: Dict[str, Any], output_path: str) -> bool:
        """
        Export spatial training data as GeoJSON.
        
        Args:
            data: Training data with spatial information
            output_path: Path to save the GeoJSON file
            
        Returns:
            bool: True if export successful
        """
        pass
    
    @abstractmethod
    async def export_batch(self, datasets: List[Dict[str, Any]], 
                          output_dir: str, format_type: str) -> List[str]:
        """
        Export multiple datasets in batch.
        
        Args:
            datasets: List of training datasets
            output_dir: Directory to save exported files
            format_type: Format type ('json' or 'geojson')
            
        Returns:
            List[str]: List of exported file paths
        """
        pass


class ITrainingDataGenerator(ABC):
    """Interface for the main training data generation system"""
    
    @abstractmethod
    async def generate_training_set(self, discovery_data: Dict[str, Any], 
                                  ai_analysis: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Generate a complete training dataset from discovery and AI analysis data.
        
        Args:
            discovery_data: Network and device discovery data
            ai_analysis: Optional AI analysis results from TinyLLM
            
        Returns:
            Dict containing complete training dataset
        """
        pass
    
    @abstractmethod
    async def create_fine_tuning_dataset(self, 
                                       training_sets: List[Dict[str, Any]],
                                       task_type: str = "device_classification") -> Dict[str, Any]:
        """
        Create a dataset optimized for fine-tuning language models.
        
        Args:
            training_sets: List of individual training sets
            task_type: Type of ML task ("device_classification", "network_analysis", etc.)
            
        Returns:
            Dict containing fine-tuning ready dataset
        """
        pass
    
    @abstractmethod
    def get_supported_formats(self) -> List[str]:
        """
        Get list of supported output formats.
        
        Returns:
            List of supported format strings
        """
        pass
    
    @abstractmethod
    async def validate_training_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validate training data quality and completeness.
        
        Args:
            data: Training data to validate
            
        Returns:
            Dict containing validation results and metrics
        """
        pass


class TrainingDataConfig:
    """Configuration class for training data generation"""
    
    def __init__(self, 
                 output_directory: str = "data/training_sets",
                 include_geolocation: bool = True,
                 include_temporal_data: bool = True,
                 anonymize_data: bool = True,
                 format_version: str = "1.0",
                 max_records_per_file: int = 1000):
        """
        Initialize training data configuration.
        
        Args:
            output_directory: Directory for saving training datasets
            include_geolocation: Whether to include spatial data for GeoJSON
            include_temporal_data: Whether to include timestamp information
            anonymize_data: Whether to anonymize sensitive data
            format_version: Version of the training data format
            max_records_per_file: Maximum records per output file
        """
        self.output_directory = output_directory
        self.include_geolocation = include_geolocation
        self.include_temporal_data = include_temporal_data
        self.anonymize_data = anonymize_data
        self.format_version = format_version
        self.max_records_per_file = max_records_per_file
        
        # Training-specific settings
        self.task_types = [
            "device_classification",
            "network_topology_analysis", 
            "security_assessment",
            "iot_device_identification",
            "protocol_detection"
        ]
        
        # Data quality requirements
        self.required_fields = {
            "device_classification": [
                "device_id", "features", "device_type", "confidence"
            ],
            "network_topology_analysis": [
                "network_id", "topology_data", "device_relationships"
            ],
            "security_assessment": [
                "target_id", "vulnerability_data", "risk_score"
            ]
        }


class TrainingDataMetrics:
    """Metrics and statistics for training data quality"""
    
    def __init__(self):
        self.total_records = 0
        self.valid_records = 0
        self.invalid_records = 0
        self.coverage_by_type = {}
        self.quality_score = 0.0
        self.creation_timestamp = datetime.now()
        
    def to_dict(self) -> Dict[str, Any]:
        """Convert metrics to dictionary format"""
        return {
            "total_records": self.total_records,
            "valid_records": self.valid_records,
            "invalid_records": self.invalid_records,
            "coverage_by_type": self.coverage_by_type,
            "quality_score": self.quality_score,
            "creation_timestamp": self.creation_timestamp.isoformat(),
            "validity_rate": self.valid_records / self.total_records if self.total_records > 0 else 0.0
        }
