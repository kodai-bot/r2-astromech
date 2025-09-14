"""
Modular Network Scanner Implementation

This module implements the INetworkScanner interface for the new modular R2 system.
It provides event-driven network scanning with proper encapsulation.
"""

import asyncio
import subprocess
import socket
import ipaddress
from typing import List, Dict, Optional, Any
from datetime import datetime
import logging

from ...core.interfaces import IModule, ModuleStatus
from ...core.events import EventBus, create_event, R2Events
from ..discovery.interfaces import INetworkScanner
from ...utils.exceptions import R2NetworkException, R2ModuleException
from ...utils.logging import get_module_logger

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
        self.port_scan_timeout = config.get('port_scan_timeout', 3)
        self.common_ports = config.get('common_ports', [22, 23, 53, 80, 135, 139, 443, 445, 993, 995, 1723, 3389, 5900, 8080])
        
        # Statistics
        self.stats = {
            'scans_completed': 0,
            'devices_discovered': 0,
            'ports_scanned': 0,
            'errors': 0
        }
        
        self.logger.info("Modular Network Scanner initialized")
    
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
            self.logger.info(f"Starting network scan: {target_network}")
            
            # Initialize scan state
            self.is_scanning = True
            self.current_scan_id = scan_id
            self.scan_progress = 0.0
            self.discovered_devices.clear()
            
            # Publish scan started event
            await self.event_bus.publish(create_event(
                R2Events.NETWORK_SCAN_STARTED,
                {
                    "scan_id": scan_id,
                    "target_network": target_network,
                    "scanner": self.module_name
                },
                self.module_name,
                correlation_id=scan_id
            ))
            
            # Perform ping sweep
            active_hosts = await self.ping_sweep(target_network, scan_id)
            
            # Analyze each discovered device
            for i, host in enumerate(active_hosts):
                device_info = {
                    'ip': host,
                    'status': 'active',
                    'discovery_method': 'ping',
                    'timestamp': datetime.now().isoformat(),
                    'scan_id': scan_id
                }
                
                # Publish device discovered event
                await self.event_bus.publish(create_event(
                    R2Events.DEVICE_DISCOVERED,
                    {
                        "device": device_info,
                        "scan_id": scan_id,
                        "device_number": i + 1,
                        "total_devices": len(active_hosts)
                    },
                    self.module_name,
                    correlation_id=scan_id
                ))
                
                # Perform port scan on the device
                port_info = await self.port_scan(host)
                device_info['port_info'] = port_info
                
                # Publish device analyzed event
                await self.event_bus.publish(create_event(
                    R2Events.DEVICE_ANALYZED,
                    {
                        "device": device_info,
                        "scan_id": scan_id,
                        "analysis_type": "port_scan"
                    },
                    self.module_name,
                    correlation_id=scan_id
                ))
                
                self.discovered_devices.append(device_info)
                self.stats['devices_discovered'] += 1
                
                # Update progress
                self.scan_progress = (i + 1) / len(active_hosts) * 100
            
            # Publish scan completed event
            await self.event_bus.publish(create_event(
                R2Events.NETWORK_SCAN_COMPLETED,
                {
                    "scan_id": scan_id,
                    "devices_found": len(self.discovered_devices),
                    "scan_duration": "N/A",  # TODO: Calculate actual duration
                    "stats": self.stats
                },
                self.module_name,
                correlation_id=scan_id
            ))
            
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
    
    async def ping_sweep(self, network: str, scan_id: str) -> List[str]:
        """
        Perform ping sweep to find active hosts.
        
        Args:
            network: Network range (e.g., '192.168.1.0/24')
            scan_id: Scan identifier for correlation
            
        Returns:
            List[str]: List of active host IPs
        """
        active_hosts = []
        
        try:
            # Parse the network range
            network_obj = ipaddress.IPv4Network(network, strict=False)
            total_hosts = list(network_obj.hosts())
            
            self.logger.info(f"Ping sweep scanning {network} ({len(total_hosts)} addresses)")
            
            # Progress tracking
            for i, host in enumerate(total_hosts):
                if not self.is_scanning:  # Check if scan was cancelled
                    break
                
                # Show progress every 10 hosts
                if i % 10 == 0:
                    progress = (i / len(total_hosts)) * 100
                    self.logger.info(f"Ping sweep progress: {i}/{len(total_hosts)} hosts checked ({progress:.1f}%)")
                
                if await self._ping_host(str(host)):
                    active_hosts.append(str(host))
                    self.logger.info(f"Active host found: {host}")
                    
                    # Publish individual host discovery event
                    await self.event_bus.publish(create_event(
                        R2Events.DEVICE_DISCOVERED,
                        {
                            "ip": str(host),
                            "discovery_method": "ping",
                            "scan_id": scan_id,
                            "host_number": len(active_hosts)
                        },
                        self.module_name,
                        correlation_id=scan_id
                    ))
            
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
        Scan ports on a specific host.
        
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
            22: "SSH", 23: "Telnet", 53: "DNS", 80: "HTTP", 
            135: "RPC", 139: "NetBIOS", 443: "HTTPS", 445: "SMB",
            993: "IMAPS", 995: "POP3S", 1723: "PPTP", 3389: "RDP", 
            5900: "VNC", 8080: "HTTP-Alt", 1883: "MQTT", 8883: "MQTT-SSL",
            5683: "CoAP", 502: "Modbus", 47808: "BACnet", 3671: "KNX"
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
        self.logger.info(f"Scanning device: {ip}")
        
        device_info = {
            'ip': ip,
            'timestamp': datetime.now().isoformat(),
            'scan_type': 'detailed'
        }
        
        # Perform port scan
        port_info = await self.port_scan(ip)
        device_info.update(port_info)
        
        # TODO: Add more detailed analysis (OS fingerprinting, service enumeration, etc.)
        
        return device_info
    
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
    
    async def _on_system_shutdown(self, event) -> None:
        """Handle system shutdown event"""
        self.logger.info("System shutdown detected")
        if self.is_scanning:
            await self.stop_scan()