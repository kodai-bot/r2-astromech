"""
R2 Astromech Project - Network Scanner Module
Running on: NVIDIA Jetson Nano 4GB
Purpose: Network device discovery and enumeration
Author: Dylan G Foley
Created: September 2025

This module handles the discovery of network devices using various
scanning techniques, mimicking R2-D2's ability to interface with
unknown systems and map their capabilities.
"""

import subprocess
import json
import socket
import ipaddress
from typing import List, Dict, Optional
import logging
from datetime import datetime
from subprocess import PIPE, TimeoutExpired, CalledProcessError

# R2 Audio Integration - Simple Sound System
try:
    from personality.r2_simple_sounds import play_scanner_event, init_simple_r2_audio
    AUDIO_AVAILABLE = True
    
except ImportError as e:
    # Fallback if audio module not available
    AUDIO_AVAILABLE = False
    def play_scanner_event(event, volume=0.7):
        pass

# Set up logging first
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize R2 simple audio after logger is set up
if AUDIO_AVAILABLE:
    try:
        init_simple_r2_audio()  # Initialize simple sound system
        logger.info("🔊 R2 simple audio initialized")
    except Exception as e:
        logger.warning(f"⚠️  R2 audio initialization failed: {e}")

class NetworkScanner:
    """
    R2-style network device discovery system.
    Scans for devices and attempts to identify their types and capabilities.
    """
    
    def __init__(self, target_network: str = None):
        """
        Initialize the network scanner.
        
        Args:
            target_network: Network to scan (e.g., '192.168.1.0/24')
                          If None, will auto-detect local network
        """
        self.target_network = target_network or self._detect_local_network()
        self.discovered_devices = []
        logger.info(f"🤖 R2 Network Scanner initialized for {self.target_network}")
        
        # R2 says hello when initialized
        if AUDIO_AVAILABLE:
            play_scanner_event('startup')
    
    def _detect_local_network(self) -> str:
        """
        Auto-detect the local network range.
        R2 would automatically assess his surroundings!
        """
        # TODO: Implement network auto-detection
        return "192.168.1.0/24"  # Default for now
        

    def scan_network(self) -> List[Dict]:
            """
            Main scanning function - discovers all devices on network.
            Returns list of discovered device dictionaries.
            """
            logger.info("🔍 R2 beginning network sweep...")
            play_scanner_event('scan_start')
            
            # First, find active hosts with ping sweep
            active_hosts = self.ping_sweep()
            
            discovered_devices = []
            for host in active_hosts:
                device_info = {
                    'ip': host,
                    'status': 'active',
                    'discovery_method': 'ping',
                    'timestamp': str(datetime.now())
                }
                discovered_devices.append(device_info)
            
            self.discovered_devices = discovered_devices
            logger.info(f"🤖 R2 network scan complete: {len(discovered_devices)} devices discovered")
            play_scanner_event('scan_complete')
            return discovered_devices
            
    
    def ping_sweep(self) -> List[str]:
                """
                Basic ping sweep to find active hosts.
                R2 probes the network to find responsive droids and systems.
                """
                active_hosts = []
                
                try:
                    # Parse the network range
                    network = ipaddress.IPv4Network(self.target_network, strict=False)
                    total_hosts = list(network.hosts())
                    logger.info(f"🔍 R2 ping sweep scanning {network} ({len(total_hosts)} addresses)")
                    
                    # Progress tracking
                    for i, host in enumerate(total_hosts):
                        # Show progress every 10 hosts
                        if i % 10 == 0:
                            print(f"🤖 R2 scanning progress: {i}/{len(total_hosts)} hosts checked...")
                        
                        if self._ping_host(str(host)):
                            active_hosts.append(str(host))
                            print(f"📡 R2 found active host: {host}")  # Show immediately when found
                            play_scanner_event('device_found')
                    
                    logger.info(f"✅ R2 ping sweep complete: {len(active_hosts)} active hosts found")
                    return active_hosts
                    
                except KeyboardInterrupt:
                    print(f"\n⚠️  R2 scan interrupted by user. Found {len(active_hosts)} hosts so far.")
                    # Note: 'scan_interrupted' not in simple vocabulary yet - could add as 'i' or 'i n'
                    return active_hosts
                except Exception as e:
                    logger.error(f"❌ R2 ping sweep failed: {e}")
                    play_scanner_event('scan_error')
                    return []
    
    def _ping_host(self, host: str, timeout: int = 1) -> bool:  # Reduced timeout to 1 second
                """
                Ping a single host to check if it's alive.
                Returns True if host responds, False otherwise.
                """
                try:
                    # Faster ping with shorter timeout
                    result = subprocess.run(
                        ['ping', '-c', '1', '-W', str(timeout), host],
                        stdout=subprocess.PIPE,
                        stderr=subprocess.PIPE,
                        universal_newlines=True,
                        timeout=timeout + 0.5  # Slightly longer than ping timeout
                    )
                    
                    return result.returncode == 0
                    
                except (subprocess.TimeoutExpired, subprocess.CalledProcessError):
                    return False
                except Exception as e:
                    return False
            
    
    def port_scan(self, host: str, ports: List[int] = None) -> Dict:
        """
        Scan common ports on a specific host.
        R2 probes for open communication channels.
        """
        if ports is None:
            # Common ports R2 should check
            ports = [22, 23, 53, 80, 135, 139, 443, 445, 993, 995, 1723, 3389, 5900, 8080]
        
        open_ports = []
        services = {}
    
        print(f"🔍 R2 scanning ports on {host}...")
        play_scanner_event('port_scan_start')
    
        for port in ports:
            if self._check_port(host, port):
                open_ports.append(port)
                service = self._identify_service(port)
                services[port] = service
                print(f"📡 R2 found open port: {host}:{port} ({service})")
                play_scanner_event('port_found')
    
        return {
            'host': host,
            'open_ports': open_ports,
            'services': services,
            'scan_time': str(datetime.now())
        }

    def _check_port(self, host: str, port: int, timeout: int = 3) -> bool:
        """
        Check if a specific port is open on a host.
        """
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(timeout)
            result = sock.connect_ex((host, port))
            sock.close()
            return result == 0
        except Exception:
            return False


    def _identify_service(self, port: int) -> str:
        """
        Identify likely service running on port.
        R2's knowledge of common galactic protocols!
        """
        common_services = {
            22: "SSH", 23: "Telnet", 53: "DNS", 80: "HTTP", 
            135: "RPC", 139: "NetBIOS", 443: "HTTPS", 445: "SMB",
            993: "IMAPS", 995: "POP3S", 1723: "PPTP", 3389: "RDP", 
            5900: "VNC", 8080: "HTTP-Alt", 1883: "MQTT", 8883: "MQTT-SSL",
            5683: "CoAP", 502: "Modbus", 47808: "BACnet", 3671: "KNX"
        }
        return common_services.get(port, f"Unknown-{port}")

    # =================================================================
    # ENHANCED DEVICE DETECTION & FINGERPRINTING
    # =================================================================
    
    def get_device_info(self, host: str) -> Dict:
        """
        Comprehensive device information gathering.
        R2 analyzes the device like a medical droid!
        """
        logger.info(f"🔍 R2 analyzing device: {host}")
        
        device_info = {
            'ip': host,
            'mac_address': self._get_mac_address(host),
            'vendor': self._get_vendor_info(host),
            'hostname': self._get_hostname(host),
            'os_fingerprint': self._fingerprint_os(host),
            'mdns_services': self._discover_mdns_services(host),
            'upnp_info': self._discover_upnp_devices(host)
        }
        1
        return device_info
    
    def _get_mac_address(self, host: str) -> Optional[str]:
        """Get MAC address via ARP table lookup."""
        # TODO: Implement ARP table parsing
        logger.debug(f"🔍 R2 looking up MAC for {host}")
        return None
    
    def _get_vendor_info(self, host: str) -> Optional[str]:
        """Identify device vendor from MAC address."""
        # TODO: Implement MAC vendor lookup using OUI database
        logger.debug(f"🔍 R2 identifying vendor for {host}")
        return None
    
    def _get_hostname(self, host: str) -> Optional[str]:
        """Resolve hostname via reverse DNS."""
        # TODO: Implement reverse DNS lookup
        logger.debug(f"🔍 R2 resolving hostname for {host}")
        return None
    
    def _fingerprint_os(self, host: str) -> Optional[str]:
        """Basic OS fingerprinting via TCP/IP stack analysis."""
        # TODO: Implement OS fingerprinting
        logger.debug(f"🔍 R2 fingerprinting OS for {host}")
        return None
    
    def _discover_mdns_services(self, host: str) -> List[Dict]:
        """Discover mDNS/Bonjour services."""
        # TODO: Implement mDNS service discovery
        logger.debug(f"🔍 R2 scanning mDNS services for {host}")
        return []
    
    def _discover_upnp_devices(self, host: str) -> List[Dict]:
        """Discover UPnP devices and services."""
        # TODO: Implement UPnP discovery
        logger.debug(f"🔍 R2 scanning UPnP devices for {host}")
        return []

    # =================================================================
    # IOT PROTOCOL DISCOVERY
    # =================================================================
    
    def scan_iot_protocols(self, host: str) -> Dict:
        """
        Scan for IoT-specific protocols and services.
        R2 speaks droid!
        """
        logger.info(f"🤖 R2 scanning IoT protocols on {host}")
        
        iot_info = {
        
            'mqtt': self._scan_mqtt(host),
            'coap': self._scan_coap(host),
            'modbus': self._scan_modbus(host),
            'bacnet': self._scan_bacnet(host),
            'knx': self._scan_knx(host),
            'zigbee': self._scan_zigbee(host),
            'zwave': self._scan_zwave(host)
        }
        
        return iot_info
    
    def _scan_mqtt(self, host: str) -> Dict:
        """Scan for MQTT brokers."""
        # TODO: Implement MQTT broker discovery and topic enumeration
        logger.debug(f"🔍 R2 scanning MQTT on {host}")
        return {'broker_available': False, 'topics': []}
    
    def _scan_coap(self, host: str) -> Dict:
        """Scan for CoAP endpoints."""
        # TODO: Implement CoAP resource discovery
        logger.debug(f"🔍 R2 scanning CoAP on {host}")
        return {'coap_available': False, 'resources': []}
    
    def _scan_modbus(self, host: str) -> Dict:
        """Scan for Modbus TCP devices."""
        # TODO: Implement Modbus device enumeration
        logger.debug(f"🔍 R2 scanning Modbus on {host}")
        return {'modbus_available': False, 'unit_ids': []}
    
    def _scan_bacnet(self, host: str) -> Dict:
        """Scan for BACnet devices."""
        # TODO: Implement BACnet device discovery
        logger.debug(f"🔍 R2 scanning BACnet on {host}")
        return {'bacnet_available': False, 'device_id': None}
    
    def _scan_knx(self, host: str) -> Dict:
        """Scan for KNX/EIB devices."""
        # TODO: Implement KNX device discovery
        logger.debug(f"🔍 R2 scanning KNX on {host}")
        return {'knx_available': False, 'group_addresses': []}
    
    def _scan_zigbee(self, host: str) -> Dict:
        """Scan for Zigbee coordinators."""
        # TODO: Implement Zigbee network discovery
        logger.debug(f"🔍 R2 scanning Zigbee on {host}")
        return {'coordinator_available': False, 'network_devices': []}
    
    def _scan_zwave(self, host: str) -> Dict:
        """Scan for Z-Wave controllers."""
        # TODO: Implement Z-Wave network discovery
        logger.debug(f"🔍 R2 scanning Z-Wave on {host}")
        return {'controller_available': False, 'node_count': 0}

    # =================================================================
    # WIRELESS ENVIRONMENT ASSESSMENT
    # =================================================================
    
    def scan_wireless_environment(self) -> Dict:
        """
        Comprehensive wireless environment scan.
        R2's electromagnetic awareness!
        """
        logger.info("📡 R2 scanning wireless environment...")
        
        wireless_info = {
            'wifi_networks': self._scan_wifi_networks(),
            'bluetooth_devices': self._scan_bluetooth_devices(),
            'rf_spectrum': self._analyze_rf_spectrum(),
            'zigbee_networks': self._scan_zigbee_networks(),
            'zwave_networks': self._scan_zwave_networks()
        }
        
        return wireless_info
    
    def _scan_wifi_networks(self) -> List[Dict]:
        """Scan for WiFi networks."""
        # TODO: Implement WiFi network enumeration
        logger.debug("🔍 R2 scanning WiFi networks")
        return []
    
    def _scan_bluetooth_devices(self) -> List[Dict]:
        """Scan for Bluetooth devices."""
        # TODO: Implement Bluetooth device discovery
        logger.debug("🔍 R2 scanning Bluetooth devices")
        return []
    
    def _analyze_rf_spectrum(self) -> Dict:
        """Analyze RF spectrum usage."""
        # TODO: Implement RF spectrum analysis
        logger.debug("🔍 R2 analyzing RF spectrum")
        return {'bands_detected': []}
    
    def _scan_zigbee_networks(self) -> List[Dict]:
        """Scan for Zigbee networks."""
        # TODO: Implement Zigbee network scanning
        logger.debug("🔍 R2 scanning Zigbee networks")
        return []
    
    def _scan_zwave_networks(self) -> List[Dict]:
        """Scan for Z-Wave networks."""
        # TODO: Implement Z-Wave network scanning
        logger.debug("🔍 R2 scanning Z-Wave networks")
        return []

    # =================================================================
    # NETWORK HEALTH & PERFORMANCE MONITORING
    # =================================================================
    
    def monitor_network_health(self, host: str) -> Dict:
        """
        Monitor network performance and health metrics.
        R2's diagnostic protocols!
        """
        logger.info(f"🩺 R2 monitoring network health for {host}")
        
        health_info = {
            'latency_stats': self._measure_latency(host),
            'bandwidth_test': self._test_bandwidth(host),
            'packet_loss': self._measure_packet_loss(host),
            'dns_performance': self._test_dns_performance(host),
            'gateway_health': self._check_gateway_health(),
            'dhcp_status': self._check_dhcp_status()
        }
        
        return health_info
    
    def _measure_latency(self, host: str) -> Dict:
        """Measure ping latency statistics."""
        # TODO: Implement comprehensive latency measurement
        logger.debug(f"🔍 R2 measuring latency to {host}")
        return {'min': 0, 'max': 0, 'avg': 0, 'jitter': 0}
    
    def _test_bandwidth(self, host: str) -> Dict:
        """Test bandwidth to specific host."""
        # TODO: Implement bandwidth testing
        logger.debug(f"🔍 R2 testing bandwidth to {host}")
        return {'upload_mbps': 0, 'download_mbps': 0}
    
    def _measure_packet_loss(self, host: str) -> float:
        """Measure packet loss percentage."""
        # TODO: Implement packet loss measurement
        logger.debug(f"🔍 R2 measuring packet loss to {host}")
        return 0.0
    
    def _test_dns_performance(self, host: str) -> Dict:
        """Test DNS resolution performance."""
        # TODO: Implement DNS performance testing
        logger.debug(f"🔍 R2 testing DNS performance for {host}")
        return {'resolution_time_ms': 0, 'dns_server': None}
    
    def _check_gateway_health(self) -> Dict:
        """Check gateway/router health."""
        # TODO: Implement gateway health checking
        logger.debug("🔍 R2 checking gateway health")
        return {'gateway_responsive': False, 'gateway_ip': None}
    
    def _check_dhcp_status(self) -> Dict:
        """Check DHCP server status and pool utilization."""
        # TODO: Implement DHCP status checking
        logger.debug("🔍 R2 checking DHCP status")
        return {'dhcp_available': False, 'pool_utilization': 0}

    # =================================================================
    # SYSTEM STATE & DIAGNOSTICS
    # =================================================================
    
    def gather_system_diagnostics(self, host: str) -> Dict:
        """
        Gather comprehensive system diagnostics.
        R2's medical droid capabilities!
        """
        logger.info(f"🩺 R2 gathering system diagnostics for {host}")
        
        diagnostics = {
            'system_resources': self._get_system_resources(host),
            'temperature_sensors': self._get_temperature_data(host),
            'power_consumption': self._get_power_data(host),
            'service_status': self._check_service_status(host),
            'security_status': self._check_security_status(host),
            'certificate_status': self._check_certificates(host)
        }
        
        return diagnostics
    
    def _get_system_resources(self, host: str) -> Dict:
        """Get CPU, memory, disk usage."""
        # TODO: Implement system resource monitoring
        logger.debug(f"🔍 R2 checking system resources for {host}")
        return {'cpu_percent': 0, 'memory_percent': 0, 'disk_percent': 0}
    
    def _get_temperature_data(self, host: str) -> Dict:
        """Get temperature sensor data."""
        # TODO: Implement temperature monitoring
        logger.debug(f"🔍 R2 checking temperature sensors for {host}")
        return {'cpu_temp': 0, 'ambient_temp': 0}
    
    def _get_power_data(self, host: str) -> Dict:
        """Get power consumption data."""
        # TODO: Implement power monitoring
        logger.debug(f"🔍 R2 checking power consumption for {host}")
        return {'power_watts': 0, 'battery_percent': None}
    
    def _check_service_status(self, host: str) -> List[Dict]:
        """Check status of critical services."""
        # TODO: Implement service status checking
        logger.debug(f"🔍 R2 checking service status for {host}")
        return []
    
    def _check_security_status(self, host: str) -> Dict:
        """Check security status and patch levels."""
        # TODO: Implement security status checking
        logger.debug(f"🔍 R2 checking security status for {host}")
        return {'patches_available': 0, 'last_update': None}
    
    def _check_certificates(self, host: str) -> List[Dict]:
        """Check SSL certificate status."""
        # TODO: Implement certificate checking
        logger.debug(f"🔍 R2 checking certificates for {host}")
        return []

    # =================================================================
    # SMART HOME DEVICE INTEGRATION
    # =================================================================
    
    def scan_smart_home_devices(self) -> Dict:
        """
        Scan for and integrate with smart home devices.
        R2's home automation interface!
        """
        logger.info("🏠 R2 scanning smart home devices...")
        
        smart_devices = {
            'hue_bridges': self._scan_hue_bridges(),
            'nest_devices': self._scan_nest_devices(),
            'security_cameras': self._scan_security_cameras(),
            'smart_switches': self._scan_smart_switches(),
            'sensors': self._scan_environmental_sensors()
        }
        
        return smart_devices
    
    def _scan_hue_bridges(self) -> List[Dict]:
        """Scan for Philips Hue bridges."""
        # TODO: Implement Hue bridge discovery and status
        logger.debug("🔍 R2 scanning Hue bridges")
        return []
    
    def _scan_nest_devices(self) -> List[Dict]:
        """Scan for Nest/Ecobee thermostats."""
        # TODO: Implement thermostat discovery
        logger.debug("🔍 R2 scanning Nest devices")
        return []
    
    def _scan_security_cameras(self) -> List[Dict]:
        """Scan for security cameras."""
        # TODO: Implement camera discovery and health check
        logger.debug("🔍 R2 scanning security cameras")
        return []
    
    def _scan_smart_switches(self) -> List[Dict]:
        """Scan for smart switches and outlets."""
        # TODO: Implement smart switch discovery
        logger.debug("🔍 R2 scanning smart switches")
        return []
    
    def _scan_environmental_sensors(self) -> List[Dict]:
        """Scan for environmental sensors."""
        # TODO: Implement sensor discovery and data collection
        logger.debug("🔍 R2 scanning environmental sensors")
        return []

    
if __name__ == "__main__":
    # This module is now controlled by r2_main.py
    # For direct testing only
    print("🤖 R2 Network Scanner Module")
    print("This module should be run via r2_main.py for full R2 functionality")
    print("Usage: python3 r2_main.py --help")
