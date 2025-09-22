"""
Industrial Automaton R2 ARP Discovery Scanner

Advanced ARP-based reconnaissance module for R2-series astromech droids.
Discovers quiet network devices by analyzing ARP tables and performing stealth probing.
Essential for finding devices that evade traditional discovery methods.

Manufactured by: Industrial Automaton, Rordis City, Nubia
Component: R2 Network Analysis Suite - ARP Discovery Module  
Model: R2-ARP Advanced Reconnaissance Probe v1.2
Intellex Compatibility: IV and later

R2 Advanced Features:
- System ARP table mining with MAC vendor identification
- Active ARP probing with adaptive timing
- Stealth reconnaissance of quiet IoT devices and infrastructure
- Compatible with R2 modular sensor complement
- Field-serviceable design following IA standards

"Finds what others miss" - Industrial Automaton Engineering
"""

import asyncio
import re
import ipaddress
import subprocess
from typing import List, Dict, Any, Optional
from datetime import datetime

from .interfaces import DiscoveryScanner, DeviceInfo, ScannerConfig

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '../../..'))
from core.events import EventBus


class ARPScanner(DiscoveryScanner):
    """
    ARP-based device discovery scanner.
    
    Finds devices by examining the ARP table and performing ARP pings.
    Excellent for discovering quiet devices that don't respond to ICMP.
    """
    
    def __init__(self, event_bus: EventBus, config: ScannerConfig):
        """Initialize the ARP scanner."""
        super().__init__(event_bus, config)
        
        # ARP-specific configuration
        self.arp_timeout = config.custom_options.get('arp_timeout', 2.0)
        self.max_concurrent_arps = config.custom_options.get('max_concurrent_arps', 50)
        self.include_arp_scan = config.custom_options.get('include_arp_scan', True)
        
        # MAC vendor database (basic built-in lookup)
        self.vendor_prefixes = {
            '00:04:4b': 'Nvidia Corporation',
            '00:0c:29': 'VMware, Inc.',
            '00:15:5d': 'Microsoft Corporation',
            '00:16:3e': 'Xensource, Inc.',
            '00:1c:42': 'Parallels, Inc.',
            '00:50:56': 'VMware, Inc.',
            '08:00:27': 'Oracle VirtualBox',
            'ac:de:48': 'Intel Corporate',
            '00:e0:4c': 'Realtek Semiconductor Co., Ltd.',
            'c8:63:f1': 'Unknown Manufacturer',
            '28:d0:ea': 'Unknown Manufacturer',
            # Apple devices
            '00:03:93': 'Apple, Inc.',
            '00:0a:95': 'Apple, Inc.',
            '00:1b:63': 'Apple, Inc.',
            '00:1f:f3': 'Apple, Inc.',
            '00:21:e9': 'Apple, Inc.',
            '00:23:df': 'Apple, Inc.',
            '00:25:00': 'Apple, Inc.',
            '00:26:08': 'Apple, Inc.',
            '04:0c:ce': 'Apple, Inc.',
            '04:15:52': 'Apple, Inc.',
            '0c:3e:9f': 'Apple, Inc.',
            '0c:74:c2': 'Apple, Inc.',
            '14:20:5e': 'Apple, Inc.',
            '20:c9:d0': 'Apple, Inc.',
            '24:a0:74': 'Apple, Inc.',
            '28:cf:da': 'Apple, Inc.',
            '2c:be:08': 'Apple, Inc.',
            '30:90:ab': 'Apple, Inc.',
            '34:36:3b': 'Apple, Inc.',
            '40:cb:c0': 'Apple, Inc.',
            '44:d8:84': 'Apple, Inc.',
            '48:43:7c': 'Apple, Inc.',
            '4c:8d:79': 'Apple, Inc.',
            '50:ed:3c': 'Apple, Inc.',
            '54:72:4f': 'Apple, Inc.',
            '58:55:ca': 'Apple, Inc.',
            '5c:96:9d': 'Apple, Inc.',
            '64:b0:a6': 'Apple, Inc.',
            '68:ab:1e': 'Apple, Inc.',
            '6c:94:66': 'Apple, Inc.',
            '70:cd:60': 'Apple, Inc.',
            '7c:6d:62': 'Apple, Inc.',
            '80:be:05': 'Apple, Inc.',
            '84:38:35': 'Apple, Inc.',
            '88:63:df': 'Apple, Inc.',
            '8c:85:90': 'Apple, Inc.',
            '90:fd:61': 'Apple, Inc.',
            '98:5a:eb': 'Apple, Inc.',
            '9c:20:7b': 'Apple, Inc.',
            'a4:83:e7': 'Apple, Inc.',
            'a8:86:dd': 'Apple, Inc.',
            'ac:87:a3': 'Apple, Inc.',
            'b0:65:bd': 'Apple, Inc.',
            'b4:f0:ab': 'Apple, Inc.',
            'b8:78:2e': 'Apple, Inc.',
            'bc:67:1c': 'Apple, Inc.',
            'c0:9a:d0': 'Apple, Inc.',
            'c4:b3:01': 'Apple, Inc.',
            'c8:bc:c8': 'Apple, Inc.',
            'cc:25:ef': 'Apple, Inc.',
            'd0:23:db': 'Apple, Inc.',
            'd4:61:9d': 'Apple, Inc.',
            'd8:30:62': 'Apple, Inc.',
            'dc:56:e7': 'Apple, Inc.',
            'e0:ac:cb': 'Apple, Inc.',
            'e4:25:e7': 'Apple, Inc.',
            'e8:80:2e': 'Apple, Inc.',
            'ec:35:86': 'Apple, Inc.',
            'f0:d1:a9': 'Apple, Inc.',
            'f4:37:b7': 'Apple, Inc.',
            'f8:0d:ac': 'Apple, Inc.',
            'fc:25:3f': 'Apple, Inc.',
            # Add more as needed
        }
    
    async def check_availability(self) -> bool:
        """Check if ARP tools are available."""
        tools_to_check = ['arp', 'arping', 'ip']
        
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
                    self.logger.info(f"✅ ARP tool {tool} available at {tool_path}")
                    
            except Exception as e:
                self.logger.debug(f"Tool {tool} not available: {e}")
        
        if 'arp' in self.available_tools or 'ip' in self.available_tools:
            return True
        else:
            self.logger.warning("No ARP tools available (arp, ip)")
            return False
    
    async def scan(self, target: str, scan_id: str) -> List[DeviceInfo]:
        """
        Perform ARP discovery scan.
        
        Args:
            target: Network range (e.g., "192.168.1.0/24") 
            scan_id: Scan identifier for event correlation
            
        Returns:
            List of devices discovered via ARP
        """
        if not self.is_running:
            self.logger.error("Scanner not initialized")
            return []
        
        self.logger.info(f"🔍 Starting ARP discovery scan for {target}")
        
        try:
            # Parse network for scanning
            network = ipaddress.IPv4Network(target, strict=False)
            
            # Step 1: Read system ARP table
            arp_table_devices = await self._read_arp_table(network, scan_id)
            
            # Step 2: Active ARP scanning (if enabled)
            active_arp_devices = []
            if self.include_arp_scan:
                active_arp_devices = await self._active_arp_scan(network, scan_id)
            
            # Step 3: Merge and deduplicate devices
            all_devices = self._merge_arp_results(arp_table_devices, active_arp_devices, scan_id)
            
            # Step 4: Publish device discovered events for R2 audio feedback
            for i, device in enumerate(all_devices, 1):
                await self._publish_device_discovered(device, i, len(all_devices))
                await asyncio.sleep(0.3)  # Brief pause for audio feedback
            
            self.logger.info(f"✅ ARP scan complete: {len(all_devices)} devices discovered")
            return all_devices
            
        except Exception as e:
            self.logger.error(f"ARP scan failed: {e}")
            return []
    
    async def discover_hosts(self, network: str, scan_id: str) -> List[str]:
        """
        Discover hosts via ARP (implements DiscoveryScanner interface).
        
        Args:
            network: Network range
            scan_id: Scan identifier
            
        Returns:
            List of IP addresses discovered via ARP
        """
        devices = await self.scan(network, scan_id)
        return [device.ip for device in devices if device.ip]
    
    async def _read_arp_table(self, network: ipaddress.IPv4Network, scan_id: str) -> List[DeviceInfo]:
        """Read the system ARP table for existing entries."""
        devices = []
        
        try:
            # Try modern 'ip neigh' command first
            if 'ip' in self.available_tools:
                devices = await self._read_arp_table_ip(network, scan_id)
            
            # Fallback to 'arp' command
            if not devices and 'arp' in self.available_tools:
                devices = await self._read_arp_table_arp(network, scan_id)
            
            self.logger.info(f"Found {len(devices)} devices in ARP table")
            return devices
            
        except Exception as e:
            self.logger.error(f"Failed to read ARP table: {e}")
            return []
    
    async def _read_arp_table_ip(self, network: ipaddress.IPv4Network, scan_id: str) -> List[DeviceInfo]:
        """Read ARP table using 'ip neigh' command."""
        devices = []
        
        try:
            process = await asyncio.create_subprocess_exec(
                'ip', 'neigh', 'show',
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            stdout, stderr = await process.communicate()
            
            if process.returncode != 0:
                self.logger.warning(f"ip neigh failed: {stderr.decode()}")
                return devices
            
            # Parse 'ip neigh' output
            # Example: 192.168.1.1 dev eno1 lladdr aa:bb:cc:dd:ee:ff REACHABLE
            for line in stdout.decode().split('\n'):
                if not line.strip():
                    continue
                
                parts = line.split()
                if len(parts) >= 5:
                    try:
                        ip = parts[0]
                        mac = None
                        
                        # Find MAC address (lladdr)
                        if 'lladdr' in parts:
                            mac_index = parts.index('lladdr') + 1
                            if mac_index < len(parts):
                                mac = parts[mac_index]
                        
                        # Check if IP is in target network
                        ip_addr = ipaddress.IPv4Address(ip)
                        if ip_addr in network and mac:
                            device = DeviceInfo(
                                ip=ip,
                                mac_address=mac,
                                status='active',
                                discovery_method='arp_table',
                                scan_id=scan_id,
                                timestamp=datetime.now().isoformat()
                            )
                            
                            # Lookup manufacturer
                            manufacturer = self._lookup_vendor(mac)
                            if manufacturer:
                                device.manufacturer = manufacturer
                                device.confidence += 0.2
                            
                            devices.append(device)
                            
                    except Exception as e:
                        self.logger.debug(f"Failed to parse ARP line: {line} - {e}")
            
        except Exception as e:
            self.logger.error(f"ip neigh command failed: {e}")
        
        return devices
    
    async def _read_arp_table_arp(self, network: ipaddress.IPv4Network, scan_id: str) -> List[DeviceInfo]:
        """Read ARP table using 'arp' command."""
        devices = []
        
        try:
            process = await asyncio.create_subprocess_exec(
                'arp', '-a',
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            stdout, stderr = await process.communicate()
            
            if process.returncode != 0:
                self.logger.warning(f"arp command failed: {stderr.decode()}")
                return devices
            
            # Parse 'arp -a' output
            # Example: router.local (192.168.1.1) at aa:bb:cc:dd:ee:ff [ether] on eno1
            for line in stdout.decode().split('\n'):
                if not line.strip():
                    continue
                
                # Extract IP and MAC using regex
                ip_match = re.search(r'\((\d+\.\d+\.\d+\.\d+)\)', line)
                mac_match = re.search(r'at ([a-f0-9:]{17})', line, re.IGNORECASE)
                
                if ip_match and mac_match:
                    try:
                        ip = ip_match.group(1)
                        mac = mac_match.group(1)
                        
                        # Check if IP is in target network
                        ip_addr = ipaddress.IPv4Address(ip)
                        if ip_addr in network:
                            device = DeviceInfo(
                                ip=ip,
                                mac_address=mac,
                                status='active',
                                discovery_method='arp_table',
                                scan_id=scan_id,
                                timestamp=datetime.now().isoformat()
                            )
                            
                            # Extract hostname if available
                            hostname_match = re.search(r'^([^\s(]+)', line)
                            if hostname_match and hostname_match.group(1) != '?':
                                device.hostname = hostname_match.group(1)
                            
                            # Lookup manufacturer
                            manufacturer = self._lookup_vendor(mac)
                            if manufacturer:
                                device.manufacturer = manufacturer
                                device.confidence += 0.2
                            
                            devices.append(device)
                            
                    except Exception as e:
                        self.logger.debug(f"Failed to parse ARP line: {line} - {e}")
        
        except Exception as e:
            self.logger.error(f"arp command failed: {e}")
        
        return devices
    
    async def _active_arp_scan(self, network: ipaddress.IPv4Network, scan_id: str) -> List[DeviceInfo]:
        """Perform active ARP scanning of the network."""
        if 'arping' not in self.available_tools:
            self.logger.info("arping not available, skipping active ARP scan")
            return []
        
        devices = []
        hosts = list(network.hosts())
        
        # Limit concurrent ARP requests
        semaphore = asyncio.Semaphore(self.max_concurrent_arps)
        
        async def arp_ping(host_ip: str) -> Optional[DeviceInfo]:
            async with semaphore:
                try:
                    process = await asyncio.create_subprocess_exec(
                        'arping', '-c', '1', '-w', str(int(self.arp_timeout)), str(host_ip),
                        stdout=asyncio.subprocess.PIPE,
                        stderr=asyncio.subprocess.PIPE
                    )
                    
                    stdout, stderr = await asyncio.wait_for(
                        process.communicate(),
                        timeout=self.arp_timeout + 1
                    )
                    
                    if process.returncode == 0:
                        # Parse arping output for MAC address
                        output = stdout.decode()
                        mac_match = re.search(r'([a-f0-9:]{17})', output, re.IGNORECASE)
                        
                        if mac_match:
                            device = DeviceInfo(
                                ip=str(host_ip),
                                mac_address=mac_match.group(1),
                                status='active',
                                discovery_method='arp_ping',
                                scan_id=scan_id,
                                timestamp=datetime.now().isoformat()
                            )
                            
                            # Lookup manufacturer
                            manufacturer = self._lookup_vendor(device.mac_address)
                            if manufacturer:
                                device.manufacturer = manufacturer
                                device.confidence += 0.2
                            
                            return device
                    
                except asyncio.TimeoutError:
                    pass
                except Exception as e:
                    self.logger.debug(f"ARP ping failed for {host_ip}: {e}")
                
                return None
        
        self.logger.info(f"Starting active ARP scan of {len(hosts)} hosts...")
        
        # Run ARP pings concurrently
        tasks = [arp_ping(host) for host in hosts]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Collect successful results
        for result in results:
            if isinstance(result, DeviceInfo):
                devices.append(result)
        
        self.logger.info(f"Active ARP scan found {len(devices)} responsive devices")
        return devices
    
    def _merge_arp_results(self, table_devices: List[DeviceInfo], active_devices: List[DeviceInfo], scan_id: str) -> List[DeviceInfo]:
        """Merge ARP table and active scan results, removing duplicates."""
        device_map = {}
        
        # Add ARP table devices first
        for device in table_devices:
            device_map[device.ip] = device
        
        # Merge active scan results
        for device in active_devices:
            if device.ip in device_map:
                # Update existing device with additional info
                existing = device_map[device.ip]
                if not existing.mac_address and device.mac_address:
                    existing.mac_address = device.mac_address
                if not existing.manufacturer and device.manufacturer:
                    existing.manufacturer = device.manufacturer
                # Combine discovery methods
                existing.discovery_method = f"{existing.discovery_method},arp_ping"
                existing.confidence = min(existing.confidence + 0.1, 1.0)
            else:
                # Add new device
                device_map[device.ip] = device
        
        return list(device_map.values())
    
    def _lookup_vendor(self, mac_address: str) -> Optional[str]:
        """Lookup MAC address vendor using OUI prefix."""
        if not mac_address:
            return None
        
        try:
            # Extract OUI (first 3 octets)
            oui = ':'.join(mac_address.lower().split(':')[:3])
            
            # Check our built-in database
            if oui in self.vendor_prefixes:
                return self.vendor_prefixes[oui]
            
            # Check broader Apple range
            if oui.startswith(('00:03:', '00:0a:', '00:1b:', '00:1f:', '00:21:', '00:23:')):
                return 'Apple, Inc.'
            
            return None
            
        except Exception as e:
            self.logger.debug(f"Failed to lookup vendor for {mac_address}: {e}")
            return None
