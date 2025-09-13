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
            "discovery.network_scanner",
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
        
        for module_name in planned_modules:
            logger.info(f"  📦 {module_name} (placeholder)")
        
        logger.info("📦 Module registration complete (placeholders)")
    
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
        
        # Keep system running
        logger.info("🤖 R2-D2 is operational! Press Ctrl+C to shutdown.")
        
        try:
            while r2_system.is_running:
                await asyncio.sleep(1)
                
                # Perform periodic health checks
                if not await r2_system.health_check():
                    logger.warning("⚠️  System health check failed")
                
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