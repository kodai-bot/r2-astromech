"""
Logging Utilities for R2 Astromech System

This module provides enhanced logging capabilities for the R2 system.
"""

import logging
import logging.handlers
import os
from typing import Optional, Dict, Any
from datetime import datetime


class R2Logger:
    """Enhanced logger for R2 system"""
    
    def __init__(self, name: str, config: Optional[Dict[str, Any]] = None):
        """
        Initialize R2 logger.
        
        Args:
            name: Logger name
            config: Logging configuration
        """
        self.name = name
        self.config = config or {}
        self.logger = logging.getLogger(name)
        self._setup_logger()
    
    def _setup_logger(self) -> None:
        """Setup logger configuration"""
        # Set level
        level = self.config.get('level', 'INFO')
        self.logger.setLevel(getattr(logging, level.upper()))
        
        # Clear existing handlers
        self.logger.handlers.clear()
        
        # Console handler
        if self.config.get('console', True):
            console_handler = logging.StreamHandler()
            console_handler.setLevel(self.logger.level)
            
            # Format for console
            console_format = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            console_handler.setFormatter(console_format)
            self.logger.addHandler(console_handler)
        
        # File handler
        log_file = self.config.get('file')
        if log_file:
            # Ensure log directory exists
            log_dir = os.path.dirname(log_file)
            if log_dir:
                os.makedirs(log_dir, exist_ok=True)
            
            # Rotating file handler
            max_bytes = self.config.get('max_size_mb', 10) * 1024 * 1024
            backup_count = self.config.get('backup_count', 5)
            
            file_handler = logging.handlers.RotatingFileHandler(
                log_file,
                maxBytes=max_bytes,
                backupCount=backup_count
            )
            file_handler.setLevel(self.logger.level)
            
            # Format for file
            file_format = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(funcName)s:%(lineno)d - %(message)s'
            )
            file_handler.setFormatter(file_format)
            self.logger.addHandler(file_handler)
    
    def debug(self, message: str, **kwargs) -> None:
        """Log debug message"""
        self._log(logging.DEBUG, message, **kwargs)
    
    def info(self, message: str, **kwargs) -> None:
        """Log info message"""
        self._log(logging.INFO, message, **kwargs)
    
    def warning(self, message: str, **kwargs) -> None:
        """Log warning message"""
        self._log(logging.WARNING, message, **kwargs)
    
    def error(self, message: str, **kwargs) -> None:
        """Log error message"""
        self._log(logging.ERROR, message, **kwargs)
    
    def critical(self, message: str, **kwargs) -> None:
        """Log critical message"""
        self._log(logging.CRITICAL, message, **kwargs)
    
    def _log(self, level: int, message: str, **kwargs) -> None:
        """Internal logging method"""
        if kwargs:
            # Add extra context to message
            context = " | ".join([f"{k}={v}" for k, v in kwargs.items()])
            message = f"{message} | {context}"
        
        self.logger.log(level, message)


class ModuleLogger(R2Logger):
    """Logger specifically for modules"""
    
    def __init__(self, module_name: str, config: Optional[Dict[str, Any]] = None):
        """
        Initialize module logger.
        
        Args:
            module_name: Name of the module
            config: Logging configuration
        """
        super().__init__(f"r2.module.{module_name}", config)
        self.module_name = module_name
    
    def log_operation(self, operation: str, status: str, **kwargs) -> None:
        """
        Log module operation.
        
        Args:
            operation: Operation name
            status: Operation status
            **kwargs: Additional context
        """
        message = f"[{self.module_name}] {operation}: {status}"
        self.info(message, **kwargs)
    
    def log_error(self, operation: str, error: Exception, **kwargs) -> None:
        """
        Log module error.
        
        Args:
            operation: Operation name
            error: Exception that occurred
            **kwargs: Additional context
        """
        message = f"[{self.module_name}] {operation} failed: {str(error)}"
        self.error(message, **kwargs)


class ServiceLogger(R2Logger):
    """Logger specifically for services"""
    
    def __init__(self, service_name: str, config: Optional[Dict[str, Any]] = None):
        """
        Initialize service logger.
        
        Args:
            service_name: Name of the service
            config: Logging configuration
        """
        super().__init__(f"r2.service.{service_name}", config)
        self.service_name = service_name
    
    def log_request(self, endpoint: str, method: str, status_code: int, **kwargs) -> None:
        """
        Log API request.
        
        Args:
            endpoint: API endpoint
            method: HTTP method
            status_code: Response status code
            **kwargs: Additional context
        """
        message = f"[{self.service_name}] {method} {endpoint} -> {status_code}"
        self.info(message, **kwargs)


def get_r2_logger(name: str, config: Optional[Dict[str, Any]] = None) -> R2Logger:
    """
    Get R2 logger instance.
    
    Args:
        name: Logger name
        config: Logging configuration
        
    Returns:
        R2Logger: Logger instance
    """
    return R2Logger(name, config)


def get_module_logger(module_name: str, config: Optional[Dict[str, Any]] = None) -> ModuleLogger:
    """
    Get module logger instance.
    
    Args:
        module_name: Module name
        config: Logging configuration
        
    Returns:
        ModuleLogger: Module logger instance
    """
    return ModuleLogger(module_name, config)


def get_service_logger(service_name: str, config: Optional[Dict[str, Any]] = None) -> ServiceLogger:
    """
    Get service logger instance.
    
    Args:
        service_name: Service name
        config: Logging configuration
        
    Returns:
        ServiceLogger: Service logger instance
    """
    return ServiceLogger(service_name, config)