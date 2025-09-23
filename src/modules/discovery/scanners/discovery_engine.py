"""
Industrial Automaton R2 Discovery Engine

Advanced 6-phase discovery engine implementing R2's autonomous network reconnaissance sequence.
Built with Industrial Automaton's legendary modular design philosophy and engineering excellence.

Manufactured by: Industrial Automaton, Rordis City, Nubia
Product Line: R2-series Astromech Network Discovery Module
Model: R2-NetRecon Advanced Discovery Engine v1.0

Features Intellex IV-based autonomous reconnaissance with:
- 6-phase sequential discovery protocol
- Modular scanner architecture for easy upgrades
- Environmental awareness and adaptive intelligence
- Real-time network topology mapping
- Multi-vector device correlation and classification

Discovery Sequence Phases:
1. Environmental Awareness (0-30s) - GPS, network interfaces, baseline topology
2. Passive Intelligence (30-90s) - Traffic observation, DNS recon, mDNS, DHCP
3. Active Host Discovery (90-180s) - Intelligent ping, ARP mining, UPnP/SSDP  
4. Service/Protocol Discovery (3-8min) - Strategic port scanning, SNMP, fingerprinting
5. Device Correlation (1-2min) - Multi-vector correlation, topology mapping
6. Deep Analysis Prep (30s) - Auth opportunities, anomaly detection, consolidation

"Modularity, Reliability, Intelligence" - Industrial Automaton Quality Since 32 BBY
"""

import asyncio
import subprocess
import ipaddress
import platform
import logging
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime
from enum import Enum

from .interfaces import DiscoveryScanner, DeviceInfo, ScannerConfig
from .arp_scanner import ARPScanner
from .mdns_scanner import MDNSScanner
from .ssdp_scanner import SSDPScanner
from .port_scanner import EnhancedPortScanner
from .snmp_scanner import SNMPScanner
from ..device_database import DeviceDatabase

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '../../..'))
from core.events import EventBus, create_event, R2Events

class DiscoveryMode(Enum):
    """Discovery scan modes."""
    SIMPLE = "simple"           # Basic 3-phase scan (legacy compatibility)
    COMPREHENSIVE = "comprehensive"  # Full 6-phase R2 sequence
    DEEP = "deep"              # Extended analysis with authentication attempts

class DiscoveryPhase(Enum):
    """R2 Discovery sequence phases."""
    ENVIRONMENTAL = "environmental"      # Phase 1: Environmental Awareness
    PASSIVE = "passive"                 # Phase 2: Passive Intelligence  
    ACTIVE = "active"                   # Phase 3: Active Host Discovery
    SERVICE = "service"                 # Phase 4: Service/Protocol Discovery
    CORRELATION = "correlation"          # Phase 5: Device Correlation
    ANALYSIS = "analysis"               # Phase 6: Deep Analysis Prep

class DiscoveryEngine(DiscoveryScanner):
    """
    R2 Advanced Discovery Engine
    
    Implements R2's 6-phase autonomous network reconnaissance sequence:
    1. Environmental Awareness - Context detection and network topology
    2. Passive Intelligence - Traffic observation and DNS reconnaissance  
    3. Active Host Discovery - Intelligent multi-method host detection
    4. Service/Protocol Discovery - Strategic service enumeration
    5. Device Correlation - Multi-vector device identification
    6. Deep Analysis Prep - Authentication and vulnerability assessment
    """
    
    def __init__(self, event_bus: EventBus, config: ScannerConfig):
        super().__init__(event_bus, config)
        
        # Discovery mode configuration
        self.discovery_mode = DiscoveryMode(config.custom_options.get('discovery_mode', 'simple'))
        self.logger.info(f"Discovery engine initialized in {self.discovery_mode.value} mode")
        
        # Phase execution tracking
        self.current_phase = None
        self.completed_phases = set()
        self.phase_results = {}
        
        # Initialize specialized scanners
        self._init_scanners(config)
        
        # Tool availability tracking
        self.available_tools = {}
        self.tool_preferences = {
            'discovery_tool': 'nmap',     # Prefer nmap (masscan requires sudo)
            'port_scanner': 'nmap',       # Use nmap for detailed port scanning
            'ping_method': 'system'       # Use system ping
        }
        
        # Discovery configuration
        self.ping_timeout = config.custom_options.get('ping_timeout', 1.0)
        self.scan_timeout = config.custom_options.get('scan_timeout', 30.0)
        self.max_concurrent = config.custom_options.get('max_concurrent', 50)
        
        # Enhanced statistics for R2 sequence
        self.stats = {
            'discovery_scans': 0,
            'hosts_discovered': 0,
            'phases_completed': 0,
            'total_scan_time': 0.0,
            # Phase-specific stats
            'environmental_detections': 0,
            'passive_intelligence': 0,
            'active_discoveries': 0,
            'service_discoveries': 0,
            'device_correlations': 0,
            'analysis_findings': 0
        }
        
        # Initialize device database
        self.device_database = DeviceDatabase()
    
    def _init_scanners(self, config: ScannerConfig) -> None:
        """Initialize all specialized scanner modules."""
        try:
            # Phase 1: Environmental Awareness scanners
            # GPS scanner (stub - will be available soon)
            self.gps_scanner = None  # GPSScanner(self.event_bus, config) when available
            
            # Phase 2: Passive Intelligence scanners  
            self.arp_scanner = ARPScanner(self.event_bus, config)
            self.mdns_scanner = MDNSScanner(self.event_bus, config)
            # self.dns_scanner = DNSScanner(self.event_bus, config)  # TODO: Implement
            # self.dhcp_scanner = DHCPScanner(self.event_bus, config)  # TODO: Implement
            # self.traffic_scanner = TrafficScanner(self.event_bus, config)  # TODO: Implement
            
            # Phase 3: Active Host Discovery scanners
            self.ssdp_scanner = SSDPScanner(self.event_bus, config)
            # self.upnp_scanner = UPnPScanner(self.event_bus, config)  # TODO: Implement (separate from SSDP)
            
            # Phase 4: Service/Protocol Discovery scanners
            self.port_scanner = EnhancedPortScanner(self.event_bus, config)
            self.snmp_scanner = SNMPScanner(self.event_bus, config)
            # self.banner_scanner = BannerScanner(self.event_bus, config)  # TODO: Implement
            # self.protocol_scanner = ProtocolScanner(self.event_bus, config)  # TODO: Implement
            
            # Phase 5: Device Correlation scanners
            # self.correlation_engine = CorrelationEngine(self.event_bus, config)  # TODO: Implement
            # self.topology_mapper = TopologyMapper(self.event_bus, config)  # TODO: Implement
            
            # Phase 6: Deep Analysis scanners
            # self.auth_scanner = AuthScanner(self.event_bus, config)  # TODO: Implement
            # self.anomaly_scanner = AnomalyScanner(self.event_bus, config)  # TODO: Implement
            
            self.logger.info("Scanner modules initialized successfully")
            
        except Exception as e:
            self.logger.error(f"Failed to initialize scanner modules: {e}")
            raise
    
    async def initialize(self) -> bool:
        """Initialize the discovery engine and all its scanners."""
        try:
            self.logger.info("Initializing DiscoveryEngine...")
            
            # Initialize child scanners
            arp_init = await self.arp_scanner.initialize()
            mdns_init = await self.mdns_scanner.initialize()
            
            if arp_init:
                self.logger.info("✅ ARP scanner initialized successfully")
            else:
                self.logger.warning("⚠️ ARP scanner initialization failed")
                
            if mdns_init:
                self.logger.info("✅ mDNS scanner initialized successfully") 
            else:
                self.logger.warning("⚠️ mDNS scanner initialization failed")
            
            # Initialize base scanner
            base_init = await super().initialize()
            
            if base_init:
                self.logger.info("DiscoveryEngine initialized successfully")
                return True
            else:
                self.logger.error("DiscoveryEngine base initialization failed")
                return False
                
        except Exception as e:
            self.logger.error(f"Failed to initialize DiscoveryEngine: {e}")
            return False

    async def check_availability(self) -> bool:
        """Check if discovery tools are available."""
        try:
            await self._check_tool_availability()
            
            # At least one discovery method should be available
            has_arp = await self.arp_scanner.check_availability()
            has_traditional = any(self.available_tools.values())
            has_mdns = await self.mdns_scanner.check_availability()
            
            return has_arp or has_traditional or has_mdns
            
        except Exception as e:
            self.logger.error(f"Tool availability check failed: {e}")
            return False
    
    async def discover_hosts(self, network: str, scan_id: str) -> List[str]:
        """
        Main discovery entry point - routes to appropriate discovery method based on mode.
        
        Args:
            network: Network range (e.g., '192.168.1.0/24')
            scan_id: Unique scan identifier
            
        Returns:
            List of discovered host IP addresses
        """
        start_time = datetime.now()
        
        try:
            if self.discovery_mode == DiscoveryMode.SIMPLE:
                hosts = await self._simple_discovery(network, scan_id)
            elif self.discovery_mode == DiscoveryMode.COMPREHENSIVE:
                hosts = await self._comprehensive_discovery(network, scan_id)
            elif self.discovery_mode == DiscoveryMode.DEEP:
                hosts = await self._deep_discovery(network, scan_id)
            else:
                self.logger.warning(f"Unknown discovery mode: {self.discovery_mode}")
                hosts = await self._simple_discovery(network, scan_id)
            
            # Update statistics
            scan_time = (datetime.now() - start_time).total_seconds()
            self.stats['total_scan_time'] += scan_time
            self.stats['discovery_scans'] += 1
            
            self.logger.info(f"Discovery completed in {scan_time:.1f}s: {len(hosts)} hosts found")
            return hosts
            
        except Exception as e:
            self.logger.error(f"Host discovery failed: {e}")
            return []
    
    async def _simple_discovery(self, network: str, scan_id: str) -> List[str]:
        """
        Simple 3-phase discovery (legacy compatibility).
        
        Phases:
        1. ARP Discovery (finds quiet devices)  
        2. Traditional Discovery (ping/nmap/masscan)
        3. mDNS Discovery (enriches device information)
        """
        self.logger.info(f"🤖 R2 Simple Discovery Mode: {network}")
        all_hosts = set()
        
        # Phase 1: ARP Discovery
        if await self.arp_scanner.check_availability():
            try:
                self.logger.info(f"Phase 1: ARP Discovery for {network}")
                arp_hosts = await self.arp_scanner.discover_hosts(network, scan_id)
                all_hosts.update(arp_hosts)
                self.logger.info(f"ARP discovery found {len(arp_hosts)} devices")
            except Exception as e:
                self.logger.warning(f"ARP discovery failed: {e}")
        
        # Phase 2: Traditional Discovery
        self.logger.info(f"Phase 2: Traditional Discovery for {network}")
        traditional_hosts = await self._traditional_discovery_methods(network, scan_id)
        all_hosts.update(traditional_hosts)
        self.logger.info(f"Traditional discovery found {len(traditional_hosts)} devices")
        
        # Phase 3: mDNS Discovery
        if await self.mdns_scanner.check_availability():
            try:
                self.logger.info(f"Phase 3: mDNS Discovery for {network}")
                mdns_hosts = await self.mdns_scanner.discover_hosts(network, scan_id)
                all_hosts.update(mdns_hosts)
                self.logger.info(f"mDNS discovery found {len(mdns_hosts)} devices")
            except Exception as e:
                self.logger.warning(f"mDNS discovery failed: {e}")
        
        return sorted(list(all_hosts))
    
    async def _comprehensive_discovery(self, network: str, scan_id: str) -> List[str]:
        """
        Comprehensive 6-phase R2 discovery sequence.
        
        Implements the full 19-step R2 autonomous reconnaissance sequence.
        """
        self.logger.info(f"🤖 R2 Comprehensive Discovery Mode: {network}")
        self.logger.info("🔍 Initiating R2's autonomous network reconnaissance sequence...")
        
        # Reset phase tracking
        self.completed_phases.clear()
        self.phase_results.clear()
        
        all_hosts = set()
        
        # Phase 1: Environmental Awareness (0-30s)
        env_context = await self._phase_1_environmental_awareness(network, scan_id)
        
        # Phase 2: Passive Intelligence Gathering (30-90s)  
        passive_intel = await self._phase_2_passive_intelligence(network, scan_id)
        all_hosts.update(passive_intel.get('discovered_hosts', []))
        
        # Phase 3: Active Host Discovery (90-180s)
        active_hosts = await self._phase_3_active_discovery(network, scan_id, env_context)
        all_hosts.update(active_hosts)
        
        # Phase 4: Service and Protocol Discovery (3-8min)
        service_hosts = await self._phase_4_service_discovery(list(all_hosts), scan_id)
        all_hosts.update(service_hosts)
        
        # Phase 5: Device Correlation and Classification (1-2min)
        correlated_hosts = await self._phase_5_device_correlation(list(all_hosts), scan_id)
        all_hosts.update(correlated_hosts)
        
        # Phase 6: Deep Analysis Preparation (30s)
        await self._phase_6_analysis_preparation(list(all_hosts), scan_id)
        
        self.logger.info(f"🎯 R2 comprehensive discovery complete: {len(all_hosts)} devices analyzed")
        return sorted(list(all_hosts))
    
    async def _deep_discovery(self, network: str, scan_id: str) -> List[str]:
        """
        Deep discovery with authentication and vulnerability assessment.
        
        Extends comprehensive discovery with credential testing and security analysis.
        """
        self.logger.info(f"🤖 R2 Deep Discovery Mode: {network}")
        
        # Start with comprehensive discovery
        hosts = await self._comprehensive_discovery(network, scan_id)
        
        # Extended Phase 7: Authentication Attempts (if configured)
        # Extended Phase 8: Vulnerability Assessment (if configured)
        # These will be implemented when authentication module is ready
        
        return hosts
    
    # ==============================================================================
    # R2 6-PHASE DISCOVERY SEQUENCE IMPLEMENTATION
    # ==============================================================================
    
    async def _phase_1_environmental_awareness(self, network: str, scan_id: str) -> Dict[str, Any]:
        """
        Phase 1: Environmental Awareness (0-30 seconds)
        
        Steps:
        1. GPS Location Acquisition (stub)
        2. Network Interface Enumeration  
        3. Baseline Network Topology
        """
        self.current_phase = DiscoveryPhase.ENVIRONMENTAL
        self.logger.info("🌍 Phase 1: Environmental Awareness")
        
        context = {
            'gps_location': None,
            'network_interfaces': [],
            'network_topology': {},
            'scan_parameters': {}
        }
        
        try:
            # Step 1: GPS Location Acquisition (stub)
            if self.gps_scanner:
                context['gps_location'] = await self._gps_location_acquisition()
            else:
                self.logger.debug("GPS scanner not available - skipping location acquisition")
            
            # Step 2: Network Interface Enumeration
            context['network_interfaces'] = await self._network_interface_enumeration()
            
            # Step 3: Baseline Network Topology  
            context['network_topology'] = await self._baseline_network_topology(network)
            
            # Set scanning parameters based on environment
            context['scan_parameters'] = self._set_environmental_scan_parameters(context)
            
            self.completed_phases.add(DiscoveryPhase.ENVIRONMENTAL)
            self.phase_results['environmental'] = context
            self.stats['environmental_detections'] += len(context['network_interfaces'])
            
            self.logger.info(f"✅ Phase 1 complete: {len(context['network_interfaces'])} interfaces, topology mapped")
            return context
            
        except Exception as e:
            self.logger.error(f"Phase 1 Environmental Awareness failed: {e}")
            return context
    
    async def _phase_2_passive_intelligence(self, network: str, scan_id: str) -> Dict[str, Any]:
        """
        Phase 2: Passive Intelligence Gathering (30-90 seconds)
        
        Steps:
        4. Passive Traffic Observation (stub)
        5. DNS Reconnaissance (stub)
        6. mDNS Service Discovery
        7. DHCP Intelligence Gathering (stub)
        """
        self.current_phase = DiscoveryPhase.PASSIVE
        self.logger.info("🕵️ Phase 2: Passive Intelligence Gathering")
        
        intel = {
            'discovered_hosts': [],
            'traffic_patterns': {},
            'dns_intel': {},
            'mdns_services': [],
            'dhcp_intel': {}
        }
        
        try:
            # Step 4: Passive Traffic Observation (stub)
            intel['traffic_patterns'] = await self._passive_traffic_observation(network)
            
            # Step 5: DNS Reconnaissance (stub)
            intel['dns_intel'] = await self._dns_reconnaissance(network)
            
            # Step 6: mDNS Service Discovery
            if await self.mdns_scanner.check_availability():
                mdns_hosts = await self.mdns_scanner.discover_hosts(network, scan_id)
                intel['discovered_hosts'].extend(mdns_hosts)
                intel['mdns_services'] = await self._get_mdns_service_details(mdns_hosts, scan_id)
            
            # Step 7: DHCP Intelligence Gathering (stub)
            intel['dhcp_intel'] = await self._dhcp_intelligence_gathering(network)
            
            self.completed_phases.add(DiscoveryPhase.PASSIVE)
            self.phase_results['passive'] = intel
            self.stats['passive_intelligence'] += len(intel['discovered_hosts'])
            
            self.logger.info(f"✅ Phase 2 complete: {len(intel['discovered_hosts'])} hosts from passive intel")
            return intel
            
        except Exception as e:
            self.logger.error(f"Phase 2 Passive Intelligence failed: {e}")
            return intel
    
    async def _phase_3_active_discovery(self, network: str, scan_id: str, env_context: Dict[str, Any]) -> List[str]:
        """
        Phase 3: Active Host Discovery (90-180 seconds)
        
        Steps:
        8. Intelligent Ping Sweep
        9. ARP Table Mining
        10. UPnP/SSDP Discovery (stub)
        """
        self.current_phase = DiscoveryPhase.ACTIVE
        self.logger.info("🎯 Phase 3: Active Host Discovery")
        
        all_hosts = set()
        
        try:
            # Step 8: Intelligent Ping Sweep
            ping_hosts = await self._intelligent_ping_sweep(network, scan_id, env_context)
            all_hosts.update(ping_hosts)
            
            # Step 9: ARP Table Mining
            if await self.arp_scanner.check_availability():
                arp_hosts = await self.arp_scanner.discover_hosts(network, scan_id)
                all_hosts.update(arp_hosts)
            
            # Step 10: UPnP/SSDP Discovery (stub)
            upnp_hosts = await self._upnp_ssdp_discovery(network, scan_id)
            all_hosts.update(upnp_hosts)
            
            discovered_hosts = list(all_hosts)
            self.completed_phases.add(DiscoveryPhase.ACTIVE)
            self.phase_results['active'] = {'discovered_hosts': discovered_hosts}
            self.stats['active_discoveries'] += len(discovered_hosts)
            
            self.logger.info(f"✅ Phase 3 complete: {len(discovered_hosts)} active hosts discovered")
            return discovered_hosts
            
        except Exception as e:
            self.logger.error(f"Phase 3 Active Discovery failed: {e}")
            return list(all_hosts)
    
    async def _phase_4_service_discovery(self, hosts: List[str], scan_id: str) -> List[str]:
        """
        Phase 4: Service and Protocol Discovery (3-8 minutes)
        
        Steps:
        11. Strategic Port Scanning
        12. SNMP Community Probing
        13. Protocol Fingerprinting (stub)
        """
        self.current_phase = DiscoveryPhase.SERVICE
        self.logger.info("🔧 Phase 4: Service and Protocol Discovery")
        
        enriched_hosts = set(hosts)
        
        try:
            # Step 11: Strategic Port Scanning
            for host in hosts:
                # Use existing port scanner logic
                pass  # Will be enhanced with strategic port selection
            
            # Step 12: SNMP Community Probing
            if hasattr(self, 'snmp_scanner') and self.snmp_scanner:
                snmp_hosts = await self._snmp_community_probing(hosts, scan_id)
                enriched_hosts.update(snmp_hosts)
            
            # Step 13: Protocol Fingerprinting (stub)
            fingerprint_results = await self._protocol_fingerprinting(hosts, scan_id)
            
            discovered_hosts = list(enriched_hosts)
            self.completed_phases.add(DiscoveryPhase.SERVICE)
            self.phase_results['service'] = {'enriched_hosts': discovered_hosts, 'fingerprints': fingerprint_results}
            self.stats['service_discoveries'] += len(discovered_hosts)
            
            self.logger.info(f"✅ Phase 4 complete: {len(discovered_hosts)} hosts with service data")
            return discovered_hosts
            
        except Exception as e:
            self.logger.error(f"Phase 4 Service Discovery failed: {e}")
            return hosts
    
    async def _phase_5_device_correlation(self, hosts: List[str], scan_id: str) -> List[str]:
        """
        Phase 5: Device Correlation and Classification (1-2 minutes)
        
        Steps:
        14. Multi-Vector Device Correlation (stub)
        15. Network Topology Mapping (stub)
        16. Environmental Context Application (stub)
        """
        self.current_phase = DiscoveryPhase.CORRELATION
        self.logger.info("🧠 Phase 5: Device Correlation and Classification")
        
        try:
            # Step 14: Multi-Vector Device Correlation (stub)
            correlation_results = await self._multi_vector_device_correlation(hosts, scan_id)
            
            # Step 15: Network Topology Mapping (stub)
            topology_map = await self._network_topology_mapping(hosts, scan_id)
            
            # Step 16: Environmental Context Application (stub)
            context_results = await self._environmental_context_application(hosts, scan_id)
            
            self.completed_phases.add(DiscoveryPhase.CORRELATION)
            self.phase_results['correlation'] = {
                'correlation_results': correlation_results,
                'topology_map': topology_map,
                'context_results': context_results
            }
            self.stats['device_correlations'] += len(hosts)
            
            self.logger.info(f"✅ Phase 5 complete: {len(hosts)} devices correlated and classified")
            return hosts
            
        except Exception as e:
            self.logger.error(f"Phase 5 Device Correlation failed: {e}")
            return hosts
    
    async def _phase_6_analysis_preparation(self, hosts: List[str], scan_id: str) -> Dict[str, Any]:
        """
        Phase 6: Deep Analysis Preparation (30 seconds)
        
        Steps:
        17. Authentication Opportunity Identification (stub)
        18. Anomaly and Security Flagging (stub)
        19. Scan Result Consolidation
        """
        self.current_phase = DiscoveryPhase.ANALYSIS
        self.logger.info("📊 Phase 6: Deep Analysis Preparation")
        
        analysis_prep = {
            'auth_opportunities': [],
            'security_flags': [],
            'consolidated_results': {}
        }
        
        try:
            # Step 17: Authentication Opportunity Identification (stub)
            analysis_prep['auth_opportunities'] = await self._authentication_opportunity_identification(hosts, scan_id)
            
            # Step 18: Anomaly and Security Flagging (stub)  
            analysis_prep['security_flags'] = await self._anomaly_and_security_flagging(hosts, scan_id)
            
            # Step 19: Scan Result Consolidation
            analysis_prep['consolidated_results'] = await self._scan_result_consolidation(hosts, scan_id)
            
            self.completed_phases.add(DiscoveryPhase.ANALYSIS)
            self.phase_results['analysis'] = analysis_prep
            self.stats['analysis_findings'] += len(analysis_prep['auth_opportunities']) + len(analysis_prep['security_flags'])
            self.stats['phases_completed'] = len(self.completed_phases)
            
            self.logger.info(f"✅ Phase 6 complete: Analysis prepared for {len(hosts)} devices")
            return analysis_prep
            
        except Exception as e:
            self.logger.error(f"Phase 6 Analysis Preparation failed: {e}")
            return analysis_prep
    
    async def scan(self, target: str, scan_id: str) -> List[DeviceInfo]:
        """
        Perform comprehensive network discovery scan.
        
        Args:
            target: Target network (e.g., '192.168.1.0/24')
            scan_id: Unique scan identifier
            
        Returns:
            List of discovered devices with enriched information
        """
        try:
            # Perform comprehensive discovery with all scanners
            all_devices = {}  # Use dict to deduplicate by IP
            
            # Phase 1: ARP Discovery
            if await self.arp_scanner.check_availability():
                try:
                    self.logger.info(f"Phase 1: ARP Discovery for {target}")
                    arp_devices = await self.arp_scanner.scan(target, scan_id)
                    for device in arp_devices:
                        all_devices[device.ip] = device
                        # Publish device discovered event
                        await self._publish_device_discovered(device, len(all_devices), len(arp_devices))
                    self.logger.info(f"ARP discovery found {len(arp_devices)} devices")
                except Exception as e:
                    self.logger.warning(f"ARP discovery failed: {e}")
            
            # Phase 2: Traditional Discovery (nmap/ping)
            self.logger.info(f"Phase 2: Traditional Discovery for {target}")
            traditional_hosts = await self._traditional_discovery_methods(target, scan_id)
            for host in traditional_hosts:
                if host not in all_devices:
                    # Create basic device info for hosts found only by traditional methods
                    device_info = DeviceInfo(
                        ip=host,
                        status="active",
                        discovery_method="traditional",
                        timestamp=datetime.now().isoformat(),
                        scan_id=scan_id,
                        confidence=0.6
                    )
                    all_devices[host] = device_info
                    # Publish device discovered event
                    await self._publish_device_discovered(device_info, len(all_devices), len(traditional_hosts))
            self.logger.info(f"Traditional discovery found {len(traditional_hosts)} devices")
            
            # Phase 3: mDNS Discovery
            if await self.mdns_scanner.check_availability():
                try:
                    self.logger.info(f"Phase 3: mDNS Discovery for {target}")
                    mdns_devices = await self.mdns_scanner.scan(target, scan_id)
                    for device in mdns_devices:
                        if device.ip in all_devices:
                            # Merge mDNS data with existing device info
                            existing = all_devices[device.ip]
                            if device.hostname:
                                existing.hostname = device.hostname
                            if device.device_type:
                                existing.device_type = device.device_type
                            if device.open_ports:
                                existing.open_ports.extend(device.open_ports)
                            if device.services:
                                existing.services.update(device.services)
                            if device.mdns_services:
                                existing.mdns_services.extend(device.mdns_services)
                            # Update confidence and method
                            existing.confidence = max(existing.confidence, device.confidence)
                            if "mdns" not in existing.discovery_method:
                                existing.discovery_method += "+mdns"
                        else:
                            # New device found only by mDNS
                            all_devices[device.ip] = device
                        
                        # Publish device discovered event
                        await self._publish_device_discovered(all_devices[device.ip], len(all_devices), len(mdns_devices))
                    self.logger.info(f"mDNS discovery found {len(mdns_devices)} devices")
                except Exception as e:
                    self.logger.warning(f"mDNS discovery failed: {e}")
            
            # Convert to list and save to database
            devices = list(all_devices.values())
            
            # Save devices to database
            saved_count = 0
            for device in devices:
                try:
                    if self.device_database.add_or_update_device(device.to_dict()):
                        saved_count += 1
                except Exception as e:
                    self.logger.warning(f"Failed to save device {device.ip} to database: {e}")
            
            self.logger.info(f"Saved {saved_count}/{len(devices)} devices to database")
            
            self.logger.info(f"Total comprehensive scan found {len(devices)} unique devices")
            return devices
            
        except Exception as e:
            self.logger.error(f"Discovery scan failed: {e}")
            return []
    
    async def _check_tool_availability(self) -> None:
        """Check availability of network scanning tools."""
        self.available_tools = {}
        
        # Check masscan
        try:
            result = await asyncio.create_subprocess_exec(
                'masscan', '--version',
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            await asyncio.wait_for(result.wait(), timeout=5.0)
            self.available_tools['masscan'] = True
            self.logger.debug("Masscan is available")
        except (FileNotFoundError, asyncio.TimeoutError, subprocess.CalledProcessError):
            self.available_tools['masscan'] = False
        
        # Check nmap
        try:
            result = await asyncio.create_subprocess_exec(
                'nmap', '--version',
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            await asyncio.wait_for(result.wait(), timeout=5.0)
            self.available_tools['nmap'] = True
            self.logger.debug("Nmap is available")
        except (FileNotFoundError, asyncio.TimeoutError, subprocess.CalledProcessError):
            self.available_tools['nmap'] = False
        
        # Check ping (should always be available)
        self.available_tools['ping'] = True
        self.logger.debug("System ping is available")
    
    async def _masscan_discovery(self, network: str, scan_id: str) -> List[str]:
        """Use masscan for fast host discovery."""
        try:
            self.logger.info(f"Using masscan for discovery: {network}")
            
            # Masscan command for host discovery
            cmd = [
                'masscan',
                network,
                '--ping',  # Only ping sweep, no port scanning
                '--rate', '1000',  # Fast rate
                '--wait', '0',  # Don't wait for results
                '-oX', '-'  # Output XML to stdout
            ]
            
            result = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            stdout, stderr = await asyncio.wait_for(
                result.communicate(), 
                timeout=self.scan_timeout
            )
            
            if result.returncode == 0:
                hosts = self._parse_masscan_output(stdout.decode())
                self.logger.info(f"Masscan found {len(hosts)} hosts")
                return hosts
            else:
                self.logger.warning(f"Masscan failed: {stderr.decode()}")
                return []
                
        except asyncio.TimeoutError:
            self.logger.warning("Masscan discovery timed out")
            return []
        except Exception as e:
            self.logger.error(f"Masscan discovery failed: {e}")
            return []
    
    async def _nmap_discovery(self, network: str, scan_id: str) -> List[str]:
        """Use nmap for host discovery."""
        try:
            self.logger.info(f"Using nmap for discovery: {network}")
            
            # Nmap command for host discovery
            cmd = [
                'nmap',
                '-sn',  # Ping scan only
                '--max-retries', '1',
                '--host-timeout', '10s',
                network
            ]
            
            result = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            stdout, stderr = await asyncio.wait_for(
                result.communicate(), 
                timeout=self.scan_timeout
            )
            
            if result.returncode == 0:
                hosts = self._parse_nmap_output(stdout.decode())
                self.logger.info(f"Nmap found {len(hosts)} hosts")
                return hosts
            else:
                self.logger.warning(f"Nmap failed: {stderr.decode()}")
                return []
                
        except asyncio.TimeoutError:
            self.logger.warning("Nmap discovery timed out")
            return []
        except Exception as e:
            self.logger.error(f"Nmap discovery failed: {e}")
            return []
    
    async def _basic_ping_sweep(self, network: str, scan_id: str) -> List[str]:
        """Basic ping sweep using system ping."""
        try:
            self.logger.info(f"Using basic ping sweep: {network}")
            
            # Generate IP addresses to ping
            network_obj = ipaddress.IPv4Network(network, strict=False)
            hosts_to_ping = list(network_obj.hosts())
            
            # Limit concurrent pings
            semaphore = asyncio.Semaphore(self.max_concurrent)
            
            async def ping_host(ip):
                async with semaphore:
                    try:
                        if platform.system().lower() == 'windows':
                            cmd = ['ping', '-n', '1', '-w', '1000', str(ip)]
                        else:
                            cmd = ['ping', '-c', '1', '-W', '1', str(ip)]
                        
                        result = await asyncio.create_subprocess_exec(
                            *cmd,
                            stdout=asyncio.subprocess.PIPE,
                            stderr=asyncio.subprocess.PIPE
                        )
                        
                        await asyncio.wait_for(result.wait(), timeout=self.ping_timeout)
                        
                        if result.returncode == 0:
                            return str(ip)
                        return None
                        
                    except (asyncio.TimeoutError, subprocess.CalledProcessError):
                        return None
            
            # Ping all hosts concurrently
            tasks = [ping_host(ip) for ip in hosts_to_ping]
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # Filter successful pings
            active_hosts = [ip for ip in results if ip is not None and not isinstance(ip, Exception)]
            
            self.logger.info(f"Basic ping sweep found {len(active_hosts)} hosts")
            return active_hosts
            
        except Exception as e:
            self.logger.error(f"Basic ping sweep failed: {e}")
            return []
    
    def _parse_masscan_output(self, output: str) -> List[str]:
        """Parse masscan XML output to extract host IPs."""
        hosts = []
        try:
            import xml.etree.ElementTree as ET
            root = ET.fromstring(output)
            
            for host in root.findall('.//host'):
                address = host.find('address')
                if address is not None:
                    hosts.append(address.get('addr'))
                    
        except Exception as e:
            self.logger.warning(f"Failed to parse masscan output: {e}")
            
        return hosts
    
    def _parse_nmap_output(self, output: str) -> List[str]:
        """Parse nmap output to extract host IPs."""
        hosts = []
        try:
            import re
            # Look for "Nmap scan report for" lines
            pattern = r'Nmap scan report for (\d+\.\d+\.\d+\.\d+)'
            matches = re.findall(pattern, output)
            hosts.extend(matches)
            
        except Exception as e:
            self.logger.warning(f"Failed to parse nmap output: {e}")
            
        return hosts
    
    async def start(self) -> bool:
        """Start the discovery engine (required by IModule interface)."""
        try:
            self.logger.info("Starting discovery engine...")
            self.is_running = True
            self.logger.info("Discovery engine started successfully")
            return True
        except Exception as e:
            self.logger.error(f"Failed to start discovery engine: {e}")
            return False
    
    async def stop(self) -> bool:
        """Stop the discovery engine (required by IModule interface)."""
        try:
            self.logger.info("Stopping discovery engine...")
            self.is_running = False
            self.logger.info("Discovery engine stopped successfully")
            return True
        except Exception as e:
            self.logger.error(f"Failed to stop discovery engine: {e}")
            return False
    
    async def cleanup(self) -> None:
        """Cleanup the discovery engine (required by IModule interface)."""
        try:
            self.logger.info("Cleaning up discovery engine...")
            await self.shutdown()
            self.logger.info("Discovery engine cleanup complete")
        except Exception as e:
            self.logger.error(f"Failed to cleanup discovery engine: {e}")
    
    def get_status(self) -> str:
        """Get the current status of the discovery engine."""
        return "running" if self.is_running else "stopped"
    
    # ==============================================================================
    # HELPER METHODS FOR 19-STEP DISCOVERY SEQUENCE
    # ==============================================================================
    
    async def _traditional_discovery_methods(self, network: str, scan_id: str) -> List[str]:
        """Traditional discovery methods (nmap/masscan/ping)."""
        # Check tool availability if not done yet
        if not self.available_tools:
            await self._check_tool_availability()
        
        # Choose the best available discovery method
        discovery_tool = self.tool_preferences.get('discovery_tool', 'nmap')
        
        if discovery_tool == 'masscan' and 'masscan' in self.available_tools:
            return await self._masscan_discovery(network, scan_id)
        elif 'nmap' in self.available_tools:
            self.logger.info("Masscan not available, using nmap discovery")
            return await self._nmap_discovery(network, scan_id)
        else:
            self.logger.info("Using basic ping sweep (no enhanced tools available)")
            return await self._basic_ping_sweep(network, scan_id)
    
    # Phase 1 Helper Methods (Environmental Awareness)
    async def _gps_location_acquisition(self) -> Optional[Dict[str, Any]]:
        """Step 1: GPS Location Acquisition (stub)."""
        self.logger.debug("GPS location acquisition - stub implementation")
        # TODO: Implement GPS when hardware is available
        return None
    
    async def _network_interface_enumeration(self) -> List[Dict[str, Any]]:
        """Step 2: Network Interface Enumeration."""
        interfaces = []
        try:
            import netifaces
            for interface in netifaces.interfaces():
                addrs = netifaces.ifaddresses(interface)
                if netifaces.AF_INET in addrs:
                    for addr_info in addrs[netifaces.AF_INET]:
                        interfaces.append({
                            'interface': interface,
                            'ip': addr_info.get('addr'),
                            'netmask': addr_info.get('netmask'),
                            'type': 'ipv4'
                        })
        except ImportError:
            self.logger.warning("netifaces not available, using basic interface detection")
            # Fallback to basic detection
            interfaces = [{'interface': 'unknown', 'ip': 'unknown', 'type': 'unknown'}]
        except Exception as e:
            self.logger.error(f"Network interface enumeration failed: {e}")
        
        return interfaces
    
    async def _baseline_network_topology(self, network: str) -> Dict[str, Any]:
        """Step 3: Baseline Network Topology."""
        topology = {
            'default_gateway': None,
            'dns_servers': [],
            'network_range': network,
            'architecture': 'unknown'
        }
        
        try:
            # Basic topology detection
            import socket
            try:
                # Try to determine default gateway
                s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
                s.connect(("8.8.8.8", 80))
                local_ip = s.getsockname()[0]
                s.close()
                
                # Extract gateway from IP (simple heuristic)
                ip_parts = local_ip.split('.')
                if len(ip_parts) == 4:
                    topology['default_gateway'] = f"{ip_parts[0]}.{ip_parts[1]}.{ip_parts[2]}.1"
                    
            except Exception:
                pass
                
        except Exception as e:
            self.logger.warning(f"Baseline topology detection failed: {e}")
        
        return topology
    
    def _set_environmental_scan_parameters(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Set scanning parameters based on environmental context."""
        params = {
            'timing': 'normal',
            'intensity': 'medium',
            'stealth': False
        }
        
        # Adjust based on number of interfaces (proxy for network size)
        interface_count = len(context.get('network_interfaces', []))
        if interface_count > 3:
            params['timing'] = 'aggressive'
            params['intensity'] = 'high'
        
        return params
    
    # Phase 2 Helper Methods (Passive Intelligence)
    async def _passive_traffic_observation(self, network: str) -> Dict[str, Any]:
        """Step 4: Passive Traffic Observation (stub)."""
        self.logger.debug("Passive traffic observation - stub implementation")
        # TODO: Implement traffic capture and analysis
        return {'patterns': [], 'protocols': []}
    
    async def _dns_reconnaissance(self, network: str) -> Dict[str, Any]:
        """Step 5: DNS Reconnaissance (stub)."""
        self.logger.debug("DNS reconnaissance - stub implementation")
        # TODO: Implement DNS enumeration, zone transfers, etc.
        return {'hostnames': [], 'zone_info': {}}
    
    async def _get_mdns_service_details(self, hosts: List[str], scan_id: str) -> List[Dict[str, Any]]:
        """Get detailed mDNS service information."""
        services = []
        # TODO: Extract detailed service info from mDNS scanner results
        return services
    
    async def _dhcp_intelligence_gathering(self, network: str) -> Dict[str, Any]:
        """Step 7: DHCP Intelligence Gathering (stub)."""
        self.logger.debug("DHCP intelligence gathering - stub implementation")
        # TODO: Implement DHCP discovery and lease table analysis
        return {'lease_info': [], 'dhcp_options': {}}
    
    # Phase 3 Helper Methods (Active Discovery)
    async def _intelligent_ping_sweep(self, network: str, scan_id: str, env_context: Dict[str, Any]) -> List[str]:
        """Step 8: Intelligent Ping Sweep with TTL analysis."""
        # For now, use traditional methods but with environmental context
        params = env_context.get('scan_parameters', {})
        
        if params.get('timing') == 'aggressive':
            # Use faster scanning
            return await self._nmap_discovery(network, scan_id)
        else:
            # Use standard scanning
            return await self._traditional_discovery_methods(network, scan_id)
    
    async def _upnp_ssdp_discovery(self, network: str, scan_id: str) -> List[str]:
        """Step 10: UPnP/SSDP Discovery."""
        discovered_hosts = []
        
        if hasattr(self, 'ssdp_scanner') and self.ssdp_scanner:
            try:
                if await self.ssdp_scanner.check_availability():
                    self.logger.info("🔍 Performing SSDP/UPnP discovery")
                    
                    # Perform SSDP discovery (network parameter not used for multicast)
                    ssdp_devices = await self.ssdp_scanner.scan(network, scan_id)
                    
                    # Extract host IPs from discovered devices
                    for device in ssdp_devices:
                        if device.ip and device.ip not in discovered_hosts:
                            discovered_hosts.append(device.ip)
                    
                    self.logger.info(f"✅ SSDP discovery found {len(ssdp_devices)} UPnP devices on {len(discovered_hosts)} hosts")
                    
                else:
                    self.logger.debug("SSDP scanner not available")
                    
            except Exception as e:
                self.logger.warning(f"SSDP discovery failed: {e}")
        else:
            self.logger.debug("SSDP scanner not initialized")
        
        return discovered_hosts
    
    # Phase 4 Helper Methods (Service Discovery)
    async def _snmp_community_probing(self, hosts: List[str], scan_id: str) -> List[str]:
        """Step 12: SNMP Community Probing."""
        discovered_hosts = []
        if hasattr(self, 'snmp_scanner') and self.snmp_scanner:
            try:
                # TODO: Implement SNMP community string testing
                self.logger.debug("SNMP community probing - using existing scanner")
            except Exception as e:
                self.logger.warning(f"SNMP probing failed: {e}")
        return discovered_hosts
    
    async def _protocol_fingerprinting(self, hosts: List[str], scan_id: str) -> Dict[str, Any]:
        """Step 13: Protocol Fingerprinting (stub)."""
        self.logger.debug("Protocol fingerprinting - stub implementation")
        # TODO: Implement banner grabbing, SSL cert analysis, etc.
        return {'fingerprints': []}
    
    # Phase 5 Helper Methods (Device Correlation)
    async def _multi_vector_device_correlation(self, hosts: List[str], scan_id: str) -> Dict[str, Any]:
        """Step 14: Multi-Vector Device Correlation (stub)."""
        self.logger.debug("Multi-vector device correlation - stub implementation")
        # TODO: Implement device profiling and correlation
        return {'correlations': []}
    
    async def _network_topology_mapping(self, hosts: List[str], scan_id: str) -> Dict[str, Any]:
        """Step 15: Network Topology Mapping (stub)."""
        self.logger.debug("Network topology mapping - stub implementation")
        # TODO: Implement CDP/LLDP discovery, switch mapping
        return {'topology': {}}
    
    async def _environmental_context_application(self, hosts: List[str], scan_id: str) -> Dict[str, Any]:
        """Step 16: Environmental Context Application (stub)."""
        self.logger.debug("Environmental context application - stub implementation")
        # TODO: Apply location-based device classification
        return {'context_applied': []}
    
    # Phase 6 Helper Methods (Analysis Preparation)
    async def _authentication_opportunity_identification(self, hosts: List[str], scan_id: str) -> List[Dict[str, Any]]:
        """Step 17: Authentication Opportunity Identification (stub)."""
        self.logger.debug("Authentication opportunity identification - stub implementation")
        # TODO: Identify devices with default credentials, open auth, etc.
        return []
    
    async def _anomaly_and_security_flagging(self, hosts: List[str], scan_id: str) -> List[Dict[str, Any]]:
        """Step 18: Anomaly and Security Flagging (stub)."""
        self.logger.debug("Anomaly and security flagging - stub implementation")
        # TODO: Identify security issues, unusual configurations
        return []
    
    async def _scan_result_consolidation(self, hosts: List[str], scan_id: str) -> Dict[str, Any]:
        """Step 19: Scan Result Consolidation."""
        self.logger.debug("Consolidating scan results...")
        
        consolidation = {
            'total_hosts': len(hosts),
            'phases_completed': list(self.completed_phases),
            'phase_results': self.phase_results,
            'statistics': self.stats.copy(),
            'scan_id': scan_id,
            'timestamp': datetime.now().isoformat()
        }
        
        return consolidation
