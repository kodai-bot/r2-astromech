#!/usr/bin/env python3
"""
R2-D2 Modular System Demo

This demo shows the new modular R2 system in action, demonstrating:
- Event-driven communication between modules
- Network scanning with audio and text output
- Proper encapsulation and dependency injection
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


class R2ModularDemo:
    """
    Demo of the modular R2 system
    
    This demo shows how the new modular architecture works with
    event-driven communication between modules.
    """
    
    def __init__(self):
        """Initialize the demo"""
        self.container = DIContainer()
        self.config = None
        self.event_bus = None
        self.network_scanner = None
        self.audio_engine = None
        self.text_output = None
        
        logger.info("🤖 R2-D2 Modular Demo initializing...")
    
    async def initialize(self) -> bool:
        """Initialize the demo system"""
        try:
            logger.info("🔧 Initializing demo components...")
            
            # Initialize configuration
            self.config = Configuration(environment="development")
            
            # Register configuration in container
            self.container.register_factory(Configuration, lambda container: self.config)
            
            # Initialize event bus
            self.event_bus = await self.container.get_service(EventBus)
            
            # Get module configurations
            discovery_config = self.config.get_section('modules.discovery')
            personality_config = self.config.get_section('modules.personality')
            
            # Initialize modules
            self.network_scanner = ModularNetworkScanner(self.event_bus, discovery_config)
            self.audio_engine = ModularAudioEngine(self.event_bus, personality_config)
            self.text_output = TextOutputModule(self.event_bus, {"enabled": True})
            
            # Register modules with container
            self.container.register_module("network_scanner", self.network_scanner)
            self.container.register_module("audio_engine", self.audio_engine)
            self.container.register_module("text_output", self.text_output)
            
            logger.info("✅ Demo initialization complete")
            return True
            
        except Exception as e:
            logger.error(f"❌ Demo initialization failed: {e}")
            return False
    
    async def start(self) -> bool:
        """Start the demo system"""
        try:
            logger.info("🚀 Starting demo system...")
            
            # Initialize all modules
            if not await self.container.initialize_all_modules():
                logger.error("❌ Module initialization failed")
                return False
            
            # Start all modules
            if not await self.container.start_all_modules():
                logger.error("❌ Module startup failed")
                return False
            
            # Publish startup event
            await self.event_bus.publish(create_event(
                R2Events.SYSTEM_STARTUP,
                {"environment": "demo", "version": "2.0.0"},
                "demo_system"
            ))
            
            logger.info("🎉 R2-D2 Modular Demo is operational!")
            return True
            
        except Exception as e:
            logger.error(f"❌ Demo startup failed: {e}")
            return False
    
    async def run_network_scan_demo(self, target_network: str = "192.168.1.0/24") -> None:
        """
        Run a network scan demo showing event-driven communication.
        
        Args:
            target_network: Network to scan
        """
        try:
            logger.info(f"🔍 Starting network scan demo: {target_network}")
            
            # Perform network scan
            devices = await self.network_scanner.scan_network(target_network)
            
            # Display results summary
            print(f"\n🎯 Demo Results Summary:")
            print(f"📊 Devices discovered: {len(devices)}")
            
            if devices:
                print(f"\n📡 Discovered Devices:")
                for i, device in enumerate(devices, 1):
                    ip = device.get('ip', 'unknown')
                    status = device.get('status', 'unknown')
                    method = device.get('discovery_method', 'unknown')
                    
                    print(f"  {i}. {ip} - {status} ({method})")
                    
                    # Show port information if available
                    port_info = device.get('port_info', {})
                    if port_info.get('open_ports'):
                        open_ports = port_info['open_ports']
                        services = port_info.get('services', {})
                        print(f"     📡 Open ports: {open_ports}")
                        if services:
                            service_list = [f"{port}:{service}" for port, service in services.items()]
                            print(f"     🛠️  Services: {', '.join(service_list)}")
                    else:
                        print(f"     🔒 No open ports detected")
            
            logger.info("✅ Network scan demo completed")
            
        except Exception as e:
            logger.error(f"❌ Network scan demo failed: {e}")
    
    async def stop(self) -> bool:
        """Stop the demo system"""
        try:
            logger.info("🛑 Stopping demo system...")
            
            # Publish shutdown event
            await self.event_bus.publish(create_event(
                R2Events.SYSTEM_SHUTDOWN,
                {"demo_completed": True},
                "demo_system"
            ))
            
            # Stop all modules
            await self.container.stop_all_modules()
            
            # Cleanup all modules
            await self.container.cleanup_all_modules()
            
            logger.info("👋 R2-D2 Modular Demo shutdown complete")
            return True
            
        except Exception as e:
            logger.error(f"❌ Demo shutdown error: {e}")
            return False


async def main():
    """Main demo function"""
    print("🤖 R2-D2 Modular System Demo")
    print("=" * 50)
    print("This demo shows the new modular architecture with:")
    print("• Event-driven communication between modules")
    print("• Network scanning with audio and text output")
    print("• Proper encapsulation and dependency injection")
    print("=" * 50)
    
    # Initialize demo
    demo = R2ModularDemo()
    
    try:
        # Initialize system
        if not await demo.initialize():
            logger.error("❌ Demo initialization failed")
            return 1
        
        # Start system
        if not await demo.start():
            logger.error("❌ Demo startup failed")
            return 1
        
        # Wait a moment for modules to fully start
        await asyncio.sleep(1)
        
        # Run network scan demo
        print(f"\n🔍 Starting Network Scan Demo...")
        print(f"📡 This will demonstrate event-driven scanning with audio and text output")
        print(f"🎵 Audio events will play for each discovery (if sound files are available)")
        print(f"📝 Text output will show detailed scan information")
        print(f"\nPress Enter to start the scan, or Ctrl+C to exit...")
        
        try:
            input()  # Wait for user input
        except KeyboardInterrupt:
            print("\n🛑 Demo cancelled by user")
            await demo.stop()
            return 0
        
        # Run the scan
        await demo.run_network_scan_demo()
        
        # Wait a moment to see final output
        await asyncio.sleep(2)
        
        # Stop system
        await demo.stop()
        
        print(f"\n🎉 Demo completed successfully!")
        print(f"📊 The modular system demonstrated:")
        print(f"   • Event-driven communication")
        print(f"   • Modular architecture")
        print(f"   • Audio and text output coordination")
        print(f"   • Proper error handling and cleanup")
        
        return 0
        
    except KeyboardInterrupt:
        print("\n🛑 Demo interrupted by user")
        await demo.stop()
        return 0
        
    except Exception as e:
        logger.error(f"❌ Demo error: {e}")
        await demo.stop()
        return 1


if __name__ == "__main__":
    try:
        exit_code = asyncio.run(main())
        sys.exit(exit_code)
    except KeyboardInterrupt:
        print("\n🛑 Demo interrupted by user")
        sys.exit(0)
    except Exception as e:
        print(f"❌ Fatal error: {e}")
        sys.exit(1)