"""
Base Interfaces for Discovery Scanners

Defines common interfaces and data structures for all specialized scanners.
Ensures consistency and maintains event broadcasting for R2's audio system.
"""

from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
import logging

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '../../..'))

from core.events import EventBus


@dataclass
class ScannerConfig:
    """Configuration for scanner modules"""
    enabled: bool = True
    timeout: float = 30.0
    max_concurrent: int = 10
    custom_options: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.custom_options is None:
            self.custom_options = {}


@dataclass 
class DeviceInfo:
    """Enhanced device information structure"""
    ip: str
    status: str = "unknown"
    hostname: Optional[str] = None
    mac_address: Optional[str] = None
    manufacturer: Optional[str] = None
    device_type: Optional[str] = None
    os_family: Optional[str] = None
    open_ports: List[int] = None
    services: Dict[int, str] = None
    mdns_services: List[Dict[str, Any]] = None
    snmp_info: Dict[str, Any] = None
    confidence: float = 0.0
    discovery_method: str = "unknown"
    timestamp: str = ""
    scan_id: str = ""
    first_seen: Optional[str] = None
    last_seen: Optional[str] = None
    discovery_count: int = 1
    
    def __post_init__(self):
        if self.open_ports is None:
            self.open_ports = []
        if self.services is None:
            self.services = {}
        if self.mdns_services is None:
            self.mdns_services = []
        if self.snmp_info is None:
            self.snmp_info = {}
        if not self.first_seen:
            self.first_seen = self.timestamp
        if not self.last_seen:
            self.last_seen = self.timestamp
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert DeviceInfo to dictionary for database storage"""
        return {
            'ip': self.ip,
            'status': self.status,
            'hostname': self.hostname,
            'mac_address': self.mac_address,
            'manufacturer': self.manufacturer,
            'device_type': self.device_type,
            'os_family': self.os_family,
            'open_ports': self.open_ports,
            'services': self.services,
            'mdns_services': self.mdns_services,
            'snmp_info': self.snmp_info,
            'confidence': self.confidence,
            'discovery_method': self.discovery_method,
            'timestamp': self.timestamp,
            'scan_id': self.scan_id,
            'first_seen': self.first_seen,
            'last_seen': self.last_seen,
            'discovery_count': self.discovery_count
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'DeviceInfo':
        """Create DeviceInfo from dictionary (e.g., loaded from database)"""
        return cls(**{k: v for k, v in data.items() if k in cls.__annotations__})
    
    def get_friendly_name(self) -> str:
        """Get a friendly name for the device"""
        if self.hostname and self.hostname != 'unknown':
            return self.hostname
        if self.device_type and self.device_type != 'unknown':
            return f"{self.device_type.replace('_', ' ').title()} ({self.ip})"
        if self.manufacturer and self.manufacturer not in ['unknown', 'Unknown Manufacturer']:
            return f"{self.manufacturer} Device ({self.ip})"
        return f"Device {self.ip}"
    
    def get_device_icon(self) -> str:
        """Get an appropriate emoji icon for the device type"""
        icons = {
            'game_console': '🎮',
            'smart_speaker': '🔊',
            'printer': '🖨️',
            'camera': '📷',
            'server': '🖥️',
            'network_device': '🌐',
            'apple_device': '🍎',
            'smart_home_device': '🏠',
            'media_device': '📺',
            'network_service': '⚙️'
        }
        return icons.get(self.device_type, '💻')


class BaseScanner(ABC):
    """
    Base class for all specialized scanners.
    
    Ensures consistent event publishing for R2's audio feedback system
    and maintains common scanning patterns.
    """
    
    def __init__(self, event_bus: EventBus, config: ScannerConfig, logger: logging.Logger = None):
        """
        Initialize the base scanner.
        
        Args:
            event_bus: Event bus for R2 audio feedback
            config: Scanner configuration
            logger: Logger instance
        """
        self.event_bus = event_bus
        self.config = config
        self.logger = logger or logging.getLogger(self.__class__.__name__)
        
        # Scanner state
        self.is_running = False
        self.available_tools = {}
        
    @abstractmethod
    async def scan(self, target: str, scan_id: str) -> List[DeviceInfo]:
        """
        Perform the specialized scan.
        
        Args:
            target: Target network or host (e.g., "192.168.1.0/24")
            scan_id: Unique scan identifier for event correlation
            
        Returns:
            List of discovered devices with enriched information
        """
        pass
    
    @abstractmethod
    async def check_availability(self) -> bool:
        """
        Check if required tools/dependencies are available.
        
        Returns:
            True if scanner can operate, False otherwise
        """
        pass
    
    async def initialize(self) -> bool:
        """Initialize the scanner and check tool availability."""
        try:
            self.logger.info(f"Initializing {self.__class__.__name__}...")
            
            # Check tool availability
            is_available = await self.check_availability()
            if not is_available:
                self.logger.warning(f"{self.__class__.__name__} tools not available")
                return False
            
            self.is_running = True
            self.logger.info(f"{self.__class__.__name__} initialized successfully")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to initialize {self.__class__.__name__}: {e}")
            return False
    
    async def shutdown(self) -> None:
        """Shutdown the scanner and cleanup resources."""
        self.is_running = False
        self.logger.info(f"{self.__class__.__name__} shutdown complete")
    
    async def _publish_device_discovered(self, device: DeviceInfo, device_number: int, total_devices: int) -> None:
        """
        Publish device discovered event for R2 audio feedback.
        
        Args:
            device: Discovered device information
            device_number: Sequential device number in scan
            total_devices: Total expected devices in scan
        """
        try:
            from core.events import create_event, R2Events
            
            await self.event_bus.publish(create_event(
                R2Events.DEVICE_DISCOVERED,
                {
                    "device": device.__dict__,
                    "scan_id": device.scan_id,
                    "device_number": device_number,
                    "total_devices": total_devices,
                    "scanner_type": self.__class__.__name__
                },
                source=f"scanner.{self.__class__.__name__.lower()}",
                correlation_id=device.scan_id
            ))
            
            self.logger.debug(f"Published device discovered event for {device.ip}")
            
        except Exception as e:
            self.logger.warning(f"Failed to publish device discovered event: {e}")
    
    async def _publish_progress(self, progress: float, scan_id: str, message: str = "") -> None:
        """
        Publish scan progress for user feedback.
        
        Args:
            progress: Progress percentage (0.0-100.0)
            scan_id: Scan identifier
            message: Optional progress message
        """
        try:
            from core.events import create_event, R2Events
            
            await self.event_bus.publish(create_event(
                R2Events.SCAN_PROGRESS,
                {
                    "progress": progress,
                    "scan_id": scan_id,
                    "scanner_type": self.__class__.__name__,
                    "message": message
                },
                source=f"scanner.{self.__class__.__name__.lower()}",
                correlation_id=scan_id
            ))
            
        except Exception as e:
            self.logger.warning(f"Failed to publish progress event: {e}")


class DiscoveryScanner(BaseScanner):
    """Base class for network discovery scanners (ping, ARP, mDNS)"""
    
    @abstractmethod
    async def discover_hosts(self, network: str, scan_id: str) -> List[str]:
        """
        Discover active hosts in the network.
        
        Args:
            network: Network range (e.g., "192.168.1.0/24")
            scan_id: Scan identifier
            
        Returns:
            List of discovered IP addresses
        """
        pass


class AnalysisScanner(BaseScanner):
    """Base class for device analysis scanners (port, SNMP, banner)"""
    
    @abstractmethod
    async def analyze_device(self, ip: str, scan_id: str) -> DeviceInfo:
        """
        Analyze a specific device for detailed information.
        
        Args:
            ip: Device IP address
            scan_id: Scan identifier
            
        Returns:
            Enriched device information
        """
        pass
