"""
Training Data Exporter

This module handles exporting training data to various formats including
JSON and GeoJSON for machine learning and geospatial analysis.
"""

import json
import os
import asyncio
from typing import Dict, List, Any, Optional
from datetime import datetime
import logging

from .interfaces import ITrainingDataExporter, TrainingDataConfig
logger = logging.getLogger("training.data_exporter")


class TrainingDataExporter(ITrainingDataExporter):
    """
    Exports training data to JSON and GeoJSON formats.
    
    This exporter handles the conversion of structured training data
    into files suitable for machine learning frameworks and GIS applications.
    """
    
    def __init__(self, config: TrainingDataConfig):
        """
        Initialize the training data exporter.
        
        Args:
            config: Training data configuration
        """
        self.config = config
        self.logger = logger
        self._ensure_output_directory()
        
        logger.info(f"Training data exporter initialized with output directory: {config.output_directory}")
    
    async def export_json(self, data: Dict[str, Any], output_path: str) -> bool:
        """
        Export training data as JSON.
        
        Args:
            data: Training data to export
            output_path: Path to save the JSON file
            
        Returns:
            bool: True if export successful
        """
        try:
            # Ensure output directory exists
            os.makedirs(os.path.dirname(output_path), exist_ok=True)
            
            # Add export metadata
            export_data = {
                "export_info": {
                    "format": "json",
                    "version": self.config.format_version,
                    "exported_at": datetime.now().isoformat(),
                    "anonymized": self.config.anonymize_data,
                    "record_count": self._count_records(data)
                },
                "data": data
            }
            
            # Write JSON file
            with open(output_path, 'w') as f:
                json.dump(export_data, f, indent=2, default=str)
            
            logger.info(f"Successfully exported {self._count_records(data)} records to {output_path}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to export JSON to {output_path}: {e}")
            return False
    
    async def export_geojson(self, data: Dict[str, Any], output_path: str) -> bool:
        """
        Export spatial training data as GeoJSON.
        
        Args:
            data: Training data with spatial information
            output_path: Path to save the GeoJSON file
            
        Returns:
            bool: True if export successful
        """
        try:
            # Ensure output directory exists
            os.makedirs(os.path.dirname(output_path), exist_ok=True)
            
            # Convert to GeoJSON format
            geojson_data = self._convert_to_geojson(data)
            
            # Write GeoJSON file
            with open(output_path, 'w') as f:
                json.dump(geojson_data, f, indent=2, default=str)
            
            feature_count = len(geojson_data.get('features', []))
            logger.info(f"Successfully exported {feature_count} features to GeoJSON: {output_path}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to export GeoJSON to {output_path}: {e}")
            return False
    
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
        exported_files = []
        
        try:
            # Ensure output directory exists
            os.makedirs(output_dir, exist_ok=True)
            
            # Export each dataset
            for i, dataset in enumerate(datasets):
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                filename = f"training_data_{timestamp}_{i+1:03d}.{format_type}"
                output_path = os.path.join(output_dir, filename)
                
                if format_type == 'json':
                    success = await self.export_json(dataset, output_path)
                elif format_type == 'geojson':
                    success = await self.export_geojson(dataset, output_path)
                else:
                    logger.error(f"Unsupported format type: {format_type}")
                    continue
                
                if success:
                    exported_files.append(output_path)
                    
                # Add small delay to prevent overwhelming the filesystem
                await asyncio.sleep(0.1)
            
            logger.info(f"Batch export completed: {len(exported_files)}/{len(datasets)} files exported")
            return exported_files
            
        except Exception as e:
            logger.error(f"Batch export failed: {e}")
            return exported_files
    
    def export_training_metadata(self, datasets: List[Dict[str, Any]], 
                               output_path: str) -> bool:
        """
        Export metadata about the training datasets.
        
        Args:
            datasets: List of training datasets
            output_path: Path to save metadata
            
        Returns:
            bool: True if export successful
        """
        try:
            metadata = {
                "dataset_info": {
                    "total_datasets": len(datasets),
                    "created_at": datetime.now().isoformat(),
                    "format_version": self.config.format_version,
                    "anonymized": self.config.anonymize_data
                },
                "statistics": self._calculate_dataset_statistics(datasets),
                "quality_metrics": self._calculate_quality_metrics(datasets),
                "format_details": {
                    "supported_record_types": list(self.config.required_fields.keys()),
                    "required_fields": self.config.required_fields,
                    "max_records_per_file": self.config.max_records_per_file
                }
            }
            
            # Ensure output directory exists
            os.makedirs(os.path.dirname(output_path), exist_ok=True)
            
            with open(output_path, 'w') as f:
                json.dump(metadata, f, indent=2, default=str)
            
            logger.info(f"Training metadata exported to {output_path}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to export training metadata: {e}")
            return False
    
    def _convert_to_geojson(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Convert training data to GeoJSON format.
        
        Args:
            data: Training data
            
        Returns:
            Dict in GeoJSON format
        """
        geojson = {
            "type": "FeatureCollection",
            "metadata": {
                "generated_by": "R2-D2 Astromech Unit",
                "format_version": self.config.format_version,
                "created_at": datetime.now().isoformat(),
                "anonymized": self.config.anonymize_data
            },
            "features": []
        }
        
        # Handle different data structures
        if isinstance(data, dict):
            if 'data' in data:
                # Handle wrapped data format
                records = data['data']
            else:
                # Handle single record
                records = [data]
        elif isinstance(data, list):
            # Handle list of records
            records = data
        else:
            logger.warning("Unexpected data format for GeoJSON conversion")
            return geojson
        
        # Convert records to GeoJSON features
        for record in records:
            if isinstance(record, dict):
                feature = self._record_to_geojson_feature(record)
                if feature:
                    geojson["features"].append(feature)
        
        return geojson
    
    def _record_to_geojson_feature(self, record: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Convert a single training record to a GeoJSON feature.
        
        Args:
            record: Training record
            
        Returns:
            GeoJSON feature or None if no spatial data
        """
        # Extract location data
        location_features = record.get('location_features', {})
        coordinates = location_features.get('coordinates')
        
        if not coordinates or len(coordinates) != 2:
            # No valid coordinates, skip this record for GeoJSON
            return None
        
        # Create GeoJSON feature
        feature = {
            "type": "Feature",
            "geometry": {
                "type": "Point",
                "coordinates": coordinates  # [longitude, latitude]
            },
            "properties": {}
        }
        
        # Add all non-location data as properties
        for key, value in record.items():
            if key != 'location_features':
                # Flatten nested structures for GeoJSON properties
                if isinstance(value, dict):
                    for sub_key, sub_value in value.items():
                        feature["properties"][f"{key}_{sub_key}"] = sub_value
                else:
                    feature["properties"][key] = value
        
        # Add location metadata
        feature["properties"]["location_type"] = location_features.get('type', 'unknown')
        feature["properties"]["location_source"] = location_features.get('source', 'unknown')
        feature["properties"]["location_accuracy"] = location_features.get('accuracy', 'unknown')
        
        return feature
    
    def _count_records(self, data: Any) -> int:
        """Count the number of records in the data."""
        if isinstance(data, dict):
            if 'data' in data:
                return self._count_records(data['data'])
            else:
                return 1
        elif isinstance(data, list):
            return len(data)
        else:
            return 1
    
    def _calculate_dataset_statistics(self, datasets: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Calculate statistics across all datasets."""
        stats = {
            "total_records": 0,
            "record_types": {},
            "device_types": {},
            "network_count": 0
        }
        
        for dataset in datasets:
            # Count records
            record_count = self._count_records(dataset)
            stats["total_records"] += record_count
            
            # Analyze record types
            records = self._extract_records_from_dataset(dataset)
            for record in records:
                record_type = record.get('record_type', 'unknown')
                stats["record_types"][record_type] = stats["record_types"].get(record_type, 0) + 1
                
                # Count device types for device classification records
                if record_type == "device_classification":
                    device_type = record.get('device_type', 'unknown')
                    stats["device_types"][device_type] = stats["device_types"].get(device_type, 0) + 1
                
                # Count networks
                elif record_type == "network_topology_analysis":
                    stats["network_count"] += 1
        
        return stats
    
    def _calculate_quality_metrics(self, datasets: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Calculate quality metrics for the datasets."""
        metrics = {
            "completeness": 0.0,
            "validity": 0.0,
            "consistency": 0.0,
            "anonymization_rate": 0.0
        }
        
        total_records = 0
        valid_records = 0
        complete_records = 0
        anonymized_records = 0
        
        for dataset in datasets:
            records = self._extract_records_from_dataset(dataset)
            
            for record in records:
                total_records += 1
                
                # Check validity (has required fields)
                record_type = record.get('record_type', 'unknown')
                required_fields = self.config.required_fields.get(record_type, [])
                
                if all(field in record for field in required_fields):
                    valid_records += 1
                
                # Check completeness (no empty values in key fields)
                key_fields = ['device_id', 'features', 'metadata']
                if all(record.get(field) for field in key_fields if field in record):
                    complete_records += 1
                
                # Check anonymization
                metadata = record.get('metadata', {})
                if metadata.get('anonymized', False):
                    anonymized_records += 1
        
        if total_records > 0:
            metrics["validity"] = valid_records / total_records
            metrics["completeness"] = complete_records / total_records
            metrics["anonymization_rate"] = anonymized_records / total_records
            metrics["consistency"] = 1.0  # Placeholder - could add more sophisticated checks
        
        return metrics
    
    def _extract_records_from_dataset(self, dataset: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Extract individual records from a dataset."""
        if 'data' in dataset:
            data = dataset['data']
        else:
            data = dataset
        
        if isinstance(data, list):
            return data
        elif isinstance(data, dict):
            return [data]
        else:
            return []
    
    def _ensure_output_directory(self) -> None:
        """Ensure the output directory exists."""
        try:
            os.makedirs(self.config.output_directory, exist_ok=True)
            logger.debug(f"Output directory ensured: {self.config.output_directory}")
        except Exception as e:
            logger.error(f"Failed to create output directory {self.config.output_directory}: {e}")
            raise
    
    async def create_training_manifest(self, exported_files: List[str], 
                                     output_path: str) -> bool:
        """
        Create a manifest file listing all exported training files.
        
        Args:
            exported_files: List of exported file paths
            output_path: Path to save the manifest
            
        Returns:
            bool: True if manifest created successfully
        """
        try:
            manifest = {
                "manifest_info": {
                    "created_at": datetime.now().isoformat(),
                    "total_files": len(exported_files),
                    "format_version": self.config.format_version
                },
                "files": []
            }
            
            for file_path in exported_files:
                try:
                    file_stats = os.stat(file_path)
                    file_info = {
                        "path": file_path,
                        "filename": os.path.basename(file_path),
                        "size_bytes": file_stats.st_size,
                        "format": "geojson" if file_path.endswith('.geojson') else "json",
                        "created_at": datetime.fromtimestamp(file_stats.st_ctime).isoformat()
                    }
                    manifest["files"].append(file_info)
                except Exception as e:
                    logger.warning(f"Could not get stats for file {file_path}: {e}")
            
            # Save manifest
            with open(output_path, 'w') as f:
                json.dump(manifest, f, indent=2, default=str)
            
            logger.info(f"Training manifest created: {output_path}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to create training manifest: {e}")
            return False
