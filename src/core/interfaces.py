"""
Core Interfaces for R2 Astromech System

This module defines the base interfaces that all modules must implement
to ensure proper encapsulation and communication.
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, Callable
from dataclasses import dataclass
from datetime import datetime


@dataclass
class ModuleStatus:
    """Status information for a module"""
    name: str
    status: str  # 'initializing', 'running', 'stopped', 'error', 'maintenance'
    health_score: float  # 0.0 to 1.0
    last_heartbeat: datetime
    error_message: Optional[str] = None
    uptime_seconds: float = 0.0
    memory_usage_mb: Optional[float] = None


@dataclass
class Event:
    """Base event class for inter-module communication"""
    name: str
    data: Dict[str, Any]
    timestamp: datetime
    source: str
    correlation_id: Optional[str] = None
    priority: int = 0  # 0=normal, 1=high, 2=critical


class IModule(ABC):
    """Base interface for all R2 modules"""
    
    @property
    @abstractmethod
    def module_name(self) -> str:
        """Get the module name"""
        pass
    
    @abstractmethod
    async def initialize(self) -> bool:
        """
        Initialize the module.
        
        Returns:
            bool: True if initialization successful, False otherwise
        """
        pass
    
    @abstractmethod
    async def start(self) -> bool:
        """
        Start the module.
        
        Returns:
            bool: True if start successful, False otherwise
        """
        pass
    
    @abstractmethod
    async def stop(self) -> bool:
        """
        Stop the module gracefully.
        
        Returns:
            bool: True if stop successful, False otherwise
        """
        pass
    
    @abstractmethod
    async def get_status(self) -> ModuleStatus:
        """
        Get current module status.
        
        Returns:
            ModuleStatus: Current status information
        """
        pass
    
    @abstractmethod
    async def health_check(self) -> bool:
        """
        Perform health check.
        
        Returns:
            bool: True if healthy, False otherwise
        """
        pass
    
    @abstractmethod
    async def cleanup(self) -> bool:
        """
        Cleanup module resources.
        
        Returns:
            bool: True if cleanup successful, False otherwise
        """
        pass


class IEventBus(ABC):
    """Event bus interface for inter-module communication"""
    
    @abstractmethod
    async def publish(self, event: Event) -> None:
        """
        Publish an event to the bus.
        
        Args:
            event: Event to publish
        """
        pass
    
    @abstractmethod
    async def subscribe(self, event_name: str, handler: Callable[[Event], None]) -> None:
        """
        Subscribe to an event.
        
        Args:
            event_name: Name of event to subscribe to
            handler: Function to call when event occurs
        """
        pass
    
    @abstractmethod
    async def unsubscribe(self, event_name: str, handler: Callable[[Event], None]) -> None:
        """
        Unsubscribe from an event.
        
        Args:
            event_name: Name of event to unsubscribe from
            handler: Handler function to remove
        """
        pass
    
    @abstractmethod
    async def get_event_history(self, limit: int = 100) -> List[Event]:
        """
        Get recent event history.
        
        Args:
            limit: Maximum number of events to return
            
        Returns:
            List[Event]: Recent events
        """
        pass


class IConfiguration(ABC):
    """Configuration interface"""
    
    @abstractmethod
    def get(self, key: str, default: Any = None) -> Any:
        """
        Get configuration value using dot notation.
        
        Args:
            key: Configuration key (e.g., 'modules.ai.enabled')
            default: Default value if key not found
            
        Returns:
            Any: Configuration value
        """
        pass
    
    @abstractmethod
    def set(self, key: str, value: Any) -> None:
        """
        Set configuration value using dot notation.
        
        Args:
            key: Configuration key (e.g., 'modules.ai.enabled')
            value: Value to set
        """
        pass
    
    @abstractmethod
    def reload(self) -> None:
        """Reload configuration from source"""
        pass
    
    @abstractmethod
    def save(self) -> None:
        """Save current configuration to source"""
        pass
    
    @abstractmethod
    def get_section(self, section: str) -> Dict[str, Any]:
        """
        Get entire configuration section.
        
        Args:
            section: Section name (e.g., 'modules.ai')
            
        Returns:
            Dict[str, Any]: Section configuration
        """
        pass


class IServiceRegistry(ABC):
    """Service registry interface for dependency injection"""
    
    @abstractmethod
    def register_singleton(self, interface: type, implementation: type) -> None:
        """
        Register a singleton service.
        
        Args:
            interface: Interface type
            implementation: Implementation type
        """
        pass
    
    @abstractmethod
    def register_factory(self, interface: type, factory: Callable) -> None:
        """
        Register a factory for service creation.
        
        Args:
            interface: Interface type
            factory: Factory function
        """
        pass
    
    @abstractmethod
    async def get_service(self, interface: type) -> Any:
        """
        Get service instance.
        
        Args:
            interface: Interface type
            
        Returns:
            Any: Service instance
        """
        pass
    
    @abstractmethod
    def register_module(self, name: str, module: IModule) -> None:
        """
        Register a module.
        
        Args:
            name: Module name
            module: Module instance
        """
        pass
    
    @abstractmethod
    async def get_module(self, name: str) -> IModule:
        """
        Get module instance.
        
        Args:
            name: Module name
            
        Returns:
            IModule: Module instance
        """
        pass


class ILogger(ABC):
    """Logger interface"""
    
    @abstractmethod
    def debug(self, message: str, **kwargs) -> None:
        """Log debug message"""
        pass
    
    @abstractmethod
    def info(self, message: str, **kwargs) -> None:
        """Log info message"""
        pass
    
    @abstractmethod
    def warning(self, message: str, **kwargs) -> None:
        """Log warning message"""
        pass
    
    @abstractmethod
    def error(self, message: str, **kwargs) -> None:
        """Log error message"""
        pass
    
    @abstractmethod
    def critical(self, message: str, **kwargs) -> None:
        """Log critical message"""
        pass