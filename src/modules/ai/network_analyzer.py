"""
Modular Network Analysis AI Module

This module provides intelligent analysis of network scan results using AI models.
It acts as a bridge between the network scanner and AI models, providing
contextual analysis and insights.
"""

import asyncio
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime
import json

from ...core.interfaces import IModule, ModuleStatus
from ...core.events import EventBus, create_event, R2Events
from ..ai.interfaces import INetworkAnalyzer
from ...utils.exceptions import R2AIException, R2ModuleException
from ...utils.logging import get_module_logger

logger = get_module_logger("ai.network_analyzer")


class ModularNetworkAnalyzer(INetworkAnalyzer):
    """
    Modular Network Analysis AI implementation
    
    This analyzer uses AI models to provide intelligent analysis of network
    scan results, device behavior patterns, and security assessments.
    """
    
    def __init__(self, event_bus: EventBus, config: Dict[str, Any]):
        """
        Initialize the modular network analyzer.
        
        Args:
            event_bus: Event bus for communication
            config: Analyzer configuration
        """
        self.event_bus = event_bus
        self.config = config
        self.logger = logger
        
        # Analyzer state
        self.is_running = False
        self.ai_manager = None  # Will be injected
        self.analysis_history: List[Dict[str, Any]] = []
        
        # Analysis configuration
        self.max_history = config.get('max_history', 50)
        self.auto_analyze = config.get('auto_analyze', True)
        self.security_threshold = config.get('security_threshold', 70)
        
        # Analysis templates
        self.analysis_templates = {
            'device_summary': self._create_device_summary_template(),
            'security_assessment': self._create_security_assessment_template(),
            'network_overview': self._create_network_overview_template(),
            'iot_analysis': self._create_iot_analysis_template(),
            'behavioral_analysis': self._create_behavioral_analysis_template()
        }
        
        self.logger.info("Modular Network Analyzer initialized")
    
    @property
    def module_name(self) -> str:
        """Get the module name"""
        return "network_analyzer"
    
    async def initialize(self) -> bool:
        """Initialize the network analyzer"""
        try:
            self.logger.info("Initializing network analyzer...")
            
            # Subscribe to relevant events
            await self.event_bus.subscribe(R2Events.SYSTEM_STARTUP, self._on_system_startup)
            await self.event_bus.subscribe(R2Events.SYSTEM_SHUTDOWN, self._on_system_shutdown)
            await self.event_bus.subscribe("network.scan_completed", self._on_scan_completed)
            await self.event_bus.subscribe("network.device_discovered", self._on_device_discovered)
            await self.event_bus.subscribe("ai.analysis_requested", self._on_analysis_requested)
            
            self.logger.info("Network analyzer initialized successfully")
            return True
            
        except Exception as e:
            self.logger.error(f"Network analyzer initialization failed: {e}")
            return False
    
    async def start(self) -> bool:
        """Start the network analyzer"""
        try:
            self.logger.info("Starting network analyzer...")
            
            # Publish module started event
            await self.event_bus.publish(create_event(
                R2Events.MODULE_STARTED,
                {
                    "module": self.module_name,
                    "capabilities": [
                        "device_analysis", 
                        "security_assessment", 
                        "behavioral_analysis",
                        "iot_identification",
                        "network_intelligence"
                    ]
                },
                self.module_name
            ))
            
            self.is_running = True
            self.logger.info("Network analyzer started successfully")
            return True
            
        except Exception as e:
            self.logger.error(f"Network analyzer start failed: {e}")
            return False
    
    async def stop(self) -> bool:
        """Stop the network analyzer"""
        try:
            self.logger.info("Stopping network analyzer...")
            
            # Publish module stopped event
            await self.event_bus.publish(create_event(
                R2Events.MODULE_STOPPED,
                {"module": self.module_name, "analysis_count": len(self.analysis_history)},
                self.module_name
            ))
            
            self.is_running = False
            self.logger.info("Network analyzer stopped successfully")
            return True
            
        except Exception as e:
            self.logger.error(f"Network analyzer stop failed: {e}")
            return False
    
    async def get_status(self) -> ModuleStatus:
        """Get current module status"""
        return ModuleStatus(
            name=self.module_name,
            status='running' if self.is_running else 'stopped',
            health_score=1.0,
            last_heartbeat=datetime.now(),
            memory_usage_mb=None
        )
    
    async def health_check(self) -> bool:
        """Perform health check"""
        return self.is_running and self.ai_manager is not None
    
    async def cleanup(self) -> bool:
        """Cleanup network analyzer resources"""
        try:
            self.logger.info("Cleaning up network analyzer...")
            self.analysis_history.clear()
            self.logger.info("Network analyzer cleanup complete")
            return True
            
        except Exception as e:
            self.logger.error(f"Network analyzer cleanup failed: {e}")
            return False
    
    def set_ai_manager(self, ai_manager) -> None:
        """Set the AI manager reference"""
        self.ai_manager = ai_manager
    
    async def analyze_discovered_devices(self, devices: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Analyze discovered network devices using AI.
        
        Args:
            devices: List of discovered devices
            
        Returns:
            Dict[str, Any]: Analysis results including R2 response
        """
        try:
            self.logger.info(f"Analyzing {len(devices)} discovered devices")
            
            # Publish analysis started event
            await self.event_bus.publish(create_event(
                R2Events.AI_ANALYSIS_STARTED,
                {"device_count": len(devices), "analysis_type": "device_discovery"},
                self.module_name
            ))
            
            # Create comprehensive analysis
            analysis_results = {
                'timestamp': datetime.now().isoformat(),
                'device_count': len(devices),
                'analysis_type': 'device_discovery',
                'summary': await self._generate_network_summary(devices),
                'device_analysis': await self._analyze_individual_devices(devices),
                'security_assessment': await self._assess_network_security(devices),
                'iot_identification': await self._identify_iot_devices(devices),
                'behavioral_patterns': await self._analyze_behavioral_patterns(devices),
                'r2_insights': await self._generate_r2_insights(devices),
                'recommendations': await self._generate_recommendations(devices)
            }
            
            # Store analysis in history
            self.analysis_history.append(analysis_results)
            if len(self.analysis_history) > self.max_history:
                self.analysis_history = self.analysis_history[-self.max_history:]
            
            # Publish analysis completed event
            await self.event_bus.publish(create_event(
                R2Events.AI_ANALYSIS_COMPLETED,
                {
                    "device_count": len(devices),
                    "analysis_type": "device_discovery",
                    "insights_generated": len(analysis_results.get('r2_insights', [])),
                    "recommendations": len(analysis_results.get('recommendations', []))
                },
                self.module_name
            ))
            
            return analysis_results
            
        except Exception as e:
            self.logger.error(f"Device analysis failed: {e}")
            raise R2AIException(f"Device analysis failed: {e}")
    
    async def analyze_network_issue(self, device_data: str, symptoms: str) -> Dict[str, Any]:
        """
        Diagnose a network issue using AI.
        
        Args:
            device_data: Device information
            symptoms: Description of symptoms
            
        Returns:
            Dict[str, Any]: Diagnosis results
        """
        try:
            self.logger.info("Analyzing network issue")
            
            # Create diagnostic prompt
            diagnostic_prompt = f"""
Network Issue Diagnosis Request:
Device Data: {device_data}
Symptoms: {symptoms}

Please analyze this network issue and provide:
1. Likely cause of the problem
2. Severity assessment
3. Recommended troubleshooting steps
4. Preventive measures
"""
            
            # Use AI to analyze the issue
            if self.ai_manager:
                diagnosis = await self.ai_manager.generate_response(diagnostic_prompt)
            else:
                diagnosis = "AI analysis unavailable - no model loaded"
            
            # Create diagnosis results
            diagnosis_results = {
                'timestamp': datetime.now().isoformat(),
                'analysis_type': 'network_issue',
                'device_data': device_data,
                'symptoms': symptoms,
                'diagnosis': diagnosis,
                'severity': self._assess_issue_severity(symptoms),
                'recommended_actions': self._generate_troubleshooting_steps(symptoms)
            }
            
            # Store in history
            self.analysis_history.append(diagnosis_results)
            
            return diagnosis_results
            
        except Exception as e:
            self.logger.error(f"Network issue analysis failed: {e}")
            raise R2AIException(f"Network issue analysis failed: {e}")
    
    async def assess_security_posture(self, devices: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Perform security assessment of network devices.
        
        Args:
            devices: List of devices to assess
            
        Returns:
            Dict[str, Any]: Security assessment results
        """
        try:
            self.logger.info(f"Assessing security posture of {len(devices)} devices")
            
            # Analyze security aspects
            security_analysis = {
                'timestamp': datetime.now().isoformat(),
                'analysis_type': 'security_assessment',
                'device_count': len(devices),
                'overall_risk_score': 0,
                'vulnerabilities': [],
                'security_recommendations': [],
                'device_security_scores': {},
                'network_security_summary': ''
            }
            
            total_risk = 0
            for device in devices:
                device_security = await self._assess_device_security(device)
                security_analysis['device_security_scores'][device.get('ip', 'unknown')] = device_security
                total_risk += device_security.get('risk_score', 0)
                
                # Collect vulnerabilities
                if device_security.get('vulnerabilities'):
                    security_analysis['vulnerabilities'].extend(device_security['vulnerabilities'])
            
            # Calculate overall risk score
            security_analysis['overall_risk_score'] = total_risk / len(devices) if devices else 0
            
            # Generate security recommendations
            security_analysis['security_recommendations'] = await self._generate_security_recommendations(
                security_analysis['vulnerabilities'], 
                security_analysis['overall_risk_score']
            )
            
            # Generate network security summary
            security_analysis['network_security_summary'] = await self._generate_security_summary(security_analysis)
            
            # Store in history
            self.analysis_history.append(security_analysis)
            
            return security_analysis
            
        except Exception as e:
            self.logger.error(f"Security assessment failed: {e}")
            raise R2AIException(f"Security assessment failed: {e}")
    
    async def get_analysis_history(self, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Get recent analysis history.
        
        Args:
            limit: Maximum number of analyses to return
            
        Returns:
            List[Dict[str, Any]]: Recent analyses
        """
        return self.analysis_history[-limit:] if self.analysis_history else []
    
    async def _generate_network_summary(self, devices: List[Dict[str, Any]]) -> str:
        """Generate a comprehensive network summary"""
        if not self.ai_manager:
            return "AI analysis unavailable"
        
        # Create summary prompt
        device_summary = self._create_device_summary_data(devices)
        summary_prompt = f"""
Network Discovery Summary:
{device_summary}

Please provide a comprehensive analysis of this network environment, including:
1. Network topology assessment
2. Device type distribution
3. Service patterns
4. Potential IoT devices
5. Security observations
6. R2's perspective on the environment
"""
        
        return await self.ai_manager.generate_response(summary_prompt)
    
    async def _analyze_individual_devices(self, devices: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Analyze individual devices"""
        device_analyses = []
        
        for device in devices:
            device_analysis = {
                'ip': device.get('ip'),
                'device_type': device.get('device_type', 'unknown'),
                'manufacturer': device.get('manufacturer', 'unknown'),
                'open_ports': device.get('open_ports', []),
                'services': device.get('services', {}),
                'ai_insights': await self._generate_device_insights(device),
                'security_notes': await self._generate_security_notes(device)
            }
            device_analyses.append(device_analysis)
        
        return device_analyses
    
    async def _assess_network_security(self, devices: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Assess overall network security"""
        security_issues = []
        secure_devices = 0
        
        for device in devices:
            device_security = await self._assess_device_security(device)
            if device_security.get('risk_score', 0) > self.security_threshold:
                security_issues.append({
                    'ip': device.get('ip'),
                    'issues': device_security.get('vulnerabilities', []),
                    'risk_score': device_security.get('risk_score', 0)
                })
            else:
                secure_devices += 1
        
        return {
            'total_devices': len(devices),
            'secure_devices': secure_devices,
            'devices_with_issues': len(security_issues),
            'security_issues': security_issues,
            'overall_security_score': (secure_devices / len(devices) * 100) if devices else 100
        }
    
    async def _identify_iot_devices(self, devices: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Identify potential IoT devices"""
        iot_devices = []
        
        for device in devices:
            if self._is_potential_iot_device(device):
                iot_analysis = {
                    'ip': device.get('ip'),
                    'device_type': device.get('device_type'),
                    'manufacturer': device.get('manufacturer'),
                    'iot_indicators': self._get_iot_indicators(device),
                    'protocols': self._get_iot_protocols(device),
                    'security_concerns': self._get_iot_security_concerns(device)
                }
                iot_devices.append(iot_analysis)
        
        return iot_devices
    
    async def _analyze_behavioral_patterns(self, devices: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze behavioral patterns across devices"""
        patterns = {
            'service_patterns': {},
            'port_patterns': {},
            'manufacturer_distribution': {},
            'device_type_distribution': {},
            'communication_patterns': []
        }
        
        # Analyze patterns
        for device in devices:
            # Service patterns
            services = device.get('services', {})
            for port, service in services.items():
                patterns['service_patterns'][service] = patterns['service_patterns'].get(service, 0) + 1
            
            # Port patterns
            ports = device.get('open_ports', [])
            for port in ports:
                patterns['port_patterns'][port] = patterns['port_patterns'].get(port, 0) + 1
            
            # Manufacturer distribution
            manufacturer = device.get('manufacturer', 'unknown')
            patterns['manufacturer_distribution'][manufacturer] = patterns['manufacturer_distribution'].get(manufacturer, 0) + 1
            
            # Device type distribution
            device_type = device.get('device_type', 'unknown')
            patterns['device_type_distribution'][device_type] = patterns['device_type_distribution'].get(device_type, 0) + 1
        
        return patterns
    
    async def _generate_r2_insights(self, devices: List[Dict[str, Any]]) -> List[str]:
        """Generate R2-style insights"""
        insights = []
        
        if not self.ai_manager:
            return ["AI analysis unavailable"]
        
        # Create insights prompt
        insights_prompt = f"""
As R2-D2, provide 3-5 insightful observations about this network environment:
{self._create_device_summary_data(devices)}

Focus on:
- Interesting device discoveries
- Potential security concerns
- Network topology insights
- IoT device observations
- R2's perspective on the environment

Respond in R2's characteristic style - helpful, curious, and sometimes cheeky.
"""
        
        ai_response = await self.ai_manager.generate_response(insights_prompt)
        
        # Split response into individual insights
        insights = [insight.strip() for insight in ai_response.split('\n') if insight.strip()]
        
        return insights[:5]  # Limit to 5 insights
    
    async def _generate_recommendations(self, devices: List[Dict[str, Any]]) -> List[str]:
        """Generate actionable recommendations"""
        recommendations = []
        
        # Security recommendations
        security_assessment = await self._assess_network_security(devices)
        if security_assessment['overall_security_score'] < 80:
            recommendations.append("Consider implementing stronger security measures for devices with open insecure ports")
        
        # IoT recommendations
        iot_devices = await self._identify_iot_devices(devices)
        if iot_devices:
            recommendations.append(f"Found {len(iot_devices)} potential IoT devices - ensure they're properly secured")
        
        # Network optimization recommendations
        if len(devices) > 20:
            recommendations.append("Large network detected - consider implementing network segmentation")
        
        return recommendations
    
    def _create_device_summary_data(self, devices: List[Dict[str, Any]]) -> str:
        """Create a summary data string for AI analysis"""
        summary_data = f"Network Scan Results - {len(devices)} devices discovered:\n\n"
        
        for i, device in enumerate(devices, 1):
            summary_data += f"Device {i}:\n"
            summary_data += f"  IP: {device.get('ip', 'unknown')}\n"
            summary_data += f"  Type: {device.get('device_type', 'unknown')}\n"
            summary_data += f"  Manufacturer: {device.get('manufacturer', 'unknown')}\n"
            summary_data += f"  Open Ports: {device.get('open_ports', [])}\n"
            summary_data += f"  Services: {device.get('services', {})}\n"
            summary_data += f"  Hostname: {device.get('hostname', 'unknown')}\n\n"
        
        return summary_data
    
    def _is_potential_iot_device(self, device: Dict[str, Any]) -> bool:
        """Determine if a device is likely an IoT device"""
        # IoT indicators
        iot_indicators = [
            'router', 'camera', 'sensor', 'thermostat', 'smart', 'iot',
            'hue', 'nest', 'ring', 'wyze', 'tp-link', 'belkin'
        ]
        
        device_type = device.get('device_type', '').lower()
        manufacturer = device.get('manufacturer', '').lower()
        hostname = device.get('hostname', '').lower()
        
        # Check for IoT indicators
        for indicator in iot_indicators:
            if indicator in device_type or indicator in manufacturer or indicator in hostname:
                return True
        
        # Check for IoT-specific ports
        iot_ports = [1883, 5683, 502, 47808, 3671]  # MQTT, CoAP, Modbus, BACnet, KNX
        open_ports = device.get('open_ports', [])
        if any(port in open_ports for port in iot_ports):
            return True
        
        return False
    
    def _get_iot_indicators(self, device: Dict[str, Any]) -> List[str]:
        """Get IoT indicators for a device"""
        indicators = []
        
        device_type = device.get('device_type', '').lower()
        manufacturer = device.get('manufacturer', '').lower()
        hostname = device.get('hostname', '').lower()
        
        if 'router' in device_type:
            indicators.append('Network infrastructure device')
        if 'camera' in device_type or 'camera' in hostname:
            indicators.append('Security camera')
        if 'sensor' in device_type or 'sensor' in hostname:
            indicators.append('Environmental sensor')
        if 'smart' in device_type or 'smart' in manufacturer:
            indicators.append('Smart home device')
        
        return indicators
    
    def _get_iot_protocols(self, device: Dict[str, Any]) -> List[str]:
        """Get IoT protocols detected on device"""
        protocols = []
        services = device.get('services', {})
        
        protocol_mapping = {
            1883: 'MQTT',
            8883: 'MQTT-SSL',
            5683: 'CoAP',
            502: 'Modbus',
            47808: 'BACnet',
            3671: 'KNX'
        }
        
        for port, service in services.items():
            if port in protocol_mapping:
                protocols.append(protocol_mapping[port])
        
        return protocols
    
    def _get_iot_security_concerns(self, device: Dict[str, Any]) -> List[str]:
        """Get security concerns for IoT device"""
        concerns = []
        services = device.get('services', {})
        
        # Check for insecure protocols
        insecure_ports = [21, 23, 80]  # FTP, Telnet, HTTP
        for port in insecure_ports:
            if port in services:
                concerns.append(f"Insecure protocol on port {port}: {services[port]}")
        
        return concerns
    
    async def _assess_device_security(self, device: Dict[str, Any]) -> Dict[str, Any]:
        """Assess security of individual device"""
        risk_score = 0
        vulnerabilities = []
        
        services = device.get('services', {})
        open_ports = device.get('open_ports', [])
        
        # Check for insecure services
        insecure_services = {
            21: 'FTP (insecure)',
            23: 'Telnet (insecure)',
            80: 'HTTP (insecure)',
            135: 'RPC (potentially insecure)',
            139: 'NetBIOS (insecure)',
            445: 'SMB (potentially insecure)'
        }
        
        for port, service in insecure_services.items():
            if port in open_ports:
                risk_score += 20
                vulnerabilities.append(f"Insecure service: {service} on port {port}")
        
        # Check for default/weak services
        if 22 in open_ports:  # SSH
            vulnerabilities.append("SSH service detected - ensure strong authentication")
            risk_score += 10
        
        # Calculate risk level
        if risk_score >= 80:
            risk_level = 'High'
        elif risk_score >= 50:
            risk_level = 'Medium'
        else:
            risk_level = 'Low'
        
        return {
            'risk_score': risk_score,
            'risk_level': risk_level,
            'vulnerabilities': vulnerabilities,
            'security_recommendations': self._get_device_security_recommendations(vulnerabilities)
        }
    
    def _get_device_security_recommendations(self, vulnerabilities: List[str]) -> List[str]:
        """Get security recommendations for device"""
        recommendations = []
        
        for vuln in vulnerabilities:
            if 'FTP' in vuln or 'Telnet' in vuln:
                recommendations.append("Replace insecure protocols with encrypted alternatives")
            elif 'HTTP' in vuln:
                recommendations.append("Enable HTTPS for web services")
            elif 'SSH' in vuln:
                recommendations.append("Implement key-based SSH authentication")
        
        return recommendations
    
    async def _generate_device_insights(self, device: Dict[str, Any]) -> str:
        """Generate AI insights for individual device"""
        if not self.ai_manager:
            return "AI analysis unavailable"
        
        device_info = f"""
Device Analysis:
IP: {device.get('ip')}
Type: {device.get('device_type', 'unknown')}
Manufacturer: {device.get('manufacturer', 'unknown')}
Open Ports: {device.get('open_ports', [])}
Services: {device.get('services', {})}
Hostname: {device.get('hostname', 'unknown')}

Provide insights about this device's role and characteristics.
"""
        
        return await self.ai_manager.generate_response(device_info)
    
    async def _generate_security_notes(self, device: Dict[str, Any]) -> str:
        """Generate security notes for device"""
        security_assessment = await self._assess_device_security(device)
        return f"Risk Level: {security_assessment['risk_level']} ({security_assessment['risk_score']}/100)"
    
    def _assess_issue_severity(self, symptoms: str) -> str:
        """Assess severity of network issue"""
        symptoms_lower = symptoms.lower()
        
        if any(word in symptoms_lower for word in ['down', 'offline', 'unreachable', 'critical']):
            return 'High'
        elif any(word in symptoms_lower for word in ['slow', 'intermittent', 'degraded']):
            return 'Medium'
        else:
            return 'Low'
    
    def _generate_troubleshooting_steps(self, symptoms: str) -> List[str]:
        """Generate troubleshooting steps based on symptoms"""
        steps = []
        
        symptoms_lower = symptoms.lower()
        
        if 'ping' in symptoms_lower:
            steps.extend([
                "Check network connectivity",
                "Verify IP address configuration",
                "Test with different network interface"
            ])
        
        if 'port' in symptoms_lower:
            steps.extend([
                "Verify service is running",
                "Check firewall settings",
                "Test port accessibility"
            ])
        
        if 'dns' in symptoms_lower:
            steps.extend([
                "Check DNS server configuration",
                "Test with different DNS servers",
                "Verify hostname resolution"
            ])
        
        return steps[:5]  # Limit to 5 steps
    
    async def _generate_security_recommendations(self, vulnerabilities: List[str], risk_score: float) -> List[str]:
        """Generate security recommendations"""
        recommendations = []
        
        if risk_score > 70:
            recommendations.append("Immediate security review required - high risk detected")
        
        if any('telnet' in vuln.lower() for vuln in vulnerabilities):
            recommendations.append("Replace Telnet with SSH for secure remote access")
        
        if any('ftp' in vuln.lower() for vuln in vulnerabilities):
            recommendations.append("Replace FTP with SFTP or FTPS for secure file transfer")
        
        if any('http' in vuln.lower() for vuln in vulnerabilities):
            recommendations.append("Enable HTTPS for all web services")
        
        return recommendations
    
    async def _generate_security_summary(self, security_analysis: Dict[str, Any]) -> str:
        """Generate security summary"""
        if not self.ai_manager:
            return "AI analysis unavailable"
        
        summary_prompt = f"""
Security Assessment Summary:
Overall Risk Score: {security_analysis['overall_risk_score']}/100
Devices Assessed: {security_analysis['device_count']}
Vulnerabilities Found: {len(security_analysis['vulnerabilities'])}

Provide a concise security summary and recommendations.
"""
        
        return await self.ai_manager.generate_response(summary_prompt)
    
    def _create_device_summary_template(self) -> str:
        """Create device summary template"""
        return """
Device Summary Template:
- IP Address: {ip}
- Device Type: {device_type}
- Manufacturer: {manufacturer}
- Open Ports: {open_ports}
- Services: {services}
- Security Status: {security_status}
"""
    
    def _create_security_assessment_template(self) -> str:
        """Create security assessment template"""
        return """
Security Assessment Template:
- Risk Score: {risk_score}/100
- Risk Level: {risk_level}
- Vulnerabilities: {vulnerabilities}
- Recommendations: {recommendations}
"""
    
    def _create_network_overview_template(self) -> str:
        """Create network overview template"""
        return """
Network Overview Template:
- Total Devices: {device_count}
- Device Types: {device_types}
- Services: {services}
- Security Score: {security_score}
- IoT Devices: {iot_count}
"""
    
    def _create_iot_analysis_template(self) -> str:
        """Create IoT analysis template"""
        return """
IoT Analysis Template:
- IoT Devices Found: {iot_count}
- Protocols Detected: {protocols}
- Security Concerns: {concerns}
- Recommendations: {recommendations}
"""
    
    def _create_behavioral_analysis_template(self) -> str:
        """Create behavioral analysis template"""
        return """
Behavioral Analysis Template:
- Service Patterns: {service_patterns}
- Communication Patterns: {communication_patterns}
- Device Distribution: {device_distribution}
- Anomalies: {anomalies}
"""
    
    async def _on_system_startup(self, event) -> None:
        """Handle system startup event"""
        self.logger.info("System startup detected")
    
    async def _on_system_shutdown(self, event) -> None:
        """Handle system shutdown event"""
        self.logger.info("System shutdown detected")
    
    async def _on_scan_completed(self, event) -> None:
        """Handle scan completed event"""
        if self.auto_analyze:
            devices = event.data.get('devices', [])
            if devices:
                self.logger.info(f"Auto-analyzing {len(devices)} discovered devices")
                try:
                    await self.analyze_discovered_devices(devices)
                except Exception as e:
                    self.logger.error(f"Auto-analysis failed: {e}")
    
    async def _on_device_discovered(self, event) -> None:
        """Handle device discovered event"""
        # Could implement real-time device analysis here
        pass
    
    async def _on_analysis_requested(self, event) -> None:
        """Handle analysis request event"""
        analysis_type = event.data.get('analysis_type')
        if analysis_type == 'devices':
            devices = event.data.get('devices', [])
            await self.analyze_discovered_devices(devices)
        elif analysis_type == 'security':
            devices = event.data.get('devices', [])
            await self.assess_security_posture(devices)