#!/usr/bin/env python3
"""
Simple Network Scanner Test

Test just the network scanner without AI module loading for faster testing.
This will help us debug the scanner logic and masscan detection.
"""

import asyncio
import sys
import os
from datetime import datetime

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from core.container import DIContainer
from core.config import get_config
from core.events import EventBus, R2Events
from modules.discovery.network_scanner import ModularNetworkScanner
from modules.discovery.device_database import DeviceDatabase

async def test_scanner():
    """Test the network scanner directly."""
    print("🔍 R2 Network Scanner Direct Test")
    print("=" * 50)
    
    # Create event bus
    event_bus = EventBus()
    await event_bus.initialize()
    
    # Get configuration
    config = get_config("config/r2_config.yaml", "testing")  # Use testing environment to disable AI
    discovery_config = config.get_module_config("discovery")
    
    # Override debug mode to see what's happening
    discovery_config['debug_mode'] = False  # Turn off debug mode for cleaner output
    
    print(f"📊 Scanner Configuration:")
    print(f"   Default Network: {discovery_config.get('default_network', '192.168.1.0/24')}")
    print(f"   Scan Timeout: {discovery_config.get('scan_timeout', 30)}s")
    print(f"   Debug Mode: {discovery_config.get('debug_mode', False)}")
    
    # Create network scanner
    scanner = ModularNetworkScanner(event_bus, discovery_config)
    
    # Set up event handlers to monitor scanning
    scan_results = {}
    
    def on_scan_started(event):
        print(f"🚀 Scan started: {event.data.get('scan_id')}")
        print(f"   Target: {event.data.get('network_range')}")
        scan_results['started'] = True
    
    def on_device_discovered(event):
        device = event.data.get('device', {})
        print(f"📱 Device discovered: {device.get('ip', 'unknown')}")
        if 'devices' not in scan_results:
            scan_results['devices'] = []
        scan_results['devices'].append(device)
    
    def on_scan_complete(event):
        print(f"✅ Scan completed: {event.data.get('scan_id')}")
        print(f"   Devices found: {event.data.get('device_count', 0)}")
        scan_results['completed'] = True
        scan_results['device_count'] = event.data.get('device_count', 0)
    
    # Subscribe to events
    event_bus.subscribe(R2Events.NETWORK_SCAN_STARTED, on_scan_started)
    event_bus.subscribe(R2Events.DEVICE_DISCOVERED, on_device_discovered)
    event_bus.subscribe(R2Events.NETWORK_SCAN_COMPLETED, on_scan_complete)
    
    try:
        # Initialize and start scanner
        print("\n🔧 Initializing scanner...")
        await scanner.initialize()
        await scanner.start()
        
        print("✅ Scanner initialized and started")
        
        # Test tool availability
        print(f"\n🛠️ Available tools: {scanner.available_tools}")
        
        # Run a scan
        print(f"\n🔍 Starting network scan...")
        start_time = datetime.now()
        
        devices = await scanner.scan_network("192.168.1.0/24")
        
        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()
        
        # Results
        print(f"\n📊 Scan Results:")
        print(f"   Duration: {duration:.2f} seconds")
        print(f"   Devices found: {len(devices)}")
        print(f"   Event system working: {scan_results.get('completed', False)}")
        
        if devices:
            print(f"\n📱 Discovered Devices:")
            for device in devices:
                print(f"   {device.get('ip', 'unknown')} - {device.get('hostname', 'unknown')}")
        else:
            print("\n❓ No devices found. This could be normal if:")
            print("   • Network is isolated/empty")
            print("   • Firewall blocking ICMP/masscan")
            print("   • Wrong network range")
            print("   • Tool permissions issue")
        
        # Check what actually happened in masscan
        print(f"\n🔍 Scanner Statistics:")
        print(f"   {scanner.stats}")
        
    except Exception as e:
        print(f"❌ Scanner test failed: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        # Cleanup
        print(f"\n🧹 Cleaning up...")
        await scanner.stop()
        await scanner.cleanup()
        await event_bus.shutdown()
        print("✅ Cleanup complete")

async def test_masscan_directly():
    """Test masscan directly to see if it's working."""
    print("\n🔧 Testing Masscan Directly")
    print("=" * 40)
    
    import subprocess
    import asyncio
    
    try:
        # Check if masscan is available
        which_result = await asyncio.create_subprocess_exec(
            'which', 'masscan',
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        stdout, stderr = await which_result.communicate()
        
        if which_result.returncode == 0:
            masscan_path = stdout.decode().strip()
            print(f"✅ Masscan found at: {masscan_path}")
        else:
            print(f"❌ Masscan not found in PATH")
            return
        
        # Test masscan version
        version_result = await asyncio.create_subprocess_exec(
            'masscan', '--version',
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        stdout, stderr = await version_result.communicate()
        
        if version_result.returncode == 0:
            print(f"📦 Masscan version: {stdout.decode().strip()}")
        
        # Test a simple masscan ping sweep
        print(f"\n🔍 Testing masscan ping sweep on 192.168.1.1-192.168.1.10...")
        
        ping_result = await asyncio.create_subprocess_exec(
            'masscan', '192.168.1.1-192.168.1.10',
            '--ping',
            '--rate', '100',
            '--output-format', 'json',
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        stdout, stderr = await asyncio.wait_for(ping_result.communicate(), timeout=30)
        
        print(f"Return code: {ping_result.returncode}")
        print(f"Stdout: {stdout.decode()}")
        if stderr:
            print(f"Stderr: {stderr.decode()}")
        
        if ping_result.returncode == 0:
            print("✅ Masscan ping test successful")
        else:
            print("❌ Masscan ping test failed")
            print("This might be due to:")
            print("   • Insufficient permissions (try with sudo)")
            print("   • Network configuration")
            print("   • Firewall rules")
        
    except Exception as e:
        print(f"❌ Direct masscan test failed: {e}")

async def main():
    """Main test function."""
    try:
        # Test masscan directly first
        await test_masscan_directly()
        
        # Then test the scanner
        await test_scanner()
        
    except KeyboardInterrupt:
        print("\n🛑 Test interrupted by user")
    except Exception as e:
        print(f"\n❌ Test failed: {e}")

if __name__ == "__main__":
    asyncio.run(main())
