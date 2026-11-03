#!/usr/bin/env python3
"""
R2-A1 SSDP/UPnP Discovery Demo

Simple demonstration of R2's SSDP discovery capabilities.
This script runs a focused SSDP scan to find UPnP devices.

Usage:
    python3 demo_ssdp_only.py
"""

import asyncio
import logging
import sys
import os
from datetime import datetime

# Add src to path for imports
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path[:0] = [ROOT, os.path.join(ROOT, "src")]

from src.core.events import EventBus, R2Events
from src.core.config import Configuration
from src.modules.discovery.scanners.interfaces import ScannerConfig
from src.modules.discovery.scanners.ssdp_scanner import SSDPScanner

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)

class R2SSDPDemo:
    """R2-A1 SSDP Discovery Demo"""
    
    def __init__(self):
        self.event_bus = EventBus()
        self.config = Configuration()
        self.ssdp_scanner = None
        
        # Demo state
        self.demo_running = False
        self.devices_found = []
    
    async def initialize(self) -> bool:
        """Initialize the SSDP demo."""
        try:
            logger.info("🤖 Initializing R2-A1 SSDP Discovery Demo...")
            
            # Configure SSDP scanner
            ssdp_config = ScannerConfig(
                enabled=True,
                timeout=15.0,
                custom_options={
                    'scan_timeout': 12,
                    'max_responses': 50,
                    'follow_descriptions': True,
                    'description_timeout': 5,
                    'search_targets': [
                        "upnp:rootdevice",
                        "ssdp:all",
                        "urn:schemas-upnp-org:device:MediaRenderer:1",
                        "urn:schemas-upnp-org:device:MediaServer:1", 
                        "urn:schemas-upnp-org:device:InternetGatewayDevice:1",
                        "urn:dial-multiscreen-org:service:dial:1"
                    ]
                }
            )
            
            # Initialize SSDP scanner
            self.ssdp_scanner = SSDPScanner(self.event_bus, ssdp_config)
            
            # Subscribe to device discovery events
            await self.event_bus.subscribe(R2Events.NETWORK_DEVICE_DISCOVERED, self._on_device_discovered)
            
            logger.info("✅ R2-A1 SSDP Demo initialized successfully")
            return True
            
        except Exception as e:
            logger.error(f"❌ Demo initialization failed: {e}")
            return False
    
    async def start(self) -> bool:
        """Start the demo."""
        try:
            logger.info("🚀 Starting R2-A1 SSDP Demo...")
            
            # Start scanner
            await self.ssdp_scanner.start()
            
            self.demo_running = True
            logger.info("✅ Demo started successfully")
            return True
            
        except Exception as e:
            logger.error(f"❌ Demo startup failed: {e}")
            return False
    
    async def run_ssdp_discovery(self) -> None:
        """Run SSDP discovery demonstration."""
        try:
            print("\n🔍 R2-A1 SSDP/UPnP Network Discovery")
            print("=" * 50)
            print("🤖 R2-A1 is scanning for UPnP devices...")
            print("📡 Using SSDP multicast discovery")
            print("⏱️  This will take about 12-15 seconds...")
            print()
            
            # Check scanner availability
            if not await self.ssdp_scanner.check_availability():
                print("❌ SSDP scanner not available")
                return
            
            # Perform SSDP discovery
            scan_id = f"ssdp_demo_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            
            print("🔍 Starting SSDP M-SEARCH discovery...")
            devices = await self.ssdp_scanner.scan("network", scan_id)
            
            # Display results
            print("\n🎉 SSDP Discovery Complete!")
            print(f"📊 Found {len(devices)} UPnP devices")
            print("=" * 50)
            
            if devices:
                for i, device in enumerate(devices, 1):
                    print(f"\n📱 UPnP Device {i}:")
                    print(f"   🌐 IP Address: {device.ip}")
                    print(f"   🏷️  Device Name: {device.hostname or 'Unknown'}")
                    print(f"   🏭 Manufacturer: {device.vendor or 'Unknown'}")
                    print(f"   📦 Device Type: {device.device_type}")
                    print(f"   💻 System Info: {device.os_info or 'Unknown'}")
                    
                    # Show UPnP-specific information
                    if device.metadata:
                        upnp_device_type = device.metadata.get('upnp_device_type', '')
                        ssdp_location = device.metadata.get('ssdp_location', '')
                        services_count = device.metadata.get('upnp_services_count', 0)
                        
                        if upnp_device_type:
                            print(f"   🔧 UPnP Type: {upnp_device_type}")
                        if services_count > 0:
                            print(f"   ⚙️  Services: {services_count} available")
                        if ssdp_location:
                            print(f"   📍 Description: {ssdp_location}")
                    
                    # Show discovered services
                    if device.services:
                        print(f"   🔌 UPnP Services: {len(device.services)}")
                        for service in device.services[:3]:  # Show first 3
                            service_info = service.get('info', 'Unknown')
                            if 'urn:schemas-upnp-org:service:' in service_info:
                                service_name = service_info.split(':')[-2] if ':' in service_info else service_info
                                print(f"      • {service_name}")
                
                # Device type summary
                device_types = {}
                for device in devices:
                    dtype = device.device_type
                    device_types[dtype] = device_types.get(dtype, 0) + 1
                
                print("\n📈 Discovery Summary:")
                for dtype, count in device_types.items():
                    print(f"   • {dtype.replace('_', ' ').title()}: {count}")
                
            else:
                print("📭 No UPnP devices discovered")
                print("\n💡 Troubleshooting tips:")
                print("   • Ensure you're connected to a network with UPnP devices")
                print("   • Check that smart TVs, media players, or routers are powered on")
                print("   • Some networks may block SSDP multicast traffic")
                print("   • Corporate networks often disable UPnP for security")
            
        except Exception as e:
            logger.error(f"❌ SSDP discovery failed: {e}")
            print(f"❌ Discovery error: {e}")
    
    async def stop(self) -> None:
        """Stop the demo."""
        try:
            logger.info("🛑 Stopping R2-A1 SSDP Demo...")
            
            self.demo_running = False
            
            if self.ssdp_scanner:
                await self.ssdp_scanner.stop()
            
            logger.info("✅ Demo stopped successfully")
            
        except Exception as e:
            logger.error(f"❌ Demo shutdown error: {e}")
    
    async def _on_device_discovered(self, event) -> None:
        """Handle device discovery events."""
        try:
            device_info = event.data.get('device', {})
            device_ip = device_info.get('ip', 'unknown')
            
            if device_ip not in [d.get('ip') for d in self.devices_found]:
                self.devices_found.append(device_info)
                print(f"🔍 Discovered: {device_ip}")
                
        except Exception as e:
            logger.debug(f"Event handling error: {e}")

async def main():
    """Main demo function."""
    demo = R2SSDPDemo()
    
    try:
        # Initialize demo
        if not await demo.initialize():
            logger.error("❌ Demo initialization failed")
            return 1
        
        # Start demo
        if not await demo.start():
            logger.error("❌ Demo startup failed")
            return 1
        
        # Wait a moment for system startup
        await asyncio.sleep(1)
        
        # Run SSDP discovery
        await demo.run_ssdp_discovery()
        
        # Stop demo
        await demo.stop()
        
        print("\n🎉 R2-A1 SSDP Demo completed successfully!")
        print("📊 Demonstrated SSDP/UPnP discovery capabilities")
        
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
        print("🚀 Starting R2-A1 SSDP Discovery Demo...")
        exit_code = asyncio.run(main())
        sys.exit(exit_code)
    except KeyboardInterrupt:
        print("\n🛑 Demo interrupted by user")
        sys.exit(0)
    except Exception as e:
        print(f"❌ Fatal error: {e}")
        sys.exit(1)
