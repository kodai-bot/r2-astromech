#!/usr/bin/env python3
"""
R2-D2 AI-Network Scanner Integration Demo

This demo shows the complete integration between the AI system and network scanner,
demonstrating intelligent network analysis with both Phi-3 and TinyLLM models.
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


class R2AINetworkIntegrationDemo:
    """
    Demo of the complete AI-Network Scanner integration
    
    This demo shows how the AI system intelligently analyzes network scan results
    using both Phi-3 for general analysis and TinyLLM for IoT-specific insights.
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
        
        logger.info("🤖 R2-D2 AI-Network Integration Demo initializing...")
    
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
            
            logger.info("🎉 R2-D2 AI-Network Integration Demo is operational!")
            return True
            
        except Exception as e:
            logger.error(f"❌ Demo startup failed: {e}")
            return False
    
    async def run_integration_demo(self) -> None:
        """Run the AI-Network integration demo"""
        try:
            print(f"\n🤖 R2-D2 AI-Network Integration Demo")
            print("=" * 70)
            print("This demo shows R2's intelligent network analysis with:")
            print("• Network scanning with nmap/masscan")
            print("• AI-powered device analysis (Phi-3)")
            print("• IoT-specific analysis (TinyLLM)")
            print("• Security assessment and recommendations")
            print("• R2's intelligent insights and personality")
            print("=" * 70)
            
            # Step 1: Load AI models
            print(f"\n🧠 Step 1: Loading AI Models")
            print("-" * 40)
            
            # Load Phi-3 for general analysis
            print("Loading Phi-3 model for general network analysis...")
            phi3_success = await self.ai_manager.load_model('phi-3')
            if phi3_success:
                print("✅ Phi-3 model loaded successfully")
            else:
                print("❌ Failed to load Phi-3 model")
                return
            
            # Load TinyLLM for IoT analysis
            print("Loading TinyLLM model for IoT analysis...")
            tinyllm_success = await self.ai_manager.load_model('tinyllm')
            if tinyllm_success:
                print("✅ TinyLLM model loaded successfully")
            else:
                print("❌ Failed to load TinyLLM model")
                return
            
            # Step 2: Perform network scan
            print(f"\n🔍 Step 2: Network Discovery")
            print("-" * 40)
            
            print("Starting network scan...")
            print("This will scan the current network for devices...")
            
            # Perform network scan
            devices = await self.network_scanner.scan_network()
            
            print(f"\n📊 Network Scan Results:")
            print(f"   Devices discovered: {len(devices)}")
            
            if devices:
                print(f"\n📡 Discovered Devices:")
                for i, device in enumerate(devices, 1):
                    ip = device.get('ip', 'unknown')
                    device_type = device.get('device_type', 'unknown')
                    manufacturer = device.get('manufacturer', 'unknown')
                    open_ports = device.get('open_ports', [])
                    
                    print(f"   {i}. {ip}")
                    print(f"      Type: {device_type}")
                    print(f"      Manufacturer: {manufacturer}")
                    print(f"      Open Ports: {open_ports}")
            else:
                print("   No devices found on this network")
            
            # Step 3: AI Analysis
            print(f"\n🤖 Step 3: AI-Powered Analysis")
            print("-" * 40)
            
            if devices:
                print("R2 is analyzing the discovered devices...")
                
                # Comprehensive AI analysis
                analysis_results = await self.network_analyzer.analyze_discovered_devices(devices)
                
                # Display analysis results
                print(f"\n🧠 R2's Network Analysis:")
                print("=" * 50)
                
                # Network summary
                summary = analysis_results.get('summary', 'No summary available')
                print(f"\n📋 Network Summary:")
                print(f"   {summary}")
                
                # R2 insights
                insights = analysis_results.get('r2_insights', [])
                if insights:
                    print(f"\n💡 R2's Insights:")
                    for i, insight in enumerate(insights, 1):
                        print(f"   {i}. {insight}")
                
                # Security assessment
                security_assessment = analysis_results.get('security_assessment', {})
                if security_assessment:
                    print(f"\n🔒 Security Assessment:")
                    print(f"   Overall Security Score: {security_assessment.get('overall_security_score', 0):.1f}/100")
                    print(f"   Secure Devices: {security_assessment.get('secure_devices', 0)}")
                    print(f"   Devices with Issues: {security_assessment.get('devices_with_issues', 0)}")
                
                # IoT analysis
                iot_devices = analysis_results.get('iot_identification', [])
                if iot_devices:
                    print(f"\n🏠 IoT Device Analysis:")
                    print(f"   IoT Devices Found: {len(iot_devices)}")
                    for iot_device in iot_devices:
                        ip = iot_device.get('ip')
                        indicators = iot_device.get('iot_indicators', [])
                        protocols = iot_device.get('protocols', [])
                        print(f"   • {ip}: {', '.join(indicators)}")
                        if protocols:
                            print(f"     Protocols: {', '.join(protocols)}")
                
                # Recommendations
                recommendations = analysis_results.get('recommendations', [])
                if recommendations:
                    print(f"\n💡 R2's Recommendations:")
                    for i, rec in enumerate(recommendations, 1):
                        print(f"   {i}. {rec}")
                
                # Step 4: Model-specific analysis
                print(f"\n🔬 Step 4: Specialized AI Analysis")
                print("-" * 40)
                
                # Switch to TinyLLM for IoT-specific analysis
                print("Switching to TinyLLM for IoT-specific analysis...")
                await self.ai_manager.switch_model('tinyllm')
                
                # Create IoT-focused analysis prompt
                iot_prompt = f"""
IoT Network Analysis Request:
I've discovered {len(devices)} devices on the network. Please provide specialized IoT analysis focusing on:
1. IoT device identification and classification
2. Protocol analysis (MQTT, CoAP, Modbus, etc.)
3. Security implications of IoT devices
4. Network topology from IoT perspective
5. Recommendations for IoT security

Device details: {self._create_device_summary_for_ai(devices)}
"""
                
                print("Generating IoT-specific analysis...")
                iot_analysis = await self.ai_manager.generate_response(iot_prompt)
                
                print(f"\n🔬 TinyLLM IoT Analysis:")
                print("=" * 50)
                print(iot_analysis)
                
                # Switch back to Phi-3 for general insights
                print("\nSwitching back to Phi-3 for general insights...")
                await self.ai_manager.switch_model('phi-3')
                
                # Generate R2 personality response
                personality_prompt = f"""
As R2-D2, provide your perspective on this network environment:
{self._create_device_summary_for_ai(devices)}

Be helpful, curious, and show your characteristic personality. Include:
- Your thoughts on the network discovery
- Any concerns or observations
- Your excitement about finding devices
- R2-style commentary
"""
                
                print("Generating R2 personality response...")
                r2_response = await self.ai_manager.generate_response(personality_prompt)
                
                print(f"\n🤖 R2's Perspective:")
                print("=" * 50)
                print(r2_response)
                
                # Test R2 sound translation
                print(f"\n🔊 R2 Sound Translation:")
                print("-" * 30)
                test_phrases = [
                    "I found interesting devices on the network!",
                    "Security concerns detected!",
                    "IoT devices discovered!"
                ]
                
                for phrase in test_phrases:
                    r2_sounds = await self.ai_manager.translate_to_r2(phrase)
                    print(f"   '{phrase}' → {r2_sounds}")
            
            else:
                print("No devices found to analyze")
            
            # Step 5: Show system status
            print(f"\n📊 Step 5: System Status")
            print("-" * 40)
            
            # AI model status
            model_status = await self.ai_manager.get_model_status()
            print(f"🤖 AI Model Status:")
            print(f"   Current Model: {model_status.get('current_model', 'None')}")
            print(f"   Status: {model_status.get('status', 'Unknown')}")
            
            # Memory usage
            memory_info = await self.ai_manager.get_memory_usage()
            print(f"\n💾 Memory Usage:")
            print(f"   System Memory: {memory_info['system_memory']['used_mb']}MB / {memory_info['system_memory']['total_mb']}MB")
            if 'gpu_memory' in memory_info:
                print(f"   GPU Memory: {memory_info['gpu_memory']['allocated_mb']}MB / {memory_info['gpu_memory']['total_mb']}MB")
            
            # Analysis history
            analysis_history = await self.network_analyzer.get_analysis_history(5)
            print(f"\n📚 Recent Analysis History:")
            print(f"   Analyses performed: {len(analysis_history)}")
            for analysis in analysis_history[-3:]:  # Show last 3
                analysis_type = analysis.get('analysis_type', 'unknown')
                timestamp = analysis.get('timestamp', 'unknown')
                print(f"   • {analysis_type} at {timestamp}")
            
            logger.info("✅ AI-Network integration demo completed")
            
        except Exception as e:
            logger.error(f"❌ Integration demo failed: {e}")
            print(f"❌ Integration demo failed: {e}")
    
    def _create_device_summary_for_ai(self, devices: List[dict]) -> str:
        """Create a concise device summary for AI analysis"""
        if not devices:
            return "No devices discovered"
        
        summary = f"Network scan discovered {len(devices)} devices:\n"
        for i, device in enumerate(devices, 1):
            summary += f"{i}. {device.get('ip', 'unknown')} - {device.get('device_type', 'unknown')} "
            summary += f"({device.get('manufacturer', 'unknown')}) "
            summary += f"Ports: {device.get('open_ports', [])}\n"
        
        return summary
    
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
            
            logger.info("👋 R2-D2 AI-Network Integration Demo shutdown complete")
            return True
            
        except Exception as e:
            logger.error(f"❌ Demo shutdown error: {e}")
            return False


async def main():
    """Main demo function"""
    print("🤖 R2-D2 AI-Network Scanner Integration Demo")
    print("=" * 70)
    print("This demo shows the complete integration between:")
    print("• Network Scanner (nmap/masscan)")
    print("• AI Models (Phi-3 + TinyLLM)")
    print("• Network Analyzer (intelligent analysis)")
    print("• R2 Personality (sounds + insights)")
    print("=" * 70)
    
    # Initialize demo
    demo = R2AINetworkIntegrationDemo()
    
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
        
        # Run integration demo
        print(f"\n🚀 Starting AI-Network Integration Demo...")
        print(f"📡 This will demonstrate intelligent network analysis")
        print(f"🧠 Using both Phi-3 and TinyLLM models")
        print(f"🎵 With R2's personality and sound system")
        print(f"\nPress Enter to start, or Ctrl+C to exit...")
        
        try:
            input()  # Wait for user input
        except KeyboardInterrupt:
            print("\n🛑 Demo cancelled by user")
            await demo.stop()
            return 0
        
        # Run the demo
        await demo.run_integration_demo()
        
        # Wait a moment to see final output
        await asyncio.sleep(2)
        
        # Stop system
        await demo.stop()
        
        print(f"\n🎉 Demo completed successfully!")
        print(f"📊 The AI-Network integration demonstrated:")
        print(f"   • Intelligent network scanning")
        print(f"   • AI-powered device analysis")
        print(f"   • IoT-specific insights (TinyLLM)")
        print(f"   • General analysis (Phi-3)")
        print(f"   • Security assessment")
        print(f"   • R2 personality integration")
        print(f"   • Event-driven communication")
        
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