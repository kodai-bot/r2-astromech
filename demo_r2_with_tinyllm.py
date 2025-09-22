#!/usr/bin/env python3
"""
R2 Training Data Generation with TinyLLM Integration

This demo shows R2's full capability by integrating the TinyLLM model
for AI-powered device analysis and enhanced training data generation.

The output combines network discovery with AI analysis to create
higher-quality training datasets.

Author: Dylan G Foley  
Created: September 2025
"""

import asyncio
import json
import os
import sys
from datetime import datetime
from typing import Dict, List, Any, Optional

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

# Import TinyLLM directly
from modules.ai.models.tinyllm_model import TinyLLMModel

def load_discovery_data():
    """Load existing discovery data from the device database."""
    print("📊 Loading discovery data...")
    
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

async def setup_tinyllm():
    """Set up the TinyLLM model."""
    print("🧠 Loading TinyLLM model...")
    
    try:
        model_config = {
            'model_path': 'weiser/82M-0.4',
            'device': 'cpu',
            'max_length': 128,
            'temperature': 0.6,
            'iot_mode': True,
            'sensor_data_context': True
        }
        
        tinyllm = TinyLLMModel(model_config)
        await tinyllm.initialize()
        
        if tinyllm.is_loaded:
            print("✅ TinyLLM model loaded successfully")
            return tinyllm
        else:
            print("⚠️  TinyLLM model failed to load")
            return None
            
    except Exception as e:
        print(f"❌ TinyLLM setup failed: {e}")
        return None

async def analyze_device_with_ai(device_data: Dict[str, Any], tinyllm) -> Dict[str, Any]:
    """Analyze a device using TinyLLM."""
    try:
        hostname = device_data.get('hostname', 'unknown')
        ip = device_data.get('ip', 'unknown')
        open_ports = device_data.get('open_ports', [])
        manufacturer = device_data.get('manufacturer', 'unknown')
        
        # Create analysis prompt
        prompt = f"""Analyze this network device:
IP: {ip}
Hostname: {hostname}  
Manufacturer: {manufacturer}
Open Ports: {open_ports}

What type of device is this? Consider IoT sensors, routers, printers, computers, cameras, etc."""
        
        # Get AI response
        ai_response = await tinyllm.generate_response(prompt)
        
        # Parse the response for device classification
        device_type = extract_device_type_from_response(ai_response, device_data)
        confidence = calculate_confidence(ai_response, device_data)
        
        return {
            'ai_classification': device_type,
            'ai_confidence': confidence,
            'ai_reasoning': ai_response[:200] + "..." if len(ai_response) > 200 else ai_response,
            'security_assessment': assess_security(device_data, ai_response),
            'recommendations': generate_recommendations(device_type, device_data)
        }
        
    except Exception as e:
        print(f"⚠️  AI analysis failed for device: {e}")
        return {
            'ai_classification': 'unknown',
            'ai_confidence': 0.0,
            'ai_reasoning': 'Analysis failed',
            'security_assessment': {'risk_level': 'unknown'},
            'recommendations': []
        }

def extract_device_type_from_response(response: str, device_data: Dict[str, Any]) -> str:
    """Extract device type from AI response."""
    response_lower = response.lower()
    
    # AI-based classification with fallback to rule-based
    if any(word in response_lower for word in ['router', 'gateway', 'access point']):
        return 'router'
    elif any(word in response_lower for word in ['sensor', 'iot', 'temperature', 'humidity']):
        return 'iot_sensor'
    elif any(word in response_lower for word in ['camera', 'surveillance', 'webcam']):
        return 'security_camera'
    elif any(word in response_lower for word in ['printer', 'print server']):
        return 'printer'
    elif any(word in response_lower for word in ['computer', 'pc', 'workstation', 'laptop']):
        return 'computer'
    elif any(word in response_lower for word in ['switch', 'network switch']):
        return 'switch'
    elif any(word in response_lower for word in ['nas', 'storage', 'file server']):
        return 'nas'
    elif any(word in response_lower for word in ['smart home', 'alexa', 'echo', 'nest']):
        return 'smart_home'
    else:
        # Fallback to rule-based classification
        hostname = device_data.get('hostname', '').lower()
        open_ports = device_data.get('open_ports', [])
        
        if 'router' in hostname or ('gateway' in hostname and 22 in open_ports):
            return 'router'
        elif len(open_ports) < 3 and any(port in [1883, 8883, 5683] for port in open_ports):
            return 'iot_sensor'
        elif 'printer' in hostname or 631 in open_ports:
            return 'printer'
        else:
            return 'unknown'

def calculate_confidence(ai_response: str, device_data: Dict[str, Any]) -> float:
    """Calculate confidence based on AI response and device characteristics."""
    confidence = 0.5  # Base confidence
    
    response_lower = ai_response.lower()
    
    # Higher confidence for definitive statements
    if any(phrase in response_lower for phrase in ['this is a', 'appears to be', 'likely a']):
        confidence += 0.2
    
    # Higher confidence if multiple indicators align
    hostname = device_data.get('hostname', '').lower()
    open_ports = device_data.get('open_ports', [])
    
    if hostname != 'unknown' and hostname in response_lower:
        confidence += 0.1
    
    if open_ports and any(str(port) in response_lower for port in open_ports):
        confidence += 0.1
    
    # Cap at 0.9 for AI-based classification
    return min(confidence, 0.9)

def assess_security(device_data: Dict[str, Any], ai_response: str) -> Dict[str, Any]:
    """Assess security characteristics of the device."""
    risk_level = 'low'
    vulnerabilities = []
    recommendations = []
    
    open_ports = device_data.get('open_ports', [])
    hostname = device_data.get('hostname', 'unknown')
    
    # Check for common security concerns
    if 23 in open_ports:  # Telnet
        risk_level = 'high'
        vulnerabilities.append('Telnet service exposed')
        recommendations.append('Disable Telnet, use SSH instead')
    
    if 21 in open_ports:  # FTP
        risk_level = 'medium' if risk_level == 'low' else risk_level
        vulnerabilities.append('FTP service exposed')
        recommendations.append('Consider secure FTP alternatives')
    
    if len(open_ports) > 10:
        risk_level = 'medium' if risk_level == 'low' else risk_level
        vulnerabilities.append('Many open ports detected')
        recommendations.append('Audit and close unnecessary ports')
    
    if hostname == 'unknown':
        vulnerabilities.append('Device not properly identified')
        recommendations.append('Investigate device identity and purpose')
    
    return {
        'risk_level': risk_level,
        'vulnerabilities': vulnerabilities,
        'recommendations': recommendations,
        'open_port_count': len(open_ports)
    }

def generate_recommendations(device_type: str, device_data: Dict[str, Any]) -> List[str]:
    """Generate device-specific recommendations."""
    recommendations = []
    
    if device_type == 'iot_sensor':
        recommendations.extend([
            'Monitor for unusual network activity',
            'Ensure device firmware is up to date',
            'Consider network segmentation for IoT devices'
        ])
    elif device_type == 'router':
        recommendations.extend([
            'Ensure strong admin passwords',
            'Keep firmware updated',
            'Monitor for unauthorized configuration changes'
        ])
    elif device_type == 'security_camera':
        recommendations.extend([
            'Change default passwords',
            'Enable encryption if available',
            'Monitor for unauthorized access'
        ])
    elif device_type == 'computer':
        recommendations.extend([
            'Ensure endpoint protection is installed',
            'Keep operating system updated',
            'Monitor for suspicious activity'
        ])
    else:
        recommendations.extend([
            'Investigate device purpose and legitimacy',
            'Monitor network traffic patterns',
            'Apply security best practices'
        ])
    
    return recommendations

def format_device_for_training_with_ai(device_id: str, device_data: Dict[str, Any], 
                                     ai_analysis: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """Format a device record for training with AI enhancement."""
    
    # Basic features
    features = {
        'has_hostname': device_data.get('hostname', 'unknown') != 'unknown',
        'has_mac': device_data.get('mac', 'unknown') != 'unknown',
        'port_count': len(device_data.get('open_ports', [])),
        'has_web_ports': any(port in [80, 443, 8080] for port in device_data.get('open_ports', [])),
        'has_ssh': 22 in device_data.get('open_ports', []),
        'has_telnet': 23 in device_data.get('open_ports', []),
        'has_ftp': 21 in device_data.get('open_ports', []),
        'has_iot_ports': any(port in [1883, 8883, 5683] for port in device_data.get('open_ports', [])),
        'discovery_count': device_data.get('discovery_count', 1),
        'is_persistent': device_data.get('discovery_count', 1) > 1
    }
    
    # Use AI classification if available, otherwise fallback
    if ai_analysis:
        device_type = ai_analysis.get('ai_classification', 'unknown')
        confidence = ai_analysis.get('ai_confidence', 0.5)
    else:
        # Simple rule-based fallback
        device_type = 'unknown'
        confidence = 0.3
    
    # Create enhanced training record
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
            "anonymized": True,
            "ai_enhanced": ai_analysis is not None
        }
    }
    
    # Add AI analysis features if available
    if ai_analysis:
        training_record["ai_features"] = {
            "ai_reasoning": ai_analysis.get('ai_reasoning', ''),
            "security_assessment": ai_analysis.get('security_assessment', {}),
            "recommendations": ai_analysis.get('recommendations', []),
            "ai_confidence": ai_analysis.get('ai_confidence', 0.0)
        }
    
    # Add synthetic location
    if device_id:
        ip_hash = hash(device_id) % 1000
        lat = 40.7128 + (ip_hash / 1000.0 - 0.5) * 0.1
        lon = -74.0060 + (ip_hash / 1000.0 - 0.5) * 0.1
        
        training_record["location_features"] = {
            "type": "inferred",
            "source": "network_subnet",
            "accuracy": "low",
            "coordinates": [lon, lat]
        }
    
    return training_record

def create_enhanced_fine_tuning_examples(training_records: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Create enhanced fine-tuning examples with AI insights."""
    examples = []
    
    for record in training_records:
        if record.get('record_type') != 'device_classification':
            continue
        
        features = record.get('features', {})
        device_type = record.get('device_type', 'unknown')
        ai_features = record.get('ai_features', {})
        
        # Create enhanced natural language description
        description_parts = []
        
        # Basic features
        if features.get('has_hostname'):
            description_parts.append("Device has a configured hostname")
        
        port_count = features.get('port_count', 0)
        if port_count > 0:
            description_parts.append(f"Device has {port_count} open ports")
            
            if features.get('has_web_ports'):
                description_parts.append("Web services are running")
            
            if features.get('has_ssh'):
                description_parts.append("SSH access is available")
            
            if features.get('has_telnet'):
                description_parts.append("Telnet service is exposed")
            
            if features.get('has_iot_ports'):
                description_parts.append("IoT protocols detected")
        
        if features.get('is_persistent'):
            description_parts.append("Device appears consistently in scans")
        
        # Add AI reasoning if available
        ai_reasoning = ai_features.get('ai_reasoning', '')
        if ai_reasoning:
            description_parts.append(f"AI analysis: {ai_reasoning[:100]}")
        
        input_text = ". ".join(description_parts) + "."
        
        example = {
            "input": input_text,
            "output": device_type,
            "confidence": record.get('confidence', 0.0),
            "ai_enhanced": record.get('metadata', {}).get('ai_enhanced', False),
            "metadata": record.get('metadata', {})
        }
        
        examples.append(example)
    
    return examples

async def main():
    """Main demo function."""
    print("🤖 R2-D2 AI-Enhanced Training Data Generation")
    print("=" * 60)
    
    # Setup
    output_dir = "data/training_sets"
    os.makedirs(output_dir, exist_ok=True)
    
    # Load discovery data
    devices, networks = load_discovery_data()
    
    if not devices:
        print("❌ No device data found")
        return 1
    
    # Setup TinyLLM
    tinyllm = await setup_tinyllm()
    
    print(f"\n🔍 Analyzing {len(devices)} devices...")
    training_records = []
    
    # Analyze each device
    for i, (device_id, device_data) in enumerate(devices.items(), 1):
        print(f"📱 Analyzing device {i}/{len(devices)}: {device_id}")
        
        # Get AI analysis if model is available
        ai_analysis = None
        if tinyllm:
            ai_analysis = await analyze_device_with_ai(device_data, tinyllm)
            print(f"   🧠 AI Classification: {ai_analysis.get('ai_classification', 'unknown')}")
        
        # Format for training
        record = format_device_for_training_with_ai(device_id, device_data, ai_analysis)
        training_records.append(record)
    
    print(f"\n✅ Generated {len(training_records)} AI-enhanced training records")
    
    # Create main training dataset
    training_dataset = {
        "dataset_info": {
            "generated_at": datetime.now().isoformat(),
            "format_version": "1.0",
            "total_records": len(training_records),
            "ai_enhanced_records": sum(1 for r in training_records if r.get('ai_features')),
            "anonymized": True,
            "source": "R2-D2 Astromech with TinyLLM Analysis",
            "ai_model": "weiser/82M-0.4" if tinyllm else None
        },
        "records": training_records
    }
    
    # Export enhanced training data
    print("\n💾 Exporting AI-enhanced training data...")
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    # JSON export
    json_path = os.path.join(output_dir, f"r2_ai_enhanced_training_{timestamp}.json")
    with open(json_path, 'w') as f:
        json.dump(training_dataset, f, indent=2, default=str)
    print(f"✅ JSON export: {json_path}")
    
    # GeoJSON export
    geojson_features = []
    for record in training_records:
        location_features = record.get('location_features', {})
        coordinates = location_features.get('coordinates')
        
        if coordinates:
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
                    "ai_enhanced": bool(record.get('ai_features')),
                    "security_risk": record.get('ai_features', {}).get('security_assessment', {}).get('risk_level', 'unknown')
                }
            }
            geojson_features.append(feature)
    
    geojson_data = {
        "type": "FeatureCollection",
        "metadata": {
            "generated_by": "R2-D2 Astromech Unit with TinyLLM",
            "created_at": datetime.now().isoformat(),
            "total_features": len(geojson_features),
            "ai_enhanced": tinyllm is not None
        },
        "features": geojson_features
    }
    
    geojson_path = os.path.join(output_dir, f"r2_ai_spatial_data_{timestamp}.geojson")
    with open(geojson_path, 'w') as f:
        json.dump(geojson_data, f, indent=2, default=str)
    print(f"✅ GeoJSON export: {geojson_path}")
    
    # Enhanced fine-tuning dataset
    print("\n🎓 Creating AI-enhanced fine-tuning dataset...")
    fine_tuning_examples = create_enhanced_fine_tuning_examples(training_records)
    
    split_point = int(len(fine_tuning_examples) * 0.8)
    
    fine_tuning_dataset = {
        "task_type": "ai_enhanced_device_classification",
        "created_at": datetime.now().isoformat(),
        "total_examples": len(fine_tuning_examples),
        "ai_enhanced_examples": sum(1 for ex in fine_tuning_examples if ex.get('ai_enhanced')),
        "training_examples": fine_tuning_examples[:split_point],
        "validation_examples": fine_tuning_examples[split_point:],
        "metadata": {
            "format": "text_classification_with_ai",
            "ai_model_used": "weiser/82M-0.4" if tinyllm else None,
            "target_classes": list(set(ex["output"] for ex in fine_tuning_examples)),
            "source": "R2-D2 Network Discovery + TinyLLM Analysis"
        }
    }
    
    finetune_path = os.path.join(output_dir, f"r2_ai_enhanced_finetune_{timestamp}.json")
    with open(finetune_path, 'w') as f:
        json.dump(fine_tuning_dataset, f, indent=2, default=str)
    print(f"✅ AI-enhanced fine-tuning dataset: {finetune_path}")
    
    # Statistics
    device_types = {}
    ai_enhanced_count = 0
    
    for record in training_records:
        device_type = record.get('device_type', 'unknown')
        device_types[device_type] = device_types.get(device_type, 0) + 1
        if record.get('ai_features'):
            ai_enhanced_count += 1
    
    # Cleanup
    if tinyllm:
        await tinyllm.cleanup()
    
    # Summary
    print("\n" + "=" * 60)
    print("🎉 R2 AI-Enhanced Training Data Generation Complete!")
    print("=" * 60)
    print(f"\n📁 Output directory: {output_dir}")
    print(f"📊 Generated {len(training_records)} training records")
    print(f"🧠 AI-enhanced records: {ai_enhanced_count}")
    print(f"🌍 Spatial features: {len(geojson_features)}")
    print(f"🎓 Fine-tuning examples: {len(fine_tuning_examples)}")
    
    print(f"\n📈 Device type distribution:")
    for device_type, count in device_types.items():
        print(f"  - {device_type}: {count}")
    
    print(f"\n🚀 AI-Enhanced datasets ready for:")
    print("  - Advanced machine learning training")
    print("  - Language model fine-tuning with AI insights")
    print("  - Security analysis and threat detection")
    print("  - IoT device identification with AI reasoning")
    
    return 0

if __name__ == "__main__":
    exit(asyncio.run(main()))
