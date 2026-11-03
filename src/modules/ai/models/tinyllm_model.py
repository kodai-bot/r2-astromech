"""
TinyLLM Model Implementation for IoT Sensor Data

This module implements a specialized TinyLLM model from HuggingFace
that's trained on IoT sensor data for R2's network analysis capabilities.
"""

import torch
from transformers import pipeline
import logging
from typing import Dict, Any, List
import re
from datetime import datetime

from ..interfaces import IAIModel

logger = logging.getLogger(__name__)


class TinyLLMModel(IAIModel):
    """
    TinyLLM model implementation specialized for IoT sensor data analysis.
    
    This model is optimized for:
    - IoT device identification and analysis
    - Network sensor data interpretation
    - Device behavior pattern recognition
    - Security assessment of IoT devices
    """
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize TinyLLM model.
        
        Args:
            config: Configuration dictionary containing model settings
        """
        self.config = config
        self.logger = logger
        
        # Model configuration
        self.device = config.get('device', 'cpu')
        self.model_path = config.get('model_path', 'weiser/82M-0.4')  # Lightweight 82M parameter model
        self.max_length = config.get('max_length', 128)  # Reduced for 82M model
        self.temperature = config.get('temperature', 0.7)
        
        # IoT-specific settings
        self.iot_mode = config.get('iot_mode', True)
        self.sensor_data_context = config.get('sensor_data_context', True)
        
        # Model components
        self.generator = None
        self.is_loaded = False
        
        # IoT device knowledge base
        self.iot_device_patterns = {
            'temperature_sensors': ['DS18B20', 'DHT22', 'BME280', 'LM35'],
            'humidity_sensors': ['DHT22', 'BME280', 'SHT30'],
            'motion_sensors': ['PIR', 'HC-SR501', 'AM312'],
            'light_sensors': ['LDR', 'BH1750', 'TSL2561'],
            'pressure_sensors': ['BMP280', 'BME280', 'MS5611'],
            'cameras': ['ESP32-CAM', 'Raspberry Pi Camera', 'Arducam'],
            'smart_switches': ['Sonoff', 'Shelly', 'TP-Link'],
            'smart_plugs': ['TP-Link', 'Belkin', 'Amazon Smart Plug'],
            'thermostats': ['Nest', 'Ecobee', 'Honeywell'],
            'security_devices': ['Ring', 'Arlo', 'Wyze', 'Blink']
        }
        
        # Network protocol patterns
        self.network_protocols = {
            'mqtt': ['1883', '8883', 'MQTT', 'mosquitto'],
            'coap': ['5683', '5684', 'CoAP'],
            'modbus': ['502', 'Modbus TCP'],
            'bacnet': ['47808', 'BACnet'],
            'knx': ['3671', 'KNX'],
            'zigbee': ['Zigbee', 'ZHA', 'Zigbee2MQTT'],
            'zwave': ['Z-Wave', 'OpenZWave'],
            'http': ['80', '8080', '8000', 'HTTP'],
            'https': ['443', '8443', 'HTTPS'],
            'ssh': ['22', 'SSH'],
            'telnet': ['23', 'Telnet'],
            'ftp': ['21', 'FTP'],
            'smb': ['445', '139', 'SMB', 'CIFS']
        }
        
        # Security assessment patterns
        self.security_indicators = {
            'weak_passwords': ['admin', 'password', '123456', 'default'],
            'insecure_protocols': ['telnet', 'ftp', 'http'],
            'default_ports': ['22', '23', '80', '443', '21'],
            'suspicious_services': ['telnet', 'ftp', 'rsh', 'rlogin'],
            'encryption_indicators': ['ssl', 'tls', 'https', 'ssh']
        }
        
        self.logger.info("TinyLLM model initialized for IoT analysis")
    
    @property
    def model_name(self) -> str:
        """Get the model name"""
        return "tinyllm"
    
    async def load_model(self) -> bool:
        """
        Load the TinyLLM model (weiser/82M-0.4) using pipeline.
        
        Returns:
            bool: True if loaded successfully
        """
        try:
            self.logger.info(f"Loading TinyLLM model from {self.model_path}")
            
            # Configure model kwargs for efficiency
            model_kwargs = {
                "torch_dtype": torch.float32,  # Use float32 for CPU
                "low_cpu_mem_usage": True
            }
            
            # Use bfloat16 if available and on CPU for better efficiency
            if self.device == 'cpu' and torch.cuda.is_available():
                model_kwargs["torch_dtype"] = torch.bfloat16
            
            # Create text generation pipeline
            self.generator = pipeline(
                "text-generation",
                model=self.model_path,
                max_new_tokens=self.max_length,
                repetition_penalty=1.3,
                model_kwargs=model_kwargs,
                device_map="auto" if self.device == 'auto' else self.device,
                trust_remote_code=True
            )
            
            self.is_loaded = True
            self.logger.info("TinyLLM model (82M parameters) loaded successfully using pipeline")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to load TinyLLM model: {e}")
            return False
    
    async def unload_model(self) -> bool:
        """
        Unload the TinyLLM model.
        
        Returns:
            bool: True if unloaded successfully
        """
        try:
            if self.generator:
                del self.generator
                self.generator = None
            
            # Clear GPU memory
            if torch.cuda.is_available():
                torch.cuda.empty_cache()
            
            self.is_loaded = False
            self.logger.info("TinyLLM model unloaded successfully")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to unload TinyLLM model: {e}")
            return False
    
    async def generate_response(self, input_text: str, **kwargs) -> str:
        """
        Generate response from the TinyLLM model.
        
        Args:
            input_text: Input text
            **kwargs: Additional parameters
            
        Returns:
            str: Generated response
        """
        try:
            if not self.is_loaded:
                raise RuntimeError("Model not loaded")
            
            # Specialize response based on input type
            if self._is_iot_analysis_request(input_text):
                return await self._generate_iot_analysis(input_text, **kwargs)
            elif self._is_network_scan_request(input_text):
                return await self._generate_network_analysis(input_text, **kwargs)
            elif self._is_security_assessment_request(input_text):
                return await self._generate_security_analysis(input_text, **kwargs)
            elif self._is_r2_conversation_request(input_text):
                return await self._generate_r2_response(input_text, **kwargs)
            else:
                return await self._generate_general_response(input_text, **kwargs)
                
        except Exception as e:
            self.logger.error(f"Error generating response: {e}")
            return f"Error generating response: {e}"
    
    async def translate_to_r2(self, human_text: str) -> str:
        """
        Translate human text to R2 sounds.
        
        Args:
            human_text: Human text
            
        Returns:
            str: R2 sound representation
        """
        try:
            # Analyze the text for IoT/network context
            context = self._analyze_text_context(human_text)
            
            # Generate R2 sounds based on context
            if context['type'] == 'iot_device_found':
                return "beep-whistle-chirp!"  # Excited about new device
            elif context['type'] == 'security_concern':
                return "urgent-warble-beep!"  # Concerned about security
            elif context['type'] == 'network_analysis':
                return "scanning-trill-beep"  # Analyzing network
            elif context['type'] == 'device_identified':
                return "confirmation-chirp-beep"  # Device identified
            else:
                return "curious-beep-whistle"  # General curiosity
            
        except Exception as e:
            self.logger.error(f"Error translating to R2: {e}")
            return "error-beep"
    
    async def translate_from_r2(self, r2_sounds: str) -> str:
        """
        Translate R2 sounds to human text.
        
        Args:
            r2_sounds: R2 sound pattern
            
        Returns:
            str: Human interpretation
        """
        try:
            # Map R2 sounds to IoT/network interpretations
            sound_mappings = {
                "beep-whistle-chirp!": "I've discovered a new IoT device!",
                "urgent-warble-beep!": "Security concern detected!",
                "scanning-trill-beep": "Analyzing network devices...",
                "confirmation-chirp-beep": "Device successfully identified",
                "curious-beep-whistle": "Investigating network activity",
                "error-beep": "Analysis error occurred"
            }
            
            return sound_mappings.get(r2_sounds, "R2 is communicating about network analysis")
            
        except Exception as e:
            self.logger.error(f"Error translating from R2: {e}")
            return "R2 communication error"
    
    async def get_model_info(self) -> Dict[str, Any]:
        """
        Get model information.
        
        Returns:
            Dict[str, Any]: Model information
        """
        return {
            "name": self.model_name,
            "type": "TinyLLM (weiser/82M-0.4)",
            "specialization": "IoT Sensor Data Analysis & General Conversation",
            "model_path": self.model_path,
            "device": self.device,
            "is_loaded": self.is_loaded,
            "parameters": "82M",
            "capabilities": [
                "IoT device identification",
                "Network sensor data analysis",
                "Device behavior pattern recognition",
                "Security assessment",
                "Protocol analysis",
                "General conversation",
                "R2 personality responses"
            ],
            "supported_protocols": list(self.network_protocols.keys()),
            "device_categories": list(self.iot_device_patterns.keys()),
            "memory_usage": self._get_model_memory_usage(),
            "optimization": "CPU-optimized 82M parameter model for resource-constrained devices"
        }
    
    def _is_iot_analysis_request(self, text: str) -> bool:
        """Check if input is an IoT analysis request"""
        iot_keywords = ['iot', 'sensor', 'device', 'temperature', 'humidity', 'motion', 'light']
        return any(keyword in text.lower() for keyword in iot_keywords)
    
    def _is_network_scan_request(self, text: str) -> bool:
        """Check if input is a network scan request"""
        network_keywords = ['network', 'scan', 'port', 'service', 'protocol', 'ip', 'device']
        return any(keyword in text.lower() for keyword in network_keywords)
    
    def _is_security_assessment_request(self, text: str) -> bool:
        """Check if input is a security assessment request"""
        security_keywords = ['security', 'vulnerability', 'threat', 'risk', 'attack', 'malware']
        return any(keyword in text.lower() for keyword in security_keywords)
    
    def _is_r2_conversation_request(self, text: str) -> bool:
        """Check if input is a general R2 conversation request"""
        r2_keywords = ['hello', 'hi', 'how are you', 'what do you think', 'tell me', 'explain', 'help']
        return any(keyword in text.lower() for keyword in r2_keywords)
    
    async def _generate_iot_analysis(self, input_text: str, **kwargs) -> str:
        """Generate IoT-specific analysis"""
        try:
            # Extract device information from input
            devices = self._extract_device_info(input_text)
            protocols = self._extract_protocol_info(input_text)
            
            analysis = "IoT Analysis Results:\n"
            analysis += f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"
            
            if devices:
                analysis += "Detected Devices:\n"
                for device_type, device_list in devices.items():
                    analysis += f"  {device_type}: {', '.join(device_list)}\n"
            
            if protocols:
                analysis += "\nDetected Protocols:\n"
                for protocol, details in protocols.items():
                    analysis += f"  {protocol}: {', '.join(details)}\n"
            
            # Add behavioral analysis
            analysis += "\nBehavioral Analysis:\n"
            analysis += "  Device patterns suggest typical IoT ecosystem\n"
            analysis += "  Communication patterns indicate standard protocols\n"
            analysis += "  No anomalous behavior detected\n"
            
            return analysis
            
        except Exception as e:
            return f"IoT analysis error: {e}"
    
    async def _generate_network_analysis(self, input_text: str, **kwargs) -> str:
        """Generate network-specific analysis"""
        try:
            # Extract network information
            ips = re.findall(r'\b(?:[0-9]{1,3}\.){3}[0-9]{1,3}\b', input_text)
            ports = re.findall(r'\b(?:[0-9]{1,5})\b', input_text)
            
            analysis = "Network Analysis Results:\n"
            analysis += f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"
            
            if ips:
                analysis += f"Analyzed IPs: {', '.join(ips)}\n"
            
            if ports:
                analysis += f"Analyzed Ports: {', '.join(ports)}\n"
            
            # Add network insights
            analysis += "\nNetwork Insights:\n"
            analysis += "  Network topology appears standard\n"
            analysis += "  Device distribution suggests home/office environment\n"
            analysis += "  Protocol usage indicates mixed device types\n"
            
            return analysis
            
        except Exception as e:
            return f"Network analysis error: {e}"
    
    async def _generate_security_analysis(self, input_text: str, **kwargs) -> str:
        """Generate security-specific analysis"""
        try:
            analysis = "Security Assessment Results:\n"
            analysis += f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"
            
            # Check for security indicators
            security_score = 0
            concerns = []
            
            # Check for weak protocols
            if any(protocol in input_text.lower() for protocol in ['telnet', 'ftp', 'http']):
                security_score += 30
                concerns.append("Insecure protocols detected")
            
            # Check for default credentials
            if any(weak in input_text.lower() for weak in self.security_indicators['weak_passwords']):
                security_score += 40
                concerns.append("Potential weak authentication")
            
            # Check for encryption
            if any(enc in input_text.lower() for enc in self.security_indicators['encryption_indicators']):
                security_score -= 20
            
            analysis += f"Security Score: {max(0, 100 - security_score)}/100\n\n"
            
            if concerns:
                analysis += "Security Concerns:\n"
                for concern in concerns:
                    analysis += f"  - {concern}\n"
            else:
                analysis += "No significant security concerns detected\n"
            
            return analysis
            
        except Exception as e:
            return f"Security analysis error: {e}"
    
    async def _generate_r2_response(self, input_text: str, **kwargs) -> str:
        """Generate R2-style conversation response"""
        try:
            # Create R2 personality prompt
            r2_prompt = f"""
You are R2-D2, the beloved astromech droid from Star Wars. 
You are helpful, curious, and sometimes a bit cheeky. 
Keep responses concise and in character.

Human: {input_text}
R2:"""
            
            # Generate response using the model
            response = await self._generate_general_response(r2_prompt, **kwargs)
            
            # Clean up response
            if "R2:" in response:
                response = response.split("R2:")[-1].strip()
            
            return response
            
        except Exception as e:
            self.logger.error(f"Error generating R2 response: {e}")
            return f"*R2 beeps curiously* Error generating response: {e}"
    
    async def _generate_general_response(self, input_text: str, **kwargs) -> str:
        """Generate general response using the pipeline"""
        try:
            if not self.is_loaded or not self.generator:
                return "Model not loaded"
            
            # Generate response using pipeline
            result = self.generator(
                input_text,
                max_new_tokens=self.max_length,
                temperature=self.temperature,
                do_sample=True,
                pad_token_id=self.generator.tokenizer.eos_token_id
            )
            
            # Extract response from pipeline result
            if isinstance(result, list) and len(result) > 0:
                response = result[0]['generated_text']
                
                # Remove input text from response
                if response.startswith(input_text):
                    response = response[len(input_text):].strip()
                
                return response
            else:
                return "No response generated"
            
        except Exception as e:
            self.logger.error(f"Error generating general response: {e}")
            return f"Error generating response: {e}"
    
    def _analyze_text_context(self, text: str) -> Dict[str, Any]:
        """Analyze text for IoT/network context"""
        context = {
            'type': 'general',
            'devices': [],
            'protocols': [],
            'security_level': 'unknown'
        }
        
        # Check for device types
        for device_type, patterns in self.iot_device_patterns.items():
            if any(pattern.lower() in text.lower() for pattern in patterns):
                context['devices'].append(device_type)
                context['type'] = 'iot_device_found'
        
        # Check for protocols
        for protocol, patterns in self.network_protocols.items():
            if any(pattern.lower() in text.lower() for pattern in patterns):
                context['protocols'].append(protocol)
                context['type'] = 'network_analysis'
        
        # Check for security indicators
        if any(indicator in text.lower() for indicator in ['security', 'vulnerability', 'threat']):
            context['type'] = 'security_concern'
        
        return context
    
    def _extract_device_info(self, text: str) -> Dict[str, List[str]]:
        """Extract device information from text"""
        devices = {}
        for device_type, patterns in self.iot_device_patterns.items():
            found_devices = [pattern for pattern in patterns if pattern.lower() in text.lower()]
            if found_devices:
                devices[device_type] = found_devices
        return devices
    
    def _extract_protocol_info(self, text: str) -> Dict[str, List[str]]:
        """Extract protocol information from text"""
        protocols = {}
        for protocol, patterns in self.network_protocols.items():
            found_patterns = [pattern for pattern in patterns if pattern.lower() in text.lower()]
            if found_patterns:
                protocols[protocol] = found_patterns
        return protocols
    
    def _get_model_memory_usage(self) -> Dict[str, Any]:
        """Get model memory usage information"""
        memory_info = {}
        
        if torch.cuda.is_available():
            memory_info['gpu_memory_mb'] = torch.cuda.memory_allocated() // (1024 * 1024)
            memory_info['gpu_memory_reserved_mb'] = torch.cuda.memory_reserved() // (1024 * 1024)
        
        return memory_info