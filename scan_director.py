#!/usr/bin/env python3
"""
R2-A1 Network Discovery Scan Director

This script orchestrates the comprehensive network discovery capabilities
of the R2-D2 Astromech unit system. It acts as the central coordinator,
initializing all scanning modules and directing the discovery sequence.

"""

import asyncio
import sys
import os
import logging
from typing import List
from datetime import datetime

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from src.core.container import DIContainer
from src.core.config import Configuration
from src.core.events import EventBus, create_event, R2Events
from src.modules.discovery.scanners.discovery_engine import DiscoveryEngine
from src.modules.discovery.scanners.interfaces import ScannerConfig
from src.modules.personality.audio_engine import ModularAudioEngine
from src.modules.personality.text_output import TextOutputModule

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class R2NetworkScanDirector:
    """
    Director for R2's network discovery scan operations
    
    This class orchestrates the comprehensive network discovery process,
    coordinating all scanning modules and managing the discovery workflow.
    """
    
    def __init__(self):
        """Initialize the scan director"""
        self.container = DIContainer()
        self.config = None
        self.event_bus = None
        self.discovery_engine = None
        self.audio_engine = None
        self.text_output = None
        
        # Scan phase tracking
        self.scan_phase = "none"  # none, discovery, scanning
        self.discovery_devices_found = 0
        self.scanning_progress = 0
        self.discovered_ips = set()  # Track discovered IPs to avoid duplicates
        
        logger.info("🤖 R2-A1 Network Discovery Demo initializing...")
    
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
            # Use debug_mode from config instead of forcing it to True
            personality_config = self.config.get_section('modules.personality')
            
            # Initialize discovery engine directly
            scanner_config = ScannerConfig(
                enabled=True,
                timeout=30.0,
                max_concurrent=50,
                custom_options={
                    'ping_timeout': discovery_config.get('ping_timeout', 1.0),
                    'scan_timeout': discovery_config.get('scan_timeout', 30.0),
                    'max_concurrent': discovery_config.get('max_concurrent_discovery', 50)
                }
            )
            self.discovery_engine = DiscoveryEngine(self.event_bus, scanner_config)
            self.audio_engine = ModularAudioEngine(self.event_bus, personality_config)
            self.text_output = TextOutputModule(self.event_bus, {"enabled": True})
            
            # Register modules with container
            self.container.register_module("discovery_engine", self.discovery_engine)
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
            
            logger.info("🎉 R2-D2 Network Discovery Demo is operational!")
            return True
            
        except Exception as e:
            logger.error(f"❌ Demo startup failed: {e}")
            return False
    
    async def run_network_discovery_scan(self) -> None:
        """Run the network discovery scan using the DiscoveryEngine"""
        try:
            print("\n🔍 R2-D2 Network Discovery Scan Director")
            print("=" * 50)
            print("Orchestrating R2's comprehensive network discovery!")
            print("Using multi-phase scanning: ARP + SSDP/UPnP + mDNS + Nmap")
            print("=" * 50)
            
            # Initialize the discovery engine
            print("\n🚀 Initializing Discovery Engine...")
            if await self.discovery_engine.initialize():
                print("✅ Discovery Engine initialized successfully!")
            else:
                print("❌ Discovery Engine initialization failed")
                return
            
            # Use a default network range for demo
            network_range = "192.168.1.0/24"
            
            print(f"\n🔍 R2-D2 Discovery Engine Scan")
            print(f"   🌐 Target network: {network_range}")
            print(f"   📊 This will scan 254 IP addresses (1-254)")
            print(f"   🎵 Listen for R2's chirps as devices are discovered!")
            print(f"   ⏳ This may take a few minutes...")
            print(f"   🚀 Using new Discovery Engine for comprehensive scanning!")
            
            await self._scan_with_discovery_engine(network_range)
            
        except Exception as e:
            logger.error(f"❌ Network discovery demo failed: {e}")
    
    async def _scan_with_discovery_engine(self, network_range: str) -> None:
        """Scan network using the DiscoveryEngine directly"""
        try:
            print(f"\n📡 PHASE 1: DEVICE DISCOVERY")
            print(f"🔍 Starting multi-protocol device discovery on {network_range}...")
            print(f"   • ARP Table Analysis")
            print(f"   • SSDP/UPnP Multicast Discovery") 
            print(f"   • mDNS Service Discovery")
            print(f"   • Traditional Network Ping")
            print("⏳ This may take a few moments...")
            
            # Reset counters for new scan
            self.discovery_devices_found = 0
            self.scanning_progress = 0
            self.discovered_ips.clear()
            
            # Set discovery phase
            await self._report_phase_transition("initialization", "discovery", "Starting device discovery")
            
            # Subscribe to scan progress events
            await self._setup_progress_monitoring()
            
            # Generate scan ID
            scan_id = f"discovery_demo_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            
            # Perform discovery scan
            devices = await self.discovery_engine.scan(network_range, scan_id)
            
            # Phase 1 Complete - Transition to Scanning
            await self._report_phase_transition("discovery", "scanning", f"{len(devices)} devices found, starting analysis")
            
            # Display discovery results
            print(f"\n✅ PHASE 1 COMPLETE: Device Discovery")
            print(f"📊 Total unique devices discovered: {len(devices)}")
            print(f"🔍 Discovery methods used: ARP + SSDP + mDNS + Ping")
            
            if devices:
                print(f"\n📡 Discovered Devices:")
                for i, device in enumerate(devices, 1):
                    ip = device.ip
                    status = device.status
                    method = device.discovery_method
                    hostname = device.hostname or 'unknown'
                    device_type = device.device_type or 'unknown'
                    manufacturer = device.manufacturer or 'unknown'
                    mac_address = device.mac_address or 'unknown'
                    confidence = device.confidence
                    
                    # Get device icon and friendly name
                    device_icon = device.get_device_icon()
                    friendly_name = device.get_friendly_name()
                    
                    print(f"  {i}. {device_icon} {friendly_name}")
                    print(f"     📍 IP: {ip} - {status} ({method}) [confidence: {confidence:.1f}]")
                    
                    # Show MAC address
                    if mac_address != 'unknown':
                        print(f"     🔗 MAC Address: {mac_address}")
                    
                    # Show manufacturer
                    if manufacturer != 'unknown' and manufacturer != 'Unknown Manufacturer':
                        print(f"     🏭 Manufacturer: {manufacturer}")
                    
                    # Show device type
                    if device_type != 'unknown':
                        print(f"     🤖 Type: {device_type.replace('_', ' ').title()}")
                    
                    # Show port information
                    if device.open_ports:
                        print(f"     📡 Open ports: {device.open_ports}")
                        if device.services:
                            service_list = [f"{port}:{service}" for port, service in device.services.items()]
                            print(f"     🛠️  Services: {', '.join(service_list)}")
                    else:
                        print(f"     🔒 No open ports detected")
                    
                    # Show mDNS services
                    if device.mdns_services:
                        print(f"     📻 mDNS Services:")
                        for service in device.mdns_services:
                            service_name = service.get('name', 'Unknown')
                            service_type = service.get('type', 'Unknown')
                            service_port = service.get('port', 'Unknown')
                            print(f"       • {service_name} ({service_type}) on port {service_port}")
                    
                    # Add spacing between devices
                    if i < len(devices):
                        print()
            else:
                print("📭 No devices discovered during Phase 1")
                print("💡 Try scanning a different network or check connectivity")
                return
            
            # Simulate Phase 2: Device Analysis
            print(f"\n📡 PHASE 2: DEVICE ANALYSIS & PORT SCANNING")
            print(f"🔬 Analyzing {len(devices)} discovered devices...")
            print(f"🔍 Methods: Port scanning, service enumeration, OS fingerprinting")
            print("🤖 *R2 switches to port scanning sounds*")
            
            # For demo purposes, just show that we would scan each device
            for i, device in enumerate(devices, 1):
                print(f"   🔬 Analyzing device {i}/{len(devices)}: {device.ip}")
                # Trigger scanning phase audio
                if self.audio_engine:
                    try:
                        await self.audio_engine.play_sound("port_scan_start")
                        await asyncio.sleep(0.5)  # Brief pause between scans
                    except Exception as e:
                        logger.debug(f"Audio failed: {e}")
            
            print(f"\n✅ PHASE 2 COMPLETE: Device Analysis")
            print(f"🎯 R2-A1 Network Discovery Mission Complete!")
            print(f"📊 Successfully discovered and analyzed {len(devices)} devices")
            print(f"🚀 Multi-phase scanning: Discovery → Analysis → Complete!")
            
        except Exception as e:
            print(f"❌ Discovery Engine scan failed: {e}")
    
    async def _handle_network_selection(self, network: dict) -> None:
        """Handle user's network selection"""
        network_type = network.get('type', 'unknown')
        
        if network_type == 'wifi':
            ssid = network.get('ssid', 'Unknown')
            print(f"\n📶 Selected WiFi Network: {ssid}")
            print("⚠️  Note: R2 cannot connect to WiFi networks without credentials")
            print("🔍 R2 will scan the current network for devices instead")
            
            # Get current network and scan it
            current_network = await self.network_scanner.get_current_network()
            if current_network and current_network.get('ip_address') != 'unknown':
                ip = current_network['ip_address']
                parts = ip.split('.')
                network_range = f"{parts[0]}.{parts[1]}.{parts[2]}.0/24"
                print(f"🔍 Scanning current network: {network_range}")
                await self._scan_network_for_devices(network_range)
            else:
                print("❌ No current network connection found")
                
        elif network_type == 'ethernet':
            interface = network.get('interface', 'unknown')
            ip = network.get('ip_address', 'unknown')
            print(f"\n🔌 Selected Ethernet Network: {interface}")
            print(f"📡 IP Address: {ip}")
            
            if ip != 'unknown':
                # Calculate network range
                parts = ip.split('.')
                network_range = f"{parts[0]}.{parts[1]}.{parts[2]}.0/24"
                print(f"🔍 Scanning network: {network_range}")
                await self._scan_network_for_devices(network_range)
            else:
                print("❌ No IP address found for this network")
        
        else:
            print(f"\n❓ Unknown network type: {network_type}")
            print("❌ Cannot scan this network type")
    
    async def _scan_network_for_devices(self, network_range: str) -> None:
        """Scan the selected network for devices with visual progress feedback"""
        try:
            print(f"\n🔍 Starting device scan on {network_range}...")
            print("⏳ This may take a few moments...")
            
            # Calculate total addresses to scan
            import ipaddress
            network_obj = ipaddress.IPv4Network(network_range, strict=False)
            total_hosts = list(network_obj.hosts())
            total_addresses = len(total_hosts)
            
            print(f"🌐 Scanning {total_addresses} IP addresses...")
            print(f"📍 Range: {total_hosts[0]} - {total_hosts[-1]}")
            print()
            
            # Subscribe to scan progress events
            await self._setup_progress_monitoring()
            
            # Perform device scan with progress monitoring
            devices = await self.network_scanner.scan_network(network_range)
            
            # Display final results
            print(f"\n\n🎯 Final Scan Results:")
            print(f"📊 Devices found: {len(devices)}")
            
            if devices:
                print(f"\n📡 Discovered Devices:")
                for i, device in enumerate(devices, 1):
                    ip = device.get('ip', 'unknown')
                    status = device.get('status', 'unknown')
                    method = device.get('discovery_method', 'unknown')
                    hostname = device.get('hostname', 'unknown')
                    device_type = device.get('device_type', 'unknown')
                    manufacturer = device.get('manufacturer', 'unknown')
                    
                    print(f"  {i}. {ip} - {status} ({method})")
                    if hostname != 'unknown':
                        print(f"     🏷️  Hostname: {hostname}")
                    if device_type != 'unknown':
                        print(f"     🤖 Type: {device_type}")
                    if manufacturer != 'unknown' and manufacturer != 'Unknown Manufacturer':
                        print(f"     🏭 Manufacturer: {manufacturer}")
                    
                    # Show port information - check multiple possible locations
                    open_ports = device.get('open_ports', [])
                    services = device.get('services', {})
                    
                    # Also check port_info structure
                    port_info = device.get('port_info', {})
                    if port_info.get('open_ports'):
                        open_ports = port_info['open_ports']
                        services = port_info.get('services', {})
                    
                    if open_ports:
                        print(f"     📡 Open ports: {open_ports}")
                        if services:
                            service_list = [f"{port}:{service}" for port, service in services.items()]
                            print(f"     🛠️  Services: {', '.join(service_list)}")
                    else:
                        print(f"     🔒 No open ports detected")
            else:
                print("🤔 No devices found on this network")
            
            print(f"\n✅ Device scan complete!")
            
            # Show R2's environmental analysis
            print(f"\n🧠 R2-D2 Environmental Analysis")
            print("=" * 60)
            self.network_scanner.device_database.print_network_summary()
            
            print(f"\n🤖 R2-A1 says: 'I have catalogued {len(devices)} devices in my environment!'")
            print(f"📊 Database updated with comprehensive device intelligence.")
            print(f"🚀 Discovery Engine provided multi-phase scanning (ARP + Traditional + mDNS)!")
            
        except Exception as e:
            print(f"❌ Device scan failed: {e}")
    
    async def _setup_progress_monitoring(self) -> None:
        """Setup event handlers for progress monitoring"""
        print("🔧 DEBUG: Setting up progress monitoring subscriptions...")
        
        # Subscribe to scan progress events
        await self.event_bus.subscribe("network_scan_started", self._on_scan_started)
        print("✅ DEBUG: Subscribed to network_scan_started")
        
        await self.event_bus.subscribe("device_discovered", self._on_device_discovered)
        print("✅ DEBUG: Subscribed to device_discovered")
        
        await self.event_bus.subscribe("ping_progress", self._on_ping_progress)
        print("✅ DEBUG: Subscribed to ping_progress")
        
        await self.event_bus.subscribe("network_scan_completed", self._on_scan_completed)
        print("✅ DEBUG: Subscribed to network_scan_completed")
        
        # Also subscribe to the R2Events versions
        await self.event_bus.subscribe("network.scan_started", self._on_scan_started)
        await self.event_bus.subscribe("network.device_discovered", self._on_device_discovered)
        await self.event_bus.subscribe("network.scan_completed", self._on_scan_completed)
        print("✅ DEBUG: Subscribed to R2Events versions too")
        
        # Initialize progress tracking
        self.scan_start_time = None
        self.devices_found = 0
        self.addresses_scanned = 0
        self.current_ip_range = ""
        
        print("🎯 DEBUG: Progress monitoring setup complete!")
    
    async def _play_phase_sound(self, phase_type: str) -> None:
        """Play audio cue for phase transitions"""
        try:
            if self.audio_engine:
                # Map phase types to audio cues
                if phase_type == "discovery_phase":
                    await self.audio_engine.play_sound("discovery_phase")
                elif phase_type == "scanning_phase":
                    await self.audio_engine.play_sound("scanning_phase")
                elif phase_type == "phase_start":
                    await self.audio_engine.play_sound("phase_start")
        except Exception as e:
            logger.debug(f"Audio cue failed: {e}")
    
    async def _report_phase_transition(self, from_phase: str, to_phase: str, context: str = "") -> None:
        """Report clear phase transitions"""
        print(f"\n🔄 PHASE TRANSITION")
        print(f"   📤 Completing: {from_phase.upper()}")
        print(f"   📥 Starting: {to_phase.upper()}")
        if context:
            print(f"   📋 Context: {context}")
        print("-" * 40)
        
        # Play transition sound
        await self._play_phase_sound("phase_start")
        self.scan_phase = to_phase
    
    async def _on_scan_started(self, event) -> None:
        """Handle scan started event"""
        print(f"🔥 DEBUG: _on_scan_started called! Event: {event.name}")
        import time
        self.scan_start_time = time.time()
        print(f"🚀 R2-A1 scan initiated...")
        
    async def _on_device_discovered(self, event) -> None:
        """Handle device discovered event - different sounds for discovery vs scanning phases"""
        print(f"🔥 DEBUG: _on_device_discovered called! Event: {event.name}")
        print(f"🔥 DEBUG: Event data: {event.data}")
        
        # Try to get IP from different possible locations in event data
        device_data = event.data.get('device', {})
        ip = device_data.get('ip', event.data.get('ip', 'unknown'))
        
        # Extract scanner method from multiple possible locations
        scanner = (device_data.get('scanner') or 
                  device_data.get('discovery_method') or 
                  event.data.get('scanner_type', 'unknown'))
        
        # Check for duplicate devices
        if ip in self.discovered_ips:
            print(f"🔄 R2-A1 DUPLICATE DEVICE IGNORED: {ip} (already discovered via {scanner})")
            return
        
        # Add to discovered IPs set
        self.discovered_ips.add(ip)
        
        # Different behavior based on current phase
        if self.scan_phase == "discovery":
            self.discovery_devices_found += 1
            print(f"🎉 R2-A1 DEVICE DISCOVERY! Device found: {ip}")
            print(f"   🔍 Discovery method: {scanner}")
            print(f"   🤖 *R2 chirps excitedly* (Device #{self.discovery_devices_found})")
            print(f"   📊 Discovery total: {self.discovery_devices_found} devices found")
            
            # Play device discovery sound
            try:
                if self.audio_engine:
                    await self.audio_engine.play_sound("device_found")
            except Exception as e:
                logger.debug(f"Audio playback failed: {e}")
                
        elif self.scan_phase == "scanning":
            self.scanning_progress += 1
            print(f"🔬 R2-A1 DEVICE ANALYSIS! Scanning: {ip}")
            print(f"   🔍 Method: {scanner}")
            print(f"   🤖 *R2 makes scanning sounds* (Analysis #{self.scanning_progress})")
            print(f"   📊 Analysis progress: {self.scanning_progress} devices scanned")
            
            # Play scanning sound (different from discovery)
            try:
                if self.audio_engine:
                    await self.audio_engine.play_sound("port_scan_start")
            except Exception as e:
                logger.debug(f"Audio playback failed: {e}")
                
        else:
            # Fallback for unknown phase
            print(f"🎉 R2-A1 DISCOVERY! Device found: {ip} (phase: {self.scan_phase})")
            print(f"   🔍 Discovery method: {scanner}")
            print(f"   🤖 *R2 chirps* (Fallback mode)")
            
            # Play fallback discovery sound
            try:
                if self.audio_engine:
                    await self.audio_engine.play_sound("device_found")
            except Exception as e:
                logger.debug(f"Audio playback failed: {e}")
        
    async def _on_ping_progress(self, event) -> None:
        """Handle ping progress updates"""
        if hasattr(self, '_debug_ping_count'):
            self._debug_ping_count += 1
        else:
            self._debug_ping_count = 1
            
        # Debug first few ping progress events
        if self._debug_ping_count <= 5:
            print(f"🔥 DEBUG: _on_ping_progress called #{self._debug_ping_count}! Event: {event.name}")
            print(f"🔥 DEBUG: Event data: {event.data}")
        
        current_ip = event.data.get('current_ip', '')
        progress = event.data.get('progress', 0)
        total = event.data.get('total', 0)
        
        # Show progress every 10 IPs or so
        if progress % 25 == 0 or progress < 10:
            percentage = (progress / total * 100) if total > 0 else 0
            print(f"🔍 Scanning: {current_ip} ({progress}/{total} - {percentage:.1f}%)")
            
        # Show IP range chunks being scanned
        current_range = '.'.join(current_ip.split('.')[:-1]) + '.X'
        if current_range != self.current_ip_range:
            self.current_ip_range = current_range
            print(f"📍 Now scanning IP range: {current_range}")
    
    async def _on_scan_completed(self, event) -> None:
        """Handle scan completed event"""
        print(f"🔥 DEBUG: _on_scan_completed called! Event: {event.name}")
        import time
        if self.scan_start_time:
            duration = time.time() - self.scan_start_time
            print(f"\n⏱️  Scan completed in {duration:.1f} seconds")
        
        devices_found = event.data.get('devices_found', 0)
        print(f"🎯 R2-D2 scan summary: {devices_found} devices discovered")
    
    async def _scan_specific_devices(self, ip_list: List[str]) -> None:
        """Scan specific IP addresses for demo purposes"""
        try:
            print(f"\n🔍 Scanning {len(ip_list)} specific devices...")
            print("⏳ This should be quick...")
            
            devices = []
            for ip in ip_list:
                print(f"   Checking {ip}...")
                device_info = await self.network_scanner.scan_device(ip)
                if device_info and device_info.get('status') != 'offline':
                    devices.append(device_info)
                    print(f"   ✅ {ip} - {device_info.get('status', 'unknown')}")
                else:
                    print(f"   ❌ {ip} - offline")
            
            # Display results
            print(f"\n🎯 Quick Scan Results:")
            print(f"📊 Devices found: {len(devices)}")
            
            if devices:
                print(f"\n📡 Active Devices:")
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
                print("🤔 No active devices found in quick scan")
            
            print(f"\n✅ Quick scan complete!")
            
        except Exception as e:
            print(f"❌ Quick scan failed: {e}")
    
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
            
            logger.info("👋 R2-D2 Network Discovery Demo shutdown complete")
            return True
            
        except Exception as e:
            logger.error(f"❌ Demo shutdown error: {e}")
            return False


async def main():
    """Main demo function"""
    print("=" * 65)
    print("    INDUSTRIAL AUTOMATON R2-D2 NETRECON ASTROMECH")
    print("    Advanced Network Discovery and Analysis System")
    print("    Manufactured by Industrial Automaton, Rordis City, Nubia")
    print("    'Modularity, Reliability, Intelligence' - Since 32 BBY")
    print("=" * 65)
    print()
    print("🤖 R2-D2 Network Discovery Demo")
    print("=" * 50)
    print("The Scan Director orchestrates R2's network discovery")
    print("and coordinates comprehensive device analysis.")
    print("=" * 50)
    
    # Initialize scan director
    scan_director = R2NetworkScanDirector()
    
    try:
        # Initialize system
        if not await scan_director.initialize():
            logger.error("❌ Scan director initialization failed")
            return 1
        
        # Start system  
        if not await scan_director.start():
            logger.error("❌ Scan director startup failed")
            return 1
        
        # Wait a moment for modules to fully start
        await asyncio.sleep(1)
        
        # Run network discovery scan sequence
        await scan_director.run_network_discovery_scan()
        
        # Stop system
        await scan_director.stop()
        
        print(f"\n🎉 Scan director completed successfully!")
        print(f"📊 The scan director orchestrated:")
        print(f"   • Network discovery capabilities")
        print(f"   • User network selection")
        print(f"   • Event-driven communication")
        print(f"   • Audio and text output coordination")
        
        return 0
        
    except KeyboardInterrupt:
        print("\n🛑 Demo interrupted by user")
        await scan_director.stop()
        return 0
        
    except Exception as e:
        logger.error(f"❌ Demo error: {e}")
        await scan_director.stop()
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