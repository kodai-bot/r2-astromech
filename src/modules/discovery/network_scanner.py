"""
Industrial Automaton R2 Modular Network Scanner

Primary network discovery and analysis module for R2-series astromech droids.
Implements Industrial Automaton's proven modular design philosophy with 
event-driven architecture for reliable field operations.

Manufactured by: Industrial Automaton, Rordis City, Nubia
Product Line: R2-series Astromech Network Analysis Suite  
Model: R2-NetScan Modular Discovery System v2.0
Compatible with: Intellex IV Computer Core and later

Key Features:
- Modular scanner architecture following IA design standards
- Event-driven progress reporting with R2 audio feedback
- Multiple discovery methods for comprehensive reconnaissance
- Compatible with standard R2 tool complement and upgrades
- Field-serviceable components with standardized interfaces

"Engineered to R2 specifications for any environment"
Industrial Automaton - Since 32 BBY
"""

import asyncio
import subprocess
import socket
import ipaddress
import platform
import re
import hashlib
import time
from typing import List, Dict, Optional, Any
from datetime import datetime
import logging
import json
import xml.etree.ElementTree as ET

from ...core.interfaces import IModule, ModuleStatus
from ...core.events import EventBus, create_event, R2Events
from ..discovery.interfaces import INetworkScanner
from ...utils.exceptions import R2NetworkException, R2ModuleException
from ...utils.logging import get_module_logger
from .device_database import DeviceDatabase
from .scanners.arp_scanner import ARPScanner
from .scanners.mdns_scanner import MDNSScanner
from .scanners.discovery_engine import DiscoveryEngine
from .scanners.interfaces import ScannerConfig

logger = get_module_logger("discovery.network_scanner")


class ModularNetworkScanner(INetworkScanner):
    """
    Modular Network Scanner implementation
    
    This scanner uses event-driven communication and follows the new
    modular architecture principles.
    """
    
    def __init__(self, event_bus: EventBus, config: Dict[str, Any]):
        """
        Initialize the modular network scanner.
        
        Args:
            event_bus: Event bus for communication
            config: Scanner configuration
        """
        self.event_bus = event_bus
        self.config = config
        self.logger = logger
        
        # Scanner state
        self.is_running = False
        self.is_scanning = False
        self.current_scan_id: Optional[str] = None
        self.scan_progress = 0.0
        self.discovered_devices: List[Dict[str, Any]] = []
        
        # Configuration
        self.default_network = config.get('default_network', '192.168.1.0/24')
        self.scan_timeout = config.get('scan_timeout', 30)
        self.ping_timeout = config.get('ping_timeout', 1)
        self.port_scan_timeout = config.get('port_scan_timeout', 5)  # Increased for NAS detection
        self.common_ports = config.get('common_ports', [
            # Standard services
            21, 22, 23, 25, 53, 80, 110, 143, 443, 993, 995,
            # Windows services  
            135, 139, 445, 1723, 3389,
            # Remote access
            5900, 5901, 5902,  # VNC
            # Web services
            8080, 8443, 8000, 8008, 8888,
            # NAS/Storage services (Synology, QNAP, etc.)
            5000, 5001,  # Synology DSM
            8006, 8007,  # Synology additional ports
            9000, 9001,  # Synology additional services
            548,         # AFP (Apple Filing Protocol)
            2049,        # NFS
            111,         # RPC
            # Database services
            3306, 5432, 1433, 1521,  # MySQL, PostgreSQL, SQL Server, Oracle
            # Other common services
            21, 990,     # FTP/FTPS
            6881, 6882,  # BitTorrent
            32400,       # Plex
            8096,        # Emby
            7878,        # Radarr
            8989,        # Sonarr
            # Printer ports
            9100,        # RAW/JetDirect printer port
            631,         # IPP (Internet Printing Protocol)
            161,         # SNMP
        ])
        
        # Statistics
        self.stats = {
            'scans_completed': 0,
            'devices_discovered': 0,
            'ports_scanned': 0,
            'errors': 0
        }
        
        # Initialize device database
        self.device_database = DeviceDatabase()
        
        # Initialize specialized scanners
        self._init_specialized_scanners(config)
        
        # Initialize discovery engine
        self._init_discovery_engine(config)
        
        # Debug mode for bypassing event publishing
        self.debug_mode = config.get('debug_mode', False)
        if self.debug_mode:
            print("🔧 DEBUG MODE: Event publishing will be bypassed")
        
        # Enhanced tool availability and preferences
        self.available_tools = {}
        self.tool_preferences = config.get('tool_preferences', {
            'discovery_tool': 'masscan',  # masscan, nmap, or basic (masscan fastest for discovery)
            'port_scan_tool': 'nmap',     # nmap or basic (nmap best for detailed analysis)
            'fallback_to_basic': True
        })
        
        self.logger.info("Modular Network Scanner initialized")
    
    def _init_discovery_engine(self, config: Dict[str, Any]) -> None:
        """Initialize the discovery engine."""
        try:
            # Configure discovery engine
            discovery_config = ScannerConfig(
                enabled=config.get('enable_discovery_engine', True),
                timeout=config.get('discovery_timeout', 30.0),
                max_concurrent=config.get('max_concurrent_discovery', 50),
                custom_options={
                    'ping_timeout': config.get('ping_timeout', 1.0),
                    'scan_timeout': config.get('scan_timeout', 30.0),
                    'max_concurrent': config.get('max_concurrent_discovery', 50)
                }
            )
            
            # Initialize discovery engine
            self.discovery_engine = DiscoveryEngine(self.event_bus, discovery_config)
            
            self.logger.info("Discovery engine initialized")
            
        except Exception as e:
            self.logger.error(f"Failed to initialize discovery engine: {e}")
            self.discovery_engine = None
    
    def _init_specialized_scanners(self, config: Dict[str, Any]) -> None:
        """Initialize specialized discovery scanners."""
        try:
            # Configure ARP scanner
            arp_config = ScannerConfig(
                enabled=config.get('enable_arp_discovery', True),
                timeout=config.get('arp_timeout', 10.0),
                custom_options={
                    'arp_timeout': config.get('arp_timeout', 2.0),
                    'max_concurrent_arps': config.get('max_concurrent_arps', 50),
                    'include_arp_scan': config.get('include_active_arp_scan', False)  # Default to ARP table only
                }
            )
            
            # Initialize ARP scanner
            self.arp_scanner = ARPScanner(self.event_bus, arp_config)
            
            # Configure mDNS scanner
            mdns_config = ScannerConfig(
                enabled=config.get('enable_mdns_discovery', True),
                timeout=config.get('mdns_timeout', 15.0),
                custom_options={
                    'scan_duration': config.get('mdns_scan_duration', 8),
                    'service_types': config.get('mdns_service_types', [
                        '_http._tcp', '_https._tcp', '_ssh._tcp', '_ftp._tcp',
                        '_airplay._tcp', '_raop._tcp', '_spotify-connect._tcp',
                        '_ipp._tcp', '_hap._tcp', '_googlecast._tcp'
                    ])
                }
            )
            
            # Initialize mDNS scanner
            self.mdns_scanner = MDNSScanner(self.event_bus, mdns_config)
            
            self.logger.info("Specialized scanners initialized")
            
        except Exception as e:
            self.logger.error(f"Failed to initialize specialized scanners: {e}")
            self.arp_scanner = None
            self.mdns_scanner = None
    
    async def _initialize_specialized_scanners(self) -> None:
        """Initialize and start specialized scanners."""
        try:
            # Initialize ARP scanner if available
            if self.arp_scanner:
                if await self.arp_scanner.initialize():
                    self.logger.info("✅ ARP scanner initialized and ready")
                else:
                    self.logger.warning("❌ ARP scanner initialization failed")
                    self.arp_scanner = None
            
            # Initialize mDNS scanner if available
            if self.mdns_scanner:
                if await self.mdns_scanner.initialize():
                    self.logger.info("✅ mDNS scanner initialized and ready")
                else:
                    self.logger.warning("❌ mDNS scanner initialization failed (tools not available)")
                    self.mdns_scanner = None
            
        except Exception as e:
            self.logger.error(f"Failed to initialize specialized scanners: {e}")
    
    async def _initialize_discovery_engine(self) -> None:
        """Initialize and start the discovery engine."""
        try:
            if self.discovery_engine:
                if await self.discovery_engine.initialize():
                    self.logger.info("✅ Discovery engine initialized and ready")
                else:
                    self.logger.warning("❌ Discovery engine initialization failed")
                    self.discovery_engine = None
            else:
                self.logger.warning("❌ Discovery engine not available")
                
        except Exception as e:
            self.logger.error(f"Failed to initialize discovery engine: {e}")
    
    async def _safe_publish_event(self, event, timeout: float = 3.0, description: str = "event") -> bool:
        """
        Safely publish an event with timeout protection and debug mode bypass.
        
        Args:
            event: Event to publish
            timeout: Timeout in seconds
            description: Description for logging
            
        Returns:
            bool: True if successful or bypassed
        """
        if self.debug_mode:
            print(f"🔧 DEBUG MODE: Skipping {description} event publishing")
            return True
        
        try:
            await asyncio.wait_for(
                self.event_bus.publish(event),
                timeout=timeout
            )
            print(f"✅ DEBUG: {description} event published successfully")
            return True
        except asyncio.TimeoutError:
            print(f"⏰ DEBUG: {description} event timed out after {timeout}s")
            return False
        except Exception as e:
            print(f"❌ DEBUG: {description} event failed: {e}")
            return False
    
    async def _check_tool_availability(self):
        """Check which enhanced scanning tools are available"""
        tools_to_check = ['nmap', 'masscan', 'netdiscover', 'snmpwalk']
        
        for tool in tools_to_check:
            try:
                process = await asyncio.create_subprocess_exec(
                    'which', tool,
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE
                )
                stdout, _ = await process.communicate()
                if process.returncode == 0:
                    self.available_tools[tool] = stdout.decode().strip()
                    self.logger.info(f"✅ Enhanced tool {tool} available at {self.available_tools[tool]}")
                else:
                    self.logger.debug(f"❌ Enhanced tool {tool} not available")
            except Exception as e:
                self.logger.warning(f"❌ Error checking {tool}: {e}")
        
        # Report available tools
        if self.available_tools:
            tools_list = ', '.join(self.available_tools.keys())
            print(f"🔧 Enhanced tools available: {tools_list}")
        else:
            print("🔧 No enhanced tools available - using basic scanning methods")
    
    @property
    def module_name(self) -> str:
        """Get module name"""
        return "discovery.network_scanner"
    
    async def initialize(self) -> bool:
        """Initialize the scanner module"""
        try:
            self.logger.info("Initializing network scanner...")
            
            # Subscribe to relevant events
            await self.event_bus.subscribe(R2Events.SYSTEM_STARTUP, self._on_system_startup)
            await self.event_bus.subscribe(R2Events.SYSTEM_SHUTDOWN, self._on_system_shutdown)
            
            self.logger.info("Network scanner initialized successfully")
            return True
            
        except Exception as e:
            self.logger.error("Failed to initialize network scanner", error=str(e))
            raise R2ModuleException(self.module_name, f"Initialization failed: {e}", e)
    
    async def start(self) -> bool:
        """Start the scanner module"""
        try:
            self.logger.info("Starting network scanner...")
            self.is_running = True
            
            # Initialize specialized scanners
            await self._initialize_specialized_scanners()
            
            # Initialize discovery engine
            await self._initialize_discovery_engine()
            
            # Publish module started event
            await self.event_bus.publish(create_event(
                R2Events.MODULE_STARTED,
                {"module": self.module_name, "capabilities": ["network_scan", "port_scan", "device_discovery"]},
                self.module_name
            ))
            
            self.logger.info("Network scanner started successfully")
            return True
            
        except Exception as e:
            self.logger.error("Failed to start network scanner", error=str(e))
            raise R2ModuleException(self.module_name, f"Start failed: {e}", e)
    
    async def stop(self) -> bool:
        """Stop the scanner module"""
        try:
            self.logger.info("Stopping network scanner...")
            
            # Stop any active scans
            if self.is_scanning:
                await self.stop_scan()
            
            self.is_running = False
            
            # Publish module stopped event
            await self.event_bus.publish(create_event(
                R2Events.MODULE_STOPPED,
                {"module": self.module_name, "stats": self.stats},
                self.module_name
            ))
            
            self.logger.info("Network scanner stopped successfully")
            return True
            
        except Exception as e:
            self.logger.error("Failed to stop network scanner", error=str(e))
            return False
    
    async def get_status(self) -> ModuleStatus:
        """Get module status"""
        return ModuleStatus(
            name=self.module_name,
            status='running' if self.is_running else 'stopped',
            health_score=1.0 if self.is_running and not self.is_scanning else 0.8,
            last_heartbeat=datetime.now(),
            uptime_seconds=0.0,  # TODO: Calculate actual uptime
            memory_usage_mb=None  # TODO: Add memory monitoring
        )
    
    async def health_check(self) -> bool:
        """Perform health check"""
        try:
            # Basic health check - can we create a socket?
            test_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            test_socket.close()
            return True
        except Exception as e:
            self.logger.error("Health check failed", error=str(e))
            return False
    
    async def cleanup(self) -> bool:
        """Cleanup module resources"""
        try:
            self.logger.info("Cleaning up network scanner...")
            
            # Stop any active operations
            if self.is_scanning:
                await self.stop_scan()
            
            # Clear discovered devices
            self.discovered_devices.clear()
            
            self.logger.info("Network scanner cleanup complete")
            return True
            
        except Exception as e:
            self.logger.error("Cleanup failed", error=str(e))
            return False
    
    async def scan_network(self, target: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Scan network for devices with event-driven communication.
        
        Args:
            target: Target network (e.g., '192.168.1.0/24'). If None, uses default.
            
        Returns:
            List[Dict[str, Any]]: List of discovered devices
        """
        if not self.is_running:
            raise R2ModuleException(self.module_name, "Scanner not running")
        
        if self.is_scanning:
            raise R2ModuleException(self.module_name, "Scan already in progress")
        
        target_network = target or self.default_network
        scan_id = f"scan_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        try:
            print(f"🔧 DEBUG: scan_network method started, target: {target_network}")
            self.logger.info(f"Starting network scan: {target_network}")
            
            # Initialize scan state
            print(f"🔧 DEBUG: Initializing scan state...")
            self.is_scanning = True
            self.current_scan_id = scan_id
            self.scan_progress = 0.0
            self.discovered_devices.clear()
            print(f"🔧 DEBUG: Scan state initialized. is_scanning={self.is_scanning}")
            
            # Publish scan started event
            print(f"🔧 DEBUG: Publishing scan started event...")
            try:
                await asyncio.wait_for(
                    self.event_bus.publish(create_event(
                        R2Events.NETWORK_SCAN_STARTED,
                        {
                            "scan_id": scan_id,
                            "target_network": target_network,
                            "scanner": self.module_name
                        },
                        self.module_name,
                        correlation_id=scan_id
                    )),
                    timeout=5.0  # 5 second timeout
                )
                print(f"🔧 DEBUG: Scan started event published successfully")
            except asyncio.TimeoutError:
                print(f"❌ DEBUG: Event publishing timed out after 5 seconds!")
                # Continue anyway - don't let event issues block the scan
            except Exception as e:
                print(f"❌ DEBUG: Event publishing failed: {e}")
                # Continue anyway - don't let event issues block the scan
            
            # Perform ping sweep
            print(f"🔧 DEBUG: About to call ping_sweep with network: {target_network}, scan_id: {scan_id}")
            active_hosts = await self.ping_sweep(target_network, scan_id)
            print(f"🔧 DEBUG: ping_sweep returned {len(active_hosts)} active hosts")
            
            # Analyze each discovered device
            print(f"\n🔬 R2-D2 Beginning Deep Analysis Phase...")
            print(f"📊 Analyzing {len(active_hosts)} discovered devices...")
            
            for i, host in enumerate(active_hosts):
                print(f"\n🎯 Processing Device {i+1}/{len(active_hosts)}: {host}")
                
                device_info = {
                    'ip': host,
                    'status': 'active',
                    'discovery_method': 'ping',
                    'timestamp': datetime.now().isoformat(),
                    'scan_id': scan_id
                }
                
                # Publish device discovered event with timeout protection
                await self._safe_publish_event(
                    create_event(
                        R2Events.DEVICE_DISCOVERED,
                        {
                            "device": device_info,
                            "scan_id": scan_id,
                            "device_number": i + 1,
                            "total_devices": len(active_hosts)
                        },
                        self.module_name,
                        correlation_id=scan_id
                    ),
                    timeout=3.0,
                    description=f"DEVICE_DISCOVERED for {host}"
                )
                
                # Perform deep device analysis 
                print(f"🔬 R2-D2 Starting Deep Analysis for Device #{i+1}: {host}")
                try:
                    detailed_device_info = await asyncio.wait_for(
                        self.scan_device(host),
                        timeout=60.0  # 60 second timeout for device analysis
                    )
                    print(f"✅ Deep analysis completed for {host}")
                except asyncio.TimeoutError:
                    print(f"⏰ Deep analysis timed out for {host}, using basic info")
                    detailed_device_info = {'analysis_timeout': True}
                except Exception as e:
                    print(f"❌ Deep analysis failed for {host}: {e}")
                    detailed_device_info = {'analysis_error': str(e)}
                
                # Merge basic info with detailed analysis
                device_info.update(detailed_device_info)
                
                # Store device in database
                self.device_database.add_or_update_device(device_info)
                
                # Publish device analyzed event
                await self._safe_publish_event(
                    create_event(
                        R2Events.DEVICE_ANALYZED,
                        {
                            "device": device_info,
                            "scan_id": scan_id,
                            "analysis_type": "comprehensive"
                        },
                        self.module_name,
                        correlation_id=scan_id
                    ),
                    timeout=2.0,
                    description=f"DEVICE_ANALYZED for {host}"
                )
                
                self.discovered_devices.append(device_info)
                self.stats['devices_discovered'] += 1
                
                # Show device summary
                self._print_device_summary(device_info, i + 1)
                
                # Update progress
                self.scan_progress = (i + 1) / len(active_hosts) * 100
            
            # Generate network fingerprint
            print(f"\n🔍 Generating Network Fingerprint...")
            gateway_ip = await self._get_default_gateway()
            network_fingerprint = self._generate_network_fingerprint(
                target_network, 
                gateway_ip, 
                self.discovered_devices
            )
            
            print(f"🏷️  Network Code: {network_fingerprint['network_code']}")
            print(f"📅 Scan Date: {network_fingerprint['scan_date']} {network_fingerprint['scan_time']}")
            print(f"🚪 Gateway: {gateway_ip}")
            print(f"📊 Devices: {len(self.discovered_devices)}")
            
            # Store network fingerprint in database
            self.device_database.add_network_fingerprint(network_fingerprint)
            
            # Publish scan completed event with timeout protection
            print(f"🔧 DEBUG: Publishing NETWORK_SCAN_COMPLETED event...")
            try:
                await asyncio.wait_for(
                    self.event_bus.publish(create_event(
                        R2Events.NETWORK_SCAN_COMPLETED,
                        {
                            "scan_id": scan_id,
                            "devices_found": len(self.discovered_devices),
                            "network_fingerprint": network_fingerprint,
                            "scan_duration": "N/A",  # TODO: Calculate actual duration
                            "stats": self.stats
                        },
                        self.module_name,
                        correlation_id=scan_id
                    )),
                    timeout=5.0  # 5 second timeout
                )
                print(f"✅ DEBUG: NETWORK_SCAN_COMPLETED event published successfully")
            except asyncio.TimeoutError:
                print(f"⏰ DEBUG: NETWORK_SCAN_COMPLETED event timed out")
            except Exception as e:
                print(f"❌ DEBUG: NETWORK_SCAN_COMPLETED event failed: {e}")
            
            self.stats['scans_completed'] += 1
            self.logger.info(f"Network scan completed: {len(self.discovered_devices)} devices found")
            
            return self.discovered_devices.copy()
            
        except Exception as e:
            self.logger.error(f"Network scan failed: {e}")
            
            # Publish scan error event
            await self.event_bus.publish(create_event(
                R2Events.NETWORK_SCAN_ERROR,
                {
                    "scan_id": scan_id,
                    "error": str(e),
                    "target_network": target_network
                },
                self.module_name,
                correlation_id=scan_id
            ))
            
            self.stats['errors'] += 1
            raise R2NetworkException(f"Network scan failed: {e}")
            
        finally:
            # Reset scan state
            self.is_scanning = False
            self.current_scan_id = None
            self.scan_progress = 0.0
    
    async def _masscan_discovery(self, network: str, scan_id: str) -> List[str]:
        """Use masscan for ultra-high-speed network discovery"""
        if 'masscan' not in self.available_tools:
            self.logger.warning("Masscan not available, falling back to nmap")
            return await self._nmap_discovery(network, scan_id)
        
        try:
            # Convert network to masscan format
            network_obj = ipaddress.IPv4Network(network, strict=False)
            target = str(network_obj)
            
            # Masscan command for discovery (ping sweep equivalent)
            cmd = [
                'masscan', target,
                '--ping',           # Ping sweep mode
                '--rate', '1000',   # 1000 packets/second (fast but not overwhelming)
                '--output-format', 'json'
            ]
            
            self.logger.info(f"🚀 Running masscan discovery: {' '.join(cmd)}")
            print(f"🚀 Masscan: Ultra-high-speed discovery of {network}")
            
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            stdout, stderr = await asyncio.wait_for(process.communicate(), timeout=300)
            
            if process.returncode == 0:
                active_hosts = self._parse_masscan_output(stdout.decode())
                self.logger.info(f"Masscan discovery found {len(active_hosts)} active hosts")
                return active_hosts
            else:
                error_msg = stderr.decode()
                self.logger.error(f"Masscan discovery failed: {error_msg}")
                return await self._nmap_discovery(network, scan_id)
                
        except Exception as e:
            self.logger.error(f"Masscan discovery failed: {e}")
            return await self._nmap_discovery(network, scan_id)
    
    def _parse_masscan_output(self, output: str) -> List[str]:
        """Parse masscan JSON output to extract active IP addresses"""
        active_hosts = []
        
        for line in output.strip().split('\n'):
            if line.strip():
                try:
                    result = json.loads(line)
                    if 'ip' in result:
                        active_hosts.append(result['ip'])
                except json.JSONDecodeError:
                    continue
        
        return list(set(active_hosts))  # Remove duplicates
    
    async def _masscan_port_scan(self, network: str, ports: Optional[List[int]] = None) -> Dict[str, List[Dict[str, Any]]]:
        """Use masscan for ultra-fast port scanning across a network"""
        if 'masscan' not in self.available_tools:
            self.logger.warning("Masscan not available for port scanning")
            return {}
        
        try:
            # Convert network to masscan format
            network_obj = ipaddress.IPv4Network(network, strict=False)
            target = str(network_obj)
            
            if ports:
                port_list = ','.join(map(str, ports))
            else:
                port_list = ','.join(map(str, self.common_ports))
            
            # Masscan command for port scanning
            cmd = [
                'masscan', target,
                '-p', port_list,
                '--rate', '1000',   # 1000 packets/second
                '--output-format', 'json'
            ]
            
            self.logger.info(f"🚀 Running masscan port scan: {' '.join(cmd)}")
            print(f"🚀 Masscan: Ultra-fast port scan of {network}")
            
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            stdout, stderr = await asyncio.wait_for(process.communicate(), timeout=600)  # 10 min timeout
            
            if process.returncode == 0:
                return self._parse_masscan_port_output(stdout.decode())
            else:
                error_msg = stderr.decode()
                self.logger.error(f"Masscan port scan failed: {error_msg}")
                return {}
                
        except Exception as e:
            self.logger.error(f"Masscan port scan failed: {e}")
            return {}
    
    def _parse_masscan_port_output(self, output: str) -> Dict[str, List[Dict[str, Any]]]:
        """Parse masscan port scan JSON output"""
        results = {}
        
        for line in output.strip().split('\n'):
            if line.strip():
                try:
                    result = json.loads(line)
                    if 'ip' in result and 'port' in result:
                        ip = result['ip']
                        if ip not in results:
                            results[ip] = []
                        results[ip].append({
                            'port': result['port'],
                            'protocol': result.get('protocol', 'tcp'),
                            'status': result.get('status', 'open')
                        })
                except json.JSONDecodeError:
                    continue
        
        return results

    async def _nmap_discovery(self, network: str, scan_id: str) -> List[str]:
        """Use nmap for network discovery (ping sweep equivalent)"""
        if 'nmap' not in self.available_tools:
            self.logger.warning("Nmap not available, falling back to basic ping")
            return await self._basic_ping_sweep(network, scan_id)
        
        try:
            # Build nmap ping sweep command
            cmd = [
                'nmap', '-sn',  # Ping sweep (no port scan)
                '-T4',          # Aggressive timing
                '--max-retries', '1',  # Fast scanning
                network
            ]
            
            self.logger.info(f"🚀 Running nmap discovery: {' '.join(cmd)}")
            print(f"🚀 Nmap: High-speed discovery of {network}")
            
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            stdout, stderr = await asyncio.wait_for(process.communicate(), timeout=300)
            
            if process.returncode == 0:
                active_hosts = self._parse_nmap_discovery_output(stdout.decode())
                self.logger.info(f"Nmap discovery found {len(active_hosts)} active hosts")
                return active_hosts
            else:
                error_msg = stderr.decode()
                self.logger.error(f"Nmap discovery failed: {error_msg}")
                return await self._basic_ping_sweep(network, scan_id)
                
        except Exception as e:
            self.logger.error(f"Nmap discovery failed: {e}")
            return await self._basic_ping_sweep(network, scan_id)
    
    def _parse_nmap_discovery_output(self, output: str) -> List[str]:
        """Parse nmap discovery output to extract active IP addresses"""
        active_hosts = []
        
        for line in output.split('\n'):
            if 'Nmap scan report for' in line:
                # Handle both formats:
                # "Nmap scan report for 192.168.1.1"
                # "Nmap scan report for hostname.domain (192.168.1.1)"
                
                # First, try to find IP in parentheses
                paren_match = re.search(r'\((\d+\.\d+\.\d+\.\d+)\)', line)
                if paren_match:
                    active_hosts.append(paren_match.group(1))
                else:
                    # Fall back to finding IP in the line
                    ip_match = re.search(r'\d+\.\d+\.\d+\.\d+', line)
                    if ip_match:
                        active_hosts.append(ip_match.group(0))
        
        return active_hosts
    
    async def _nmap_port_scan(self, host: str, ports: Optional[List[int]] = None) -> Dict[str, Any]:
        """Use nmap for professional port scanning"""
        if 'nmap' not in self.available_tools:
            self.logger.warning("Nmap not available, falling back to basic port scan")
            return await self._basic_port_scan(host, ports)
        
        try:
            # Build nmap command for detailed scan (non-root compatible)
            cmd = [
                'nmap', '-sT',      # TCP connect scan (works without root)
                '-sV',              # Service version detection
                '--version-all',    # Try all version detection probes
                '-T4',              # Aggressive timing
                '--osscan-guess'    # OS detection without requiring root
            ]
            
            if ports:
                port_list = ','.join(map(str, ports))
                cmd.extend(['-p', port_list])
            else:
                # Use our common ports list
                port_list = ','.join(map(str, self.common_ports))
                cmd.extend(['-p', port_list])
            
            cmd.extend(['-oX', '-', host])  # XML output to stdout
            
            self.logger.info(f"🎯 Running nmap port scan: nmap -sT -sV {host}")
            print(f"🎯 Nmap: Professional TCP connect scan of {host}")
            
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            stdout, stderr = await asyncio.wait_for(process.communicate(), timeout=300)
            
            if process.returncode == 0:
                xml_data = stdout.decode()
                return self._parse_nmap_xml(xml_data)
            else:
                error_msg = stderr.decode()
                self.logger.warning(f"Nmap scan failed, falling back to basic: {error_msg}")
                return await self._basic_port_scan(host, ports)
                
        except Exception as e:
            self.logger.error(f"Nmap scan failed: {e}")
            return await self._basic_port_scan(host, ports)
    
    def _parse_nmap_xml(self, xml_data: str) -> Dict[str, Any]:
        """Parse nmap XML output into our standard format"""
        try:
            root = ET.fromstring(xml_data)
            result = {
                'open_ports': [],
                'services': {},
                'os_info': {},
                'scan_method': 'nmap',
                'nmap_data': {}
            }
            
            # Find host element
            host = root.find('host')
            if host is None:
                return result
            
            # Parse ports
            ports = host.find('ports')
            if ports is not None:
                for port in ports.findall('port'):
                    port_id = int(port.get('portid'))
                    protocol = port.get('protocol', 'tcp')
                    
                    # Check if port is open
                    state = port.find('state')
                    if state is not None and state.get('state') == 'open':
                        result['open_ports'].append(port_id)
                        
                        # Get service information
                        service = port.find('service')
                        if service is not None:
                            service_name = service.get('name', f'unknown-{port_id}')
                            version = service.get('version', '')
                            product = service.get('product', '')
                            
                            if version and product:
                                service_info = f"{product} {version}"
                            elif product:
                                service_info = product
                            else:
                                service_info = service_name
                            
                            result['services'][port_id] = service_info
            
            # Parse OS information
            os_elem = host.find('os')
            if os_elem is not None:
                osmatch = os_elem.find('osmatch')
                if osmatch is not None:
                    result['os_info'] = {
                        'name': osmatch.get('name', 'Unknown'),
                        'accuracy': int(osmatch.get('accuracy', 0)),
                        'family': self._extract_os_family(osmatch.get('name', ''))
                    }
                    result['nmap_data']['os_detection'] = osmatch.get('name', 'Unknown')
            
            # Add scan statistics
            result['nmap_data']['scan_type'] = 'TCP connect scan with OS and service detection'
            
            return result
            
        except ET.ParseError as e:
            self.logger.error(f"Failed to parse nmap XML: {e}")
            return {
                'open_ports': [], 
                'services': {}, 
                'os_info': {}, 
                'scan_method': 'nmap', 
                'parse_error': str(e)
            }
    
    def _extract_os_family(self, os_name: str) -> str:
        """Extract OS family from nmap OS detection"""
        if not os_name:
            return 'Unknown'
            
        os_name_lower = os_name.lower()
        if 'windows' in os_name_lower:
            return 'Windows'
        elif any(term in os_name_lower for term in ['linux', 'ubuntu', 'debian', 'centos', 'fedora', 'redhat']):
            return 'Linux'
        elif any(term in os_name_lower for term in ['macos', 'mac os', 'darwin']):
            return 'macOS'
        elif any(term in os_name_lower for term in ['freebsd', 'openbsd', 'netbsd']):
            return 'BSD'
        elif any(term in os_name_lower for term in ['cisco', 'juniper']):
            return 'Network Device'
        else:
            return 'Unknown'
    
    async def _basic_ping_sweep(self, network: str, scan_id: str) -> List[str]:
        """Fallback to basic ping sweep - this will call the existing implementation"""
        return await self._original_ping_sweep(network, scan_id)
    
    async def _basic_port_scan(self, host: str, ports: Optional[List[int]] = None) -> Dict[str, Any]:
        """Fallback to basic port scan - this will call the existing implementation"""
        return await self._original_port_scan(host, ports)

    async def ping_sweep(self, network: str, scan_id: str) -> List[str]:
        """
        Enhanced ping sweep using the discovery engine for comprehensive device detection.
        """
        try:
            # Use discovery engine if available
            if self.discovery_engine and await self.discovery_engine.check_availability():
                self.logger.info(f"Using discovery engine for ping sweep: {network}")
                hosts = await self.discovery_engine.discover_hosts(network, scan_id)
                print(f"✅ Discovery engine found {len(hosts)} devices: {hosts}")
                return hosts
            else:
                # Fallback to legacy method if discovery engine not available
                self.logger.warning("Discovery engine not available, using legacy ping sweep")
                return await self._legacy_ping_sweep(network, scan_id)
                
        except Exception as e:
            self.logger.error(f"Ping sweep failed: {e}")
            return []
    
    async def _legacy_ping_sweep(self, network: str, scan_id: str) -> List[str]:
        """
        Legacy ping sweep method as fallback when discovery engine is not available.
        """
        all_hosts = set()  # Use set to avoid duplicates
        
        # Phase 1: ARP Discovery (fast, finds quiet devices)
        if self.arp_scanner:
            try:
                print(f"🔍 Phase 1: ARP Discovery for {network}")
                arp_hosts = await self.arp_scanner.discover_hosts(network, scan_id)
                all_hosts.update(arp_hosts)
                print(f"✅ ARP discovery found {len(arp_hosts)} devices: {arp_hosts}")
            except Exception as e:
                print(f"⚠️ ARP discovery failed: {e}")
                self.logger.warning(f"ARP discovery failed: {e}")
        
        # Phase 2: Traditional Discovery (ping/nmap/masscan)
        print(f"🔍 Phase 2: Traditional Discovery for {network}")
        
        # Check tool availability if not done yet
        if not self.available_tools:
            await self._check_tool_availability()
        
        # Choose the best available discovery method
        discovery_tool = self.tool_preferences.get('discovery_tool', 'masscan')
        
        traditional_hosts = []
        if discovery_tool == 'masscan' and 'masscan' in self.available_tools:
            traditional_hosts = await self._masscan_discovery(network, scan_id)
        elif 'nmap' in self.available_tools:
            self.logger.info("Masscan not available, using nmap discovery")
            traditional_hosts = await self._nmap_discovery(network, scan_id)
        else:
            self.logger.info("Using basic ping sweep (no enhanced tools available)")
            traditional_hosts = await self._original_ping_sweep(network, scan_id)
        
        # Merge traditional discovery results
        all_hosts.update(traditional_hosts)
        print(f"✅ Traditional discovery found {len(traditional_hosts)} devices: {traditional_hosts}")
        
        # Phase 3: mDNS Discovery (enriches device information)
        if self.mdns_scanner:
            try:
                print(f"🔍 Phase 3: mDNS Discovery for {network}")
                mdns_hosts = await self.mdns_scanner.discover_hosts(network, scan_id)
                all_hosts.update(mdns_hosts)
                print(f"✅ mDNS discovery found {len(mdns_hosts)} devices: {mdns_hosts}")
            except Exception as e:
                print(f"⚠️ mDNS discovery failed: {e}")
                self.logger.warning(f"mDNS discovery failed: {e}")
        else:
            print(f"ℹ️ mDNS discovery not available (tools not installed)")
        
        # Final results
        final_hosts = sorted(list(all_hosts))
        print(f"🎯 Combined discovery found {len(final_hosts)} unique devices: {final_hosts}")
        self.logger.info(f"Enhanced discovery complete: {len(final_hosts)} total devices found")
        
        return final_hosts
    
    async def _original_ping_sweep(self, network: str, scan_id: str) -> List[str]:
        """
        Original basic ping sweep method (fallback).
        
        Args:
            network: Network range (e.g., '192.168.1.0/24')
            scan_id: Scan identifier for correlation
            
        Returns:
            List[str]: List of active host IPs
        """
        print(f"🔧 DEBUG: ping_sweep method called with network={network}, scan_id={scan_id}")
        active_hosts = []
        
        try:
            print(f"🔧 DEBUG: Parsing network {network}")
            # Parse the network range
            network_obj = ipaddress.IPv4Network(network, strict=False)
            total_hosts = list(network_obj.hosts())
            
            print(f"🔧 DEBUG: Network parsed successfully, {len(total_hosts)} hosts to scan")
            self.logger.info(f"Ping sweep scanning {network} ({len(total_hosts)} addresses)")
            
            # Progress tracking with visual feedback
            print(f"🔧 DEBUG: Starting ping sweep of {len(total_hosts)} hosts")
            for i, host in enumerate(total_hosts):
                if not self.is_scanning:  # Check if scan was cancelled
                    print(f"🛑 DEBUG: Scan cancelled, breaking at host {i}")
                    break
                
                # DEBUG: Show every single IP being scanned for first 10, then every 5
                if i < 10 or i % 5 == 0:
                    print(f"🔍 DEBUG: Pinging {host} ({i+1}/{len(total_hosts)})")
                
                # Publish progress event for every IP scanned for better feedback
                try:
                    await asyncio.wait_for(
                        self.event_bus.publish(create_event(
                            R2Events.PING_PROGRESS,
                            {
                                "current_ip": str(host),
                                "progress": i + 1,
                                "total": len(total_hosts),
                                "scan_id": scan_id
                            },
                            self.module_name,
                            correlation_id=scan_id
                        )),
                        timeout=1.0  # 1 second timeout for progress events
                    )
                    if i < 5:  # Debug first few events
                        print(f"✅ DEBUG: Published ping_progress event for {host}")
                except asyncio.TimeoutError:
                    if i < 5:  # Only show for first few
                        print(f"⏰ DEBUG: ping_progress event timed out for {host}")
                except Exception as e:
                    print(f"❌ DEBUG: Failed to publish ping_progress event: {e}")
                
                # Show progress in logs every 25 hosts to avoid spam
                if (i + 1) % 25 == 0 or i < 10:
                    progress = ((i + 1) / len(total_hosts)) * 100
                    self.logger.info(f"Ping sweep progress: {i+1}/{len(total_hosts)} hosts checked ({progress:.1f}%)")
                    print(f"📊 DEBUG: Progress logged - {progress:.1f}% complete")
                
                ping_result = await self._ping_host(str(host))
                if i < 5:  # Debug first few ping results
                    print(f"🏓 DEBUG: Ping result for {host}: {ping_result}")
                
                if ping_result:
                    active_hosts.append(str(host))
                    self.logger.info(f"Active host found: {host}")
                    print(f"🎉 DEBUG: DEVICE FOUND! {host} - publishing discovery event")
                    
                    # Publish individual host discovery event
                    try:
                        await asyncio.wait_for(
                            self.event_bus.publish(create_event(
                                R2Events.DEVICE_DISCOVERED,
                                {
                                    "ip": str(host),
                                    "discovery_method": "ping",
                                    "scan_id": scan_id,
                                    "host_number": len(active_hosts)
                                },
                                self.module_name,
                                correlation_id=scan_id
                            )),
                            timeout=2.0  # 2 second timeout for device discovery
                        )
                        print(f"✅ DEBUG: Published DEVICE_DISCOVERED event for {host}")
                    except asyncio.TimeoutError:
                        print(f"⏰ DEBUG: DEVICE_DISCOVERED event timed out for {host}")
                    except Exception as e:
                        print(f"❌ DEBUG: Failed to publish DEVICE_DISCOVERED event: {e}")
            
            self.logger.info(f"Ping sweep complete: {len(active_hosts)} active hosts found")
            return active_hosts
            
        except Exception as e:
            self.logger.error(f"Ping sweep failed: {e}")
            raise R2NetworkException(f"Ping sweep failed: {e}")
    
    async def _ping_host(self, host: str) -> bool:
        """
        Ping a single host to check if it's alive.
        
        Args:
            host: Host IP address
            
        Returns:
            bool: True if host responds, False otherwise
        """
        try:
            # Use asyncio to run ping in a subprocess
            process = await asyncio.create_subprocess_exec(
                'ping', '-c', '1', '-W', str(self.ping_timeout), host,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            stdout, stderr = await asyncio.wait_for(
                process.communicate(), 
                timeout=self.ping_timeout + 0.5
            )
            
            return process.returncode == 0
            
        except (asyncio.TimeoutError, subprocess.SubprocessError, Exception):
            return False
    

    async def port_scan(self, host: str, ports: Optional[List[int]] = None) -> Dict[str, Any]:
        """
        Intelligent port scan using the best available tool
        """
        # Check tool availability if not done yet
        if not self.available_tools:
            await self._check_tool_availability()
        
        # Choose the best available port scanning method
        port_scan_tool = self.tool_preferences.get('port_scan_tool', 'nmap')
        
        if port_scan_tool == 'nmap' and 'nmap' in self.available_tools:
            return await self._nmap_port_scan(host, ports)
        else:
            self.logger.info("Using basic port scan (nmap not available)")
            return await self._original_port_scan(host, ports)
    
    async def _original_port_scan(self, host: str, ports: Optional[List[int]] = None) -> Dict[str, Any]:
        """
        Original basic port scan method (fallback).
        
        Args:
            host: Host IP address
            ports: List of ports to scan. If None, uses common ports.
            
        Returns:
            Dict[str, Any]: Port scan results
        """
        if ports is None:
            ports = self.common_ports
        
        open_ports = []
        services = {}
        
        self.logger.info(f"Scanning ports on {host}...")
        
        for port in ports:
            if not self.is_scanning:  # Check if scan was cancelled
                break
                
            if await self._check_port(host, port):
                open_ports.append(port)
                service = self._identify_service(port)
                services[port] = service
                
                self.logger.info(f"Open port found: {host}:{port} ({service})")
                
                # Publish port found event
                await self.event_bus.publish(create_event(
                    R2Events.DEVICE_ANALYZED,
                    {
                        "host": host,
                        "port": port,
                        "service": service,
                        "analysis_type": "port_discovery"
                    },
                    self.module_name
                ))
                
                self.stats['ports_scanned'] += 1
        
        return {
            'host': host,
            'open_ports': open_ports,
            'services': services,
            'scan_time': datetime.now().isoformat(),
            'ports_scanned': len(ports)
        }
    
    async def _check_port(self, host: str, port: int) -> bool:
        """
        Check if a specific port is open on a host.
        
        Args:
            host: Host IP address
            port: Port number
            
        Returns:
            bool: True if port is open
        """
        try:
            # Use asyncio for socket operations
            reader, writer = await asyncio.wait_for(
                asyncio.open_connection(host, port),
                timeout=self.port_scan_timeout
            )
            writer.close()
            await writer.wait_closed()
            return True
            
        except (asyncio.TimeoutError, ConnectionRefusedError, OSError):
            return False
    

    def _identify_service(self, port: int) -> str:
        """
        Identify likely service running on port.
        
        Args:
            port: Port number
            
        Returns:
            str: Service name
        """
        common_services = {
            # Standard services
            21: "FTP", 22: "SSH", 23: "Telnet", 25: "SMTP", 53: "DNS", 
            80: "HTTP", 110: "POP3", 143: "IMAP", 443: "HTTPS",
            993: "IMAPS", 995: "POP3S", 990: "FTPS",
            # Windows services
            135: "RPC", 139: "NetBIOS", 445: "SMB", 1723: "PPTP", 3389: "RDP",
            # Remote access
            5900: "VNC", 5901: "VNC", 5902: "VNC",
            # Web services
            8080: "HTTP-Alt", 8443: "HTTPS-Alt", 8000: "HTTP-Alt", 8008: "HTTP-Alt", 8888: "HTTP-Alt",
            # NAS services (Synology, QNAP, etc.)
            5000: "Synology-DSM-HTTP", 5001: "Synology-DSM-HTTPS",
            8006: "Synology-PhotoStation", 8007: "Synology-AudioStation",
            9000: "Synology-CloudStation", 9001: "Synology-CloudStation-HTTPS",
            548: "AFP", 2049: "NFS", 111: "RPC-Portmapper",
            # Database services
            3306: "MySQL", 5432: "PostgreSQL", 1433: "SQL-Server", 1521: "Oracle",
            # Media services
            32400: "Plex", 8096: "Emby", 7878: "Radarr", 8989: "Sonarr",
            # P2P
            6881: "BitTorrent", 6882: "BitTorrent",
            # IoT protocols
            1883: "MQTT", 8883: "MQTT-SSL", 5683: "CoAP", 502: "Modbus", 
            47808: "BACnet", 3671: "KNX"
        }
        return common_services.get(port, f"Unknown-{port}")
    


    async def scan_device(self, ip: str) -> Dict[str, Any]:
        """
        Scan specific device for detailed information.
        
        Args:
            ip: Device IP address
            
        Returns:
            Dict[str, Any]: Device information
        """
        print(f"🔍 R2-A1 Deep Device Analysis: {ip}")
        self.logger.info(f"Scanning device: {ip}")
        
        device_info = {
            'ip': ip,
            'timestamp': datetime.now().isoformat(),
            'scan_type': 'detailed',
            'analysis_phase': 'port_scan'
        }
        
        # Phase 1: Port scan
        print(f"📡 Phase 1: Port scanning {ip}...")
        port_info = await self.port_scan(ip)
        device_info.update(port_info)
        
        # Phase 2: Hostname resolution
        device_info['analysis_phase'] = 'hostname_resolution'
        print(f"🏷️  Phase 2: Resolving hostname for {ip}...")
        hostname_info = await self._resolve_hostname(ip)
        device_info.update(hostname_info)
        
        # Phase 3: OS fingerprinting
        device_info['analysis_phase'] = 'os_fingerprinting'
        print(f"🖥️  Phase 3: OS fingerprinting {ip}...")
        os_info = await self._os_fingerprint(ip)
        device_info.update(os_info)
        
        # Phase 4: Service banner grabbing
        device_info['analysis_phase'] = 'service_analysis'
        print(f"🛠️  Phase 4: Service analysis for {ip}...")
        service_info = await self._analyze_services(ip, device_info.get('open_ports', []))
        device_info.update(service_info)
        
        # Phase 5: Device type identification
        device_info['analysis_phase'] = 'device_identification'
        print(f"🤖 Phase 5: Device identification for {ip}...")
        device_type_info = await self._identify_device_type(device_info)
        device_info.update(device_type_info)
        
        # Phase 6: Manufacturer identification
        device_info['analysis_phase'] = 'manufacturer_lookup'
        print(f"🏭 Phase 6: Manufacturer lookup for {ip}...")
        manufacturer_info = await self._identify_manufacturer(ip)
        device_info.update(manufacturer_info)
        
        device_info['analysis_phase'] = 'complete'
        device_info['analysis_complete'] = True
        
        print(f"✅ Deep analysis complete for {ip}")
        return device_info
    
    async def _resolve_hostname(self, ip: str) -> Dict[str, Any]:
        """Resolve hostname for IP address"""
        hostname_info = {
            'hostname': 'unknown',
            'fqdn': 'unknown',
            'hostname_resolution_time': datetime.now().isoformat()
        }
        
        try:
            # Reverse DNS lookup
            result = socket.gethostbyaddr(ip)
            hostname_info['hostname'] = result[0].split('.')[0]  # Short name
            hostname_info['fqdn'] = result[0]  # Full domain name
            print(f"   🏷️  Hostname: {hostname_info['hostname']} ({hostname_info['fqdn']})")
        except (socket.herror, socket.gaierror):
            print(f"   ❌ No hostname found for {ip}")
        except Exception as e:
            print(f"   ⚠️  Hostname resolution error: {e}")
        
        return hostname_info
    
    async def _os_fingerprint(self, ip: str) -> Dict[str, Any]:
        """Perform basic OS fingerprinting"""
        os_info = {
            'os_type': 'unknown',
            'os_family': 'unknown',
            'ttl_signature': None,
            'os_confidence': 0.0
        }
        
        try:
            # Use ping TTL for basic OS detection
            process = await asyncio.create_subprocess_exec(
                'ping', '-c', '1', ip,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            stdout, stderr = await asyncio.wait_for(process.communicate(), timeout=5)
            
            if process.returncode == 0:
                output = stdout.decode()
                # Extract TTL from ping output
                ttl_match = re.search(r'ttl=(\d+)', output.lower())
                if ttl_match:
                    ttl = int(ttl_match.group(1))
                    os_info['ttl_signature'] = ttl
                    
                    # Basic OS detection based on TTL
                    if ttl <= 64:
                        os_info['os_family'] = 'Linux/Unix'
                        os_info['os_type'] = 'Linux/Unix-like'
                        os_info['os_confidence'] = 0.7
                    elif ttl <= 128:
                        os_info['os_family'] = 'Windows'
                        os_info['os_type'] = 'Microsoft Windows'
                        os_info['os_confidence'] = 0.7
                    elif ttl <= 255:
                        os_info['os_family'] = 'Network Device'
                        os_info['os_type'] = 'Router/Switch/Network Device'
                        os_info['os_confidence'] = 0.6
                    
                    print(f"   🖥️  OS Family: {os_info['os_family']} (TTL: {ttl}, Confidence: {os_info['os_confidence']:.1%})")
        except Exception as e:
            print(f"   ⚠️  OS fingerprinting error: {e}")
        
        return os_info
    
    async def _analyze_services(self, ip: str, open_ports: List[int]) -> Dict[str, Any]:
        """Analyze services running on open ports"""
        service_info = {
            'service_banners': {},
            'detected_services': {},
            'web_servers': [],
            'database_servers': [],
            'iot_protocols': []
        }
        
        # Banner grabbing for common ports
        banner_ports = [21, 22, 23, 25, 53, 80, 110, 143, 443, 993, 995]
        
        for port in open_ports:
            if port in banner_ports:
                banner = await self._grab_banner(ip, port)
                if banner:
                    service_info['service_banners'][port] = banner
                    print(f"   🛠️  Port {port}: {banner[:50]}...")
        
        # Detect web servers
        web_ports = [80, 443, 8080, 8443, 3000, 5000]
        for port in open_ports:
            if port in web_ports:
                web_info = await self._check_web_service(ip, port)
                if web_info:
                    service_info['web_servers'].append(web_info)
        
        # Detect IoT protocols
        iot_info = await self._detect_iot_protocols(ip, open_ports)
        service_info['iot_protocols'] = iot_info
        
        return service_info
    
    async def _grab_banner(self, ip: str, port: int) -> Optional[str]:
        """Grab banner from a service"""
        try:
            reader, writer = await asyncio.wait_for(
                asyncio.open_connection(ip, port),
                timeout=3
            )
            
            # Wait for banner
            banner = await asyncio.wait_for(reader.read(512), timeout=2)
            writer.close()
            await writer.wait_closed()
            
            return banner.decode('utf-8', errors='ignore').strip()
        except Exception:
            return None
    
    async def _check_web_service(self, ip: str, port: int) -> Optional[Dict[str, Any]]:
        """Check if port is running a web service"""
        try:
            url = f"http://{ip}:{port}" if port != 443 else f"https://{ip}"
            
            # Simple HTTP check (would need requests library for full implementation)
            reader, writer = await asyncio.wait_for(
                asyncio.open_connection(ip, port),
                timeout=3
            )
            
            # Send basic HTTP request
            request = f"GET / HTTP/1.1\r\nHost: {ip}\r\n\r\n"
            writer.write(request.encode())
            await writer.drain()
            
            response = await asyncio.wait_for(reader.read(1024), timeout=3)
            writer.close()
            await writer.wait_closed()
            
            response_text = response.decode('utf-8', errors='ignore')
            if 'HTTP/' in response_text:
                return {
                    'port': port,
                    'protocol': 'https' if port == 443 else 'http',
                    'url': url,
                    'response_snippet': response_text[:200]
                }
        except Exception:
            pass
        return None
    
    async def _detect_iot_protocols(self, ip: str, open_ports: List[int]) -> List[Dict[str, Any]]:
        """Detect IoT-specific protocols"""
        iot_protocols = []
        
        # MQTT
        if 1883 in open_ports or 8883 in open_ports:
            iot_protocols.append({'protocol': 'MQTT', 'ports': [p for p in [1883, 8883] if p in open_ports]})
        
        # CoAP
        if 5683 in open_ports or 5684 in open_ports:
            iot_protocols.append({'protocol': 'CoAP', 'ports': [p for p in [5683, 5684] if p in open_ports]})
        
        # Modbus
        if 502 in open_ports:
            iot_protocols.append({'protocol': 'Modbus', 'ports': [502]})
        
        # BACnet
        if 47808 in open_ports:
            iot_protocols.append({'protocol': 'BACnet', 'ports': [47808]})
        
        # Home automation protocols
        if 80 in open_ports:
            # Check for common IoT web interfaces
            web_check = await self._check_iot_web_interface(ip)
            if web_check:
                iot_protocols.append(web_check)
        
        return iot_protocols
    
    async def _check_iot_web_interface(self, ip: str) -> Optional[Dict[str, Any]]:
        """Check for common IoT web interfaces"""
        # This would check for Philips Hue, Nest, etc.
        # Simplified implementation
        return None
    
    async def _identify_device_type(self, device_info: Dict[str, Any]) -> Dict[str, Any]:
        """Identify device type based on collected information"""
        device_type_info = {
            'device_type': 'unknown',
            'device_category': 'unknown',
            'confidence': 0.0,
            'identifying_features': []
        }
        
        open_ports = device_info.get('open_ports', [])
        hostname = device_info.get('hostname', '').lower()
        os_family = device_info.get('os_family', '').lower()
        
        # NAS/Storage device detection (highest priority)
        synology_ports = [5000, 5001, 8006, 8007, 9000, 9001]
        nas_ports = [548, 2049, 111] + synology_ports  # AFP, NFS, RPC + Synology
        if any(p in open_ports for p in synology_ports):
            device_type_info['device_type'] = 'synology_nas'
            device_type_info['device_category'] = 'storage'
            device_type_info['confidence'] = 0.95
            device_type_info['identifying_features'].append('synology_services_detected')
        elif any(p in open_ports for p in nas_ports):
            device_type_info['device_type'] = 'nas_storage'
            device_type_info['device_category'] = 'storage'
            device_type_info['confidence'] = 0.85
            device_type_info['identifying_features'].append('nas_services_detected')
        
        # Router detection
        elif [53, 80, 443] == [p for p in [53, 80, 443] if p in open_ports]:  # DNS + HTTP + HTTPS
            device_type_info['device_type'] = 'router'
            device_type_info['device_category'] = 'network_infrastructure'
            device_type_info['confidence'] = 0.9
            device_type_info['identifying_features'].append('router_service_triad')
        elif len([p for p in [53, 80, 443, 22, 23] if p in open_ports]) >= 3:
            device_type_info['device_type'] = 'router'
            device_type_info['device_category'] = 'network_infrastructure'
            device_type_info['confidence'] = 0.8
            device_type_info['identifying_features'].append('multiple_network_services')
        
        # Computer detection
        elif any(p in open_ports for p in [22, 3389, 5900]):  # SSH, RDP, VNC
            if 'windows' in os_family:
                device_type_info['device_type'] = 'windows_computer'
            elif 'linux' in os_family:
                device_type_info['device_type'] = 'linux_computer'
            else:
                device_type_info['device_type'] = 'computer'
            device_type_info['device_category'] = 'computer'
            device_type_info['confidence'] = 0.7
        
        # IoT device detection
        elif device_info.get('iot_protocols'):
            device_type_info['device_type'] = 'iot_device'
            device_type_info['device_category'] = 'smart_home'
            device_type_info['confidence'] = 0.9
            device_type_info['identifying_features'].append('iot_protocols_detected')
        
        # Printer detection
        elif any(p in open_ports for p in [515, 631, 9100]):  # LPD, IPP, JetDirect
            device_type_info['device_type'] = 'printer'
            device_type_info['device_category'] = 'peripheral'
            device_type_info['confidence'] = 0.9
        
        print(f"   🤖 Device Type: {device_type_info['device_type']} (Confidence: {device_type_info['confidence']:.1%})")
        return device_type_info
    
    async def _identify_manufacturer(self, ip: str) -> Dict[str, Any]:
        """Identify device manufacturer using MAC address OUI lookup"""
        manufacturer_info = {
            'manufacturer': 'unknown',
            'mac_address': 'unknown',
            'oui': 'unknown',
            'vendor_info': {}
        }
        
        try:
            # Get MAC address using ARP
            if platform.system() == "Linux":
                result = await asyncio.create_subprocess_exec(
                    'arp', '-n', ip,
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE
                )
                stdout, stderr = await asyncio.wait_for(result.communicate(), timeout=3)
                
                if result.returncode == 0:
                    arp_output = stdout.decode()
                    # Extract MAC address from ARP output
                    mac_match = re.search(r'([0-9a-fA-F]{2}[:-]){5}[0-9a-fA-F]{2}', arp_output)
                    if mac_match:
                        mac_address = mac_match.group(0)
                        manufacturer_info['mac_address'] = mac_address
                        
                        # Extract OUI (first 3 octets)
                        oui = mac_address.replace(':', '').replace('-', '').upper()[:6]
                        manufacturer_info['oui'] = oui
                        
                        # Basic manufacturer lookup (would need OUI database for full implementation)
                        manufacturer = self._lookup_manufacturer_by_oui(oui)
                        manufacturer_info['manufacturer'] = manufacturer
                        
                        print(f"   🏭 Manufacturer: {manufacturer} (MAC: {mac_address})")
        
        except Exception as e:
            print(f"   ⚠️  Manufacturer lookup error: {e}")
        
        return manufacturer_info
    
    def _lookup_manufacturer_by_oui(self, oui: str) -> str:
        """Lookup manufacturer by OUI (simplified)"""
        # Simplified OUI database - in production would use full IEEE OUI database
        oui_database = {
            '00:50:56': 'VMware',
            '08:00:27': 'Oracle VirtualBox',
            '00:0C:29': 'VMware',
            '00:16:3E': 'Xensource',
            '52:54:00': 'QEMU/KVM',
            '00:1B:63': 'Apple',
            '00:21:CC': 'Apple',
            'B8:27:EB': 'Raspberry Pi Foundation',
            'DC:A6:32': 'Raspberry Pi Foundation',
            '00:04:20': 'Slim Devices (Logitech)',
            '00:22:6B': 'Logitech',
            '00:0A:95': 'Apple',
            '28:CF:E9': 'Apple',
            '3C:22:FB': 'Apple',
            '70:56:81': 'Apple',
            'AC:BC:32': 'Apple',
            'F0:18:98': 'Apple'
        }
        
        return oui_database.get(oui, 'Unknown Manufacturer')
    
    def _generate_network_fingerprint(self, network_range: str, gateway_ip: str = None, devices: List[Dict] = None) -> Dict[str, Any]:
        """
        Generate a unique fingerprint for the network to distinguish between similar IP ranges.
        
        Args:
            network_range: Network range (e.g., '192.168.1.0/24')
            gateway_ip: Gateway IP address
            devices: List of discovered devices
            
        Returns:
            Dict[str, Any]: Network fingerprint information
        """
        fingerprint_data = {
            'network_range': network_range,
            'scan_timestamp': datetime.now().isoformat(),
            'gateway_ip': gateway_ip,
            'device_count': len(devices) if devices else 0,
        }
        
        # Create device signature based on MAC addresses and hostnames
        device_signatures = []
        if devices:
            for device in devices:
                signature = {
                    'ip': device.get('ip'),
                    'mac': device.get('mac_address', ''),
                    'hostname': device.get('hostname', ''),
                    'device_type': device.get('device_type', ''),
                    'manufacturer': device.get('manufacturer', '')
                }
                device_signatures.append(signature)
        
        fingerprint_data['device_signatures'] = device_signatures
        
        # Generate short network code based on unique characteristics
        fingerprint_string = f"{network_range}_{gateway_ip}_" + "_".join([
            f"{d.get('mac_address', '')}_{d.get('hostname', '')}" 
            for d in device_signatures[:3]  # Use first 3 devices for fingerprint
        ])
        
        # Create short hash for network code
        hash_object = hashlib.md5(fingerprint_string.encode())
        network_hash = hash_object.hexdigest()[:8].upper()
        
        # Generate human-readable network code
        network_code = f"NET-{network_hash}"
        
        fingerprint_data.update({
            'network_code': network_code,
            'network_hash': network_hash,
            'fingerprint_string': fingerprint_string,
            'scan_date': datetime.now().strftime('%Y-%m-%d'),
            'scan_time': datetime.now().strftime('%H:%M:%S')
        })
        
        return fingerprint_data
    
    async def _get_default_gateway(self) -> Optional[str]:
        """
        Get the default gateway IP address.
        
        Returns:
            Optional[str]: Gateway IP address or None if not found
        """
        try:
            if platform.system() == "Windows":
                result = subprocess.run(['route', 'print', '0.0.0.0'], 
                                       capture_output=True, text=True, timeout=10)
                for line in result.stdout.split('\n'):
                    if '0.0.0.0' in line and 'Gateway' in line:
                        parts = line.split()
                        for part in parts:
                            if re.match(r'\d+\.\d+\.\d+\.\d+', part):
                                return part
            else:
                # Linux/macOS
                result = subprocess.run(['ip', 'route', 'show', 'default'], 
                                       capture_output=True, text=True, timeout=10)
                if result.returncode == 0:
                    for line in result.stdout.split('\n'):
                        if 'default' in line:
                            parts = line.split()
                            if 'via' in parts:
                                via_index = parts.index('via')
                                if via_index + 1 < len(parts):
                                    gateway = parts[via_index + 1]
                                    if re.match(r'\d+\.\d+\.\d+\.\d+', gateway):
                                        return gateway
                
                # Fallback to route command
                result = subprocess.run(['route', '-n'], 
                                       capture_output=True, text=True, timeout=10)
                if result.returncode == 0:
                    for line in result.stdout.split('\n'):
                        if line.startswith('0.0.0.0'):
                            parts = line.split()
                            if len(parts) >= 2:
                                gateway = parts[1]
                                if re.match(r'\d+\.\d+\.\d+\.\d+', gateway):
                                    return gateway
        except Exception as e:
            self.logger.warning(f"Failed to get default gateway: {e}")
        
        return None
    
    def _print_device_summary(self, device_info: Dict[str, Any], device_number: int) -> None:
        """Print a summary of the analyzed device"""
        print(f"\n📋 Device #{device_number} Analysis Complete")
        print("─" * 50)
        print(f"🌐 IP Address: {device_info.get('ip', 'unknown')}")
        print(f"🏷️  Hostname: {device_info.get('hostname', 'unknown')}")
        print(f"🖥️  OS Family: {device_info.get('os_family', 'unknown')}")
        print(f"🤖 Device Type: {device_info.get('device_type', 'unknown')}")
        print(f"🏭 Manufacturer: {device_info.get('manufacturer', 'unknown')}")
        
        open_ports = device_info.get('open_ports', [])
        if open_ports:
            print(f"📡 Open Ports: {', '.join(map(str, open_ports))}")
        
        iot_protocols = device_info.get('iot_protocols', [])
        if iot_protocols:
            protocol_names = [p.get('protocol', 'unknown') for p in iot_protocols]
            print(f"🏠 IoT Protocols: {', '.join(protocol_names)}")
        
        web_servers = device_info.get('web_servers', [])
        if web_servers:
            print(f"🌐 Web Services: {len(web_servers)} detected")
        
        print("─" * 50)
    
    async def get_scan_status(self) -> Dict[str, Any]:
        """
        Get current scan status.
        
        Returns:
            Dict[str, Any]: Current scan status
        """
        return {
            'is_scanning': self.is_scanning,
            'scan_id': self.current_scan_id,
            'progress': self.scan_progress,
            'devices_discovered': len(self.discovered_devices),
            'stats': self.stats.copy()
        }
    
    async def stop_scan(self) -> bool:
        """
        Stop current scan operation.
        
        Returns:
            bool: True if scan stopped successfully
        """
        if not self.is_scanning:
            return True
        
        self.logger.info("Stopping current scan...")
        self.is_scanning = False
        self.current_scan_id = None
        self.scan_progress = 0.0
        
        # Publish scan stopped event
        await self.event_bus.publish(create_event(
            R2Events.NETWORK_SCAN_ERROR,  # Using error event for cancelled scans
            {
                "scan_id": self.current_scan_id,
                "error": "Scan cancelled by user",
                "reason": "user_cancelled"
            },
            self.module_name
        ))
        
        return True
    
    async def _on_system_startup(self, event) -> None:
        """Handle system startup event"""
        self.logger.info("System startup detected")
    
    async def discover_available_networks(self) -> List[Dict[str, Any]]:
        """
        Discover available networks (WiFi, etc.).
        
        Returns:
            List[Dict[str, Any]]: List of available networks with details
        """
        try:
            self.logger.info("Discovering available networks...")
            
            # Publish network discovery started event
            await self.event_bus.publish(create_event(
                R2Events.NETWORK_SCAN_STARTED,
                {
                    "scan_type": "network_discovery",
                    "scanner": self.module_name
                },
                self.module_name
            ))
            
            networks = []
            
            # Get current network info first
            current_network = await self.get_current_network()
            if current_network:
                networks.append(current_network)
            
            # Discover WiFi networks
            wifi_networks = await self._discover_wifi_networks()
            networks.extend(wifi_networks)
            
            # Discover wired networks
            wired_networks = await self._discover_wired_networks()
            networks.extend(wired_networks)
            
            # Publish network discovery completed event
            await self.event_bus.publish(create_event(
                R2Events.NETWORK_SCAN_COMPLETED,
                {
                    "scan_type": "network_discovery",
                    "networks_found": len(networks),
                    "networks": networks
                },
                self.module_name
            ))
            
            self.logger.info(f"Network discovery complete: {len(networks)} networks found")
            return networks
            
        except Exception as e:
            self.logger.error(f"Network discovery failed: {e}")
            
            # Publish network discovery error event
            await self.event_bus.publish(create_event(
                R2Events.NETWORK_SCAN_ERROR,
                {
                    "scan_type": "network_discovery",
                    "error": str(e)
                },
                self.module_name
            ))
            
            raise R2NetworkException(f"Network discovery failed: {e}")
    
    async def get_current_network(self) -> Dict[str, Any]:
        """
        Get information about the current network connection.
        
        Returns:
            Dict[str, Any]: Current network information
        """
        try:
            network_info = {
                'type': 'unknown',
                'interface': 'unknown',
                'ip_address': 'unknown',
                'subnet': 'unknown',
                'gateway': 'unknown',
                'dns_servers': [],
                'status': 'unknown'
            }
            
            # Get current IP and interface
            current_ip = await self._get_current_ip()
            if current_ip:
                network_info['ip_address'] = current_ip
                network_info['subnet'] = await self._get_subnet_mask(current_ip)
                network_info['gateway'] = await self._get_default_gateway()
                network_info['dns_servers'] = await self._get_dns_servers()
                network_info['status'] = 'connected'
            
            # Determine network type
            network_info['type'] = await self._determine_network_type()
            network_info['interface'] = await self._get_network_interface()
            
            return network_info
            
        except Exception as e:
            self.logger.error(f"Failed to get current network info: {e}")
            return {
                'type': 'unknown',
                'interface': 'unknown',
                'ip_address': 'unknown',
                'subnet': 'unknown',
                'gateway': 'unknown',
                'dns_servers': [],
                'status': 'error',
                'error': str(e)
            }
    
    async def _discover_wifi_networks(self) -> List[Dict[str, Any]]:
        """Discover WiFi networks"""
        networks = []
        
        try:
            # First check if we have any wireless interfaces
            if not await self._has_wireless_interfaces():
                self.logger.info("No wireless interfaces detected - skipping WiFi discovery")
                return networks
            
            if platform.system() == "Linux":
                # Use iwlist for Linux with shorter timeout for testing
                try:
                    result = await asyncio.create_subprocess_exec(
                        'iwlist', 'scan',
                        stdout=asyncio.subprocess.PIPE,
                        stderr=asyncio.subprocess.PIPE
                    )
                    stdout, stderr = await asyncio.wait_for(result.communicate(), timeout=3)
                    
                    if result.returncode == 0:
                        networks = self._parse_iwlist_output(stdout.decode())
                    else:
                        self.logger.info("iwlist scan failed, trying nmcli with short timeout")
                        networks = await self._discover_wifi_nmcli()
                        
                except asyncio.TimeoutError:
                    self.logger.warning("iwlist scan timed out, trying nmcli")
                    networks = await self._discover_wifi_nmcli()
            
            elif platform.system() == "Darwin":  # macOS
                networks = await self._discover_wifi_airport()
            
            else:
                self.logger.warning(f"WiFi discovery not implemented for {platform.system()}")
                
        except Exception as e:
            self.logger.warning(f"WiFi discovery failed: {e}")
        
        return networks
    
    async def _discover_wifi_nmcli(self) -> List[Dict[str, Any]]:
        """Discover WiFi networks using nmcli"""
        networks = []
        
        try:
            result = await asyncio.create_subprocess_exec(
                'nmcli', '-t', '-f', 'SSID,SIGNAL,SECURITY', 'dev', 'wifi',
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            # Shorter timeout for testing - nmcli hangs on systems without WiFi
            stdout, stderr = await asyncio.wait_for(result.communicate(), timeout=2)
            
            if result.returncode == 0:
                lines = stdout.decode().strip().split('\n')
                for line in lines:
                    if line and ':' in line:
                        parts = line.split(':')
                        if len(parts) >= 3:
                            ssid = parts[0] if parts[0] else 'Hidden Network'
                            signal = parts[1] if parts[1] else '0'
                            security = parts[2] if parts[2] else 'Open'
                            
                            networks.append({
                                'type': 'wifi',
                                'ssid': ssid,
                                'signal_strength': int(signal) if signal.isdigit() else 0,
                                'security': security,
                                'status': 'available',
                                'encryption': 'WPA2' if 'WPA' in security else 'Open' if security == 'Open' else 'Unknown'
                            })
                            
        except asyncio.TimeoutError:
            self.logger.warning("nmcli WiFi discovery timed out - likely no wireless interfaces")
        except Exception as e:
            self.logger.warning(f"nmcli WiFi discovery failed: {e}")
        
        return networks
    
    async def _has_wireless_interfaces(self) -> bool:
        """Check if system has wireless interfaces"""
        try:
            # Check for wireless interfaces using ip link
            result = await asyncio.create_subprocess_exec(
                'ip', 'link', 'show',
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            stdout, stderr = await asyncio.wait_for(result.communicate(), timeout=2)
            
            if result.returncode == 0:
                output = stdout.decode()
                # Look for common wireless interface patterns
                wireless_patterns = ['wlan', 'wifi', 'wlp', 'wlx']
                for pattern in wireless_patterns:
                    if pattern in output.lower():
                        return True
            
            return False
            
        except Exception as e:
            self.logger.warning(f"Failed to check wireless interfaces: {e}")
            return False  # Assume no wireless if we can't check
    
    async def _discover_wifi_airport(self) -> List[Dict[str, Any]]:
        """Discover WiFi networks using airport on macOS"""
        networks = []
        
        try:
            # Try to find airport utility
            airport_paths = [
                '/System/Library/PrivateFrameworks/Apple80211.framework/Versions/Current/Resources/airport',
                '/usr/local/bin/airport'
            ]
            
            airport_cmd = None
            for path in airport_paths:
                try:
                    result = await asyncio.create_subprocess_exec(
                        'test', '-f', path,
                        stdout=asyncio.subprocess.PIPE,
                        stderr=asyncio.subprocess.PIPE
                    )
                    await result.wait()
                    if result.returncode == 0:
                        airport_cmd = path
                        break
                except:
                    continue
            
            if airport_cmd:
                result = await asyncio.create_subprocess_exec(
                    airport_cmd, '-s',
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE
                )
                stdout, stderr = await asyncio.wait_for(result.communicate(), timeout=10)
                
                if result.returncode == 0:
                    networks = self._parse_airport_output(stdout.decode())
                    
        except Exception as e:
            self.logger.warning(f"airport WiFi discovery failed: {e}")
        
        return networks
    
    def _parse_iwlist_output(self, output: str) -> List[Dict[str, Any]]:
        """Parse iwlist scan output"""
        networks = []
        
        try:
            # Simple parsing of iwlist output
            cells = output.split('Cell ')
            for cell in cells[1:]:  # Skip first empty part
                network = {
                    'type': 'wifi',
                    'ssid': 'Unknown',
                    'signal_strength': 0,
                    'security': 'Unknown',
                    'status': 'available',
                    'encryption': 'Unknown'
                }
                
                # Extract SSID
                ssid_match = re.search(r'ESSID:"([^"]*)"', cell)
                if ssid_match:
                    network['ssid'] = ssid_match.group(1) if ssid_match.group(1) else 'Hidden Network'
                
                # Extract signal strength
                signal_match = re.search(r'Signal level=(-?\d+)', cell)
                if signal_match:
                    network['signal_strength'] = int(signal_match.group(1))
                
                # Extract encryption
                if 'WPA2' in cell:
                    network['encryption'] = 'WPA2'
                    network['security'] = 'WPA2'
                elif 'WPA' in cell:
                    network['encryption'] = 'WPA'
                    network['security'] = 'WPA'
                elif 'WEP' in cell:
                    network['encryption'] = 'WEP'
                    network['security'] = 'WEP'
                else:
                    network['encryption'] = 'Open'
                    network['security'] = 'Open'
                
                networks.append(network)
                
        except Exception as e:
            self.logger.warning(f"Failed to parse iwlist output: {e}")
        
        return networks
    
    def _parse_airport_output(self, output: str) -> List[Dict[str, Any]]:
        """Parse airport scan output"""
        networks = []
        
        try:
            lines = output.strip().split('\n')
            for line in lines[1:]:  # Skip header
                parts = line.split()
                if len(parts) >= 6:
                    ssid = parts[0]
                    signal = parts[1]
                    security = ' '.join(parts[5:]) if len(parts) > 5 else 'Open'
                    
                    networks.append({
                        'type': 'wifi',
                        'ssid': ssid,
                        'signal_strength': int(signal) if signal.isdigit() else 0,
                        'security': security,
                        'status': 'available',
                        'encryption': 'WPA2' if 'WPA2' in security else 'WPA' if 'WPA' in security else 'Open'
                    })
                    
        except Exception as e:
            self.logger.warning(f"Failed to parse airport output: {e}")
        
        return networks
    
    async def _discover_wired_networks(self) -> List[Dict[str, Any]]:
        """Discover wired network connections"""
        networks = []
        
        try:
            # Get current wired connection info
            current_network = await self.get_current_network()
            if current_network and current_network['type'] == 'ethernet':
                networks.append(current_network)
                
        except Exception as e:
            self.logger.warning(f"Wired network discovery failed: {e}")
        
        return networks
    
    # =================================================================
    # IOT PROTOCOL DISCOVERY
    # =================================================================
    
    async def scan_iot_protocols(self, host: str) -> Dict[str, Any]:
        """
        Scan for IoT-specific protocols and services.
        R2 speaks droid!
        """
        self.logger.info(f"🤖 R2 scanning IoT protocols on {host}")
        
        iot_info = {
            'mqtt': await self._scan_mqtt(host),
            'coap': await self._scan_coap(host),
            'modbus': await self._scan_modbus(host),
            'bacnet': await self._scan_bacnet(host),
            'knx': await self._scan_knx(host),
            'zigbee': await self._scan_zigbee(host),
            'zwave': await self._scan_zwave(host)
        }
        
        return iot_info
    
    async def _scan_mqtt(self, host: str) -> Dict[str, Any]:
        """Scan for MQTT brokers."""
        # TODO: Implement MQTT broker discovery and topic enumeration
        self.logger.debug(f"🔍 R2 scanning MQTT on {host}")
        return {'broker_available': False, 'topics': []}
    
    async def _scan_coap(self, host: str) -> Dict[str, Any]:
        """Scan for CoAP endpoints."""
        # TODO: Implement CoAP resource discovery
        self.logger.debug(f"🔍 R2 scanning CoAP on {host}")
        return {'coap_available': False, 'resources': []}
    
    async def _scan_modbus(self, host: str) -> Dict[str, Any]:
        """Scan for Modbus TCP devices."""
        # TODO: Implement Modbus device enumeration
        self.logger.debug(f"🔍 R2 scanning Modbus on {host}")
        return {'modbus_available': False, 'unit_ids': []}
    
    async def _scan_bacnet(self, host: str) -> Dict[str, Any]:
        """Scan for BACnet devices."""
        # TODO: Implement BACnet device discovery
        self.logger.debug(f"🔍 R2 scanning BACnet on {host}")
        return {'bacnet_available': False, 'device_id': None}
    
    async def _scan_knx(self, host: str) -> Dict[str, Any]:
        """Scan for KNX/EIB devices."""
        # TODO: Implement KNX device discovery
        self.logger.debug(f"🔍 R2 scanning KNX on {host}")
        return {'knx_available': False, 'group_addresses': []}
    
    async def _scan_zigbee(self, host: str) -> Dict[str, Any]:
        """Scan for Zigbee coordinators."""
        # TODO: Implement Zigbee network discovery
        self.logger.debug(f"🔍 R2 scanning Zigbee on {host}")
        return {'coordinator_available': False, 'network_devices': []}
    
    async def _scan_zwave(self, host: str) -> Dict[str, Any]:
        """Scan for Z-Wave controllers."""
        # TODO: Implement Z-Wave network discovery
        self.logger.debug(f"🔍 R2 scanning Z-Wave on {host}")
        return {'controller_available': False, 'node_count': 0}

    # =================================================================
    # WIRELESS ENVIRONMENT ASSESSMENT
    # =================================================================
    
    async def scan_wireless_environment(self) -> Dict[str, Any]:
        """
        Comprehensive wireless environment scan.
        R2's electromagnetic awareness!
        """
        self.logger.info("📡 R2 scanning wireless environment...")
        
        wireless_info = {
            'wifi_networks': await self._scan_wifi_networks(),
            'bluetooth_devices': await self._scan_bluetooth_devices(),
            'rf_spectrum': await self._analyze_rf_spectrum(),
            'zigbee_networks': await self._scan_zigbee_networks(),
            'zwave_networks': await self._scan_zwave_networks()
        }
        
        return wireless_info
    
    async def _scan_wifi_networks(self) -> List[Dict[str, Any]]:
        """Scan for WiFi networks."""
        # TODO: Implement WiFi network enumeration
        self.logger.debug("🔍 R2 scanning WiFi networks")
        return []
    
    async def _scan_bluetooth_devices(self) -> List[Dict[str, Any]]:
        """Scan for Bluetooth devices."""
        # TODO: Implement Bluetooth device discovery
        self.logger.debug("🔍 R2 scanning Bluetooth devices")
        return []
    
    async def _analyze_rf_spectrum(self) -> Dict[str, Any]:
        """Analyze RF spectrum usage."""
        # TODO: Implement RF spectrum analysis
        self.logger.debug("🔍 R2 analyzing RF spectrum")
        return {'bands_detected': []}
    
    async def _scan_zigbee_networks(self) -> List[Dict[str, Any]]:
        """Scan for Zigbee networks."""
        # TODO: Implement Zigbee network scanning
        self.logger.debug("🔍 R2 scanning Zigbee networks")
        return []
    
    async def _scan_zwave_networks(self) -> List[Dict[str, Any]]:
        """Scan for Z-Wave networks."""
        # TODO: Implement Z-Wave network scanning
        self.logger.debug("🔍 R2 scanning Z-Wave networks")
        return []

    # =================================================================
    # SMART HOME DEVICE INTEGRATION
    # =================================================================
    
    async def scan_smart_home_devices(self) -> Dict[str, Any]:
        """
        Scan for and integrate with smart home devices.
        R2's home automation interface!
        """
        self.logger.info("🏠 R2 scanning smart home devices...")
        
        smart_devices = {
            'hue_bridges': await self._scan_hue_bridges(),
            'nest_devices': await self._scan_nest_devices(),
            'security_cameras': await self._scan_security_cameras(),
            'smart_switches': await self._scan_smart_switches(),
            'sensors': await self._scan_environmental_sensors()
        }
        
        return smart_devices
    
    async def _scan_hue_bridges(self) -> List[Dict[str, Any]]:
        """Scan for Philips Hue bridges."""
        # TODO: Implement Hue bridge discovery and status
        self.logger.debug("🔍 R2 scanning Hue bridges")
        return []
    
    async def _scan_nest_devices(self) -> List[Dict[str, Any]]:
        """Scan for Nest/Ecobee thermostats."""
        # TODO: Implement thermostat discovery
        self.logger.debug("🔍 R2 scanning Nest devices")
        return []
    
    async def _scan_security_cameras(self) -> List[Dict[str, Any]]:
        """Scan for security cameras."""
        # TODO: Implement camera discovery and health check
        self.logger.debug("🔍 R2 scanning security cameras")
        return []
    
    async def _scan_smart_switches(self) -> List[Dict[str, Any]]:
        """Scan for smart switches and outlets."""
        # TODO: Implement smart switch discovery
        self.logger.debug("🔍 R2 scanning smart switches")
        return []
    
    async def _scan_environmental_sensors(self) -> List[Dict[str, Any]]:
        """Scan for environmental sensors."""
        # TODO: Implement sensor discovery and data collection
        self.logger.debug("🔍 R2 scanning environmental sensors")
        return []
    
    async def _get_current_ip(self) -> Optional[str]:
        """Get current IP address"""
        try:
            # Connect to a remote address to determine local IP
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(("8.8.8.8", 80))
            ip = s.getsockname()[0]
            s.close()
            return ip
        except Exception:
            return None
    
    async def _get_subnet_mask(self, ip: str) -> str:
        """Get subnet mask for IP"""
        try:
            # Simple heuristic based on IP class
            parts = ip.split('.')
            if len(parts) == 4:
                first_octet = int(parts[0])
                if 1 <= first_octet <= 126:
                    return "255.0.0.0"  # Class A
                elif 128 <= first_octet <= 191:
                    return "255.255.0.0"  # Class B
                elif 192 <= first_octet <= 223:
                    return "255.255.255.0"  # Class C
            return "255.255.255.0"  # Default
        except Exception:
            return "255.255.255.0"
    
    async def _get_default_gateway(self) -> Optional[str]:
        """Get default gateway"""
        try:
            if platform.system() == "Linux":
                result = await asyncio.create_subprocess_exec(
                    'ip', 'route', 'show', 'default',
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE
                )
                stdout, stderr = await asyncio.wait_for(result.communicate(), timeout=2)
                if result.returncode == 0:
                    lines = stdout.decode().strip().split('\n')
                    for line in lines:
                        if 'default' in line:
                            parts = line.split()
                            if len(parts) >= 3:
                                return parts[2]
            elif platform.system() == "Darwin":
                result = await asyncio.create_subprocess_exec(
                    'route', '-n', 'get', 'default',
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE
                )
                stdout, stderr = await asyncio.wait_for(result.communicate(), timeout=2)
                if result.returncode == 0:
                    lines = stdout.decode().strip().split('\n')
                    for line in lines:
                        if 'gateway:' in line:
                            return line.split(':')[1].strip()
        except Exception:
            pass
        return None
    
    async def _get_dns_servers(self) -> List[str]:
        """Get DNS servers"""
        try:
            if platform.system() == "Linux":
                with open('/etc/resolv.conf', 'r') as f:
                    lines = f.readlines()
                    dns_servers = []
                    for line in lines:
                        if line.startswith('nameserver'):
                            dns_servers.append(line.split()[1])
                    return dns_servers
        except Exception:
            pass
        return []
    
    async def _determine_network_type(self) -> str:
        """Determine network type (ethernet, wifi, etc.)"""
        try:
            # Use our existing wireless interface detection
            if await self._has_wireless_interfaces():
                return 'wifi'
            else:
                return 'ethernet'
        except Exception:
            pass
        return 'unknown'
    
    async def _get_network_interface(self) -> str:
        """Get network interface name"""
        try:
            if platform.system() == "Linux":
                result = await asyncio.create_subprocess_exec(
                    'ip', 'route', 'show', 'default',
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE
                )
                stdout, stderr = await asyncio.wait_for(result.communicate(), timeout=2)
                if result.returncode == 0:
                    lines = stdout.decode().strip().split('\n')
                    for line in lines:
                        if 'default' in line:
                            parts = line.split()
                            if len(parts) >= 5:
                                return parts[4]
        except asyncio.TimeoutError:
            self.logger.warning("Network interface detection timed out")
        except Exception as e:
            self.logger.warning(f"Network interface detection failed: {e}")
        return 'unknown'
    
    async def _on_system_shutdown(self, event) -> None:
        """Handle system shutdown event"""
        self.logger.info("System shutdown detected")
        if self.is_scanning:
            await self.stop_scan()