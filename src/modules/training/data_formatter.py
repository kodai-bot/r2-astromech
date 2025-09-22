"""
Network Data Formatter for Training Data Generation

This module converts raw network discovery data into structured formats
suitable for machine learning training datasets.
"""

import json
import hashlib
import re
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime
import logging

from .interfaces import IDataFormatter, TrainingDataConfig
logger = logging.getLogger("training.data_formatter")


class NetworkDataFormatter(IDataFormatter):
    """
    Formats network discovery data into structured training datasets.
    
    This formatter specializes in converting R2's network discovery results
    into clean, consistent training data for various ML tasks.
    """
    
    def __init__(self, config: TrainingDataConfig):
        """
        Initialize the network data formatter.
        
        Args:
            config: Training data configuration
        """
        self.config = config
        self.logger = logger
        
        # Device type classification patterns
        self.device_patterns = {
            'router': [
                r'router', r'gateway', r'linksys', r'netgear', r'dlink', r'asus'
            ],
            'switch': [
                r'switch', r'cisco', r'juniper', r'hp.*switch'
            ],
            'wireless_ap': [
                r'ap\d+', r'access.*point', r'wifi', r'wireless'
            ],
            'printer': [
                r'printer', r'hp.*laserjet', r'canon', r'epson', r'brother'
            ],
            'iot_sensor': [
                r'sensor', r'esp32', r'arduino', r'raspberry.*pi'
            ],
            'smart_home': [
                r'nest', r'alexa', r'echo', r'smart.*plug', r'philips.*hue'
            ],
            'security_camera': [
                r'camera', r'cam\d+', r'hikvision', r'axis', r'foscam'
            ],
            'nas': [
                r'nas', r'synology', r'qnap', r'storage'
            ],
            'computer': [
                r'pc\d+', r'desktop', r'laptop', r'workstation'
            ],
            'mobile_device': [
                r'android', r'iphone', r'ipad', r'phone', r'tablet'
            ]
        }
        
        # Network service patterns
        self.service_patterns = {
            'web_server': [80, 443, 8080, 8443],
            'ssh_server': [22],
            'telnet': [23],
            'ftp': [21],
            'smtp': [25, 587],
            'dns': [53],
            'dhcp': [67, 68],
            'snmp': [161, 162],
            'rdp': [3389],
            'vnc': [5900, 5901, 5902],
            'database': [3306, 5432, 1521, 1433],
            'iot_protocols': [1883, 8883, 5683]  # MQTT, CoAP
        }
        
        logger.info("Network data formatter initialized")
    
    def format_device_data(self, device_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Format individual device discovery data for training.
        
        Args:
            device_data: Raw device discovery data
            
        Returns:
            Dict containing formatted device training data
        """
        try:
            # Extract base device information
            device_id = device_data.get('ip', 'unknown')
            timestamp = device_data.get('timestamp', datetime.now().isoformat())
            
            # Anonymize IP if requested
            if self.config.anonymize_data:
                device_id = self._anonymize_ip(device_id)
            
            # Classify device type
            device_type, confidence = self._classify_device(device_data)
            
            # Extract and format features
            features = self._extract_device_features(device_data)
            
            # Format the training record
            training_record = {
                "record_type": "device_classification",
                "device_id": device_id,
                "features": features,
                "device_type": device_type,
                "confidence": confidence,
                "metadata": {
                    "format_version": self.config.format_version,
                    "created_at": datetime.now().isoformat(),
                    "source_timestamp": timestamp,
                    "anonymized": self.config.anonymize_data
                }
            }
            
            # Add temporal data if enabled
            if self.config.include_temporal_data:
                training_record["temporal_features"] = self._extract_temporal_features(device_data)
            
            # Add location data if available and enabled
            if self.config.include_geolocation:
                location_data = self._extract_location_data(device_data)
                if location_data:
                    training_record["location_features"] = location_data
            
            return training_record
            
        except Exception as e:
            logger.error(f"Failed to format device data: {e}")
            return {}
    
    def format_network_data(self, network_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Format network-level discovery data for training.
        
        Args:
            network_data: Raw network discovery data
            
        Returns:
            Dict containing formatted network training data
        """
        try:
            # Extract network identifier
            network_id = network_data.get('network_code', 'unknown')
            network_range = network_data.get('network_range', 'unknown')
            
            # Anonymize network range if requested  
            if self.config.anonymize_data:
                network_range = self._anonymize_network_range(network_range)
            
            # Extract network topology features
            topology_features = self._extract_topology_features(network_data)
            
            # Analyze device relationships
            device_relationships = self._analyze_device_relationships(network_data)
            
            # Format the training record
            training_record = {
                "record_type": "network_topology_analysis",
                "network_id": network_id,
                "network_range": network_range,
                "topology_features": topology_features,
                "device_relationships": device_relationships,
                "device_count": network_data.get('device_count', 0),
                "metadata": {
                    "format_version": self.config.format_version,
                    "created_at": datetime.now().isoformat(),
                    "scan_timestamp": network_data.get('scan_timestamp', ''),
                    "anonymized": self.config.anonymize_data
                }
            }
            
            # Add security assessment if available
            security_features = self._extract_security_features(network_data)
            if security_features:
                training_record["security_features"] = security_features
            
            return training_record
            
        except Exception as e:
            logger.error(f"Failed to format network data: {e}")
            return {}
    
    def validate_output(self, data: Dict[str, Any]) -> bool:
        """
        Validate that the formatted data meets training requirements.
        
        Args:
            data: Formatted training data
            
        Returns:
            bool: True if data is valid for training
        """
        try:
            record_type = data.get('record_type')
            if not record_type:
                return False
            
            # Check required fields based on record type
            required_fields = self.config.required_fields.get(record_type, [])
            
            for field in required_fields:
                if field not in data:
                    logger.warning(f"Missing required field '{field}' for record type '{record_type}'")
                    return False
            
            # Validate metadata
            metadata = data.get('metadata', {})
            if not metadata.get('format_version'):
                return False
            
            # Validate features are not empty
            if record_type == "device_classification":
                features = data.get('features', {})
                if not features or len(features) == 0:
                    return False
            
            return True
            
        except Exception as e:
            logger.error(f"Validation failed: {e}")
            return False
    
    def _classify_device(self, device_data: Dict[str, Any]) -> Tuple[str, float]:
        """
        Classify device type based on discovery data.
        
        Args:
            device_data: Device discovery data
            
        Returns:
            Tuple of (device_type, confidence_score)
        """
        hostname = device_data.get('hostname', '').lower()
        manufacturer = device_data.get('manufacturer', '').lower()
        open_ports = device_data.get('open_ports', [])
        
        # Score each device type
        scores = {}
        
        for device_type, patterns in self.device_patterns.items():
            score = 0.0
            
            # Check hostname patterns
            for pattern in patterns:
                if re.search(pattern, hostname, re.IGNORECASE):
                    score += 0.4
                if re.search(pattern, manufacturer, re.IGNORECASE):
                    score += 0.3
            
            # Check service patterns
            for service_type, ports in self.service_patterns.items():
                if any(port in open_ports for port in ports):
                    if service_type in ['web_server', 'ssh_server'] and device_type in ['router', 'switch']:
                        score += 0.2
                    elif service_type == 'iot_protocols' and device_type == 'iot_sensor':
                        score += 0.5
            
            scores[device_type] = min(score, 1.0)  # Cap at 1.0
        
        # Find the highest scoring device type
        if scores:
            best_type = max(scores, key=scores.get)
            confidence = scores[best_type]
            
            if confidence < 0.3:
                return "unknown", confidence
            
            return best_type, confidence
        
        return "unknown", 0.0
    
    def _extract_device_features(self, device_data: Dict[str, Any]) -> Dict[str, Any]:
        """Extract meaningful features from device data."""
        features = {}
        
        # Basic network features
        features['has_hostname'] = bool(device_data.get('hostname') and device_data['hostname'] != 'unknown')
        features['has_mac_address'] = bool(device_data.get('mac') and device_data['mac'] != 'unknown')
        features['has_manufacturer'] = bool(device_data.get('manufacturer') and device_data['manufacturer'] != 'Unknown Manufacturer')
        
        # Port analysis features
        open_ports = device_data.get('open_ports', [])
        features['port_count'] = len(open_ports)
        features['has_web_ports'] = any(port in [80, 443, 8080, 8443] for port in open_ports)
        features['has_ssh'] = 22 in open_ports
        features['has_telnet'] = 23 in open_ports
        features['has_ftp'] = 21 in open_ports
        features['has_iot_ports'] = any(port in [1883, 8883, 5683] for port in open_ports)
        
        # Response characteristics
        features['responds_to_ping'] = device_data.get('discovery_method') == 'ping'
        features['analysis_complete'] = device_data.get('analysis_complete', False)
        
        # Discovery history
        features['discovery_count'] = device_data.get('discovery_count', 1)
        features['is_persistent'] = features['discovery_count'] > 1
        
        return features
    
    def _extract_temporal_features(self, device_data: Dict[str, Any]) -> Dict[str, Any]:
        """Extract temporal features from device data."""
        temporal_features = {}
        
        # Basic timestamps
        first_seen = device_data.get('first_seen')
        last_seen = device_data.get('last_seen')
        
        if first_seen:
            temporal_features['first_seen'] = first_seen
        
        if last_seen:
            temporal_features['last_seen'] = last_seen
        
        # Calculate time differences
        if first_seen and last_seen:
            try:
                first_dt = datetime.fromisoformat(first_seen.replace('Z', '+00:00'))
                last_dt = datetime.fromisoformat(last_seen.replace('Z', '+00:00'))
                duration = (last_dt - first_dt).total_seconds()
                temporal_features['observation_duration_seconds'] = duration
            except Exception:
                pass
        
        # Status history analysis
        status_history = device_data.get('status_history', [])
        if status_history:
            temporal_features['status_changes'] = len(status_history)
            temporal_features['always_active'] = all(
                entry.get('status') == 'active' for entry in status_history
            )
        
        return temporal_features
    
    def _extract_location_data(self, device_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Extract or infer location data for GeoJSON support."""
        # For now, we'll use network-based location inference
        # In a real deployment, this could integrate with actual geolocation services
        
        ip = device_data.get('ip', '')
        if not ip or ip == 'unknown':
            return None
        
        # Create a synthetic location based on network subnet for demo purposes
        # In production, this would use actual geolocation APIs
        location_data = {
            "type": "inferred",
            "source": "network_subnet",
            "accuracy": "low",
            "coordinates": self._infer_location_from_ip(ip)
        }
        
        return location_data
    
    def _infer_location_from_ip(self, ip: str) -> List[float]:
        """Infer approximate location from IP address (synthetic for demo)."""
        # This is a synthetic location generator for demonstration
        # In production, use actual geolocation services
        
        # Create consistent but synthetic coordinates based on IP hash
        ip_hash = hashlib.md5(ip.encode()).hexdigest()
        lat_offset = int(ip_hash[:2], 16) / 255.0 * 2 - 1  # -1 to 1
        lon_offset = int(ip_hash[2:4], 16) / 255.0 * 2 - 1  # -1 to 1
        
        # Base location (center of a typical region)
        base_lat = 40.7128  # NYC as example
        base_lon = -74.0060
        
        # Add small offset for demo
        lat = base_lat + lat_offset * 0.1
        lon = base_lon + lon_offset * 0.1
        
        return [lon, lat]  # GeoJSON format: [longitude, latitude]
    
    def _extract_topology_features(self, network_data: Dict[str, Any]) -> Dict[str, Any]:
        """Extract network topology features."""
        topology_features = {}
        
        device_signatures = network_data.get('device_signatures', [])
        
        # Basic topology metrics
        topology_features['total_devices'] = len(device_signatures)
        topology_features['has_gateway'] = bool(network_data.get('gateway_ip'))
        
        # Device type distribution
        device_types = {}
        manufacturers = {}
        
        for device in device_signatures:
            device_type = device.get('device_type', 'unknown')
            manufacturer = device.get('manufacturer', 'unknown')
            
            device_types[device_type] = device_types.get(device_type, 0) + 1
            manufacturers[manufacturer] = manufacturers.get(manufacturer, 0) + 1
        
        topology_features['device_type_distribution'] = device_types
        topology_features['manufacturer_distribution'] = manufacturers
        topology_features['device_diversity'] = len(device_types)
        topology_features['manufacturer_diversity'] = len(manufacturers)
        
        return topology_features
    
    def _analyze_device_relationships(self, network_data: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze relationships between devices in the network."""
        relationships = {}
        
        device_signatures = network_data.get('device_signatures', [])
        gateway_ip = network_data.get('gateway_ip')
        
        # Identify gateway relationships
        if gateway_ip:
            gateway_device = next(
                (device for device in device_signatures if device.get('ip') == gateway_ip),
                None
            )
            
            if gateway_device:
                relationships['gateway'] = {
                    'ip': gateway_ip,
                    'hostname': gateway_device.get('hostname', 'unknown'),
                    'connected_devices': len(device_signatures) - 1
                }
        
        # Analyze subnet relationships
        ip_segments = {}
        for device in device_signatures:
            ip = device.get('ip', '')
            if ip and '.' in ip:
                # Group by /24 subnet
                subnet = '.'.join(ip.split('.')[:3]) + '.0/24'
                if subnet not in ip_segments:
                    ip_segments[subnet] = []
                ip_segments[subnet].append(device)
        
        relationships['subnet_groups'] = {
            subnet: len(devices) for subnet, devices in ip_segments.items()
        }
        
        return relationships
    
    def _extract_security_features(self, network_data: Dict[str, Any]) -> Dict[str, Any]:
        """Extract security-related features from network data."""
        security_features = {}
        
        device_signatures = network_data.get('device_signatures', [])
        
        # Count devices with unknown attributes (potential security concerns)
        unknown_devices = sum(
            1 for device in device_signatures 
            if device.get('device_type') == 'unknown'
        )
        
        unknown_manufacturers = sum(
            1 for device in device_signatures
            if device.get('manufacturer') in ['Unknown Manufacturer', 'unknown']
        )
        
        security_features['unknown_device_count'] = unknown_devices
        security_features['unknown_manufacturer_count'] = unknown_manufacturers
        security_features['identification_rate'] = (
            len(device_signatures) - unknown_devices
        ) / len(device_signatures) if device_signatures else 0.0
        
        # Check for potential security services
        security_services = 0
        for device in device_signatures:
            open_ports = device.get('open_ports', [])
            # Count devices with SSH (potential management interfaces)
            if 22 in open_ports:
                security_services += 1
        
        security_features['devices_with_management_ports'] = security_services
        
        return security_features
    
    def _anonymize_ip(self, ip: str) -> str:
        """Anonymize IP address while preserving structure."""
        if not ip or ip == 'unknown':
            return 'unknown'
        
        # Create a consistent hash for the IP
        ip_hash = hashlib.sha256(ip.encode()).hexdigest()[:8]
        return f"device_{ip_hash}"
    
    def _anonymize_network_range(self, network_range: str) -> str:
        """Anonymize network range while preserving CIDR structure."""
        if not network_range or network_range == 'unknown':
            return 'unknown'
        
        # Extract CIDR notation
        if '/' in network_range:
            _, cidr = network_range.split('/')
            range_hash = hashlib.sha256(network_range.encode()).hexdigest()[:8]
            return f"network_{range_hash}/{cidr}"
        else:
            range_hash = hashlib.sha256(network_range.encode()).hexdigest()[:8]
            return f"network_{range_hash}"
