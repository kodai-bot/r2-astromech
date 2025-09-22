#!/usr/bin/env python3
"""
Test ARP Scanner

Simple test of the new ARP discovery scanner to verify functionality.
"""

import asyncio
import sys
import os
from datetime import datetime

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from core.events import EventBus
from modules.discovery.scanners.interfaces import ScannerConfig
from modules.discovery.scanners.arp_scanner import ARPScanner

async def test_arp_scanner():
    """Test the ARP scanner."""
    print("🔍 R2-A1 ARP Scanner Test")
    print("=" * 50)
    
    # Create event bus
    event_bus = EventBus()
    
    # Configure ARP scanner
    config = ScannerConfig(
        enabled=True,
        timeout=15.0,
        custom_options={
            'arp_timeout': 2.0,
            'max_concurrent_arps': 20,  # Reduced for testing
            'include_arp_scan': False   # Only test ARP table reading
        }
    )
    
    # Create and initialize scanner
    scanner = ARPScanner(event_bus, config)
    
    try:
        print("🔧 Initializing ARP scanner...")
        if not await scanner.initialize():
            print("❌ ARP scanner initialization failed")
            return
        
        print("✅ ARP scanner initialized")
        print(f"📦 Available tools: {scanner.available_tools}")
        
        # Test scan
        print(f"\n🔍 Starting ARP scan...")
        start_time = datetime.now()
        
        devices = await scanner.scan("192.168.1.0/24", "test_scan_002")
        
        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()
        
        # Results
        print(f"\n📊 ARP Scan Results:")
        print(f"   Duration: {duration:.2f} seconds")
        print(f"   Devices found: {len(devices)}")
        
        if devices:
            print(f"\n🎯 Discovered Devices via ARP:")
            for i, device in enumerate(devices, 1):
                print(f"\n   Device #{i}:")
                print(f"      IP: {device.ip}")
                print(f"      MAC: {device.mac_address or 'unknown'}")
                print(f"      Hostname: {device.hostname or 'unknown'}")
                print(f"      Manufacturer: {device.manufacturer or 'unknown'}")
                print(f"      Discovery Method: {device.discovery_method}")
                print(f"      Confidence: {device.confidence:.1%}")
        else:
            print("\n❓ No devices found via ARP. This could mean:")
            print("   • ARP table is empty")
            print("   • No devices in target network")
            print("   • Permission issues reading ARP table")
        
        # Test just host discovery interface
        print(f"\n🔍 Testing host discovery interface...")
        hosts = await scanner.discover_hosts("192.168.1.0/24", "test_scan_003")
        print(f"📊 Host discovery found {len(hosts)} IP addresses: {hosts}")
        
    except Exception as e:
        print(f"❌ ARP scanner test failed: {e}")
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
        await test_arp_scanner()
    except KeyboardInterrupt:
        print("\n🛑 Test interrupted by user")
    except Exception as e:
        print(f"\n❌ Test failed: {e}")

if __name__ == "__main__":
    asyncio.run(main())
