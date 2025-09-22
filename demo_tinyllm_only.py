#!/usr/bin/env python3
"""
R2-A1 TinyLLM Only Demo

This demo shows R2's AI capabilities using only the lightweight TinyLLM model,
optimized for resource-constrained devices.
"""

import asyncio
import sys
import os
import logging
import signal
from typing import List

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from src.core.container import DIContainer
from src.core.config import Configuration
from src.core.events import EventBus, create_event, R2Events
from src.modules.discovery.network_scanner import ModularNetworkScanner
from src.modules.ai.model_manager import ModularAIModelManager
from src.modules.ai.network_analyzer import ModularNetworkAnalyzer
from src.modules.personality.audio_engine import ModularAudioEngine
from src.modules.personality.text_output import TextOutputModule

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class R2TinyLLMDemo:
    """
    Demo of R2 using only the lightweight TinyLLM model
    
    This demo is optimized for resource-constrained devices and shows
    TinyLLM's capabilities for both IoT analysis and general conversation.
    """
    
    def __init__(self):
        """Initialize the demo"""
        self.container = DIContainer()
        self.config = None
        self.event_bus = None
        self.network_scanner = None
        self.ai_manager = None
        self.network_analyzer = None
        self.audio_engine = None
        self.text_output = None
        self.shutdown_requested = False
        
        # Set up signal handlers for graceful shutdown
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)
        
        logger.info("🤖 R2-D2 TinyLLM Demo initializing...")
    
    def _signal_handler(self, signum, frame):
        """Handle shutdown signals gracefully"""
        logger.info(f"🛑 Received signal {signum}, initiating graceful shutdown...")
        self.shutdown_requested = True
    
    async def initialize(self) -> bool:
        """Initialize the demo system"""
        try:
            logger.info("🔧 Initializing demo components...")
            
            # Initialize configuration
            self.config = Configuration(environment="development")
            
            # Register configuration in container
            self.container.register_factory(Configuration, lambda container: self.config)
            
            # Initialize event bus
            self.event_bus = await self.container.get_service(EventBus)
            
            # Get module configurations
            discovery_config = self.config.get_section('modules.discovery')
            discovery_config['debug_mode'] = True  # Enable debug mode
            discovery_config['scan_timeout'] = 30  # 30 second timeout
            discovery_config['ping_timeout'] = 2   # 2 second ping timeout
            
            ai_config = self.config.get_section('modules.ai')
            ai_config['debug_mode'] = True  # Enable debug mode
            ai_config['auto_load'] = False  # Manual model loading for demo
            
            personality_config = self.config.get_section('modules.personality')
            
            # Initialize modules
            self.network_scanner = ModularNetworkScanner(self.event_bus, discovery_config)
            self.ai_manager = ModularAIModelManager(self.event_bus, ai_config)
            self.network_analyzer = ModularNetworkAnalyzer(self.event_bus, ai_config)
            self.audio_engine = ModularAudioEngine(self.event_bus, personality_config)
            self.text_output = TextOutputModule(self.event_bus, {"enabled": True})
            
            # Set up AI manager reference in network analyzer
            self.network_analyzer.set_ai_manager(self.ai_manager)
            
            # Register modules with container
            self.container.register_module("network_scanner", self.network_scanner)
            self.container.register_module("ai_manager", self.ai_manager)
            self.container.register_module("network_analyzer", self.network_analyzer)
            self.container.register_module("audio_engine", self.audio_engine)
            self.container.register_module("text_output", self.text_output)
            
            logger.info("✅ Demo initialization complete")
            return True
            
        except Exception as e:
            logger.error(f"❌ Demo initialization failed: {e}")
            return False
    
    async def start(self) -> bool:
        """Start the demo system"""
        try:
            logger.info("🚀 Starting demo system...")
            
            # Initialize all modules
            if not await self.container.initialize_all_modules():
                logger.error("❌ Module initialization failed")
                return False
            
            # Start all modules
            if not await self.container.start_all_modules():
                logger.error("❌ Module startup failed")
                return False
            
            # Publish startup event
            await self.event_bus.publish(create_event(
                R2Events.SYSTEM_STARTUP,
                {"environment": "demo", "version": "2.0.0"},
                "demo_system"
            ))
            
            logger.info("🎉 R2-D2 TinyLLM Demo is operational!")
            return True
            
        except Exception as e:
            logger.error(f"❌ Demo startup failed: {e}")
            return False
    
    async def run_tinyllm_demo(self) -> None:
        """Run the TinyLLM demo"""
        try:
            print(f"\n🤖 R2-D2 TinyLLM Demo")
            print("=" * 60)
            print("This demo shows R2's lightweight AI capabilities:")
            print("• TinyLLM model optimized for resource-constrained devices")
            print("• IoT sensor data analysis")
            print("• General conversation with R2 personality")
            print("• Network analysis and security assessment")
            print("• R2 sound translation")
            print("=" * 60)
            
            # Step 1: Load TinyLLM model
            print(f"\n🧠 Step 1: Loading TinyLLM Model")
            print("-" * 40)
            
            print("Loading TinyLLM model (lightweight, CPU-optimized)...")
            success = await self.ai_manager.load_model('tinyllm')
            if success:
                print("✅ TinyLLM model loaded successfully")
                
                # Show model info
                model_status = await self.ai_manager.get_model_status()
                model_info = model_status.get('model_info', {})
                print(f"\n📋 Model Information:")
                print(f"   Name: {model_info.get('name', 'Unknown')}")
                print(f"   Type: {model_info.get('type', 'Unknown')}")
                print(f"   Specialization: {model_info.get('specialization', 'Unknown')}")
                print(f"   Device: {model_info.get('device', 'Unknown')}")
                print(f"   Optimization: {model_info.get('optimization', 'Unknown')}")
                
                capabilities = model_info.get('capabilities', [])
                print(f"\n🔧 Capabilities:")
                for capability in capabilities:
                    print(f"   • {capability}")
            else:
                print("❌ Failed to load TinyLLM model")
                return
            
            # Step 2: Test general conversation
            print(f"\n💬 Step 2: General Conversation Test")
            print("-" * 40)
            
            conversation_tests = [
                "Hello R2! How are you today?",
                "What do you think about network scanning?",
                "Can you help me understand IoT devices?",
                "Tell me about your capabilities"
            ]
            
            for test_input in conversation_tests:
                print(f"\n👤 Human: {test_input}")
                response = await self.ai_manager.generate_response(test_input)
                print(f"🤖 R2: {response}")
                
                # Test R2 sound translation
                r2_sounds = await self.ai_manager.translate_to_r2(test_input)
                print(f"🔊 R2 Sounds: {r2_sounds}")
                
                await asyncio.sleep(1)  # Brief pause
            
            # Step 3: Test IoT analysis
            print(f"\n🔬 Step 3: IoT Analysis Test")
            print("-" * 40)
            
            iot_tests = [
                "I found temperature sensors DS18B20 and humidity sensor DHT22 on the network",
                "The network scan shows MQTT broker on port 1883 and CoAP on port 5683",
                "Security assessment: found telnet on port 23 and weak password 'admin'",
                "Discovered smart home devices including Philips Hue bridge and Nest thermostat"
            ]
            
            for test_input in iot_tests:
                print(f"\n📡 IoT Data: {test_input}")
                response = await self.ai_manager.generate_response(test_input)
                print(f"🤖 R2 Analysis: {response}")
                
                # Test R2 sound translation
                r2_sounds = await self.ai_manager.translate_to_r2(test_input)
                print(f"🔊 R2 Sounds: {r2_sounds}")
                
                await asyncio.sleep(1)  # Brief pause
            
            # Step 4: Test network analysis
            print(f"\n🌐 Step 4: Network Analysis Test")
            print("-" * 40)
            
            print("Performing quick network scan...")
            devices = await self.network_scanner.scan_network()
            
            if devices:
                print(f"\n📊 Network Scan Results:")
                print(f"   Devices discovered: {len(devices)}")
                
                # Show discovered devices
                for i, device in enumerate(devices, 1):
                    ip = device.get('ip', 'unknown')
                    device_type = device.get('device_type', 'unknown')
                    manufacturer = device.get('manufacturer', 'unknown')
                    open_ports = device.get('open_ports', [])
                    
                    print(f"   {i}. {ip} - {device_type} ({manufacturer})")
                    if open_ports:
                        print(f"      Open Ports: {open_ports}")
                
                # AI analysis of discovered devices
                print(f"\n🧠 R2's AI Analysis:")
                analysis_results = await self.network_analyzer.analyze_discovered_devices(devices)
                
                # Show key insights
                insights = analysis_results.get('r2_insights', [])
                if insights:
                    print(f"\n💡 R2's Insights:")
                    for i, insight in enumerate(insights, 1):
                        print(f"   {i}. {insight}")
                
                # Show security assessment
                security_assessment = analysis_results.get('security_assessment', {})
                if security_assessment:
                    print(f"\n🔒 Security Assessment:")
                    print(f"   Overall Security Score: {security_assessment.get('overall_security_score', 0):.1f}/100")
                    print(f"   Secure Devices: {security_assessment.get('secure_devices', 0)}")
                    print(f"   Devices with Issues: {security_assessment.get('devices_with_issues', 0)}")
                
                # Show recommendations
                recommendations = analysis_results.get('recommendations', [])
                if recommendations:
                    print(f"\n💡 R2's Recommendations:")
                    for i, rec in enumerate(recommendations, 1):
                        print(f"   {i}. {rec}")
            else:
                print("   No devices found on this network")
            
            # Step 5: Show system status
            print(f"\n📊 Step 5: System Status")
            print("-" * 40)
            
            # Model status
            model_status = await self.ai_manager.get_model_status()
            print(f"🤖 AI Model Status:")
            print(f"   Current Model: {model_status.get('current_model', 'None')}")
            print(f"   Status: {model_status.get('status', 'Unknown')}")
            
            # Memory usage
            memory_info = await self.ai_manager.get_memory_usage()
            print(f"\n💾 Memory Usage:")
            print(f"   System Memory: {memory_info['system_memory']['used_mb']}MB / {memory_info['system_memory']['total_mb']}MB")
            print(f"   Memory Usage: {memory_info['system_memory']['percent']:.1f}%")
            
            # Analysis history
            analysis_history = await self.network_analyzer.get_analysis_history(3)
            print(f"\n📚 Recent Analysis History:")
            print(f"   Analyses performed: {len(analysis_history)}")
            for analysis in analysis_history:
                analysis_type = analysis.get('analysis_type', 'unknown')
                timestamp = analysis.get('timestamp', 'unknown')
                print(f"   • {analysis_type} at {timestamp}")
            
            logger.info("✅ TinyLLM demo completed")
            
        except Exception as e:
            logger.error(f"❌ TinyLLM demo failed: {e}")
            print(f"❌ TinyLLM demo failed: {e}")
    
    async def stop(self) -> bool:
        """Stop the demo system"""
        try:
            logger.info("🛑 Stopping demo system...")
            
            # Publish shutdown event
            await self.event_bus.publish(create_event(
                R2Events.SYSTEM_SHUTDOWN,
                {"demo_completed": True},
                "demo_system"
            ))
            
            # Stop all modules
            await self.container.stop_all_modules()
            
            # Cleanup all modules
            await self.container.cleanup_all_modules()
            
            logger.info("👋 R2-D2 TinyLLM Demo shutdown complete")
            return True
            
        except Exception as e:
            logger.error(f"❌ Demo shutdown error: {e}")
            return False


async def main():
    """Main demo function"""
    print("🤖 R2-D2 TinyLLM Only Demo")
    print("=" * 60)
    print("This demo shows R2's lightweight AI capabilities:")
    print("• TinyLLM model optimized for resource-constrained devices")
    print("• IoT sensor data analysis")
    print("• General conversation with R2 personality")
    print("• Network analysis and security assessment")
    print("• R2 sound translation")
    print("=" * 60)
    
    # Initialize demo
    demo = R2TinyLLMDemo()
    
    try:
        # Initialize system
        if not await demo.initialize():
            logger.error("❌ Demo initialization failed")
            return 1
        
        # Start system
        if not await demo.start():
            logger.error("❌ Demo startup failed")
            return 1
        
        # Wait a moment for modules to fully start
        await asyncio.sleep(1)
        
        # Run TinyLLM demo
        print(f"\n🚀 Starting TinyLLM Demo...")
        print(f"🧠 This will demonstrate TinyLLM's capabilities")
        print(f"📡 Including IoT analysis and general conversation")
        print(f"🎵 With R2's personality and sound system")
        print(f"\nPress Enter to start, or Ctrl+C to exit...")
        
        try:
            input()  # Wait for user input
        except KeyboardInterrupt:
            print("\n🛑 Demo cancelled by user")
            await demo.stop()
            return 0
        
        # Run the demo
        await demo.run_tinyllm_demo()
        
        # Wait a moment to see final output
        await asyncio.sleep(2)
        
        # Stop system
        await demo.stop()
        
        print(f"\n🎉 Demo completed successfully!")
        print(f"📊 The TinyLLM system demonstrated:")
        print(f"   • Lightweight AI model (CPU-optimized)")
        print(f"   • IoT sensor data analysis")
        print(f"   • General conversation capabilities")
        print(f"   • Network analysis and security assessment")
        print(f"   • R2 personality integration")
        print(f"   • Resource-efficient operation")
        
        return 0
        
    except KeyboardInterrupt:
        print("\n🛑 Demo interrupted by user")
        await demo.stop()
        return 0
        
    except Exception as e:
        logger.error(f"❌ Demo error: {e}")
        await demo.stop()
        return 1


if __name__ == "__main__":
    try:
        exit_code = asyncio.run(main())
        sys.exit(exit_code)
    except KeyboardInterrupt:
        print("\n🛑 Demo interrupted by user")
        sys.exit(0)
    except Exception as e:
        print(f"❌ Fatal error: {e}")
        sys.exit(1)