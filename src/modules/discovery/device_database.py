"""
Device Database for R2 Astromech

This module provides a simple database to store and manage discovered devices,
allowing R2 to build and maintain a picture of its environment.
"""

import json
import os
from typing import Dict, List, Any, Optional
from datetime import datetime
import logging

from ...utils.logging import get_module_logger

logger = get_module_logger("discovery.device_database")


class DeviceDatabase:
    """
    Simple device database to store and manage discovered devices.
    
    This database helps R2 build and maintain a comprehensive picture
    of its network environment, tracking devices over time.
    """
    
    def __init__(self, database_path: str = "data/devices/device_database.json"):
        """
        Initialize the device database.
        
        Args:
            database_path: Path to the database file
        """
        self.database_path = database_path
        self.network_fingerprint_path = database_path.replace('.json', '_networks.json')
        self.devices: Dict[str, Dict[str, Any]] = {}
        self.network_fingerprints: Dict[str, Dict[str, Any]] = {}
        self._ensure_database_directory()
        self._load_database()
        self._load_network_fingerprints()
        
        logger.info(f"Device database initialized with {len(self.devices)} known devices and {len(self.network_fingerprints)} network fingerprints")
    
    def _ensure_database_directory(self) -> None:
        """Ensure the database directory exists"""
        os.makedirs(os.path.dirname(self.database_path), exist_ok=True)
    
    def _load_database(self) -> None:
        """Load existing database from disk"""
        try:
            if os.path.exists(self.database_path):
                with open(self.database_path, 'r') as f:
                    self.devices = json.load(f)
                logger.info(f"Loaded {len(self.devices)} devices from database")
            else:
                logger.info("No existing database found, starting fresh")
        except Exception as e:
            logger.error(f"Failed to load database: {e}")
            self.devices = {}
    
    def _load_network_fingerprints(self) -> None:
        """Load existing network fingerprints from disk"""
        try:
            if os.path.exists(self.network_fingerprint_path):
                with open(self.network_fingerprint_path, 'r') as f:
                    self.network_fingerprints = json.load(f)
                logger.info(f"Loaded {len(self.network_fingerprints)} network fingerprints")
            else:
                logger.info("No existing network fingerprints found, starting fresh")
        except Exception as e:
            logger.error(f"Failed to load network fingerprints: {e}")
            self.network_fingerprints = {}
    
    def _save_database(self) -> None:
        """Save database to disk"""
        try:
            with open(self.database_path, 'w') as f:
                json.dump(self.devices, f, indent=2, default=str)
            logger.debug(f"Database saved with {len(self.devices)} devices")
        except Exception as e:
            logger.error(f"Failed to save database: {e}")
    
    def _save_network_fingerprints(self) -> None:
        """Save network fingerprints to disk"""
        try:
            with open(self.network_fingerprint_path, 'w') as f:
                json.dump(self.network_fingerprints, f, indent=2, default=str)
            logger.debug(f"Network fingerprints saved with {len(self.network_fingerprints)} entries")
        except Exception as e:
            logger.error(f"Failed to save network fingerprints: {e}")
    
    def add_network_fingerprint(self, fingerprint_data: Dict[str, Any]) -> bool:
        """
        Add or update a network fingerprint.
        
        Args:
            fingerprint_data: Network fingerprint information
            
        Returns:
            bool: True if successful
        """
        try:
            network_code = fingerprint_data.get('network_code')
            if not network_code:
                logger.error("Network fingerprint missing network_code")
                return False
            
            # Check if this is a new network
            is_new_network = network_code not in self.network_fingerprints
            
            if is_new_network:
                logger.info(f"🆕 New network fingerprint: {network_code}")
            else:
                logger.info(f"🔄 Updated network fingerprint: {network_code}")
            
            # Store the fingerprint
            self.network_fingerprints[network_code] = fingerprint_data
            
            self._save_network_fingerprints()
            return True
            
        except Exception as e:
            logger.error(f"Failed to add network fingerprint: {e}")
            return False
    
    def add_or_update_device(self, device_info: Dict[str, Any]) -> bool:
        """
        Add a new device or update existing device information.
        
        Args:
            device_info: Device information dictionary
            
        Returns:
            bool: True if successful
        """
        try:
            ip = device_info.get('ip')
            if not ip:
                logger.error("Device info missing IP address")
                return False
            
            # Check if this is a new device or update
            is_new_device = ip not in self.devices
            
            if is_new_device:
                # New device
                self.devices[ip] = {
                    'first_seen': datetime.now().isoformat(),
                    'discovery_count': 1,
                    'status_history': []
                }
                logger.info(f"🆕 New device discovered: {ip}")
            else:
                # Update existing device
                self.devices[ip]['discovery_count'] += 1
                logger.info(f"🔄 Device updated: {ip}")
            
            # Update device information
            self.devices[ip].update(device_info)
            self.devices[ip]['last_seen'] = datetime.now().isoformat()
            
            # Add status history entry
            status_entry = {
                'timestamp': datetime.now().isoformat(),
                'status': device_info.get('status', 'unknown'),
                'open_ports': device_info.get('open_ports', []),
                'analysis_complete': device_info.get('analysis_complete', False)
            }
            
            if 'status_history' not in self.devices[ip]:
                self.devices[ip]['status_history'] = []
            self.devices[ip]['status_history'].append(status_entry)
            
            # Keep only last 10 status entries
            self.devices[ip]['status_history'] = self.devices[ip]['status_history'][-10:]
            
            self._save_database()
            return True
            
        except Exception as e:
            logger.error(f"Failed to add/update device: {e}")
            return False
    
    def get_device(self, ip: str) -> Optional[Dict[str, Any]]:
        """
        Get device information by IP address.
        
        Args:
            ip: Device IP address
            
        Returns:
            Dict[str, Any]: Device information or None if not found
        """
        return self.devices.get(ip)
    
    def get_all_devices(self) -> Dict[str, Dict[str, Any]]:
        """
        Get all devices in the database.
        
        Returns:
            Dict[str, Dict[str, Any]]: All device information
        """
        return self.devices.copy()
    
    def get_devices_by_type(self, device_type: str) -> List[Dict[str, Any]]:
        """
        Get all devices of a specific type.
        
        Args:
            device_type: Type of device to search for
            
        Returns:
            List[Dict[str, Any]]: List of devices of the specified type
        """
        matching_devices = []
        for ip, device in self.devices.items():
            if device.get('device_type') == device_type:
                matching_devices.append(device)
        return matching_devices
    
    def get_devices_by_manufacturer(self, manufacturer: str) -> List[Dict[str, Any]]:
        """
        Get all devices from a specific manufacturer.
        
        Args:
            manufacturer: Manufacturer name
            
        Returns:
            List[Dict[str, Any]]: List of devices from the manufacturer
        """
        matching_devices = []
        for ip, device in self.devices.items():
            if device.get('manufacturer', '').lower() == manufacturer.lower():
                matching_devices.append(device)
        return matching_devices
    
    def get_recently_seen_devices(self, hours: int = 24) -> List[Dict[str, Any]]:
        """
        Get devices seen within the last N hours.
        
        Args:
            hours: Number of hours to look back
            
        Returns:
            List[Dict[str, Any]]: List of recently seen devices
        """
        from datetime import timedelta
        
        cutoff_time = datetime.now() - timedelta(hours=hours)
        recent_devices = []
        
        for ip, device in self.devices.items():
            if 'last_seen' in device:
                try:
                    last_seen = datetime.fromisoformat(device['last_seen'].replace('Z', '+00:00'))
                    if last_seen > cutoff_time:
                        recent_devices.append(device)
                except ValueError:
                    continue
        
        return recent_devices
    
    def mark_device_offline(self, ip: str) -> bool:
        """
        Mark a device as offline.
        
        Args:
            ip: Device IP address
            
        Returns:
            bool: True if successful
        """
        if ip in self.devices:
            self.devices[ip]['status'] = 'offline'
            self.devices[ip]['last_offline'] = datetime.now().isoformat()
            self._save_database()
            return True
        return False
    
    def get_network_summary(self) -> Dict[str, Any]:
        """
        Get a summary of the network environment.
        
        Returns:
            Dict[str, Any]: Network summary statistics
        """
        summary = {
            'total_devices': len(self.devices),
            'device_types': {},
            'manufacturers': {},
            'active_devices': 0,
            'offline_devices': 0,
            'unknown_devices': 0
        }
        
        # Count device types and manufacturers
        for device in self.devices.values():
            # Device types
            device_type = device.get('device_type', 'unknown')
            summary['device_types'][device_type] = summary['device_types'].get(device_type, 0) + 1
            
            # Manufacturers
            manufacturer = device.get('manufacturer', 'unknown')
            summary['manufacturers'][manufacturer] = summary['manufacturers'].get(manufacturer, 0) + 1
            
            # Status counts
            status = device.get('status', 'unknown')
            if status == 'active':
                summary['active_devices'] += 1
            elif status == 'offline':
                summary['offline_devices'] += 1
            else:
                summary['unknown_devices'] += 1
        
        return summary
    
    def print_network_summary(self) -> None:
        """Print a formatted network summary to console"""
        summary = self.get_network_summary()
        
        print("\n🌐 R2-D2 Network Environment Summary")
        print("=" * 50)
        print(f"📊 Total Devices: {summary['total_devices']}")
        print(f"✅ Active: {summary['active_devices']}")
        print(f"❌ Offline: {summary['offline_devices']}")
        print(f"❓ Unknown: {summary['unknown_devices']}")
        
        if summary['device_types']:
            print(f"\n🤖 Device Types:")
            for device_type, count in summary['device_types'].items():
                print(f"   {device_type}: {count}")
        
        if summary['manufacturers']:
            print(f"\n🏭 Manufacturers:")
            for manufacturer, count in summary['manufacturers'].items():
                print(f"   {manufacturer}: {count}")
        
        print("=" * 50)
    
    def export_devices(self, export_path: str) -> bool:
        """
        Export device database to a file.
        
        Args:
            export_path: Path to export file
            
        Returns:
            bool: True if successful
        """
        try:
            with open(export_path, 'w') as f:
                json.dump(self.devices, f, indent=2, default=str)
            logger.info(f"Database exported to {export_path}")
            return True
        except Exception as e:
            logger.error(f"Failed to export database: {e}")
            return False
