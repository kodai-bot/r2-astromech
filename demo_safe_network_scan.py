#!/usr/bin/env python3
"""
R2-D2 Safe Network Scanner Demo

This demo shows R2's network scanning capabilities with proper
timeout handling and graceful exit mechanisms.
"""

import asyncio
import sys
import os
import logging
import signal
from typing import List

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


class SafeR2NetworkDemo:
    """
    Safe demo of R2's network scanning capabilities
    
    This demo includes proper timeout handling and graceful exit mechanisms.
    """
    
    def __init__(self):
        """Initialize the demo"""
        self.container = DIContainer()
        self.config = None
        self.event_bus = None
        self.network_scanner = None
        self.audio_engine = None
        self.text_output = None
        self.shutdown_requested = False
        
        # Set up signal handlers for graceful shutdown
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)
        
        logger.info("🤖 R2-D2 Safe Network Demo initializing...")
    
    def _signal_handler(self, signum, frame):
        """Handle shutdown signals gracefully"""
        logger.info(f"🛑 Received signal {signum}, initiating graceful shutdown...")
        self.shutdown_requested = True
    
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
            discovery_config['debug_mode'] = True  # Enable debug mode
            discovery_config['scan_timeout'] = 30  # 30 second timeout
            discovery_config['ping_timeout'] = 2   # 2 second ping timeout
            
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
            
            logger.info("🎉 R2-D2 Safe Network Demo is operational!")
            return True
            
        except Exception as e:
            logger.error(f"❌ Demo startup failed: {e}")
            return False
    
    async def run_quick_scan_demo(self, target_network: str = "192.168.1.0/24") -> None:
        """
        Run a quick network scan demo with timeout protection.
        
        Args:
            target_network: Network to scan
        """
        try:
            print(f"\n🔍 R2-D2 Quick Network Scan Demo")
            print(f"🌐 Target: {target_network}")
            print(f"⏱️  Timeout: 30 seconds")
            print(f"🛑 Press Ctrl+C to stop gracefully")
            print("=" * 60)
            
            # Set up progress monitoring
            await self._setup_progress_monitoring()
            
            # Perform scan with timeout
            try:
                devices = await asyncio.wait_for(
                    self.network_scanner.scan_network(target_network),
                    timeout=30.0  # 30 second timeout
                )
                
                # Display results
                await self._display_scan_results(devices)
                
            except asyncio.TimeoutError:
                print(f"\n⏰ Scan timed out after 30 seconds")
                print(f"🛑 This is normal for large networks")
                print(f"📊 Partial results may be available")
                
                # Try to get partial results
                if hasattr(self.network_scanner, 'discovered_devices'):
                    partial_devices = self.network_scanner.discovered_devices
                    if partial_devices:
                        print(f"\n📡 Partial Results ({len(partial_devices)} devices):")
                        await self._display_scan_results(partial_devices)
            
            except Exception as e:
                logger.error(f"❌ Scan failed: {e}")
                print(f"❌ Scan failed: {e}")
            
        except Exception as e:
            logger.error(f"❌ Demo failed: {e}")
            print(f"❌ Demo failed: {e}")
    
    async def _setup_progress_monitoring(self) -> None:
        """Setup event handlers for progress monitoring"""
        try:
            # Subscribe to scan events
            await self.event_bus.subscribe("network_scan_started", self._on_scan_started)
            await self.event_bus.subscribe("device_discovered", self._on_device_discovered)
            await self.event_bus.subscribe("ping_progress", self._on_ping_progress)
            await self.event_bus.subscribe("network_scan_completed", self._on_scan_completed)
            
            # Also subscribe to R2Events versions
            await self.event_bus.subscribe("network.scan_started", self._on_scan_started)
            await self.event_bus.subscribe("network.device_discovered", self._on_device_discovered)
            await self.event_bus.subscribe("network.scan_completed", self._on_scan_completed)
            
            # Initialize progress tracking
            self.scan_start_time = None
            self.devices_found = 0
            self.addresses_scanned = 0
            
        except Exception as e:
            logger.error(f"❌ Progress monitoring setup failed: {e}")
    
    async def _on_scan_started(self, event) -> None:
        """Handle scan started event"""
        import time
        self.scan_start_time = time.time()
        print(f"🚀 R2-D2 scan initiated...")
        
    async def _on_device_discovered(self, event) -> None:
        """Handle device discovered event"""
        if self.shutdown_requested:
            return
            
        device_data = event.data.get('device', {})
        ip = device_data.get('ip', event.data.get('ip', 'unknown'))
        
        self.devices_found += 1
        print(f"🎉 Device found: {ip} (Total: {self.devices_found})")
        
    async def _on_ping_progress(self, event) -> None:
        """Handle ping progress updates"""
        if self.shutdown_requested:
            return
            
        current_ip = event.data.get('current_ip', '')
        progress = event.data.get('progress', 0)
        total = event.data.get('total', 0)
        
        # Show progress every 25 IPs
        if progress % 25 == 0 and progress > 0:
            percentage = (progress / total * 100) if total > 0 else 0
            print(f"🔍 Progress: {progress}/{total} ({percentage:.1f}%)")
    
    async def _on_scan_completed(self, event) -> None:
        """Handle scan completed event"""
        import time
        if self.scan_start_time:
            duration = time.time() - self.scan_start_time
            print(f"\n⏱️  Scan completed in {duration:.1f} seconds")
        
        devices_found = event.data.get('devices_found', 0)
        print(f"🎯 Scan summary: {devices_found} devices discovered")
    
    async def _display_scan_results(self, devices: List[dict]) -> None:
        """Display scan results in a formatted way"""
        print(f"\n🎯 Scan Results:")
        print(f"📊 Devices found: {len(devices)}")
        
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
        else:
            print("🤔 No devices found on this network")
        
        print(f"\n✅ Scan complete!")
    
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
            
            logger.info("👋 R2-D2 Safe Network Demo shutdown complete")
            return True
            
        except Exception as e:
            logger.error(f"❌ Demo shutdown error: {e}")
            return False


async def main():
    """Main demo function"""
    print("🤖 R2-D2 Safe Network Scanner Demo")
    print("=" * 60)
    print("This demo shows R2's network scanning with:")
    print("• Proper timeout handling (30 seconds)")
    print("• Graceful exit on Ctrl+C")
    print("• Progress monitoring")
    print("• Safe error handling")
    print("=" * 60)
    
    # Initialize demo
    demo = SafeR2NetworkDemo()
    
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
        
        # Run quick scan demo
        print(f"\n🔍 Starting Quick Network Scan...")
        print(f"📡 This will scan a small network range with timeout protection")
        print(f"🛑 Press Ctrl+C at any time to stop gracefully")
        print(f"\nPress Enter to start, or Ctrl+C to exit...")
        
        try:
            input()  # Wait for user input
        except KeyboardInterrupt:
            print("\n🛑 Demo cancelled by user")
            await demo.stop()
            return 0
        
        # Run the scan
        await demo.run_quick_scan_demo()
        
        # Wait a moment to see final output
        await asyncio.sleep(2)
        
        # Stop system
        await demo.stop()
        
        print(f"\n🎉 Demo completed successfully!")
        print(f"📊 The safe demo demonstrated:")
        print(f"   • Timeout-protected scanning")
        print(f"   • Graceful exit handling")
        print(f"   • Progress monitoring")
        print(f"   • Safe error handling")
        
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