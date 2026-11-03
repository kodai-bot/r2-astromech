"""
Industrial Automaton R2 SSDP/UPnP Discovery Scanner

SSDP (Simple Service Discovery Protocol) scanner for UPnP device discovery.
Implements M-SEARCH multicast discovery to find UPnP devices and services.

Manufactured by: Industrial Automaton, Rordis City, Nubia
Product Line: R2-series Astromech Network Discovery Module
Model: R2-SSDP Advanced UPnP Discovery Scanner v1.0

Features:
- SSDP M-SEARCH multicast discovery
- UPnP device and service enumeration
- Device description XML parsing
- Smart device identification (IoT, media, network infrastructure)
- Non-invasive discovery without device interaction

"Modularity, Reliability, Intelligence" - Industrial Automaton Quality Since 32 BBY
"""

import asyncio
import socket
import xml.etree.ElementTree as ET
from typing import List, Dict, Any, Optional, Tuple
import aiohttp
from datetime import datetime

from .interfaces import DiscoveryScanner, DeviceInfo, ScannerConfig
from core.events import EventBus

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '../../..'))


class SSDPScanner(DiscoveryScanner):
    """
    SSDP/UPnP discovery scanner for enhanced device identification.
    
    Uses SSDP M-SEARCH multicast messages to discover UPnP devices and services.
    Provides rich device information including manufacturer, model, and services.
    """
    
    def __init__(self, event_bus: EventBus, config: ScannerConfig):
        """Initialize the SSDP scanner."""
        super().__init__(event_bus, config)
        
        # SSDP configuration
        self.multicast_addr = "239.255.255.250"
        self.multicast_port = 1900
        self.scan_timeout = config.custom_options.get('scan_timeout', 10)  # seconds
        self.max_responses = config.custom_options.get('max_responses', 100)
        self.follow_descriptions = config.custom_options.get('follow_descriptions', True)
        self.description_timeout = config.custom_options.get('description_timeout', 5)
        
        # Search targets for different device types
        self.search_targets = config.custom_options.get('search_targets', [
            "upnp:rootdevice",              # All UPnP root devices
            "ssdp:all",                     # All SSDP services
            "urn:schemas-upnp-org:device:Basic:1",  # Basic UPnP devices
            "urn:schemas-upnp-org:device:MediaRenderer:1",  # Media renderers (TVs, speakers)
            "urn:schemas-upnp-org:device:MediaServer:1",    # Media servers (NAS, DLNA)
            "urn:schemas-upnp-org:device:InternetGatewayDevice:1",  # Routers/gateways
            "urn:schemas-upnp-org:device:WANDevice:1",      # WAN devices
            "urn:schemas-upnp-org:device:LANDevice:1",      # LAN devices
            "urn:dial-multiscreen-org:service:dial:1",      # Chromecast/Smart TV
            "urn:microsoft.com:service:X_MS_MediaReceiverRegistrar:1",  # Windows Media
        ])
        
        # Device type classification patterns
        self.device_patterns = {
            'router': ['router', 'gateway', 'modem', 'access point'],
            'media_player': ['chromecast', 'roku', 'apple tv', 'fire tv', 'smart tv'],
            'speaker': ['speaker', 'sonos', 'bose', 'harman kardon', 'yamaha'],
            'nas': ['nas', 'storage', 'synology', 'qnap', 'drobo', 'buffalo'],
            'printer': ['printer', 'scanner', 'canon', 'epson', 'hp', 'brother'],
            'smart_home': ['hue', 'nest', 'ecobee', 'smartthings', 'wemo'],
            'camera': ['camera', 'webcam', 'ip camera', 'security camera'],
            'game_console': ['xbox', 'playstation', 'nintendo', 'steam'],
        }
        
        self.logger.info("SSDP/UPnP scanner initialized")
    
    async def check_availability(self) -> bool:
        """Check if SSDP scanning is available."""
        try:
            # Test multicast socket creation
            sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            sock.close()
            
            self.logger.debug("SSDP scanner availability check passed")
            return True
            
        except Exception as e:
            self.logger.warning(f"SSDP scanner not available: {e}")
            return False
    
    async def scan(self, target: str, scan_id: str) -> List[DeviceInfo]:
        """
        Perform SSDP/UPnP discovery scan.
        
        Args:
            target: Network range (not used for SSDP multicast)
            scan_id: Scan identifier for event correlation
            
        Returns:
            List of devices discovered via SSDP/UPnP
        """
        if not self.is_running:
            self.logger.error("Scanner not initialized")
            return []
        
        self.logger.info("🔍 Starting SSDP/UPnP discovery scan")
        
        try:
            # Perform SSDP discovery for each search target
            all_devices = {}  # Use dict to deduplicate by URL
            
            for search_target in self.search_targets:
                self.logger.debug(f"SSDP M-SEARCH for: {search_target}")
                devices = await self._ssdp_msearch(search_target, scan_id)
                
                for device in devices:
                    device_key = device.get('location', device.get('usn', ''))
                    if device_key and device_key not in all_devices:
                        all_devices[device_key] = device
                
                # Brief pause between search targets
                await asyncio.sleep(0.5)
            
            # Convert raw SSDP responses to DeviceInfo objects
            discovered_devices = []
            for i, (location, device_data) in enumerate(all_devices.items(), 1):
                try:
                    device_info = await self._create_device_info(device_data, scan_id)
                    if device_info:
                        discovered_devices.append(device_info)
                        
                        # Publish device discovered event for R2 audio feedback
                        await self._publish_device_discovered(device_info, i, len(all_devices))
                        await asyncio.sleep(0.2)  # Brief pause for audio feedback
                        
                except Exception as e:
                    self.logger.warning(f"Failed to process SSDP device {location}: {e}")
            
            self.logger.info(f"✅ SSDP scan complete: {len(discovered_devices)} UPnP devices discovered")
            return discovered_devices
            
        except Exception as e:
            self.logger.error(f"SSDP scan failed: {e}")
            return []
    
    async def _ssdp_msearch(self, search_target: str, scan_id: str) -> List[Dict[str, Any]]:
        """
        Perform SSDP M-SEARCH for a specific target.
        
        Args:
            search_target: SSDP search target (e.g., "upnp:rootdevice")
            scan_id: Scan identifier
            
        Returns:
            List of raw SSDP response data
        """
        responses = []
        
        try:
            # Create SSDP M-SEARCH message
            msearch_msg = (
                f"M-SEARCH * HTTP/1.1\r\n"
                f"HOST: {self.multicast_addr}:{self.multicast_port}\r\n"
                f"MAN: \"ssdp:discover\"\r\n"
                f"ST: {search_target}\r\n"
                f"MX: {self.scan_timeout}\r\n\r\n"
            ).encode('utf-8')
            
            # Create UDP socket for multicast
            sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            sock.settimeout(self.scan_timeout)
            
            # Send M-SEARCH message
            sock.sendto(msearch_msg, (self.multicast_addr, self.multicast_port))
            
            # Listen for responses
            start_time = datetime.now()
            while (datetime.now() - start_time).total_seconds() < self.scan_timeout:
                try:
                    data, addr = sock.recvfrom(4096)
                    response = self._parse_ssdp_response(data.decode('utf-8', errors='ignore'), addr)
                    if response:
                        responses.append(response)
                        
                    if len(responses) >= self.max_responses:
                        break
                        
                except socket.timeout:
                    break
                except Exception as e:
                    self.logger.debug(f"SSDP response parsing error: {e}")
                    continue
            
            sock.close()
            
        except Exception as e:
            self.logger.error(f"SSDP M-SEARCH failed for {search_target}: {e}")
        
        return responses
    
    def _parse_ssdp_response(self, response_data: str, addr: Tuple[str, int]) -> Optional[Dict[str, Any]]:
        """
        Parse SSDP response message.
        
        Args:
            response_data: Raw SSDP response
            addr: Source address tuple (ip, port)
            
        Returns:
            Parsed response data or None if invalid
        """
        try:
            lines = response_data.strip().split('\r\n')
            if not lines or not lines[0].startswith('HTTP/1.1 200 OK'):
                return None
            
            headers = {}
            for line in lines[1:]:
                if ':' in line:
                    key, value = line.split(':', 1)
                    headers[key.strip().lower()] = value.strip()
            
            # Extract key SSDP fields
            response = {
                'source_ip': addr[0],
                'source_port': addr[1],
                'location': headers.get('location', ''),
                'usn': headers.get('usn', ''),
                'st': headers.get('st', ''),
                'server': headers.get('server', ''),
                'cache_control': headers.get('cache-control', ''),
                'headers': headers,
                'timestamp': datetime.now().isoformat()
            }
            
            return response
            
        except Exception as e:
            self.logger.debug(f"Failed to parse SSDP response: {e}")
            return None
    
    async def _create_device_info(self, ssdp_data: Dict[str, Any], scan_id: str) -> Optional[DeviceInfo]:
        """
        Create DeviceInfo from SSDP response data.
        
        Args:
            ssdp_data: Parsed SSDP response
            scan_id: Scan identifier
            
        Returns:
            DeviceInfo object or None if creation fails
        """
        try:
            ip = ssdp_data['source_ip']
            
            # Start with basic device info from SSDP
            device_info = DeviceInfo(
                ip=ip,
                hostname="",
                mac="",
                vendor="",
                device_type="upnp_device",
                os_info="",
                open_ports=[],
                services=[],
                scan_id=scan_id,
                scanner="ssdp",
                discovery_method="ssdp_msearch"
            )
            
            # Add SSDP-specific data
            device_info.metadata.update({
                'ssdp_usn': ssdp_data.get('usn', ''),
                'ssdp_st': ssdp_data.get('st', ''),
                'ssdp_server': ssdp_data.get('server', ''),
                'ssdp_location': ssdp_data.get('location', ''),
                'ssdp_timestamp': ssdp_data.get('timestamp', '')
            })
            
            # Extract device info from server header
            server = ssdp_data.get('server', '')
            if server:
                device_info.os_info = server
                device_info.vendor = self._extract_vendor_from_server(server)
            
            # Try to get detailed device description
            if self.follow_descriptions and ssdp_data.get('location'):
                description_data = await self._fetch_device_description(ssdp_data['location'])
                if description_data:
                    self._enrich_device_from_description(device_info, description_data)
            
            # Classify device type
            device_info.device_type = self._classify_device_type(device_info)
            
            return device_info
            
        except Exception as e:
            self.logger.warning(f"Failed to create device info from SSDP data: {e}")
            return None
    
    async def _fetch_device_description(self, location_url: str) -> Optional[Dict[str, Any]]:
        """
        Fetch UPnP device description XML.
        
        Args:
            location_url: URL to device description
            
        Returns:
            Parsed device description data
        """
        try:
            timeout = aiohttp.ClientTimeout(total=self.description_timeout)
            async with aiohttp.ClientSession(timeout=timeout) as session:
                async with session.get(location_url) as response:
                    if response.status == 200:
                        xml_content = await response.text()
                        return self._parse_device_description_xml(xml_content)
                        
        except Exception as e:
            self.logger.debug(f"Failed to fetch device description from {location_url}: {e}")
            
        return None
    
    def _parse_device_description_xml(self, xml_content: str) -> Dict[str, Any]:
        """
        Parse UPnP device description XML.
        
        Args:
            xml_content: XML content string
            
        Returns:
            Parsed device data
        """
        try:
            root = ET.fromstring(xml_content)
            
            # Define XML namespaces
            namespaces = {
                'device': 'urn:schemas-upnp-org:device-1-0',
                'root': 'urn:schemas-upnp-org:device-1-0'
            }
            
            device_data = {}
            
            # Find device element
            device_elem = root.find('.//device', namespaces) or root.find('.//device')
            if device_elem is not None:
                # Extract device information
                for field in ['deviceType', 'friendlyName', 'manufacturer', 'manufacturerURL', 
                             'modelDescription', 'modelName', 'modelNumber', 'modelURL',
                             'serialNumber', 'UDN', 'presentationURL']:
                    elem = device_elem.find(field) or device_elem.find(f'.//{field}')
                    if elem is not None and elem.text:
                        device_data[field.lower()] = elem.text.strip()
                
                # Extract service list
                services = []
                service_list = device_elem.find('.//serviceList') or device_elem.find('serviceList')
                if service_list is not None:
                    for service in service_list.findall('.//service') or service_list.findall('service'):
                        service_data = {}
                        for sfield in ['serviceType', 'serviceId', 'controlURL', 'eventSubURL', 'SCPDURL']:
                            selem = service.find(sfield)
                            if selem is not None and selem.text:
                                service_data[sfield.lower()] = selem.text.strip()
                        if service_data:
                            services.append(service_data)
                
                device_data['services'] = services
            
            return device_data
            
        except Exception as e:
            self.logger.debug(f"Failed to parse device description XML: {e}")
            return {}
    
    def _enrich_device_from_description(self, device_info: DeviceInfo, description_data: Dict[str, Any]) -> None:
        """
        Enrich DeviceInfo with data from device description.
        
        Args:
            device_info: DeviceInfo to enrich
            description_data: Parsed device description
        """
        # Set friendly name as hostname
        if description_data.get('friendlyname'):
            device_info.hostname = description_data['friendlyname']
        
        # Set manufacturer as vendor
        if description_data.get('manufacturer'):
            device_info.vendor = description_data['manufacturer']
        
        # Add model info to OS info
        model_parts = []
        if description_data.get('modelname'):
            model_parts.append(description_data['modelname'])
        if description_data.get('modelnumber'):
            model_parts.append(f"v{description_data['modelnumber']}")
        if model_parts:
            device_info.os_info = f"{device_info.os_info} - {' '.join(model_parts)}"
        
        # Add UPnP services
        if description_data.get('services'):
            for service in description_data['services']:
                service_type = service.get('servicetype', '')
                if service_type:
                    device_info.services.append({
                        'name': 'upnp',
                        'version': '',
                        'info': service_type
                    })
        
        # Add metadata
        device_info.metadata.update({
            'upnp_device_type': description_data.get('devicetype', ''),
            'upnp_model_description': description_data.get('modeldescription', ''),
            'upnp_serial_number': description_data.get('serialnumber', ''),
            'upnp_udn': description_data.get('udn', ''),
            'upnp_presentation_url': description_data.get('presentationurl', ''),
            'upnp_services_count': len(description_data.get('services', []))
        })
    
    def _extract_vendor_from_server(self, server: str) -> str:
        """Extract vendor information from server header."""
        server_lower = server.lower()
        
        # Common vendor patterns
        vendor_patterns = {
            'linux': 'Linux',
            'windows': 'Microsoft', 
            'darwin': 'Apple',
            'roku': 'Roku',
            'chromecast': 'Google',
            'samsung': 'Samsung',
            'lg': 'LG Electronics',
            'sony': 'Sony',
            'panasonic': 'Panasonic',
            'philips': 'Philips',
            'netgear': 'Netgear',
            'linksys': 'Linksys',
            'dlink': 'D-Link',
            'tp-link': 'TP-Link',
            'asus': 'ASUS',
            'synology': 'Synology',
            'qnap': 'QNAP'
        }
        
        for pattern, vendor in vendor_patterns.items():
            if pattern in server_lower:
                return vendor
        
        return ""
    
    def _classify_device_type(self, device_info: DeviceInfo) -> str:
        """Classify device type based on available information."""
        
        # Check device info fields
        search_text = ' '.join([
            device_info.hostname.lower(),
            device_info.vendor.lower(),
            device_info.os_info.lower(),
            (device_info.metadata.get('upnp_device_type') or '').lower(),
            (device_info.metadata.get('ssdp_st') or '').lower(),
            (device_info.metadata.get('ssdp_server') or '').lower()
        ])
        
        # Match against device patterns
        for device_type, patterns in self.device_patterns.items():
            for pattern in patterns:
                if pattern.lower() in search_text:
                    return device_type
        
        # Default based on UPnP device type
        upnp_type = (device_info.metadata.get('upnp_device_type') or '').lower()
        if 'mediarenderer' in upnp_type:
            return 'media_player'
        elif 'mediaserver' in upnp_type:
            return 'nas'
        elif 'internetgateway' in upnp_type or 'wandevice' in upnp_type:
            return 'router'
        
        return 'upnp_device'
    
    async def discover_hosts(self, network: str, scan_id: str) -> List[str]:
        """
        Discover hosts using SSDP/UPnP discovery.
        
        Args:
            network: Network range (not used for SSDP multicast)
            scan_id: Scan identifier
            
        Returns:
            List of discovered host IP addresses
        """
        devices = await self.scan(network, scan_id)
        hosts = []
        
        for device in devices:
            if device.ip and device.ip not in hosts:
                hosts.append(device.ip)
        
        return hosts
