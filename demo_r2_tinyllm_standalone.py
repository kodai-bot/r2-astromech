#!/usr/bin/env python3
"""
R2 Training Data Generation with TinyLLM - Standalone Version

This demo integrates TinyLLM directly for AI-enhanced device analysis
and training data generation, avoiding complex import dependencies.

Author: Dylan G Foley
Created: September 2025
"""

import asyncio
import json
import os
import logging
from datetime import datetime
from typing import Dict, List, Any, Optional

# HuggingFace transformers for TinyLLM
try:
    from transformers import AutoTokenizer, AutoModelForCausalLM
    import torch
    TRANSFORMERS_AVAILABLE = True
except ImportError:
    TRANSFORMERS_AVAILABLE = False
    print("⚠️  Transformers not available, will run without AI enhancement")

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class SimpleTinyLLM:
    """Simplified TinyLLM implementation for device analysis."""
    
    def __init__(self):
        self.model = None
        self.tokenizer = None
        self.is_loaded = False
        
    async def initialize(self):
        """Initialize the TinyLLM model."""
        if not TRANSFORMERS_AVAILABLE:
            return False
            
        try:
            print("🔄 Loading TinyLLM model (weiser/82M-0.4)...")
            
            # Load tokenizer
            self.tokenizer = AutoTokenizer.from_pretrained(
                "weiser/82M-0.4",
                trust_remote_code=True
            )
            
            if self.tokenizer.pad_token is None:
                self.tokenizer.pad_token = self.tokenizer.eos_token
            
            # Load model
            self.model = AutoModelForCausalLM.from_pretrained(
                "weiser/82M-0.4",
                trust_remote_code=True,
                torch_dtype=torch.float32,
                low_cpu_mem_usage=True
            )
            
            self.is_loaded = True
            print("✅ TinyLLM model loaded successfully")
            return True
            
        except Exception as e:
            print(f"❌ Failed to load TinyLLM: {e}")
            return False
    
    async def generate_response(self, prompt: str, max_length: int = 100) -> str:
        """Generate a response using TinyLLM with simplified prompts."""
        if not self.is_loaded:
            return "Model not loaded"
            
        try:
            # Use very simple format for 82M model
            simple_prompt = f"Device type: {prompt.replace('Network device with hostname', '').replace('What type of device is this?', '').strip()}"
            
            # Tokenize input
            inputs = self.tokenizer(
                simple_prompt,
                return_tensors="pt",
                truncation=True,
                max_length=40,  # Very short for 82M model
                padding=True
            )
            
            # Generate response with conservative settings for 82M model
            with torch.no_grad():
                outputs = self.model.generate(
                    inputs['input_ids'],
                    attention_mask=inputs['attention_mask'],
                    max_length=inputs['input_ids'].shape[1] + 10,  # Very short output
                    temperature=0.5,  # Lower temperature for more focused output
                    do_sample=True,
                    top_p=0.7,
                    top_k=20,  # Smaller top_k for more focused choices
                    pad_token_id=self.tokenizer.pad_token_id,
                    eos_token_id=self.tokenizer.eos_token_id
                )
            
            # Decode response
            response = self.tokenizer.decode(
                outputs[0][inputs['input_ids'].shape[1]:],
                skip_special_tokens=True
            ).strip()
            
            return response if response else "No response generated"
            
        except Exception as e:
            logger.error(f"Generation failed: {e}")
            return f"Generation error: {e}"
    
    async def cleanup(self):
        """Clean up model resources."""
        if self.model:
            del self.model
        if self.tokenizer:
            del self.tokenizer
        self.is_loaded = False

def load_discovery_data():
    """Load existing discovery data."""
    print("📊 Loading discovery data...")
    
    device_db_path = "data/devices/device_database.json"
    
    devices = {}
    
    try:
        if os.path.exists(device_db_path):
            with open(device_db_path, 'r') as f:
                devices = json.load(f)
        
        print(f"✅ Loaded {len(devices)} devices")
        return devices
        
    except Exception as e:
        print(f"❌ Failed to load discovery data: {e}")
        return {}

async def analyze_device_with_ai(device_data: Dict[str, Any], tinyllm) -> Dict[str, Any]:
    """Analyze a device using TinyLLM."""
    try:
        hostname = device_data.get('hostname', 'unknown')
        open_ports = device_data.get('open_ports', [])
        manufacturer = device_data.get('manufacturer', 'unknown')
        
        # Create very simple prompt for 82M model
        if open_ports:
            prompt = f"'{hostname}' ports {open_ports}"
        else:
            prompt = f"'{hostname}' no ports"
        
        # Get AI response
        ai_response = await tinyllm.generate_response(prompt, max_length=30)
        
        # Extract device type using hybrid approach (AI + rules)
        device_type = extract_device_type_hybrid(ai_response, device_data)
        confidence = calculate_hybrid_confidence(ai_response, device_data, device_type)
        
        return {
            'ai_classification': device_type,
            'ai_confidence': confidence,
            'ai_reasoning': ai_response,
            'security_assessment': assess_security(device_data),
            'recommendations': generate_recommendations(device_type, device_data)
        }
        
    except Exception as e:
        print(f"⚠️  AI analysis failed: {e}")
        return {
            'ai_classification': 'unknown',
            'ai_confidence': 0.0,
            'ai_reasoning': 'Analysis failed',
            'security_assessment': {'risk_level': 'unknown'},
            'recommendations': []
        }

def extract_device_type_hybrid(ai_response: str, device_data: Dict[str, Any]) -> str:
    """Hybrid device classification using both AI hints and rule-based analysis."""
    # First try to get hints from AI response
    ai_hints = extract_ai_hints(ai_response)
    
    # Then apply rule-based classification with AI hints
    rule_based_type = apply_rule_based_classification(device_data)
    
    # Combine AI hints with rule-based analysis
    if ai_hints and ai_hints != 'unknown':
        # AI provided a hint, validate against rules
        if rule_based_type != 'unknown':
            # Both AI and rules agree or provide info
            return ai_hints if ai_hints == rule_based_type else rule_based_type
        else:
            # Only AI provided info
            return ai_hints
    else:
        # Fall back to rule-based
        return rule_based_type

def extract_ai_hints(response: str) -> str:
    """Extract device type hints from AI response."""
    if not response or len(response.strip()) < 2:
        return 'unknown'
        
    response_lower = response.lower().strip()
    
    # Look for device type keywords in the AI response
    device_keywords = {
        'router': ['router', 'gateway', 'access'],
        'printer': ['printer', 'print', 'hp', 'canon', 'epson'],
        'computer': ['computer', 'pc', 'workstation', 'desktop'],
        'iot_sensor': ['sensor', 'iot', 'arduino', 'esp'],
        'security_camera': ['camera', 'cam', 'security', 'surveillance'],
        'switch': ['switch', 'network'],
        'nas': ['nas', 'storage', 'synology']
    }
    
    for device_type, keywords in device_keywords.items():
        if any(keyword in response_lower for keyword in keywords):
            return device_type
    
    return 'unknown'

def extract_device_type_from_response(response: str, device_data: Dict[str, Any]) -> str:
    """Extract device type from AI response with fallback."""
    response_lower = response.lower().strip()
    
    # Handle "I need more data" responses
    if "need more data" in response_lower:
        return apply_rule_based_classification(device_data)
    
    # Check AI response for device types
    if any(word in response_lower for word in ['router', 'gateway', 'access point']):
        return 'router'
    elif any(word in response_lower for word in ['sensor', 'iot', 'arduino', 'esp']):
        return 'iot_sensor'
    elif any(word in response_lower for word in ['camera', 'cam', 'surveillance']):
        return 'security_camera'
    elif any(word in response_lower for word in ['printer', 'print', 'canon', 'hp', 'epson']):
        return 'printer'
    elif any(word in response_lower for word in ['computer', 'pc', 'workstation', 'laptop']):
        return 'computer'
    elif any(word in response_lower for word in ['switch', 'network switch']):
        return 'switch'
    elif any(word in response_lower for word in ['nas', 'storage', 'synology']):
        return 'nas'
    else:
        # Fallback to rule-based analysis if AI doesn't provide clear answer
        return apply_rule_based_classification(device_data)

def apply_rule_based_classification(device_data: Dict[str, Any]) -> str:
    """Apply rule-based device classification when AI is uncertain."""
    hostname = device_data.get('hostname', '').lower()
    open_ports = device_data.get('open_ports', [])
    manufacturer = device_data.get('manufacturer', '').lower()
    
    # Rule-based classification logic
    if 'router' in hostname or 'gateway' in hostname:
        return 'router'
    elif 'printer' in hostname or 631 in open_ports or any(brand in manufacturer for brand in ['hp', 'canon', 'epson', 'brother']):
        return 'printer'
    elif any(keyword in hostname for keyword in ['camera', 'cam', 'nvr']):
        return 'security_camera'
    elif len(open_ports) < 3 and any(port in [1883, 8883, 5683] for port in open_ports):
        return 'iot_sensor'
    elif 22 in open_ports and any(port in [80, 443] for port in open_ports):
        return 'router'
    elif any(port in [135, 445, 3389] for port in open_ports):
        return 'computer'
    elif 'nas' in hostname or 'synology' in manufacturer:
        return 'nas'
    else:
        return 'unknown'

def calculate_hybrid_confidence(ai_response: str, device_data: Dict[str, Any], final_device_type: str) -> float:
    """Calculate confidence for hybrid AI + rule-based classification."""
    base_confidence = 0.5
    
    # Check if AI provided useful hints
    ai_hints = extract_ai_hints(ai_response)
    if ai_hints != 'unknown':
        base_confidence += 0.2  # AI contributed
        
        # Extra confidence if AI hint matches final classification
        if ai_hints == final_device_type:
            base_confidence += 0.1
    
    # Check rule-based indicators
    hostname = device_data.get('hostname', '').lower()
    open_ports = device_data.get('open_ports', [])
    
    # Strong indicators boost confidence
    if final_device_type == 'router' and ('router' in hostname or 'gateway' in hostname):
        base_confidence += 0.2
    elif final_device_type == 'printer' and ('printer' in hostname or 631 in open_ports):
        base_confidence += 0.2
    elif final_device_type == 'computer' and any(port in [135, 445, 3389] for port in open_ports):
        base_confidence += 0.15
    elif final_device_type == 'iot_sensor' and len(open_ports) < 3:
        base_confidence += 0.1
    
    # Penalize if no clear indicators
    if hostname == 'unknown' and not open_ports:
        base_confidence -= 0.1
    
    return min(max(base_confidence, 0.3), 0.9)  # Clamp between 0.3 and 0.9

def calculate_ai_confidence(ai_response: str, device_data: Dict[str, Any]) -> float:
    """Calculate confidence based on AI response quality."""
    response_lower = ai_response.lower().strip()
    
    # Handle "I need more data" responses - lower confidence, use rule-based
    if "need more data" in response_lower:
        return 0.4  # Lower confidence for uncertain AI responses
    
    # Higher confidence for definitive AI responses
    base_confidence = 0.7
    
    # Boost confidence for clear device type identification
    device_types = ['router', 'sensor', 'camera', 'printer', 'computer', 'switch', 'nas', 'iot']
    if any(device_type in response_lower for device_type in device_types):
        base_confidence += 0.15
    
    # Additional confidence for detailed responses
    if len(response_lower) > 10 and any(word in response_lower for word in ['this is', 'appears to be', 'likely']):
        base_confidence += 0.1
    
    # Check for specific technical terms that indicate good analysis
    technical_terms = ['port', 'protocol', 'service', 'network', 'device']
    if any(term in response_lower for term in technical_terms):
        base_confidence += 0.05
    
    return min(base_confidence, 0.95)

def assess_security(device_data: Dict[str, Any]) -> Dict[str, Any]:
    """Assess security characteristics."""
    risk_level = 'low'
    vulnerabilities = []
    recommendations = []
    
    open_ports = device_data.get('open_ports', [])
    hostname = device_data.get('hostname', 'unknown')
    
    # Security checks
    if 23 in open_ports:  # Telnet
        risk_level = 'high'
        vulnerabilities.append('Telnet exposed')
        recommendations.append('Disable Telnet')
    
    if 21 in open_ports:  # FTP
        risk_level = 'medium' if risk_level == 'low' else risk_level
        vulnerabilities.append('FTP exposed')
        recommendations.append('Use secure FTP')
    
    if len(open_ports) > 10:
        risk_level = 'medium' if risk_level == 'low' else risk_level
        vulnerabilities.append('Many open ports')
        recommendations.append('Audit open ports')
    
    if hostname == 'unknown':
        vulnerabilities.append('Device unidentified')
        recommendations.append('Investigate device')
    
    return {
        'risk_level': risk_level,
        'vulnerabilities': vulnerabilities,
        'recommendations': recommendations
    }

def generate_recommendations(device_type: str, device_data: Dict[str, Any]) -> List[str]:
    """Generate device-specific recommendations."""
    recommendations = []
    
    if device_type == 'iot_sensor':
        recommendations.extend([
            'Monitor IoT device traffic',
            'Update device firmware',
            'Segment IoT network'
        ])
    elif device_type == 'router':
        recommendations.extend([
            'Secure admin access',
            'Update firmware',
            'Monitor configuration'
        ])
    elif device_type == 'printer':
        recommendations.extend([
            'Secure printer access',
            'Update printer firmware',
            'Monitor print jobs'
        ])
    else:
        recommendations.extend([
            'Investigate device',
            'Monitor traffic',
            'Apply security practices'
        ])
    
    return recommendations

def format_device_for_training(device_id: str, device_data: Dict[str, Any], 
                             ai_analysis: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """Format device for training with optional AI enhancement."""
    
    # Extract features
    features = {
        'has_hostname': device_data.get('hostname', 'unknown') != 'unknown',
        'has_mac': device_data.get('mac', 'unknown') != 'unknown',
        'port_count': len(device_data.get('open_ports', [])),
        'has_web_ports': any(port in [80, 443, 8080] for port in device_data.get('open_ports', [])),
        'has_ssh': 22 in device_data.get('open_ports', []),
        'has_telnet': 23 in device_data.get('open_ports', []),
        'has_iot_ports': any(port in [1883, 8883] for port in device_data.get('open_ports', [])),
        'discovery_count': device_data.get('discovery_count', 1),
        'is_persistent': device_data.get('discovery_count', 1) > 1
    }
    
    # Determine device type and confidence
    if ai_analysis:
        device_type = ai_analysis.get('ai_classification', 'unknown')
        confidence = ai_analysis.get('ai_confidence', 0.5)
    else:
        device_type = 'unknown'
        confidence = 0.3
    
    # Create training record
    training_record = {
        "record_type": "device_classification",
        "device_id": f"device_{hash(device_id) % 10000:04d}",
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
    
    # Add AI features if available
    if ai_analysis:
        training_record["ai_features"] = {
            "ai_reasoning": ai_analysis.get('ai_reasoning', ''),
            "security_assessment": ai_analysis.get('security_assessment', {}),
            "recommendations": ai_analysis.get('recommendations', [])
        }
    
    # Add location (synthetic)
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

async def main():
    """Main demo function."""
    print("🤖 R2-D2 AI-Enhanced Training Data Generation")
    print("=" * 60)
    print("Integrating TinyLLM for intelligent device analysis")
    print("")
    
    # Setup
    output_dir = "data/training_sets"
    os.makedirs(output_dir, exist_ok=True)
    
    # Load discovery data
    devices = load_discovery_data()
    
    if not devices:
        print("❌ No device data found")
        return 1
    
    # Initialize TinyLLM
    tinyllm = SimpleTinyLLM()
    model_loaded = await tinyllm.initialize()
    
    if model_loaded:
        print("✅ TinyLLM ready for AI-enhanced analysis")
    else:
        print("⚠️  Continuing without AI enhancement")
    
    # Analyze devices
    print(f"\n🔍 Analyzing {len(devices)} devices...")
    training_records = []
    
    for i, (device_id, device_data) in enumerate(devices.items(), 1):
        print(f"📱 Device {i}/{len(devices)}: {device_id}")
        
        # AI analysis if available
        ai_analysis = None
        if model_loaded:
            ai_analysis = await analyze_device_with_ai(device_data, tinyllm)
            classification = ai_analysis.get('ai_classification', 'unknown')
            confidence = ai_analysis.get('ai_confidence', 0.0)
            print(f"   🧠 AI: {classification} (confidence: {confidence:.2f})")
        
        # Create training record
        record = format_device_for_training(device_id, device_data, ai_analysis)
        training_records.append(record)
    
    # Create enhanced training dataset
    training_dataset = {
        "dataset_info": {
            "generated_at": datetime.now().isoformat(),
            "format_version": "1.0",
            "total_records": len(training_records),
            "ai_enhanced_records": sum(1 for r in training_records if r.get('ai_features')),
            "anonymized": True,
            "source": "R2-D2 Astromech with TinyLLM",
            "ai_model": "weiser/82M-0.4" if model_loaded else None
        },
        "records": training_records
    }
    
    # Export data
    print(f"\n💾 Exporting {len(training_records)} training records...")
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    # JSON export
    json_path = os.path.join(output_dir, f"r2_ai_training_{timestamp}.json")
    with open(json_path, 'w') as f:
        json.dump(training_dataset, f, indent=2, default=str)
    print(f"✅ JSON: {json_path}")
    
    # GeoJSON export
    geojson_features = []
    for record in training_records:
        coords = record.get('location_features', {}).get('coordinates')
        if coords:
            feature = {
                "type": "Feature",
                "geometry": {"type": "Point", "coordinates": coords},
                "properties": {
                    "device_id": record.get('device_id'),
                    "device_type": record.get('device_type'),
                    "confidence": record.get('confidence', 0.0),
                    "ai_enhanced": bool(record.get('ai_features')),
                    "risk_level": record.get('ai_features', {}).get('security_assessment', {}).get('risk_level', 'unknown')
                }
            }
            geojson_features.append(feature)
    
    geojson_data = {
        "type": "FeatureCollection",
        "metadata": {
            "generated_by": "R2-D2 with TinyLLM",
            "created_at": datetime.now().isoformat(),
            "total_features": len(geojson_features),
            "ai_enhanced": model_loaded
        },
        "features": geojson_features
    }
    
    geojson_path = os.path.join(output_dir, f"r2_ai_spatial_{timestamp}.geojson")
    with open(geojson_path, 'w') as f:
        json.dump(geojson_data, f, indent=2, default=str)
    print(f"✅ GeoJSON: {geojson_path}")
    
    # Fine-tuning dataset
    fine_tuning_examples = []
    for record in training_records:
        if record.get('record_type') == 'device_classification':
            features = record.get('features', {})
            device_type = record.get('device_type')
            ai_features = record.get('ai_features', {})
            
            # Create description
            desc_parts = []
            if features.get('has_hostname'):
                desc_parts.append("has hostname")
            if features.get('port_count', 0) > 0:
                desc_parts.append(f"{features['port_count']} open ports")
            if features.get('has_ssh'):
                desc_parts.append("SSH enabled")
            if features.get('has_iot_ports'):
                desc_parts.append("IoT protocols")
            
            # Add AI reasoning
            ai_reasoning = ai_features.get('ai_reasoning', '')
            if ai_reasoning:
                desc_parts.append(f"AI: {ai_reasoning[:50]}")
            
            input_text = f"Device with {', '.join(desc_parts)}."
            
            fine_tuning_examples.append({
                "input": input_text,
                "output": device_type,
                "confidence": record.get('confidence', 0.0),
                "ai_enhanced": bool(ai_features)
            })
    
    fine_tuning_data = {
        "task_type": "ai_enhanced_device_classification",
        "created_at": datetime.now().isoformat(),
        "total_examples": len(fine_tuning_examples),
        "ai_enhanced_count": sum(1 for ex in fine_tuning_examples if ex.get('ai_enhanced')),
        "examples": fine_tuning_examples,
        "metadata": {
            "ai_model": "weiser/82M-0.4" if model_loaded else None,
            "source": "R2-D2 Network Discovery + TinyLLM"
        }
    }
    
    finetune_path = os.path.join(output_dir, f"r2_ai_finetune_{timestamp}.json")
    with open(finetune_path, 'w') as f:
        json.dump(fine_tuning_data, f, indent=2, default=str)
    print(f"✅ Fine-tuning: {finetune_path}")
    
    # Statistics
    ai_enhanced_count = sum(1 for r in training_records if r.get('ai_features'))
    device_types = {}
    for record in training_records:
        device_type = record.get('device_type', 'unknown')
        device_types[device_type] = device_types.get(device_type, 0) + 1
    
    # Cleanup
    if model_loaded:
        await tinyllm.cleanup()
    
    # Summary
    print("\n" + "=" * 60)
    print("🎉 R2 AI-Enhanced Training Data Complete!")
    print("=" * 60)
    print(f"\n📊 Statistics:")
    print(f"  - Total records: {len(training_records)}")
    print(f"  - AI-enhanced: {ai_enhanced_count}")
    print(f"  - Spatial features: {len(geojson_features)}")
    print(f"  - Fine-tuning examples: {len(fine_tuning_examples)}")
    
    print(f"\n📈 Device distribution:")
    for device_type, count in device_types.items():
        print(f"  - {device_type}: {count}")
    
    print(f"\n🚀 Ready for:")
    print("  - ML model training with AI insights")
    print("  - Language model fine-tuning")
    print("  - Security analysis with risk assessment")
    print("  - Geospatial network analysis")
    
    return 0

if __name__ == "__main__":
    exit(asyncio.run(main()))
