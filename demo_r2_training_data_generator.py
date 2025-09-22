#!/usr/bin/env python3
"""
R2 Training Data Generator Demo

This demo showcases the R2 unit's capability to generate training datasets
from network discovery data enhanced with TinyLLM AI analysis. The output
includes both JSON and GeoJSON formats suitable for fine-tuning.

Running this demo will:
1. Load the TinyLLM model for IoT analysis
2. Process existing network discovery data  
3. Generate AI-enhanced training datasets
4. Export to JSON and GeoJSON formats
5. Create a fine-tuning ready dataset

Author: Dylan G Foley
Created: September 2025
"""

import asyncio
import sys
import os
import json
import logging
from typing import Dict, Any, Optional
from datetime import datetime

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from modules.training import (
    ModularTrainingDataGenerator, 
    TrainingDataConfig,
    NetworkDataFormatter,
    TrainingDataExporter
)
from modules.ai.models.tinyllm_model import TinyLLMModel
from modules.discovery.device_database import DeviceDatabase

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class R2TrainingDataDemo:
    """
    Demonstrates R2's training data generation capabilities with TinyLLM integration.
    """
    
    def __init__(self):
        """Initialize the demo."""
        self.tinyllm_model = None
        self.device_database = None
        self.training_generator = None
        self.config = None
        
        # Demo configuration
        self.config = TrainingDataConfig(
            output_directory="data/training_sets",
            include_geolocation=True,
            include_temporal_data=True,
            anonymize_data=True,
            format_version="1.0",
            max_records_per_file=100
        )
        
        logger.info("🤖 R2 Training Data Generator Demo initialized")
    
    async def setup(self) -> bool:
        """Set up all components for the demo."""
        try:
            print("🧠 Setting up R2 Training Data Generation System")
            print("=" * 60)
            
            # 1. Initialize TinyLLM model
            print("\n📦 Step 1: Loading TinyLLM Model")
            print("-" * 40)
            
            model_config = {
                'model_path': 'weiser/82M-0.4',
                'device': 'cpu',
                'max_length': 128,
                'temperature': 0.6,
                'iot_mode': True,
                'sensor_data_context': True
            }
            
            self.tinyllm_model = TinyLLMModel(model_config)
            
            # Load the model
            await self.tinyllm_model.initialize()
            
            if self.tinyllm_model.is_loaded:
                print("✅ TinyLLM model loaded successfully")
            else:
                print("⚠️  TinyLLM model not loaded, continuing without AI enhancement")
            
            # 2. Initialize device database
            print("\n💾 Step 2: Loading Device Database")
            print("-" * 40)
            
            self.device_database = DeviceDatabase()
            device_count = len(self.device_database.devices)
            network_count = len(self.device_database.network_fingerprints)
            
            print(f"✅ Device database loaded: {device_count} devices, {network_count} networks")
            
            # 3. Initialize training data generator
            print("\n🏭 Step 3: Initializing Training Data Generator")
            print("-" * 40)
            
            self.training_generator = ModularTrainingDataGenerator(
                self.config, 
                self.tinyllm_model if self.tinyllm_model and self.tinyllm_model.is_loaded else None
            )
            
            print("✅ Training data generator ready")
            
            return True
            
        except Exception as e:
            logger.error(f"Demo setup failed: {e}")
            return False
    
    async def demonstrate_training_generation(self):
        """Demonstrate the training data generation process."""
        try:
            print("\n🏗️  Generating Training Datasets")
            print("=" * 60)
            
            # 1. Prepare discovery data
            print("\n📊 Step 1: Preparing Discovery Data")
            print("-" * 40)
            
            discovery_data = await self._prepare_discovery_data()
            
            if not discovery_data:
                print("❌ No discovery data available")
                return False
            
            device_count = len(discovery_data.get('devices', {}))
            network_count = len(discovery_data.get('networks', {}))
            print(f"✅ Discovery data prepared: {device_count} devices, {network_count} networks")
            
            # 2. Generate AI analysis (if model is available)
            ai_analysis = None
            if self.tinyllm_model and self.tinyllm_model.is_loaded:
                print("\n🧠 Step 2: Generating AI Analysis")
                print("-" * 40)
                
                ai_analysis = await self._generate_ai_analysis(discovery_data)
                if ai_analysis:
                    print(f"✅ AI analysis completed for {len(ai_analysis)} items")
                else:
                    print("⚠️  AI analysis failed, continuing without")
            else:
                print("\n⏭️  Step 2: Skipping AI Analysis (model not loaded)")
            
            # 3. Generate training dataset
            print("\n🎯 Step 3: Generating Training Dataset")
            print("-" * 40)
            
            training_set = await self.training_generator.generate_training_set(
                discovery_data, ai_analysis
            )
            
            if not training_set:
                print("❌ Failed to generate training dataset")
                return False
            
            record_count = len(training_set.get('records', []))
            print(f"✅ Training dataset generated: {record_count} records")
            
            # 4. Validate training data
            print("\n✅ Step 4: Validating Training Data")
            print("-" * 40)
            
            validation_results = await self.training_generator.validate_training_data(training_set)
            
            if validation_results['is_valid']:
                validity_rate = validation_results['metrics']['validity_rate'] * 100
                print(f"✅ Training data validation passed ({validity_rate:.1f}% valid)")
            else:
                print("⚠️  Training data validation issues found:")
                for error in validation_results['errors']:
                    print(f"   - {error}")
            
            # 5. Export training data
            print("\n💾 Step 5: Exporting Training Data")
            print("-" * 40)
            
            await self._export_training_data(training_set)
            
            # 6. Create fine-tuning dataset
            print("\n🎓 Step 6: Creating Fine-Tuning Dataset")
            print("-" * 40)
            
            await self._create_fine_tuning_datasets([training_set])
            
            return True
            
        except Exception as e:
            logger.error(f"Training generation demonstration failed: {e}")
            return False
    
    async def _prepare_discovery_data(self) -> Dict[str, Any]:
        """Prepare discovery data from the device database."""
        discovery_data = {
            'devices': {},
            'networks': {},
            'timestamp': datetime.now().isoformat()
        }
        
        # Add device data
        for device_ip, device_info in self.device_database.devices.items():
            discovery_data['devices'][device_ip] = device_info
        
        # Add network data  
        for network_code, network_info in self.device_database.network_fingerprints.items():
            discovery_data['networks'][network_code] = network_info
        
        return discovery_data
    
    async def _generate_ai_analysis(self, discovery_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Generate AI analysis for discovery data using TinyLLM."""
        try:
            ai_analysis = {}
            
            # Analyze devices
            devices = discovery_data.get('devices', {})
            for device_id, device_data in devices.items():
                
                # Create analysis prompt for TinyLLM
                analysis_prompt = self._create_device_analysis_prompt(device_data)
                
                # Get AI analysis
                try:
                    ai_response = await self.tinyllm_model.generate_response(analysis_prompt)
                    
                    # Parse AI response (simplified for demo)
                    ai_analysis[device_id] = {
                        'classification': self._extract_classification(ai_response),
                        'confidence': 0.8,  # Simplified confidence
                        'insights': [ai_response[:100] + "..."],  # Truncated insights
                        'security_assessment': {
                            'risk_level': 'low',
                            'recommendations': ['Monitor device activity']
                        },
                        'timestamp': datetime.now().isoformat()
                    }
                    
                except Exception as e:
                    logger.warning(f"AI analysis failed for device {device_id}: {e}")
                    continue
            
            # Analyze networks
            networks = discovery_data.get('networks', {})
            for network_id, network_data in networks.items():
                
                analysis_prompt = self._create_network_analysis_prompt(network_data)
                
                try:
                    ai_response = await self.tinyllm_model.generate_response(analysis_prompt)
                    
                    ai_analysis[network_id] = {
                        'topology_analysis': ai_response[:100] + "...",
                        'security_score': 0.7,
                        'recommendations': ['Regular security scans recommended'],
                        'timestamp': datetime.now().isoformat()
                    }
                    
                except Exception as e:
                    logger.warning(f"AI analysis failed for network {network_id}: {e}")
                    continue
            
            return ai_analysis
            
        except Exception as e:
            logger.error(f"AI analysis generation failed: {e}")
            return None
    
    def _create_device_analysis_prompt(self, device_data: Dict[str, Any]) -> str:
        """Create analysis prompt for a device."""
        hostname = device_data.get('hostname', 'unknown')
        ip = device_data.get('ip', 'unknown')
        open_ports = device_data.get('open_ports', [])
        manufacturer = device_data.get('manufacturer', 'unknown')
        
        prompt = f"""Analyze this IoT device:
Device IP: {ip}
Hostname: {hostname}
Manufacturer: {manufacturer}
Open Ports: {open_ports}

What type of device is this and what are its characteristics?"""
        
        return prompt
    
    def _create_network_analysis_prompt(self, network_data: Dict[str, Any]) -> str:
        """Create analysis prompt for a network."""
        device_count = network_data.get('device_count', 0)
        network_range = network_data.get('network_range', 'unknown')
        
        prompt = f"""Analyze this network:
Network Range: {network_range}
Device Count: {device_count}

Describe the network topology and any security considerations."""
        
        return prompt
    
    def _extract_classification(self, ai_response: str) -> str:
        """Extract device classification from AI response (simplified)."""
        response_lower = ai_response.lower()
        
        # Simple keyword matching for demo
        if 'router' in response_lower or 'gateway' in response_lower:
            return 'router'
        elif 'sensor' in response_lower or 'iot' in response_lower:
            return 'iot_sensor'
        elif 'camera' in response_lower:
            return 'security_camera'
        elif 'printer' in response_lower:
            return 'printer'
        elif 'computer' in response_lower or 'pc' in response_lower:
            return 'computer'
        else:
            return 'unknown'
    
    async def _export_training_data(self, training_set: Dict[str, Any]):
        """Export training data to various formats."""
        try:
            # Export as JSON
            json_path = await self.training_generator.export_training_data(training_set, "json")
            if json_path:
                print(f"✅ JSON export: {json_path}")
            
            # Export as GeoJSON (if location data is available)
            has_location_data = any(
                'location_features' in record 
                for record in training_set.get('records', [])
            )
            
            if has_location_data:
                geojson_path = await self.training_generator.export_training_data(training_set, "geojson")
                if geojson_path:
                    print(f"✅ GeoJSON export: {geojson_path}")
            else:
                print("ℹ️  No location data available for GeoJSON export")
            
            # Export metadata
            exporter = TrainingDataExporter(self.config)
            metadata_path = os.path.join(self.config.output_directory, "training_metadata.json")
            success = exporter.export_training_metadata([training_set], metadata_path)
            
            if success:
                print(f"✅ Metadata export: {metadata_path}")
            
        except Exception as e:
            logger.error(f"Export failed: {e}")
    
    async def _create_fine_tuning_datasets(self, training_sets):
        """Create fine-tuning ready datasets for different ML tasks."""
        tasks = ["device_classification", "network_analysis", "iot_device_identification"]
        
        for task in tasks:
            try:
                print(f"📚 Creating fine-tuning dataset for: {task}")
                
                fine_tuning_data = await self.training_generator.create_fine_tuning_dataset(
                    training_sets, task
                )
                
                if fine_tuning_data:
                    # Export fine-tuning dataset
                    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                    filename = f"finetune_{task}_{timestamp}.json"
                    output_path = os.path.join(self.config.output_directory, filename)
                    
                    with open(output_path, 'w') as f:
                        json.dump(fine_tuning_data, f, indent=2, default=str)
                    
                    example_count = fine_tuning_data['metadata']['total_examples']
                    print(f"   ✅ {example_count} examples → {output_path}")
                
            except Exception as e:
                logger.error(f"Fine-tuning dataset creation failed for {task}: {e}")
    
    async def cleanup(self):
        """Clean up resources."""
        try:
            if self.tinyllm_model:
                await self.tinyllm_model.cleanup()
            
            print("\n🧹 Cleanup completed")
            
        except Exception as e:
            logger.error(f"Cleanup failed: {e}")
    
    async def run_demo(self):
        """Run the complete training data generation demo."""
        try:
            # Setup
            setup_success = await self.setup()
            if not setup_success:
                print("❌ Demo setup failed")
                return False
            
            print("\n" + "🎯 R2 TRAINING DATA GENERATION DEMO" + "\n")
            
            # Main demonstration
            demo_success = await self.demonstrate_training_generation()
            
            if demo_success:
                print("\n" + "=" * 60)
                print("🎉 R2 Training Data Generation Demo Completed Successfully!")
                print("=" * 60)
                
                print(f"\n📁 Training data exported to: {self.config.output_directory}")
                print("\nGenerated files:")
                print("  - JSON training datasets")
                print("  - GeoJSON spatial data (if available)")
                print("  - Fine-tuning ready datasets")
                print("  - Training metadata")
                
                print("\n🚀 These datasets are now ready for:")
                print("  - Machine learning model training")
                print("  - Fine-tuning language models")
                print("  - Geospatial analysis")
                print("  - IoT device classification")
                
                return True
            else:
                print("❌ Demo failed during execution")
                return False
                
        except Exception as e:
            logger.error(f"Demo execution failed: {e}")
            return False
        finally:
            await self.cleanup()


async def main():
    """Main entry point for the demo."""
    print("🤖 R2-D2 Training Data Generation Demo")
    print("=" * 60)
    print("This demo showcases R2's training data generation capabilities")
    print("with TinyLLM AI enhancement for IoT device analysis.")
    print("")
    
    demo = R2TrainingDataDemo()
    
    try:
        success = await demo.run_demo()
        return 0 if success else 1
        
    except KeyboardInterrupt:
        print("\n🛑 Demo interrupted by user")
        return 1
    except Exception as e:
        print(f"\n❌ Demo failed: {e}")
        return 1


if __name__ == "__main__":
    exit(asyncio.run(main()))
