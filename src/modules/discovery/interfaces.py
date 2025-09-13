"""
Discovery Module Interfaces

This module defines the interfaces for network discovery functionality
including network scanning, protocol detection, and device analysis.
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, Union
from datetime import datetime

from ...core.interfaces import IModule


class INetworkScanner(IModule):
    """Network Scanner interface"""
    
    @abstractmethod
    async def scan_network(self, target: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Scan network for devices.
        
        Args:
            target: Target network (e.g., '192.168.1.0/24'). If None, uses default.
            
        Returns:
            List[Dict[str, Any]]: List of discovered devices
        """
        pass
    
    @abstractmethod
    async def scan_device(self, ip: str) -> Dict[str, Any]:
        """
        Scan specific device for detailed information.
        
        Args:
            ip: Device IP address
            
        Returns:
            Dict[str, Any]: Device information
        """
        pass
    
    @abstractmethod
    async def port_scan(self, host: str, ports: Optional[List[int]] = None) -> Dict[str, Any]:
        """
        Scan ports on a specific host.
        
        Args:
            host: Host IP address
            ports: List of ports to scan. If None, uses common ports.
            
        Returns:
            Dict[str, Any]: Port scan results
        """
        pass
    
    @abstractmethod
    async def ping_sweep(self, network: str) -> List[str]:
        """
        Perform ping sweep to find active hosts.
        
        Args:
            network: Network range (e.g., '192.168.1.0/24')
            
        Returns:
            List[str]: List of active host IPs
        """
        pass
    
    @abstractmethod
    async def get_scan_status(self) -> Dict[str, Any]:
        """
        Get current scan status.
        
        Returns:
            Dict[str, Any]: Current scan status
        """
        pass
    
    @abstractmethod
    async def stop_scan(self) -> bool:
        """
        Stop current scan operation.
        
        Returns:
            bool: True if scan stopped successfully
        """
        pass


class IProtocolDetector(IModule):
    """Protocol Detection interface"""
    
    @abstractmethod
    async def detect_protocols(self, host: str, port: int) -> List[str]:
        """
        Detect protocols running on a specific port.
        
        Args:
            host: Host IP address
            port: Port number
            
        Returns:
            List[str]: Detected protocols
        """
        pass
    
    @abstractmethod
    async def identify_service(self, port: int) -> str:
        """
        Identify service running on a port.
        
        Args:
            port: Port number
            
        Returns:
            str: Service name
        """
        pass
    
    @abstractmethod
    async def detect_iot_protocols(self, host: str) -> Dict[str, Any]:
        """
        Detect IoT-specific protocols.
        
        Args:
            host: Host IP address
            
        Returns:
            Dict[str, Any]: IoT protocol information
        """
        pass


class IDeviceAnalyzer(IModule):
    """Device Analysis interface"""
    
    @abstractmethod
    async def analyze_device(self, device_info: Dict[str, Any]) -> Dict[str, Any]:
        """
        Perform comprehensive device analysis.
        
        Args:
            device_info: Basic device information
            
        Returns:
            Dict[str, Any]: Detailed device analysis
        """
        pass
    
    @abstractmethod
    async def get_device_fingerprint(self, host: str) -> Dict[str, Any]:
        """
        Generate device fingerprint.
        
        Args:
            host: Host IP address
            
        Returns:
            Dict[str, Any]: Device fingerprint
        """
        pass
    
    @abstractmethod
    async def identify_device_type(self, device_info: Dict[str, Any]) -> str:
        """
        Identify device type.
        
        Args:
            device_info: Device information
            
        Returns:
            str: Device type (e.g., 'router', 'computer', 'iot_device')
        """
        pass
    
    @abstractmethod
    async def assess_device_security(self, device_info: Dict[str, Any]) -> Dict[str, Any]:
        """
        Assess device security posture.
        
        Args:
            device_info: Device information
            
        Returns:
            Dict[str, Any]: Security assessment
        """
        pass


class IWirelessScanner(IModule):
    """Wireless Environment Scanner interface"""
    
    @abstractmethod
    async def scan_wifi_networks(self) -> List[Dict[str, Any]]:
        """
        Scan for WiFi networks.
        
        Returns:
            List[Dict[str, Any]]: WiFi network information
        """
        pass
    
    @abstractmethod
    async def scan_bluetooth_devices(self) -> List[Dict[str, Any]]:
        """
        Scan for Bluetooth devices.
        
        Returns:
            List[Dict[str, Any]]: Bluetooth device information
        """
        pass
    
    @abstractmethod
    async def scan_zigbee_networks(self) -> List[Dict[str, Any]]:
        """
        Scan for Zigbee networks.
        
        Returns:
            List[Dict[str, Any]]: Zigbee network information
        """
        pass
    
    @abstractmethod
    async def scan_zwave_networks(self) -> List[Dict[str, Any]]:
        """
        Scan for Z-Wave networks.
        
        Returns:
            List[Dict[str, Any]]: Z-Wave network information
        """
        pass
    
    @abstractmethod
    async def analyze_rf_spectrum(self) -> Dict[str, Any]:
        """
        Analyze RF spectrum usage.
        
        Returns:
            Dict[str, Any]: RF spectrum analysis
        """
        pass


class ISmartHomeScanner(IModule):
    """Smart Home Device Scanner interface"""
    
    @abstractmethod
    async def scan_hue_bridges(self) -> List[Dict[str, Any]]:
        """
        Scan for Philips Hue bridges.
        
        Returns:
            List[Dict[str, Any]]: Hue bridge information
        """
        pass
    
    @abstractmethod
    async def scan_nest_devices(self) -> List[Dict[str, Any]]:
        """
        Scan for Nest/Ecobee thermostats.
        
        Returns:
            List[Dict[str, Any]]: Thermostat information
        """
        pass
    
    @abstractmethod
    async def scan_security_cameras(self) -> List[Dict[str, Any]]:
        """
        Scan for security cameras.
        
        Returns:
            List[Dict[str, Any]]: Camera information
        """
        pass
    
    @abstractmethod
    async def scan_smart_switches(self) -> List[Dict[str, Any]]:
        """
        Scan for smart switches and outlets.
        
        Returns:
            List[Dict[str, Any]]: Smart switch information
        """
        pass
    
    @abstractmethod
    async def scan_environmental_sensors(self) -> List[Dict[str, Any]]:
        """
        Scan for environmental sensors.
        
        Returns:
            List[Dict[str, Any]]: Sensor information
        """
        pass


class INetworkMonitor(IModule):
    """Network Monitoring interface"""
    
    @abstractmethod
    async def monitor_network_health(self, host: str) -> Dict[str, Any]:
        """
        Monitor network performance and health.
        
        Args:
            host: Host to monitor
            
        Returns:
            Dict[str, Any]: Network health metrics
        """
        pass
    
    @abstractmethod
    async def measure_latency(self, host: str) -> Dict[str, float]:
        """
        Measure latency to host.
        
        Args:
            host: Target host
            
        Returns:
            Dict[str, float]: Latency statistics
        """
        pass
    
    @abstractmethod
    async def test_bandwidth(self, host: str) -> Dict[str, float]:
        """
        Test bandwidth to host.
        
        Args:
            host: Target host
            
        Returns:
            Dict[str, float]: Bandwidth test results
        """
        pass
    
    @abstractmethod
    async def measure_packet_loss(self, host: str) -> float:
        """
        Measure packet loss to host.
        
        Args:
            host: Target host
            
        Returns:
            float: Packet loss percentage
        """
        pass