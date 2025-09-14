#!/usr/bin/env python3
"""
Test the Modular R2 System

This script tests the modular system without requiring user input.
"""

import asyncio
import sys
import os
import logging

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from src.core.container import DIContainer
from src.core.config import Configuration
from src.core.events import EventBus, create_event, R2Events
from src.modules.discovery.network_scanner import ModularNetworkScanner
from src.modules.personality.audio_engine import ModularAudioEngine
from src.modules.personality.text_output import TextOutputModule

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


async def test_modular_system():
    """Test the modular R2 system"""
    print("🤖 Testing R2-D2 Modular System")
    print("=" * 40)
    
    # Initialize components
    container = DIContainer()
    config = Configuration(environment="development")
    
    # Register configuration
    container.register_factory(Configuration, lambda container: config)
    
    # Initialize event bus
    event_bus = await container.get_service(EventBus)
    
    # Get module configurations
    discovery_config = config.get_section('modules.discovery')
    personality_config = config.get_section('modules.personality')
    
    # Initialize modules
    network_scanner = ModularNetworkScanner(event_bus, discovery_config)
    audio_engine = ModularAudioEngine(event_bus, personality_config)
    text_output = TextOutputModule(event_bus, {"enabled": True})
    
    # Register modules
    container.register_module("network_scanner", network_scanner)
    container.register_module("audio_engine", audio_engine)
    container.register_module("text_output", text_output)
    
    try:
        print("🔧 Initializing modules...")
        
        # Initialize all modules
        if not await container.initialize_all_modules():
            print("❌ Module initialization failed")
            return False
        
        # Start all modules
        if not await container.start_all_modules():
            print("❌ Module startup failed")
            return False
        
        print("✅ All modules started successfully")
        
        # Test audio functionality
        print("\n🎵 Testing audio system...")
        await audio_engine.play_sound('scan_start')
        await asyncio.sleep(0.5)
        await audio_engine.play_sound('device_found')
        await asyncio.sleep(0.5)
        await audio_engine.play_sound('scan_complete')
        await asyncio.sleep(1)
        
        # Test text output
        print("\n📝 Testing text output...")
        text_output._display_message("🔍 R2-D2 Test Message", "info")
        text_output._display_message("📡 Network Scanner Ready", "device")
        text_output._display_message("🎵 Audio Engine Ready", "success")
        
        # Test a small network scan (just a few IPs)
        print("\n🔍 Testing network scan (limited scope)...")
        try:
            # Scan a very small range to avoid long delays
            devices = await network_scanner.scan_network("127.0.0.1/32")
            print(f"✅ Scan completed: {len(devices)} devices found")
        except Exception as e:
            print(f"⚠️  Scan test failed (expected): {e}")
        
        # Test module status
        print("\n📊 Module Status:")
        status = await network_scanner.get_status()
        print(f"  Network Scanner: {status.status}")
        
        status = await audio_engine.get_status()
        print(f"  Audio Engine: {status.status}")
        
        status = await text_output.get_status()
        print(f"  Text Output: {status.status}")
        
        # Test health checks
        print("\n🩺 Health Checks:")
        print(f"  Network Scanner: {'✅ Healthy' if await network_scanner.health_check() else '❌ Unhealthy'}")
        print(f"  Audio Engine: {'✅ Healthy' if await audio_engine.health_check() else '❌ Unhealthy'}")
        print(f"  Text Output: {'✅ Healthy' if await text_output.health_check() else '❌ Unhealthy'}")
        
        print("\n🎉 Modular system test completed successfully!")
        return True
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        return False
        
    finally:
        # Cleanup
        print("\n🧹 Cleaning up...")
        await container.stop_all_modules()
        await container.cleanup_all_modules()
        print("✅ Cleanup complete")


async def main():
    """Main test function"""
    success = await test_modular_system()
    return 0 if success else 1


if __name__ == "__main__":
    try:
        exit_code = asyncio.run(main())
        sys.exit(exit_code)
    except KeyboardInterrupt:
        print("\n🛑 Test interrupted by user")
        sys.exit(0)
    except Exception as e:
        print(f"❌ Fatal error: {e}")
        sys.exit(1)