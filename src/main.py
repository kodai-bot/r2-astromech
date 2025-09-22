"""
R2-D2 Astromech Unit - Modular Main Application

This is the new main entry point for the modular R2 system.
It uses dependency injection and event-driven architecture.
"""

import asyncio
import sys
import os
import logging
import argparse
from typing import Optional
from datetime import datetime

# Add src to path for imports
sys.path.insert(0, os.path.dirname(__file__))

from core.container import DIContainer
from core.config import Configuration, get_config
from core.events import EventBus, create_event, R2Events
from core.interfaces import IModule

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class R2AstromechSystem:
    """
    Main R2-D2 Astromech System
    
    This class orchestrates the entire R2 system using dependency injection
    and event-driven communication between modules.
    """
    
    def __init__(self, config_path: Optional[str] = None, environment: str = "development"):
        """
        Initialize the R2 system.
        
        Args:
            config_path: Path to configuration file
            environment: Environment name (development, production, testing)
        """
        self.config_path = config_path
        self.environment = environment
        self.container: Optional[DIContainer] = None
        self.config: Optional[Configuration] = None
        self.event_bus: Optional[EventBus] = None
        self.is_running = False
        self.startup_time: Optional[datetime] = None
        
        logger.info(f"🤖 R2-D2 Astromech System initializing (environment: {environment})")
    
    async def initialize(self) -> bool:
        """
        Initialize the R2 system.
        
        Returns:
            bool: True if initialization successful
        """
        try:
            logger.info("🔧 Initializing R2 system components...")
            
            # Initialize configuration
            self.config = Configuration(self.config_path, self.environment)
            if not self.config.validate():
                logger.error("❌ Configuration validation failed")
                return False
            
            # Initialize dependency injection container
            self.container = DIContainer()
            
            # Register configuration in container
            self.container.register_factory(Configuration, lambda container: self.config)
            
            # Initialize event bus
            self.event_bus = await self.container.get_service(EventBus)
            
            # Register modules (will be implemented in Phase 2)
            await self._register_modules()
            
            logger.info("✅ R2 system initialization complete")
            return True
            
        except Exception as e:
            logger.error(f"❌ R2 system initialization failed: {e}")
            return False
    
    async def _register_modules(self) -> None:
        """
        Register all modules with the container.
        
        This will be implemented in Phase 2 when we refactor the modules.
        For now, we'll create placeholder registrations.
        """
        logger.info("📦 Registering modules...")
        
        # TODO: In Phase 2, we'll register actual module implementations
        # For now, we'll just log what modules we plan to register
        
        planned_modules = [
            "ai.model_manager",
            "ai.network_analyzer", 
            "ai.translator",
            "discovery.scanners.discovery_engine",
            "discovery.protocol_detector",
            "discovery.device_analyzer",
            "personality.audio_engine",
            "personality.sound_generator",
            "personality.personality_manager",
            "communication.message_bus",
            "communication.api_server",
            "monitoring.health_monitor",
            "monitoring.metrics_collector",
            "monitoring.alert_manager"
        ]
        
        # Log planned modules (discovery engine will be available via demo)
        for module_name in planned_modules:
            logger.info(f"  📋 {module_name} (planned)")
        
        logger.info("📦 Module registration complete (using demo for discovery)")
    
    async def start(self) -> bool:
        """
        Start the R2 system.
        
        Returns:
            bool: True if startup successful
        """
        try:
            logger.info("🚀 Starting R2 system...")
            
            # Initialize all modules
            if not await self.container.initialize_all_modules():
                logger.error("❌ Module initialization failed")
                return False
            
            # Start all modules
            if not await self.container.start_all_modules():
                logger.error("❌ Module startup failed")
                return False
            
            # Publish startup event
            startup_event = create_event(
                R2Events.SYSTEM_STARTUP,
                {"environment": self.environment, "version": "2.0.0"},
                "system"
            )
            await self.event_bus.publish(startup_event)
            
            self.is_running = True
            self.startup_time = datetime.now()
            
            logger.info("🎉 R2-D2 Astromech System is now operational!")
            return True
            
        except Exception as e:
            logger.error(f"❌ R2 system startup failed: {e}")
            return False
    
    async def stop(self) -> bool:
        """
        Stop the R2 system gracefully.
        
        Returns:
            bool: True if shutdown successful
        """
        try:
            logger.info("🛑 Stopping R2 system...")
            
            # Publish shutdown event
            shutdown_event = create_event(
                R2Events.SYSTEM_SHUTDOWN,
                {"uptime": (datetime.now() - self.startup_time).total_seconds() if self.startup_time else 0},
                "system"
            )
            await self.event_bus.publish(shutdown_event)
            
            # Stop all modules
            await self.container.stop_all_modules()
            
            # Cleanup all modules
            await self.container.cleanup_all_modules()
            
            self.is_running = False
            
            logger.info("👋 R2-D2 Astromech System shutdown complete")
            return True
            
        except Exception as e:
            logger.error(f"❌ R2 system shutdown error: {e}")
            return False
    
    async def get_status(self) -> dict:
        """
        Get system status.
        
        Returns:
            dict: System status information
        """
        if not self.container:
            return {"status": "not_initialized"}
        
        module_status = await self.container.get_all_module_status()
        health_check = await self.container.health_check()
        
        return {
            "status": "running" if self.is_running else "stopped",
            "environment": self.environment,
            "startup_time": self.startup_time.isoformat() if self.startup_time else None,
            "uptime_seconds": (datetime.now() - self.startup_time).total_seconds() if self.startup_time else 0,
            "modules": module_status,
            "health": health_check,
            "event_bus_stats": self.event_bus.get_stats() if self.event_bus else {}
        }
    
    async def health_check(self) -> bool:
        """
        Perform system health check.
        
        Returns:
            bool: True if system is healthy
        """
        if not self.container:
            return False
        
        health_results = await self.container.health_check()
        return health_results.get('overall_health', False)


async def r2_interactive_menu(r2_system: R2AstromechSystem) -> None:
    """
    Interactive terminal menu for R2-D2 operations.
    
    Args:
        r2_system: The initialized R2 system instance
    """
    print("\n" + "="*70)
    print("    INDUSTRIAL AUTOMATON R2-D2 ASTROMECH COMMAND INTERFACE")
    print("    Advanced Network Discovery and Analysis System")
    print("    Manufactured by Industrial Automaton, Rordis City, Nubia")
    print("    'Modularity, Reliability, Intelligence' - Since 32 BBY")
    print("="*70)
    
    while r2_system.is_running:
        print("\n🤖 R2-D2 Astromech Command Menu:")
        print("   1. 🌐 Environment Scan (Network Discovery)")
        print("   2. 📡 Join Network (Connect to discovered network)")
        print("   3. 📊 System Status")
        print("   4. 🔧 Health Check")
        print("   5. 🛑 Quit")
        print("-" * 50)
        
        try:
            # Get user input
            choice = await get_user_input("Select option (1-5): ")
            
            if choice == "1":
                await handle_environment_scan(r2_system)
            elif choice == "2":
                await handle_join_network(r2_system)
            elif choice == "3":
                await handle_system_status(r2_system)
            elif choice == "4":
                await handle_health_check(r2_system)
            elif choice == "5":
                print("🛑 Shutting down R2-D2 Astromech System...")
                break
            else:
                print("❌ Invalid option. Please select 1-5.")
                
        except KeyboardInterrupt:
            print("\n🛑 Shutdown requested by user")
            break
        except Exception as e:
            print(f"❌ Error: {e}")


async def get_user_input(prompt: str) -> str:
    """Get user input asynchronously."""
    # Use synchronous input in executor for better compatibility
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(None, input, prompt)


async def handle_environment_scan(r2_system: R2AstromechSystem) -> None:
    """Handle environment scan (network discovery) operation."""
    print("\n🔍 R2-D2 Environment Scan")
    print("=" * 40)
    print("Launching R2's Network Discovery Demo...")
    
    try:
        # Run the demo network discovery script
        import subprocess
        import sys
        import os
        
        # Get the path to the scan director file
        scan_director_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "scan_director.py")
        
        print("\n🚀 Starting R2-D2 Network Discovery Scan Director...")
        print("🎵 Listen for R2's chirps as devices are discovered!")
        print("=" * 60)
        
        # Run the scan director script
        result = subprocess.run([sys.executable, scan_director_path], 
                              capture_output=False, 
                              text=True,
                              cwd=os.path.dirname(os.path.dirname(__file__)))
        
        print("=" * 60)
        if result.returncode == 0:
            print("✅ Network discovery scan completed successfully!")
        else:
            print(f"⚠️  Discovery scan completed with exit code: {result.returncode}")
            
    except FileNotFoundError:
        print("❌ Scan director script not found")
        print("💡 Make sure scan_director.py exists in the project root")
    except Exception as e:
        print(f"❌ Environment scan failed: {e}")
        print("💡 Check that scan_director.py is working correctly")
    
    await get_user_input("\nPress Enter to continue...")


async def handle_join_network(r2_system: R2AstromechSystem) -> None:
    """Handle join network operation."""
    print("\n📡 R2-D2 Network Connection")
    print("=" * 40)
    print("🚧 Network joining functionality coming soon!")
    print("This will allow R2 to connect to discovered networks and services.")
    print("\nPlanned features:")
    print("  • WiFi network connection")
    print("  • Network credential management") 
    print("  • Service endpoint discovery")
    print("  • Secure connection protocols")
    
    await get_user_input("\nPress Enter to continue...")


async def handle_system_status(r2_system: R2AstromechSystem) -> None:
    """Handle system status display."""
    print("\n📊 R2-D2 System Status")
    print("=" * 40)
    
    try:
        status = await r2_system.get_status()
        print(f"🤖 Status: {status['status']}")
        print(f"🌍 Environment: {status['environment']}")
        print(f"📦 Modules: {len(status['modules'])}")
        print(f"💚 Health: {'✅ Healthy' if status['health']['overall_health'] else '❌ Unhealthy'}")
        
        print(f"\n📋 Module Details:")
        for module_name, module_status in status['modules'].items():
            status_icon = "✅" if module_status == "running" else "❌"
            print(f"  {status_icon} {module_name}: {module_status}")
            
    except Exception as e:
        print(f"❌ Failed to get system status: {e}")
    
    await get_user_input("\nPress Enter to continue...")


async def handle_health_check(r2_system: R2AstromechSystem) -> None:
    """Handle system health check."""
    print("\n🔧 R2-D2 Health Check")
    print("=" * 40)
    
    try:
        print("🔍 Running system diagnostics...")
        is_healthy = await r2_system.health_check()
        
        if is_healthy:
            print("✅ All systems operational")
            print("🤖 R2-D2 is functioning within normal parameters")
        else:
            print("❌ System issues detected")
            print("⚠️  Check logs for detailed diagnostics")
            
    except Exception as e:
        print(f"❌ Health check failed: {e}")
    
    await get_user_input("\nPress Enter to continue...")


async def main():
    """Main entry point for R2-D2 Astromech System"""
    parser = argparse.ArgumentParser(description='R2-D2 Astromech Unit - Modular System')
    parser.add_argument('--config', '-c', help='Configuration file path')
    parser.add_argument('--environment', '-e', default='development', 
                       choices=['development', 'production', 'testing'],
                       help='Environment name')
    parser.add_argument('--status-only', '-s', action='store_true', 
                       help='Show status and exit')
    parser.add_argument('--health-check', action='store_true',
                       help='Perform health check and exit')
    parser.add_argument('--quiet', '-q', action='store_true', 
                       help='Minimize output')
    
    args = parser.parse_args()
    
    # Set logging level
    if args.quiet:
        logging.getLogger().setLevel(logging.WARNING)
    
    # Initialize R2 system
    r2_system = R2AstromechSystem(args.config, args.environment)
    
    try:
        # Initialize system
        if not await r2_system.initialize():
            logger.error("❌ R2 system initialization failed")
            return 1
        
        # Status only mode
        if args.status_only:
            status = await r2_system.get_status()
            print("🤖 R2-D2 System Status:")
            print(f"  Status: {status['status']}")
            print(f"  Environment: {status['environment']}")
            print(f"  Modules: {len(status['modules'])}")
            print(f"  Health: {'✅ Healthy' if status['health']['overall_health'] else '❌ Unhealthy'}")
            return 0
        
        # Health check mode
        if args.health_check:
            is_healthy = await r2_system.health_check()
            print(f"🤖 R2-D2 Health Check: {'✅ Healthy' if is_healthy else '❌ Unhealthy'}")
            return 0 if is_healthy else 1
        
        # Start system
        if not await r2_system.start():
            logger.error("❌ R2 system startup failed")
            return 1
        
        # Start interactive menu
        logger.info("🤖 R2-D2 is operational!")
        
        try:
            await r2_interactive_menu(r2_system)
        except KeyboardInterrupt:
            logger.info("🛑 Shutdown requested by user")
        
        # Shutdown system
        await r2_system.stop()
        return 0
        
    except Exception as e:
        logger.error(f"❌ R2 system error: {e}")
        return 1


if __name__ == "__main__":
    try:
        exit_code = asyncio.run(main())
        sys.exit(exit_code)
    except KeyboardInterrupt:
        print("\n🛑 R2 operation interrupted by user")
        sys.exit(0)
    except Exception as e:
        print(f"❌ Fatal error: {e}")
        sys.exit(1)