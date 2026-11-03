"""
Modular Training Data Generator

This module coordinates the generation of training datasets by combining
network discovery data with AI analysis from TinyLLM model.
"""

import os
from typing import Dict, List, Any, Optional
from datetime import datetime
import logging

from .interfaces import ITrainingDataGenerator, TrainingDataConfig, TrainingDataMetrics
from .data_formatter import NetworkDataFormatter
from .data_exporter import TrainingDataExporter
# from ..ai.interfaces import IAIModel  # Optional import for AI integration
logger = logging.getLogger("training.training_generator")


class ModularTrainingDataGenerator(ITrainingDataGenerator):
    """
    Main training data generator that coordinates data collection,
    AI analysis, formatting, and export for machine learning training sets.
    """
    
    def __init__(self, config: TrainingDataConfig, ai_model: Optional[Any] = None):
        """
        Initialize the modular training data generator.
        
        Args:
            config: Training data configuration
            ai_model: Optional AI model for enhanced analysis
        """
        self.config = config
        self.ai_model = ai_model
        self.logger = logger
        
        # Initialize components
        self.formatter = NetworkDataFormatter(config)
        self.exporter = TrainingDataExporter(config)
        
        # Tracking
        self.generation_history = []
        self.metrics = TrainingDataMetrics()
        
        logger.info("Modular training data generator initialized")
    
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
        try:
            logger.info("Generating training dataset from discovery data")
            
            training_set = {
                "dataset_info": {
                    "generated_at": datetime.now().isoformat(),
                    "format_version": self.config.format_version,
                    "includes_ai_analysis": ai_analysis is not None,
                    "anonymized": self.config.anonymize_data
                },
                "records": []
            }
            
            # Process device-level data
            if 'devices' in discovery_data:
                device_records = await self._process_device_data(
                    discovery_data['devices'], ai_analysis
                )
                training_set["records"].extend(device_records)
            
            # Process network-level data
            if 'networks' in discovery_data:
                network_records = await self._process_network_data(
                    discovery_data['networks'], ai_analysis
                )
                training_set["records"].extend(network_records)
            
            # Handle single device/network records
            if 'device_signatures' in discovery_data:
                # This looks like network fingerprint data
                network_record = self.formatter.format_network_data(discovery_data)
                if network_record and self.formatter.validate_output(network_record):
                    training_set["records"].append(network_record)
            
            # Add AI-enhanced features if available
            if ai_analysis and self.ai_model:
                training_set = await self._enhance_with_ai_analysis(training_set, ai_analysis)
            
            # Update metrics
            self.metrics.total_records += len(training_set["records"])
            self.metrics.valid_records += sum(
                1 for record in training_set["records"] 
                if self.formatter.validate_output(record)
            )
            
            # Add quality assessment
            training_set["quality_metrics"] = await self._assess_quality(training_set)
            
            logger.info(f"Generated training set with {len(training_set['records'])} records")
            return training_set
            
        except Exception as e:
            logger.error(f"Failed to generate training set: {e}")
            return {}
    
    async def create_fine_tuning_dataset(self, 
                                       training_sets: List[Dict[str, Any]],
                                       task_type: str = "device_classification") -> Dict[str, Any]:
        """
        Create a dataset optimized for fine-tuning language models.
        
        Args:
            training_sets: List of individual training sets
            task_type: Type of ML task
            
        Returns:
            Dict containing fine-tuning ready dataset
        """
        try:
            logger.info(f"Creating fine-tuning dataset for task: {task_type}")
            
            fine_tuning_data = {
                "dataset_info": {
                    "task_type": task_type,
                    "created_at": datetime.now().isoformat(),
                    "source_training_sets": len(training_sets),
                    "format_version": self.config.format_version
                },
                "training_examples": [],
                "validation_examples": [],
                "metadata": {
                    "total_examples": 0,
                    "task_specific_info": {}
                }
            }
            
            # Convert training sets to fine-tuning format
            if task_type == "device_classification":
                fine_tuning_data = await self._create_device_classification_dataset(
                    training_sets, fine_tuning_data
                )
            elif task_type == "network_analysis":
                fine_tuning_data = await self._create_network_analysis_dataset(
                    training_sets, fine_tuning_data
                )
            elif task_type == "iot_device_identification":
                fine_tuning_data = await self._create_iot_identification_dataset(
                    training_sets, fine_tuning_data
                )
            else:
                logger.warning(f"Unknown task type: {task_type}, using generic format")
                fine_tuning_data = await self._create_generic_dataset(
                    training_sets, fine_tuning_data
                )
            
            # Split into training and validation
            examples = fine_tuning_data["training_examples"]
            split_point = int(len(examples) * 0.8)  # 80/20 split
            
            fine_tuning_data["training_examples"] = examples[:split_point]
            fine_tuning_data["validation_examples"] = examples[split_point:]
            fine_tuning_data["metadata"]["total_examples"] = len(examples)
            fine_tuning_data["metadata"]["training_count"] = len(fine_tuning_data["training_examples"])
            fine_tuning_data["metadata"]["validation_count"] = len(fine_tuning_data["validation_examples"])
            
            logger.info(f"Created fine-tuning dataset with {len(examples)} examples")
            return fine_tuning_data
            
        except Exception as e:
            logger.error(f"Failed to create fine-tuning dataset: {e}")
            return {}
    
    def get_supported_formats(self) -> List[str]:
        """Get list of supported output formats."""
        return ["json", "geojson", "jsonl", "csv"]
    
    async def validate_training_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validate training data quality and completeness.
        
        Args:
            data: Training data to validate
            
        Returns:
            Dict containing validation results and metrics
        """
        validation_results = {
            "is_valid": True,
            "errors": [],
            "warnings": [],
            "metrics": {},
            "recommendations": []
        }
        
        try:
            records = data.get('records', [])
            
            if not records:
                validation_results["is_valid"] = False
                validation_results["errors"].append("No training records found")
                return validation_results
            
            # Validate individual records
            valid_count = 0
            for i, record in enumerate(records):
                if not self.formatter.validate_output(record):
                    validation_results["errors"].append(f"Record {i} failed validation")
                else:
                    valid_count += 1
            
            # Calculate metrics
            validation_results["metrics"] = {
                "total_records": len(records),
                "valid_records": valid_count,
                "validity_rate": valid_count / len(records),
                "record_types": self._count_record_types(records),
                "has_location_data": sum(1 for r in records if 'location_features' in r),
                "has_temporal_data": sum(1 for r in records if 'temporal_features' in r)
            }
            
            # Generate recommendations
            if validation_results["metrics"]["validity_rate"] < 0.9:
                validation_results["recommendations"].append(
                    "Consider improving data quality - validity rate below 90%"
                )
            
            if validation_results["metrics"]["has_location_data"] == 0:
                validation_results["recommendations"].append(
                    "No location data found - GeoJSON export will be limited"
                )
            
            logger.info(f"Validation completed: {valid_count}/{len(records)} records valid")
            
        except Exception as e:
            validation_results["is_valid"] = False
            validation_results["errors"].append(f"Validation failed: {e}")
            logger.error(f"Training data validation failed: {e}")
        
        return validation_results
    
    async def export_training_data(self, training_data: Dict[str, Any], 
                                 output_format: str = "json") -> Optional[str]:
        """
        Export training data to specified format.
        
        Args:
            training_data: Training data to export
            output_format: Output format ('json' or 'geojson')
            
        Returns:
            str: Path to exported file, or None if failed
        """
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"r2_training_data_{timestamp}.{output_format}"
            output_path = os.path.join(self.config.output_directory, filename)
            
            if output_format == "json":
                success = await self.exporter.export_json(training_data, output_path)
            elif output_format == "geojson":
                success = await self.exporter.export_geojson(training_data, output_path)
            else:
                logger.error(f"Unsupported output format: {output_format}")
                return None
            
            if success:
                logger.info(f"Training data exported to {output_path}")
                return output_path
            else:
                return None
                
        except Exception as e:
            logger.error(f"Failed to export training data: {e}")
            return None
    
    async def _process_device_data(self, devices_data: Dict[str, Any], 
                                 ai_analysis: Optional[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Process device-level discovery data into training records."""
        records = []
        
        for device_id, device_data in devices_data.items():
            # Format device data
            device_record = self.formatter.format_device_data(device_data)
            
            if device_record and self.formatter.validate_output(device_record):
                # Add AI analysis if available
                if ai_analysis and device_id in ai_analysis:
                    device_record = await self._add_ai_features(
                        device_record, ai_analysis[device_id]
                    )
                
                records.append(device_record)
            else:
                logger.warning(f"Failed to format device data for {device_id}")
        
        return records
    
    async def _process_network_data(self, networks_data: Dict[str, Any],
                                  ai_analysis: Optional[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Process network-level discovery data into training records."""
        records = []
        
        for network_id, network_data in networks_data.items():
            # Format network data
            network_record = self.formatter.format_network_data(network_data)
            
            if network_record and self.formatter.validate_output(network_record):
                # Add AI analysis if available
                if ai_analysis and network_id in ai_analysis:
                    network_record = await self._add_ai_features(
                        network_record, ai_analysis[network_id]
                    )
                
                records.append(network_record)
            else:
                logger.warning(f"Failed to format network data for {network_id}")
        
        return records
    
    async def _enhance_with_ai_analysis(self, training_set: Dict[str, Any],
                                      ai_analysis: Dict[str, Any]) -> Dict[str, Any]:
        """Enhance training set with AI analysis results."""
        try:
            # Add overall AI insights
            training_set["ai_insights"] = {
                "analysis_timestamp": ai_analysis.get('timestamp', datetime.now().isoformat()),
                "model_used": ai_analysis.get('model_name', 'unknown'),
                "confidence_scores": ai_analysis.get('confidence_scores', {}),
                "recommendations": ai_analysis.get('recommendations', [])
            }
            
            # Enhance individual records with AI features
            for record in training_set["records"]:
                record_id = record.get('device_id') or record.get('network_id')
                if record_id and record_id in ai_analysis:
                    record = await self._add_ai_features(record, ai_analysis[record_id])
            
            return training_set
            
        except Exception as e:
            logger.error(f"Failed to enhance training set with AI analysis: {e}")
            return training_set
    
    async def _add_ai_features(self, record: Dict[str, Any], 
                             ai_data: Dict[str, Any]) -> Dict[str, Any]:
        """Add AI-generated features to a training record."""
        record["ai_features"] = {
            "ai_classification": ai_data.get('classification', 'unknown'),
            "ai_confidence": ai_data.get('confidence', 0.0),
            "ai_insights": ai_data.get('insights', []),
            "security_assessment": ai_data.get('security_assessment', {}),
            "recommendations": ai_data.get('recommendations', [])
        }
        
        return record
    
    async def _assess_quality(self, training_set: Dict[str, Any]) -> Dict[str, Any]:
        """Assess the quality of a training set."""
        records = training_set.get('records', [])
        
        quality_metrics = {
            "completeness": 0.0,
            "consistency": 0.0,
            "diversity": 0.0,
            "coverage": {}
        }
        
        if not records:
            return quality_metrics
        
        # Completeness: records with all required fields
        complete_records = sum(
            1 for record in records 
            if self.formatter.validate_output(record)
        )
        quality_metrics["completeness"] = complete_records / len(records)
        
        # Diversity: variety of device types and record types
        record_types = set(record.get('record_type', 'unknown') for record in records)
        device_types = set(
            record.get('device_type', 'unknown') for record in records 
            if record.get('record_type') == 'device_classification'
        )
        
        quality_metrics["diversity"] = len(record_types) + len(device_types)
        quality_metrics["coverage"] = {
            "record_types": list(record_types),
            "device_types": list(device_types),
            "has_ai_features": sum(1 for r in records if 'ai_features' in r),
            "has_location_data": sum(1 for r in records if 'location_features' in r)
        }
        
        return quality_metrics
    
    async def _create_device_classification_dataset(self, training_sets: List[Dict[str, Any]],
                                                  fine_tuning_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create dataset optimized for device classification fine-tuning."""
        examples = []
        
        for training_set in training_sets:
            records = training_set.get('records', [])
            
            for record in records:
                if record.get('record_type') == 'device_classification':
                    # Create text-based training example
                    features = record.get('features', {})
                    device_type = record.get('device_type', 'unknown')
                    
                    # Create input text describing the device
                    input_text = self._device_features_to_text(features, record)
                    
                    example = {
                        "input": input_text,
                        "output": device_type,
                        "confidence": record.get('confidence', 0.0),
                        "metadata": {
                            "device_id": record.get('device_id', 'unknown'),
                            "source_record": record.get('metadata', {})
                        }
                    }
                    
                    examples.append(example)
        
        fine_tuning_data["training_examples"] = examples
        fine_tuning_data["metadata"]["task_specific_info"] = {
            "target_classes": list(set(ex["output"] for ex in examples)),
            "feature_types": ["network", "port", "hostname", "temporal"]
        }
        
        return fine_tuning_data
    
    async def _create_network_analysis_dataset(self, training_sets: List[Dict[str, Any]],
                                             fine_tuning_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create dataset for network topology analysis fine-tuning."""
        examples = []
        
        for training_set in training_sets:
            records = training_set.get('records', [])
            
            for record in records:
                if record.get('record_type') == 'network_topology_analysis':
                    # Create network analysis example
                    topology_features = record.get('topology_features', {})
                    
                    input_text = self._network_features_to_text(topology_features, record)
                    output_analysis = self._create_network_analysis_output(record)
                    
                    example = {
                        "input": input_text,
                        "output": output_analysis,
                        "metadata": {
                            "network_id": record.get('network_id', 'unknown'),
                            "device_count": topology_features.get('total_devices', 0)
                        }
                    }
                    
                    examples.append(example)
        
        fine_tuning_data["training_examples"] = examples
        return fine_tuning_data
    
    async def _create_iot_identification_dataset(self, training_sets: List[Dict[str, Any]],
                                               fine_tuning_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create dataset for IoT device identification fine-tuning."""
        examples = []
        iot_device_types = ['iot_sensor', 'smart_home', 'security_camera']
        
        for training_set in training_sets:
            records = training_set.get('records', [])
            
            for record in records:
                if (record.get('record_type') == 'device_classification' and 
                    record.get('device_type') in iot_device_types):
                    
                    features = record.get('features', {})
                    input_text = self._iot_features_to_text(features, record)
                    
                    example = {
                        "input": input_text,
                        "output": f"IoT Device: {record.get('device_type', 'unknown')}",
                        "iot_specific": True,
                        "metadata": record.get('metadata', {})
                    }
                    
                    examples.append(example)
        
        fine_tuning_data["training_examples"] = examples
        return fine_tuning_data
    
    async def _create_generic_dataset(self, training_sets: List[Dict[str, Any]],
                                    fine_tuning_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create generic fine-tuning dataset."""
        examples = []
        
        for training_set in training_sets:
            records = training_set.get('records', [])
            
            for record in records:
                example = {
                    "input": str(record.get('features', {})),
                    "output": str(record.get('device_type') or record.get('network_id', 'unknown')),
                    "record_type": record.get('record_type', 'unknown'),
                    "metadata": record.get('metadata', {})
                }
                
                examples.append(example)
        
        fine_tuning_data["training_examples"] = examples
        return fine_tuning_data
    
    def _device_features_to_text(self, features: Dict[str, Any], record: Dict[str, Any]) -> str:
        """Convert device features to natural language text."""
        text_parts = []
        
        # Basic network information
        if features.get('has_hostname'):
            text_parts.append("Device has a configured hostname")
        
        if features.get('has_mac_address'):
            text_parts.append("MAC address is available")
        
        # Port information
        port_count = features.get('port_count', 0)
        if port_count > 0:
            text_parts.append(f"Device has {port_count} open ports")
            
            if features.get('has_web_ports'):
                text_parts.append("Web services are running")
            
            if features.get('has_ssh'):
                text_parts.append("SSH access is available")
            
            if features.get('has_iot_ports'):
                text_parts.append("IoT protocols detected")
        
        # Persistence information
        if features.get('is_persistent'):
            discovery_count = features.get('discovery_count', 1)
            text_parts.append(f"Device seen {discovery_count} times")
        
        return ". ".join(text_parts) + "."
    
    def _network_features_to_text(self, topology_features: Dict[str, Any], record: Dict[str, Any]) -> str:
        """Convert network topology features to natural language text."""
        text_parts = []
        
        device_count = topology_features.get('total_devices', 0)
        text_parts.append(f"Network contains {device_count} devices")
        
        if topology_features.get('has_gateway'):
            text_parts.append("Network gateway is present")
        
        device_diversity = topology_features.get('device_diversity', 0)
        text_parts.append(f"Network has {device_diversity} different device types")
        
        return ". ".join(text_parts) + "."
    
    def _iot_features_to_text(self, features: Dict[str, Any], record: Dict[str, Any]) -> str:
        """Convert IoT-specific features to natural language text."""
        text_parts = ["This appears to be an IoT device"]
        
        if features.get('has_iot_ports'):
            text_parts.append("IoT communication protocols detected")
        
        if features.get('port_count', 0) < 3:
            text_parts.append("Limited port exposure typical of IoT devices")
        
        if not features.get('has_web_ports'):
            text_parts.append("No web interface detected")
        
        return ". ".join(text_parts) + "."
    
    def _create_network_analysis_output(self, record: Dict[str, Any]) -> str:
        """Create network analysis output text."""
        topology_features = record.get('topology_features', {})
        device_count = topology_features.get('total_devices', 0)
        
        if device_count < 5:
            return "Small network topology"
        elif device_count < 20:
            return "Medium network topology"
        else:
            return "Large network topology"
    
    def _count_record_types(self, records: List[Dict[str, Any]]) -> Dict[str, int]:
        """Count different record types in the dataset."""
        counts = {}
        for record in records:
            record_type = record.get('record_type', 'unknown')
            counts[record_type] = counts.get(record_type, 0) + 1
        return counts
