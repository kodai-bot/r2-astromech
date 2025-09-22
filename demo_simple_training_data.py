#!/usr/bin/env python3
"""
Simple R2 Training Data Generation Demo

A simplified demo that shows how R2 can generate training datasets
from existing network discovery data without complex dependencies.

This creates JSON and GeoJSON training data suitable for fine-tuning.
"""

import json
import os
import sys
from datetime import datetime
from typing import Dict, List, Any

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

def load_discovery_data():
    """Load existing discovery data from the device database."""
    print("📊 Loading discovery data...")
    
    # Load device database
    device_db_path = "data/devices/device_database.json"
    network_db_path = "data/devices/device_database_networks.json"
    
    devices = {}
    networks = {}
    
    try:
        if os.path.exists(device_db_path):
            with open(device_db_path, 'r') as f:
                devices = json.load(f)
        
        if os.path.exists(network_db_path):
            with open(network_db_path, 'r') as f:
                networks = json.load(f)
        
        print(f"✅ Loaded {len(devices)} devices and {len(networks)} networks")
        return devices, networks
        
    except Exception as e:
        print(f"❌ Failed to load discovery data: {e}")
        return {}, {}

def format_device_for_training(device_id: str, device_data: Dict[str, Any]) -> Dict[str, Any]:
    """Format a device record for training."""
    
    # Extract features
    features = {
        'has_hostname': device_data.get('hostname', 'unknown') != 'unknown',
        'has_mac': device_data.get('mac', 'unknown') != 'unknown',
        'port_count': len(device_data.get('open_ports', [])),
        'has_web_ports': any(port in [80, 443, 8080] for port in device_data.get('open_ports', [])),
        'has_ssh': 22 in device_data.get('open_ports', []),
        'discovery_count': device_data.get('discovery_count', 1),
        'is_persistent': device_data.get('discovery_count', 1) > 1
    }
    
    # Simple device classification based on patterns
    hostname = device_data.get('hostname', '').lower()
    open_ports = device_data.get('open_ports', [])
    
    device_type = 'unknown'
    confidence = 0.5
    
    if 'router' in hostname or 'gateway' in hostname:
        device_type = 'router'
        confidence = 0.8
    elif any(port in [80, 443] for port in open_ports) and 22 in open_ports:
        device_type = 'router'
        confidence = 0.7
    elif 'printer' in hostname:
        device_type = 'printer'
        confidence = 0.9
    elif len(open_ports) < 3 and any(port in [1883, 8883] for port in open_ports):
        device_type = 'iot_sensor'
        confidence = 0.6
    
    # Create training record
    training_record = {
        "record_type": "device_classification",
        "device_id": f"device_{hash(device_id) % 10000:04d}",  # Anonymized
        "features": features,
        "device_type": device_type,
        "confidence": confidence,
        "metadata": {
            "format_version": "1.0",
            "created_at": datetime.now().isoformat(),
            "source_timestamp": device_data.get('timestamp', ''),
            "anonymized": True
        }
    }
    
    # Add location for demo (synthetic)
    if device_id:
        ip_hash = hash(device_id) % 1000
        lat = 40.7128 + (ip_hash / 1000.0 - 0.5) * 0.1  # NYC area
        lon = -74.0060 + (ip_hash / 1000.0 - 0.5) * 0.1
        
        training_record["location_features"] = {
            "type": "inferred",
            "source": "network_subnet",
            "accuracy": "low",
            "coordinates": [lon, lat]  # GeoJSON format
        }
    
    return training_record

def format_network_for_training(network_id: str, network_data: Dict[str, Any]) -> Dict[str, Any]:
    """Format a network record for training."""
    
    device_signatures = network_data.get('device_signatures', [])
    
    # Extract topology features
    topology_features = {
        'total_devices': len(device_signatures),
        'has_gateway': bool(network_data.get('gateway_ip')),
        'device_diversity': len(set(d.get('device_type', 'unknown') for d in device_signatures)),
        'manufacturer_diversity': len(set(d.get('manufacturer', 'unknown') for d in device_signatures))
    }
    
    # Create training record
    training_record = {
        "record_type": "network_topology_analysis",
        "network_id": f"network_{hash(network_id) % 10000:04d}",  # Anonymized
        "network_range": "anonymized_network/24",
        "topology_features": topology_features,
        "device_count": len(device_signatures),
        "metadata": {
            "format_version": "1.0",
            "created_at": datetime.now().isoformat(),
            "scan_timestamp": network_data.get('scan_timestamp', ''),
            "anonymized": True
        }
    }
    
    return training_record

def create_geojson_feature(record: Dict[str, Any]) -> Dict[str, Any]:
    """Convert a training record to a GeoJSON feature."""
    location_features = record.get('location_features', {})
    coordinates = location_features.get('coordinates')
    
    if not coordinates:
        return None
    
    feature = {
        "type": "Feature",
        "geometry": {
            "type": "Point",
            "coordinates": coordinates
        },
        "properties": {
            "device_id": record.get('device_id', 'unknown'),
            "device_type": record.get('device_type', 'unknown'),
            "confidence": record.get('confidence', 0.0),
            "record_type": record.get('record_type', 'unknown'),
            "has_hostname": record.get('features', {}).get('has_hostname', False),
            "port_count": record.get('features', {}).get('port_count', 0),
            "is_persistent": record.get('features', {}).get('is_persistent', False)
        }
    }
    
    return feature

def create_fine_tuning_examples(training_records: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Create fine-tuning examples for device classification."""
    examples = []
    
    for record in training_records:
        if record.get('record_type') != 'device_classification':
            continue
        
        features = record.get('features', {})
        device_type = record.get('device_type', 'unknown')
        
        # Create natural language description
        description_parts = []
        
        if features.get('has_hostname'):
            description_parts.append("Device has a configured hostname")
        
        port_count = features.get('port_count', 0)
        if port_count > 0:
            description_parts.append(f"Device has {port_count} open ports")
            
            if features.get('has_web_ports'):
                description_parts.append("Web services are running")
            
            if features.get('has_ssh'):
                description_parts.append("SSH access is available")
        
        if features.get('is_persistent'):
            description_parts.append("Device appears consistently in scans")
        
        input_text = ". ".join(description_parts) + "."
        
        example = {
            "input": input_text,
            "output": device_type,
            "confidence": record.get('confidence', 0.0),
            "metadata": record.get('metadata', {})
        }
        
        examples.append(example)
    
    return examples

def main():
    """Main demo function."""
    print("🤖 R2 Simple Training Data Generation Demo")
    print("=" * 60)
    
    # Create output directory
    output_dir = "data/training_sets"
    os.makedirs(output_dir, exist_ok=True)
    
    # Load discovery data
    devices, networks = load_discovery_data()
    
    if not devices and not networks:
        print("❌ No discovery data found")
        return 1
    
    # Generate training records
    print("\n🏗️  Generating training records...")
    training_records = []
    
    # Process devices
    for device_id, device_data in devices.items():
        record = format_device_for_training(device_id, device_data)
        training_records.append(record)
    
    # Process networks
    for network_id, network_data in networks.items():
        record = format_network_for_training(network_id, network_data)
        training_records.append(record)
    
    print(f"✅ Generated {len(training_records)} training records")
    
    # Create main training dataset
    training_dataset = {
        "dataset_info": {
            "generated_at": datetime.now().isoformat(),
            "format_version": "1.0",
            "total_records": len(training_records),
            "anonymized": True,
            "source": "R2-D2 Astromech Network Discovery"
        },
        "records": training_records
    }
    
    # Export JSON
    print("\n💾 Exporting training data...")
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    json_path = os.path.join(output_dir, f"r2_training_data_{timestamp}.json")
    with open(json_path, 'w') as f:
        json.dump(training_dataset, f, indent=2, default=str)
    print(f"✅ JSON export: {json_path}")
    
    # Export GeoJSON
    geojson_features = []
    for record in training_records:
        feature = create_geojson_feature(record)
        if feature:
            geojson_features.append(feature)
    
    if geojson_features:
        geojson_data = {
            "type": "FeatureCollection",
            "metadata": {
                "generated_by": "R2-D2 Astromech Unit",
                "created_at": datetime.now().isoformat(),
                "total_features": len(geojson_features)
            },
            "features": geojson_features
        }
        
        geojson_path = os.path.join(output_dir, f"r2_spatial_data_{timestamp}.geojson")
        with open(geojson_path, 'w') as f:
            json.dump(geojson_data, f, indent=2, default=str)
        print(f"✅ GeoJSON export: {geojson_path}")
    
    # Create fine-tuning dataset
    print("\n🎓 Creating fine-tuning dataset...")
    fine_tuning_examples = create_fine_tuning_examples(training_records)
    
    # Split into training and validation
    split_point = int(len(fine_tuning_examples) * 0.8)
    
    fine_tuning_dataset = {
        "task_type": "device_classification",
        "created_at": datetime.now().isoformat(),
        "total_examples": len(fine_tuning_examples),
        "training_examples": fine_tuning_examples[:split_point],
        "validation_examples": fine_tuning_examples[split_point:],
        "metadata": {
            "format": "text_classification",
            "target_classes": list(set(ex["output"] for ex in fine_tuning_examples)),
            "source": "R2-D2 Network Discovery"
        }
    }
    
    finetune_path = os.path.join(output_dir, f"r2_finetune_device_classification_{timestamp}.json")
    with open(finetune_path, 'w') as f:
        json.dump(fine_tuning_dataset, f, indent=2, default=str)
    print(f"✅ Fine-tuning dataset: {finetune_path}")
    print(f"   Training examples: {len(fine_tuning_dataset['training_examples'])}")
    print(f"   Validation examples: {len(fine_tuning_dataset['validation_examples'])}")
    
    # Create metadata
    metadata = {
        "generation_info": {
            "generated_at": datetime.now().isoformat(),
            "source_devices": len(devices),
            "source_networks": len(networks),
            "total_training_records": len(training_records)
        },
        "files_created": [
            {"path": json_path, "type": "json", "description": "Complete training dataset"},
            {"path": geojson_path, "type": "geojson", "description": "Spatial training data"},
            {"path": finetune_path, "type": "json", "description": "Fine-tuning ready dataset"}
        ],
        "statistics": {
            "device_types": {},
            "record_types": {}
        }
    }
    
    # Calculate statistics
    for record in training_records:
        record_type = record.get('record_type', 'unknown')
        metadata["statistics"]["record_types"][record_type] = metadata["statistics"]["record_types"].get(record_type, 0) + 1
        
        if record_type == 'device_classification':
            device_type = record.get('device_type', 'unknown')
            metadata["statistics"]["device_types"][device_type] = metadata["statistics"]["device_types"].get(device_type, 0) + 1
    
    metadata_path = os.path.join(output_dir, f"training_metadata_{timestamp}.json")
    with open(metadata_path, 'w') as f:
        json.dump(metadata, f, indent=2, default=str)
    print(f"✅ Metadata: {metadata_path}")
    
    # Summary
    print("\n" + "=" * 60)
    print("🎉 R2 Training Data Generation Complete!")
    print("=" * 60)
    print(f"\n📁 Output directory: {output_dir}")
    print(f"📊 Generated {len(training_records)} training records")
    print(f"🌍 Created {len(geojson_features)} spatial features")
    print(f"🎓 Prepared {len(fine_tuning_examples)} fine-tuning examples")
    
    print("\n🚀 Ready for:")
    print("  - Machine learning model training")
    print("  - Language model fine-tuning")
    print("  - Geospatial analysis")
    print("  - IoT device classification")
    
    print(f"\n📈 Device type distribution:")
    for device_type, count in metadata["statistics"]["device_types"].items():
        print(f"  - {device_type}: {count}")
    
    return 0

if __name__ == "__main__":
    exit(main())
