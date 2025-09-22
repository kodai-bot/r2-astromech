#!/usr/bin/env python3
"""
Test mDNS Scanner

Simple test of the new mDNS discovery scanner to verify functionality.
"""

import asyncio
import sys
import os
from datetime import datetime

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from core.events import EventBus
from modules.discovery.scanners.interfaces import ScannerConfig
from modules.discovery.scanners.mdns_scanner import MDNSScanner

async def test_mdns_scanner():
    """Test the mDNS scanner."""
    print("🔍 R2-A1 mDNS Scanner Test")
    print("=" * 50)
    
    # Create event bus
    event_bus = EventBus()
    
    # Configure mDNS scanner
    config = ScannerConfig(
        enabled=True,
        timeout=15.0,
        custom_options={
            'scan_duration': 8,  # Quick test
            'service_types': [
                '_http._tcp',
                '_airplay._tcp', 
                '_ssh._tcp',
                '_ipp._tcp'
            ]
        }
    )
    
    # Create and initialize scanner
    scanner = MDNSScanner(event_bus, config)
    
    try:
        print("🔧 Initializing mDNS scanner...")
        if not await scanner.initialize():
            print("❌ mDNS scanner initialization failed")
            return
        
        print("✅ mDNS scanner initialized")
        print(f"📦 Available tools: {scanner.available_tools}")
        print(f"🛠️ Preferred tool: {scanner.preferred_tool}")
        
        # Test scan
        print(f"\n🔍 Starting mDNS scan...")
        start_time = datetime.now()
        
        devices = await scanner.scan("192.168.1.0/24", "test_scan_001")
        
        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()
        
        # Results
        print(f"\n📊 mDNS Scan Results:")
        print(f"   Duration: {duration:.2f} seconds")
        print(f"   Devices found: {len(devices)}")
        
        if devices:
            print(f"\n🎯 Discovered Devices via mDNS:")
            for i, device in enumerate(devices, 1):
                print(f"\n   Device #{i}:")
                print(f"      IP: {device.ip}")
                print(f"      Hostname: {device.hostname or 'unknown'}")
                print(f"      Device Type: {device.device_type or 'unknown'}")
                print(f"      Confidence: {device.confidence:.1%}")
                print(f"      Open Ports: {device.open_ports}")
                
                if device.mdns_services:
                    print(f"      mDNS Services:")
                    for service in device.mdns_services:
                        print(f"         - {service.get('name', 'unnamed')} ({service.get('type', 'unknown')})")
        else:
            print("\n❓ No devices found via mDNS. This could be normal if:")
            print("   • No devices advertise mDNS services")
            print("   • Network doesn't support multicast")
            print("   • Firewall blocking mDNS traffic")
            print("   • avahi-browse/dns-sd not installed")
        
    except Exception as e:
        print(f"❌ mDNS scanner test failed: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        # Cleanup
        print(f"\n🧹 Cleaning up...")
        await scanner.shutdown()
        print("✅ Cleanup complete")

async def main():
    """Main test function."""
    try:
        await test_mdns_scanner()
    except KeyboardInterrupt:
        print("\n🛑 Test interrupted by user")
    except Exception as e:
        print(f"\n❌ Test failed: {e}")

if __name__ == "__main__":
    asyncio.run(main())
