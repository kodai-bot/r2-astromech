#!/usr/bin/env python3
"""
R2-D2 Modular AI System Demo

This demo shows the new modular AI system with both Phi-3 and TinyLLM models
integrated with the event bus system.
"""

import asyncio
import sys
import os
import logging
import signal

# Add src to path for imports
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path[:0] = [ROOT, os.path.join(ROOT, "src")]

from src.core.container import DIContainer
from src.core.config import Configuration
from src.core.events import EventBus, create_event, R2Events
from src.modules.ai.model_manager import ModularAIModelManager
from src.modules.personality.audio_engine import ModularAudioEngine
from src.modules.personality.text_output import TextOutputModule

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class R2ModularAIDemo:
    """
    Demo of the modular AI system
    
    This demo shows how the new modular AI architecture works with
    event-driven communication between modules.
    """
    
    def __init__(self):
        """Initialize the demo"""
        self.container = DIContainer()
        self.config = None
        self.event_bus = None
        self.ai_manager = None
        self.audio_engine = None
        self.text_output = None
        self.shutdown_requested = False
        
        # Set up signal handlers for graceful shutdown
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)
        
        logger.info("🤖 R2-D2 Modular AI Demo initializing...")
    
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
            ai_config = self.config.get_section('modules.ai')
            ai_config['debug_mode'] = True  # Enable debug mode
            ai_config['auto_load'] = False  # Manual model loading for demo
            
            personality_config = self.config.get_section('modules.personality')
            
            # Initialize modules
            self.ai_manager = ModularAIModelManager(self.event_bus, ai_config)
            self.audio_engine = ModularAudioEngine(self.event_bus, personality_config)
            self.text_output = TextOutputModule(self.event_bus, {"enabled": True})
            
            # Register modules with container
            self.container.register_module("ai_manager", self.ai_manager)
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
            
            logger.info("🎉 R2-D2 Modular AI Demo is operational!")
            return True
            
        except Exception as e:
            logger.error(f"❌ Demo startup failed: {e}")
            return False
    
    async def run_ai_demo(self) -> None:
        """Run the AI system demo"""
        try:
            print("\n🤖 R2-D2 Modular AI System Demo")
            print("=" * 60)
            print("This demo shows R2's AI capabilities with:")
            print("• Phi-3 model for general conversation")
            print("• TinyLLM model for IoT sensor analysis")
            print("• Event-driven model switching")
            print("• R2 sound translation")
            print("=" * 60)
            
            # Show available models
            available_models = await self.ai_manager.get_available_models()
            print("\n📋 Available AI Models:")
            for model in available_models:
                print(f"   • {model}")
            
            # Test Phi-3 model
            print("\n🧠 Testing Phi-3 Model (General Conversation)")
            print("-" * 50)
            
            success = await self.ai_manager.load_model('phi-3')
            if success:
                print("✅ Phi-3 model loaded successfully")
                
                # Test general conversation
                test_inputs = [
                    "Hello R2! How are you today?",
                    "Can you help me understand network scanning?",
                    "What do you think about IoT devices?"
                ]
                
                for test_input in test_inputs:
                    print(f"\n👤 Human: {test_input}")
                    response = await self.ai_manager.generate_response(test_input)
                    print(f"🤖 R2: {response}")
                    
                    # Test R2 sound translation
                    r2_sounds = await self.ai_manager.translate_to_r2(test_input)
                    print(f"🔊 R2 Sounds: {r2_sounds}")
                    
                    await asyncio.sleep(1)  # Brief pause
            else:
                print("❌ Failed to load Phi-3 model")
            
            # Test TinyLLM model
            print("\n🔬 Testing TinyLLM Model (IoT Analysis)")
            print("-" * 50)
            
            success = await self.ai_manager.switch_model('tinyllm')
            if success:
                print("✅ TinyLLM model loaded successfully")
                
                # Test IoT analysis
                iot_test_inputs = [
                    "I found temperature sensors DS18B20 and humidity sensor DHT22 on the network",
                    "The network scan shows MQTT broker on port 1883 and CoAP on port 5683",
                    "Security assessment: found telnet on port 23 and weak password 'admin'"
                ]
                
                for test_input in iot_test_inputs:
                    print(f"\n📡 IoT Data: {test_input}")
                    response = await self.ai_manager.generate_response(test_input)
                    print(f"🤖 R2 Analysis: {response}")
                    
                    # Test R2 sound translation
                    r2_sounds = await self.ai_manager.translate_to_r2(test_input)
                    print(f"🔊 R2 Sounds: {r2_sounds}")
                    
                    await asyncio.sleep(1)  # Brief pause
            else:
                print("❌ Failed to load TinyLLM model")
            
            # Show model status
            print("\n📊 Model Status:")
            status = await self.ai_manager.get_model_status()
            print(f"   Current Model: {status.get('current_model', 'None')}")
            print(f"   Status: {status.get('status', 'Unknown')}")
            
            # Show memory usage
            memory_info = await self.ai_manager.get_memory_usage()
            print("\n💾 Memory Usage:")
            print(f"   System Memory: {memory_info['system_memory']['used_mb']}MB / {memory_info['system_memory']['total_mb']}MB")
            if 'gpu_memory' in memory_info:
                print(f"   GPU Memory: {memory_info['gpu_memory']['allocated_mb']}MB / {memory_info['gpu_memory']['total_mb']}MB")
            
            logger.info("✅ AI demo completed")
            
        except Exception as e:
            logger.error(f"❌ AI demo failed: {e}")
            print(f"❌ AI demo failed: {e}")
    
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
            
            logger.info("👋 R2-D2 Modular AI Demo shutdown complete")
            return True
            
        except Exception as e:
            logger.error(f"❌ Demo shutdown error: {e}")
            return False


async def main():
    """Main demo function"""
    print("🤖 R2-D2 Modular AI System Demo")
    print("=" * 60)
    print("This demo shows the new modular AI architecture with:")
    print("• Event-driven model management")
    print("• Phi-3 for general conversation")
    print("• TinyLLM for IoT sensor analysis")
    print("• R2 sound translation")
    print("• Proper error handling and cleanup")
    print("=" * 60)
    
    # Initialize demo
    demo = R2ModularAIDemo()
    
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
        
        # Run AI demo
        print("\n🚀 Starting AI System Demo...")
        print("📡 This will demonstrate both AI models and their capabilities")
        print("🎵 Audio events will play for each interaction (if sound files are available)")
        print("📝 Text output will show detailed AI responses")
        print("\nPress Enter to start, or Ctrl+C to exit...")
        
        try:
            input()  # Wait for user input
        except KeyboardInterrupt:
            print("\n🛑 Demo cancelled by user")
            await demo.stop()
            return 0
        
        # Run the demo
        await demo.run_ai_demo()
        
        # Wait a moment to see final output
        await asyncio.sleep(2)
        
        # Stop system
        await demo.stop()
        
        print("\n🎉 Demo completed successfully!")
        print("📊 The modular AI system demonstrated:")
        print("   • Event-driven model management")
        print("   • Phi-3 general conversation")
        print("   • TinyLLM IoT analysis")
        print("   • R2 sound translation")
        print("   • Proper error handling and cleanup")
        
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