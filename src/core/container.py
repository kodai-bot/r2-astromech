"""
Dependency Injection Container for R2 Astromech

This module provides dependency injection capabilities for managing
service instances and module dependencies.
"""

import asyncio
from typing import Dict, Type, Any, Optional, Callable, List
import logging
from datetime import datetime

from .interfaces import IModule, IServiceRegistry, ModuleStatus
from .events import EventBus, create_event, R2Events

logger = logging.getLogger(__name__)


class DIContainer(IServiceRegistry):
    """Dependency Injection Container for R2 modules and services"""
    
    def __init__(self):
        """Initialize the DI container"""
        self._services: Dict[str, Type] = {}
        self._singletons: Dict[str, Any] = {}
        self._factories: Dict[str, Callable] = {}
        self._modules: Dict[str, IModule] = {}
        self._module_status: Dict[str, ModuleStatus] = {}
        self._startup_order: List[str] = []
        self._shutdown_order: List[str] = []
        self._lock = asyncio.Lock()
        
        # Register core services
        self._register_core_services()
    
    def _register_core_services(self) -> None:
        """Register core services"""
        # Register event bus as singleton
        self.register_factory(EventBus, lambda container: EventBus())
        
        logger.info("Core services registered")
    
    def register_singleton(self, interface: Type, implementation: Type) -> None:
        """
        Register a singleton service.
        
        Args:
            interface: Interface type
            implementation: Implementation type
        """
        interface_name = interface.__name__
        self._services[interface_name] = implementation
        logger.debug(f"Registered singleton service: {interface_name}")
    
    def register_factory(self, interface: Type, factory: Callable) -> None:
        """
        Register a factory for service creation.
        
        Args:
            interface: Interface type
            factory: Factory function that takes container as argument
        """
        interface_name = interface.__name__
        self._factories[interface_name] = factory
        logger.debug(f"Registered factory service: {interface_name}")
    
    async def get_service(self, interface: Type) -> Any:
        """
        Get service instance.
        
        Args:
            interface: Interface type
            
        Returns:
            Any: Service instance
        """
        interface_name = interface.__name__
        
        async with self._lock:
            # Check if already instantiated
            if interface_name in self._singletons:
                return self._singletons[interface_name]
            
            # Create new instance
            instance = None
            
            if interface_name in self._services:
                # Direct instantiation
                implementation = self._services[interface_name]
                instance = implementation()
            elif interface_name in self._factories:
                # Factory instantiation
                factory = self._factories[interface_name]
                if asyncio.iscoroutinefunction(factory):
                    instance = await factory(self)
                else:
                    instance = factory(self)
            else:
                raise ValueError(f"Service {interface_name} not registered")
            
            # Store as singleton
            self._singletons[interface_name] = instance
            logger.debug(f"Created service instance: {interface_name}")
            
            return instance
    
    def register_module(self, name: str, module: IModule) -> None:
        """
        Register a module.
        
        Args:
            name: Module name
            module: Module instance
        """
        self._modules[name] = module
        self._module_status[name] = ModuleStatus(
            name=name,
            status='registered',
            health_score=0.0,
            last_heartbeat=datetime.now()
        )
        
        # Add to startup/shutdown order
        self._startup_order.append(name)
        self._shutdown_order.insert(0, name)  # Reverse order for shutdown
        
        logger.info(f"Registered module: {name}")
    
    async def get_module(self, name: str) -> IModule:
        """
        Get module instance.
        
        Args:
            name: Module name
            
        Returns:
            IModule: Module instance
        """
        if name not in self._modules:
            raise ValueError(f"Module {name} not registered")
        return self._modules[name]
    
    async def initialize_all_modules(self) -> bool:
        """
        Initialize all registered modules in dependency order.
        
        Returns:
            bool: True if all modules initialized successfully
        """
        logger.info("Initializing all modules...")
        success_count = 0
        
        for module_name in self._startup_order:
            try:
                module = self._modules[module_name]
                logger.info(f"Initializing module: {module_name}")
                
                success = await module.initialize()
                if success:
                    self._update_module_status(module_name, 'initialized', 1.0)
                    success_count += 1
                    logger.info(f"✓ Module {module_name} initialized successfully")
                else:
                    self._update_module_status(module_name, 'error', 0.0, "Initialization failed")
                    logger.error(f"✗ Module {module_name} initialization failed")
                
            except Exception as e:
                self._update_module_status(module_name, 'error', 0.0, str(e))
                logger.error(f"✗ Module {module_name} initialization error: {e}")
        
        logger.info(f"Module initialization complete: {success_count}/{len(self._modules)} successful")
        return success_count == len(self._modules)
    
    async def start_all_modules(self) -> bool:
        """
        Start all registered modules.
        
        Returns:
            bool: True if all modules started successfully
        """
        logger.info("Starting all modules...")
        success_count = 0
        
        for module_name in self._startup_order:
            try:
                module = self._modules[module_name]
                logger.info(f"Starting module: {module_name}")
                
                success = await module.start()
                if success:
                    self._update_module_status(module_name, 'running', 1.0)
                    success_count += 1
                    logger.info(f"✓ Module {module_name} started successfully")
                else:
                    self._update_module_status(module_name, 'error', 0.0, "Start failed")
                    logger.error(f"✗ Module {module_name} start failed")
                
            except Exception as e:
                self._update_module_status(module_name, 'error', 0.0, str(e))
                logger.error(f"✗ Module {module_name} start error: {e}")
        
        logger.info(f"Module startup complete: {success_count}/{len(self._modules)} successful")
        return success_count == len(self._modules)
    
    async def stop_all_modules(self) -> bool:
        """
        Stop all registered modules in reverse order.
        
        Returns:
            bool: True if all modules stopped successfully
        """
        logger.info("Stopping all modules...")
        success_count = 0
        
        for module_name in self._shutdown_order:
            try:
                module = self._modules[module_name]
                logger.info(f"Stopping module: {module_name}")
                
                success = await module.stop()
                if success:
                    self._update_module_status(module_name, 'stopped', 0.0)
                    success_count += 1
                    logger.info(f"✓ Module {module_name} stopped successfully")
                else:
                    logger.warning(f"⚠ Module {module_name} stop failed")
                
            except Exception as e:
                logger.error(f"✗ Module {module_name} stop error: {e}")
        
        logger.info(f"Module shutdown complete: {success_count}/{len(self._modules)} successful")
        return True  # Always return True for shutdown
    
    async def cleanup_all_modules(self) -> bool:
        """
        Cleanup all registered modules.
        
        Returns:
            bool: True if cleanup completed
        """
        logger.info("Cleaning up all modules...")
        
        for module_name in self._shutdown_order:
            try:
                module = self._modules[module_name]
                await module.cleanup()
                logger.debug(f"Cleaned up module: {module_name}")
            except Exception as e:
                logger.error(f"Error cleaning up module {module_name}: {e}")
        
        # Shutdown event bus
        try:
            event_bus = await self.get_service(EventBus)
            await event_bus.shutdown()
            logger.info("Event bus shutdown complete")
        except Exception as e:
            logger.error(f"Error shutting down event bus: {e}")
        
        logger.info("Module cleanup complete")
        return True
    
    def _update_module_status(self, module_name: str, status: str, health_score: float, 
                            error_message: Optional[str] = None) -> None:
        """Update module status"""
        if module_name in self._module_status:
            self._module_status[module_name].status = status
            self._module_status[module_name].health_score = health_score
            self._module_status[module_name].last_heartbeat = datetime.now()
            if error_message:
                self._module_status[module_name].error_message = error_message
    
    async def get_all_module_status(self) -> Dict[str, ModuleStatus]:
        """Get status of all modules"""
        # Update status for running modules
        for module_name, module in self._modules.items():
            if self._module_status[module_name].status == 'running':
                try:
                    health = await module.health_check()
                    self._update_module_status(module_name, 'running', 1.0 if health else 0.5)
                except Exception as e:
                    self._update_module_status(module_name, 'error', 0.0, str(e))
        
        return self._module_status.copy()
    
    async def get_module_status(self, module_name: str) -> Optional[ModuleStatus]:
        """Get status of specific module"""
        if module_name in self._module_status:
            return self._module_status[module_name]
        return None
    
    def get_registered_modules(self) -> List[str]:
        """Get list of registered module names"""
        return list(self._modules.keys())
    
    def get_registered_services(self) -> List[str]:
        """Get list of registered service names"""
        services = list(self._services.keys())
        factories = list(self._factories.keys())
        return services + factories
    
    async def health_check(self) -> Dict[str, Any]:
        """
        Perform health check on all modules.
        
        Returns:
            Dict[str, Any]: Health check results
        """
        results = {
            'overall_health': True,
            'module_count': len(self._modules),
            'healthy_modules': 0,
            'unhealthy_modules': 0,
            'module_details': {}
        }
        
        for module_name, module in self._modules.items():
            try:
                is_healthy = await module.health_check()
                results['module_details'][module_name] = {
                    'healthy': is_healthy,
                    'status': self._module_status[module_name].status
                }
                
                if is_healthy:
                    results['healthy_modules'] += 1
                else:
                    results['unhealthy_modules'] += 1
                    results['overall_health'] = False
                    
            except Exception as e:
                results['module_details'][module_name] = {
                    'healthy': False,
                    'error': str(e)
                }
                results['unhealthy_modules'] += 1
                results['overall_health'] = False
        
        return results