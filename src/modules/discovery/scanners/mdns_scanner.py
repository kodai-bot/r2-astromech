"""
Industrial Automaton R2 mDNS Service Discovery Scanner

Advanced multicast DNS reconnaissance module for R2-series astromech droids.
Provides rich device intelligence by analyzing mDNS/Bonjour service advertisements.
Highest yield scanner for modern device identification and service enumeration.

Manufactured by: Industrial Automaton, Rordis City, Nubia
Component: R2 Network Analysis Suite - mDNS Discovery Module
Model: R2-mDNS Service Intelligence Probe v1.1  
Intellex Compatibility: IV and later

Enhanced R2 Capabilities:
- Multicast DNS service enumeration with friendly name detection
- Apple ecosystem device identification (iPhone, iPad, Mac, Apple TV)
- IoT device discovery (smart lights, cameras, speakers, printers)
- Network service mapping (SSH, HTTP, FTP, AirPlay, Spotify Connect)
- Compatible with R2 full-spectrum transceiver array

"Intelligence through listening" - Industrial Automaton R&D
"""

import asyncio
import json
import re
import ipaddress
from typing import List, Dict, Any, Optional
from datetime import datetime

from .interfaces import DiscoveryScanner, DeviceInfo, ScannerConfig

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '../../..'))
from core.events import EventBus


class MDNSScanner(DiscoveryScanner):
    """
    mDNS/Bonjour discovery scanner for enhanced device identification.
    
    Uses avahi-browse or dns-sd to discover mDNS services and devices.
    Provides rich device information including friendly names and service types.
    """
    
    def __init__(self, event_bus: EventBus, config: ScannerConfig):
        """Initialize the mDNS scanner."""
        super().__init__(event_bus, config)
        
        # mDNS-specific configuration
        self.scan_duration = config.custom_options.get('scan_duration', 10)  # seconds
        self.service_types = config.custom_options.get('service_types', [
            '_http._tcp',           # Web services
            '_https._tcp',          # Secure web services  
            '_ssh._tcp',            # SSH services
            '_ftp._tcp',            # FTP services
            '_smb._tcp',            # SMB file sharing
            '_afp._tcp',            # Apple File Protocol
            '_ipp._tcp',            # Internet Printing Protocol
            '_airplay._tcp',        # Apple AirPlay
            '_raop._tcp',           # Remote Audio Output Protocol
            '_spotify-connect._tcp', # Spotify Connect
            '_googlecast._tcp',     # Google Cast/Chromecast
            '_sonos._tcp',          # Sonos speakers
            '_hap._tcp',            # HomeKit Accessory Protocol
            '_homekit._tcp',        # HomeKit
            '_matter._tcp',         # Matter/Thread
            '_hue._tcp',            # Philips Hue
            '_camera._tcp',         # IP cameras
            '_nvr._tcp',            # Network Video Recorder
            '_workstation._tcp',    # Network workstations
            '_device-info._tcp',    # Device information
            '_amazon-zigbee._tcp',  # Amazon Echo/Alexa devices
            '_companion-link._tcp', # Apple TV/AirPlay
            '_sleep-proxy._udp',    # Apple sleep proxy
            '_homekit._tcp',        # Apple HomeKit
            '_esphomelib._tcp',     # ESPHome devices
            '_printer._tcp',        # Additional printer discovery
        ])
        
        # Tool preferences
        self.preferred_tool = None
        self.available_tools = {}
    
    async def check_availability(self) -> bool:
        """Check if mDNS discovery tools are available."""
        tools_to_check = ['avahi-browse', 'dns-sd']
        
        for tool in tools_to_check:
            try:
                process = await asyncio.create_subprocess_exec(
                    'which', tool,
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE
                )
                stdout, _ = await process.communicate()
                
                if process.returncode == 0:
                    tool_path = stdout.decode().strip()
                    self.available_tools[tool] = tool_path
                    self.logger.info(f"✅ mDNS tool {tool} available at {tool_path}")
                    
                    if not self.preferred_tool:
                        self.preferred_tool = tool
                        
            except Exception as e:
                self.logger.debug(f"Tool {tool} not available: {e}")
        
        if self.available_tools:
            self.logger.info(f"mDNS scanner using: {self.preferred_tool}")
            return True
        else:
            self.logger.warning("No mDNS tools available (avahi-browse, dns-sd)")
            return False
    
    async def scan(self, target: str, scan_id: str) -> List[DeviceInfo]:
        """
        Perform mDNS discovery scan.
        
        Args:
            target: Network range (used for IP filtering)
            scan_id: Scan identifier for event correlation
            
        Returns:
            List of devices discovered via mDNS
        """
        if not self.is_running:
            self.logger.error("Scanner not initialized")
            return []
        
        self.logger.info(f"🔍 Starting mDNS discovery scan for {target}")
        
        try:
            # Parse network for IP filtering
            network = ipaddress.IPv4Network(target, strict=False)
            
            # Discover mDNS services
            services = await self._discover_mdns_services(scan_id)
            
            # Convert services to device information
            devices = self._process_mdns_services(services, network, scan_id)
            
            # Publish device discovered events for R2 audio feedback
            for i, device in enumerate(devices, 1):
                await self._publish_device_discovered(device, i, len(devices))
                await asyncio.sleep(0.5)  # Brief pause for audio feedback
            
            self.logger.info(f"✅ mDNS scan complete: {len(devices)} devices discovered")
            return devices
            
        except Exception as e:
            self.logger.error(f"mDNS scan failed: {e}")
            return []
    
    async def discover_hosts(self, network: str, scan_id: str) -> List[str]:
        """
        Discover hosts via mDNS (implements DiscoveryScanner interface).
        
        Args:
            network: Network range
            scan_id: Scan identifier
            
        Returns:
            List of IP addresses discovered via mDNS
        """
        devices = await self.scan(network, scan_id)
        return [device.ip for device in devices if device.ip]
    
    async def _discover_mdns_services(self, scan_id: str) -> List[Dict[str, Any]]:
        """Discover mDNS services using available tools."""
        if self.preferred_tool == 'avahi-browse':
            return await self._discover_with_avahi(scan_id)
        elif self.preferred_tool == 'dns-sd':
            return await self._discover_with_dns_sd(scan_id)
        else:
            self.logger.error("No mDNS tool available")
            return []
    
    async def _discover_with_avahi(self, scan_id: str) -> List[Dict[str, Any]]:
        """Discover services using avahi-browse."""
        services = []
        
        try:
            # Run avahi-browse for all service types
            cmd = [
                'avahi-browse',
                '--all',                    # Browse all service types
                '--resolve',                # Resolve service details
                '--no-db-lookup',          # Don't lookup in service type database
                '--parsable',              # Machine-readable output
                '--terminate'              # Terminate after scan_duration
            ]
            
            self.logger.info(f"🔍 Running avahi-browse for mDNS discovery...")
            
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            # Wait for scan duration with timeout
            try:
                stdout, stderr = await asyncio.wait_for(
                    process.communicate(), 
                    timeout=self.scan_duration + 5
                )
                
                if stdout:
                    services = self._parse_avahi_output(stdout.decode())
                    
                if stderr and process.returncode != 0:
                    self.logger.warning(f"avahi-browse warnings: {stderr.decode()}")
                    
            except asyncio.TimeoutError:
                # Kill the process if it runs too long
                process.kill()
                await process.wait()
                self.logger.warning("avahi-browse scan timed out")
            
            self.logger.info(f"avahi-browse discovered {len(services)} services")
            return services
            
        except Exception as e:
            self.logger.error(f"avahi-browse failed: {e}")
            return []
    
    async def _discover_with_dns_sd(self, scan_id: str) -> List[Dict[str, Any]]:
        """Discover services using dns-sd (Bonjour)."""
        services = []
        
        try:
            # dns-sd requires browsing specific service types
            for service_type in self.service_types:
                cmd = [
                    'dns-sd',
                    '-B',                   # Browse for services
                    service_type,           # Service type to browse
                    'local.'               # Domain
                ]
                
                self.logger.debug(f"Browsing mDNS service: {service_type}")
                
                process = await asyncio.create_subprocess_exec(
                    *cmd,
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE
                )
                
                try:
                    stdout, stderr = await asyncio.wait_for(
                        process.communicate(),
                        timeout=self.scan_duration / len(self.service_types)
                    )
                    
                    if stdout:
                        service_entries = self._parse_dns_sd_output(stdout.decode(), service_type)
                        services.extend(service_entries)
                        
                except asyncio.TimeoutError:
                    process.kill()
                    await process.wait()
            
            self.logger.info(f"dns-sd discovered {len(services)} services")
            return services
            
        except Exception as e:
            self.logger.error(f"dns-sd failed: {e}")
            return []
    
    def _parse_avahi_output(self, output: str) -> List[Dict[str, Any]]:
        """Parse avahi-browse output into service information."""
        services = []
        
        for line in output.strip().split('\n'):
            if not line or line.startswith('#'):
                continue
            
            try:
                # avahi-browse parsable format:
                # =;eth0;IPv4;My Device;_http._tcp;local;my-device.local;192.168.1.100;80;"path=/admin"
                if line.startswith('='):
                    parts = line.split(';')
                    if len(parts) >= 8:
                        service = {
                            'interface': parts[1],
                            'protocol': parts[2],
                            'name': parts[3],
                            'service_type': parts[4],
                            'domain': parts[5],
                            'hostname': parts[6],
                            'ip': parts[7],
                            'port': parts[8] if len(parts) > 8 else None,
                            'txt_record': parts[9] if len(parts) > 9 else None,
                            'discovery_method': 'mdns_avahi'
                        }
                        services.append(service)
                        
            except Exception as e:
                self.logger.debug(f"Failed to parse avahi line: {line} - {e}")
        
        return services
    
    def _parse_dns_sd_output(self, output: str, service_type: str) -> List[Dict[str, Any]]:
        """Parse dns-sd output into service information.""" 
        services = []
        
        for line in output.strip().split('\n'):
            if 'Add' in line and service_type in line:
                try:
                    # dns-sd output format varies, extract what we can
                    # Example: "13:45:30.123  Add  3  4 local.  _http._tcp.  My Device"
                    match = re.search(r'Add.*?(\d+)\s+(\d+)\s+(\S+)\s+(\S+)\s+(.+)', line)
                    if match:
                        service = {
                            'name': match.group(5).strip(),
                            'service_type': service_type,
                            'domain': match.group(3),
                            'discovery_method': 'mdns_dns_sd'
                        }
                        services.append(service)
                        
                except Exception as e:
                    self.logger.debug(f"Failed to parse dns-sd line: {line} - {e}")
        
        return services
    
    def _process_mdns_services(self, services: List[Dict[str, Any]], network: ipaddress.IPv4Network, scan_id: str) -> List[DeviceInfo]:
        """Convert mDNS services to DeviceInfo objects."""
        devices = {}  # Use dict to deduplicate by IP
        
        for service in services:
            try:
                ip = service.get('ip')
                if not ip:
                    continue
                
                # Filter to target network
                try:
                    ip_addr = ipaddress.IPv4Address(ip)
                    if ip_addr not in network:
                        continue
                except:
                    continue
                
                # Get or create device info
                if ip not in devices:
                    devices[ip] = DeviceInfo(
                        ip=ip,
                        status='active',
                        discovery_method='mdns',
                        scan_id=scan_id,
                        timestamp=datetime.now().isoformat(),
                        mdns_services=[]
                    )
                
                device = devices[ip]
                
                # Update device information from mDNS service
                if service.get('hostname') and not device.hostname:
                    device.hostname = service['hostname'].replace('.local', '')
                
                if service.get('name') and not device.hostname:
                    device.hostname = service['name']
                
                # Add service information
                service_info = {
                    'name': service.get('name', ''),
                    'type': service.get('service_type', ''),
                    'port': service.get('port'),
                    'txt_record': service.get('txt_record', '')
                }
                device.mdns_services.append(service_info)
                
                # Classify device type based on services and hostname
                device_type = self._classify_device_from_mdns(device.mdns_services, device.hostname)
                if device_type:
                    device.device_type = device_type
                    device.confidence = min(device.confidence + 0.3, 1.0)
                
                # Extract port information
                if service.get('port'):
                    try:
                        port = int(service['port'])
                        if port not in device.open_ports:
                            device.open_ports.append(port)
                    except:
                        pass
                
            except Exception as e:
                self.logger.debug(f"Failed to process mDNS service: {service} - {e}")
        
        return list(devices.values())
    
    def _classify_device_from_mdns(self, services: List[Dict[str, Any]], hostname: Optional[str] = None) -> Optional[str]:
        """Classify device type based on mDNS services."""
        service_types = [s.get('type', '') for s in services]
        service_names = [s.get('name', '').lower() for s in services]
        
        # Game consoles - Check hostname/service names first
        all_names = service_names.copy()
        if hostname:
            all_names.append(hostname.lower())
        
        if any('ps4' in name or 'playstation' in name for name in all_names):
            return 'game_console'
        if any('xbox' in name or 'nintendo' in name for name in all_names):
            return 'game_console'
        
        # Smart speakers - More specific detection
        if any('_sonos._tcp' in st for st in service_types):
            return 'smart_speaker'
        if any('echo' in name or 'alexa' in name or 'amazon' in name for name in all_names):
            return 'smart_speaker'
        if any('homepod' in name or 'google home' in name for name in all_names):
            return 'smart_speaker'
        
        # Gaming devices with Spotify (like PS4) should be game consoles, not speakers
        spotify_services = [s for s in services if '_spotify-connect._tcp' in s.get('type', '')]
        if spotify_services:
            # Check if it's a gaming device by hostname or service name
            spotify_names = all_names + [s.get('name', '').lower() for s in spotify_services]
            if any(gaming_term in name for name in spotify_names for gaming_term in ['ps4', 'ps5', 'xbox', 'playstation']):
                return 'game_console'
            # Otherwise, it's likely a smart speaker
            return 'smart_speaker'
        
        # Apple devices
        if any('_airplay._tcp' in st or '_raop._tcp' in st for st in service_types):
            return 'apple_device'
        
        # Printers
        if any('_ipp._tcp' in st or '_printer._tcp' in st for st in service_types):
            return 'printer'
        
        # Smart home devices
        if any('_hap._tcp' in st or '_homekit._tcp' in st or '_matter._tcp' in st for st in service_types):
            return 'smart_home_device'
        
        # Cameras/NVR
        if any('_camera._tcp' in st or '_nvr._tcp' in st for st in service_types):
            return 'camera'
        
        # Media devices
        if any('_googlecast._tcp' in st for st in service_types):
            return 'media_device'
        
        # Network infrastructure
        if any('_ssh._tcp' in st and '_http._tcp' in st for st in service_types):
            return 'network_device'
        
        # Servers/NAS (like "Cibo")
        if any('_smb._tcp' in st and '_ftp._tcp' in st for st in service_types):
            return 'server'
        
        # Generic network service
        if any('_http._tcp' in st or '_https._tcp' in st for st in service_types):
            return 'network_service'
        
        return None
