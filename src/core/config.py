"""
Configuration Management for R2 Astromech

This module provides centralized configuration management with support for
environment-specific configurations and hot-reloading.
"""

import os
import yaml
import json
from typing import Any, Dict, Optional, Union
from pathlib import Path
import logging

from .interfaces import IConfiguration

logger = logging.getLogger(__name__)


class Configuration(IConfiguration):
    """Centralized configuration management"""
    
    def __init__(self, config_path: Optional[str] = None, environment: str = "development"):
        """
        Initialize configuration manager.
        
        Args:
            config_path: Path to configuration file
            environment: Environment name (development, production, testing)
        """
        self.environment = environment
        self.config_path = config_path or self._get_default_config_path()
        self._config: Dict[str, Any] = {}
        self._watchers: list = []
        
        # Load configuration
        self._load_config()
        
        logger.info(f"Configuration loaded from {self.config_path} for environment: {environment}")
    
    def _get_default_config_path(self) -> str:
        """Get default configuration file path"""
        # Look for config in order of preference
        possible_paths = [
            "config/r2_config.yaml",
            "config/r2_config.yml", 
            "config/r2_config.json",
            "r2_config.yaml",
            "r2_config.yml"
        ]
        
        for path in possible_paths:
            if os.path.exists(path):
                return path
        
        # Return default path
        return "config/r2_config.yaml"
    
    def _load_config(self) -> None:
        """Load configuration from file"""
        try:
            if os.path.exists(self.config_path):
                with open(self.config_path, 'r') as f:
                    if self.config_path.endswith('.json'):
                        self._config = json.load(f) or {}
                    else:
                        self._config = yaml.safe_load(f) or {}
                
                # Apply environment-specific overrides
                self._apply_environment_overrides()
                
                logger.info(f"Configuration loaded from {self.config_path}")
            else:
                # Use default configuration
                self._config = self._get_default_config()
                logger.info("Using default configuration")
                
        except Exception as e:
            logger.error(f"Failed to load configuration: {e}")
            self._config = self._get_default_config()
    
    def _apply_environment_overrides(self) -> None:
        """Apply environment-specific configuration overrides"""
        if 'environments' in self._config and self.environment in self._config['environments']:
            env_config = self._config['environments'][self.environment]
            self._deep_merge(self._config, env_config)
            logger.debug(f"Applied {self.environment} environment overrides")
    
    def _deep_merge(self, base: Dict, override: Dict) -> None:
        """Deep merge override dict into base dict"""
        for key, value in override.items():
            if key in base and isinstance(base[key], dict) and isinstance(value, dict):
                self._deep_merge(base[key], value)
            else:
                base[key] = value
    
    def _get_default_config(self) -> Dict[str, Any]:
        """Get default configuration"""
        return {
            'system': {
                'name': 'R2-D2 Astromech Unit',
                'version': '2.0.0',
                'environment': self.environment,
                'debug': self.environment == 'development'
            },
            'modules': {
                'ai': {
                    'enabled': True,
                    'auto_load': True,
                    'default_model': 'phi-3',
                    'model_path': 'microsoft/Phi-3-mini-4k-instruct',
                    'device': 'auto',
                    'max_length': 512,
                    'temperature': 0.7
                },
                'discovery': {
                    'enabled': True,
                    'scan_timeout': 30,
                    'max_concurrent_scans': 5,
                    'default_network': '192.168.1.0/24',
                    'port_scan_timeout': 3
                },
                'personality': {
                    'enabled': True,
                    'audio_device': 'default',
                    'volume': 0.7,
                    'sound_directory': 'data/sounds',
                    'vocabulary_file': 'data/vocabulary.json'
                },
                'communication': {
                    'enabled': False,
                    'api_port': 8080,
                    'websocket_port': 8081,
                    'cors_origins': ['*']
                },
                'monitoring': {
                    'enabled': True,
                    'health_check_interval': 30,
                    'metrics_collection': True,
                    'alert_thresholds': {
                        'memory_usage': 0.8,
                        'cpu_usage': 0.8,
                        'disk_usage': 0.9
                    }
                }
            },
            'logging': {
                'level': 'INFO',
                'file': 'logs/r2.log',
                'max_size_mb': 10,
                'backup_count': 5,
                'format': '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            },
            'performance': {
                'max_concurrent_operations': 10,
                'operation_timeout': 300,
                'cache_size': 1000,
                'enable_caching': True
            },
            'security': {
                'input_validation': True,
                'max_input_length': 1000,
                'content_filtering': False,
                'rate_limiting': {
                    'enabled': True,
                    'requests_per_minute': 60
                }
            },
            'environments': {
                'development': {
                    'system': {'debug': True},
                    'logging': {'level': 'DEBUG'},
                    'modules': {'ai': {'auto_load': False}}
                },
                'production': {
                    'system': {'debug': False},
                    'logging': {'level': 'WARNING'},
                    'performance': {'enable_caching': True}
                },
                'testing': {
                    'system': {'debug': True},
                    'modules': {'ai': {'enabled': False}, 'personality': {'enabled': False}}
                }
            }
        }
    
    def get(self, key: str, default: Any = None) -> Any:
        """
        Get configuration value using dot notation.
        
        Args:
            key: Configuration key (e.g., 'modules.ai.enabled')
            default: Default value if key not found
            
        Returns:
            Any: Configuration value
        """
        keys = key.split('.')
        value = self._config
        
        try:
            for k in keys:
                if isinstance(value, dict) and k in value:
                    value = value[k]
                else:
                    return default
            return value
        except (KeyError, TypeError):
            return default
    
    def set(self, key: str, value: Any) -> None:
        """
        Set configuration value using dot notation.
        
        Args:
            key: Configuration key (e.g., 'modules.ai.enabled')
            value: Value to set
        """
        keys = key.split('.')
        config = self._config
        
        # Navigate to the parent of the target key
        for k in keys[:-1]:
            if k not in config:
                config[k] = {}
            config = config[k]
        
        # Set the value
        config[keys[-1]] = value
        
        logger.debug(f"Configuration set: {key} = {value}")
    
    def get_section(self, section: str) -> Dict[str, Any]:
        """
        Get entire configuration section.
        
        Args:
            section: Section name (e.g., 'modules.ai')
            
        Returns:
            Dict[str, Any]: Section configuration
        """
        return self.get(section, {})
    
    def reload(self) -> None:
        """Reload configuration from source"""
        logger.info("Reloading configuration...")
        self._load_config()
        
        # Notify watchers
        for watcher in self._watchers:
            try:
                watcher()
            except Exception as e:
                logger.error(f"Error in configuration watcher: {e}")
    
    def save(self) -> None:
        """Save current configuration to source"""
        try:
            # Ensure directory exists
            os.makedirs(os.path.dirname(self.config_path), exist_ok=True)
            
            with open(self.config_path, 'w') as f:
                if self.config_path.endswith('.json'):
                    json.dump(self._config, f, indent=2)
                else:
                    yaml.dump(self._config, f, default_flow_style=False)
            
            logger.info(f"Configuration saved to {self.config_path}")
        except Exception as e:
            logger.error(f"Failed to save configuration: {e}")
    
    def add_watcher(self, callback: callable) -> None:
        """
        Add configuration change watcher.
        
        Args:
            callback: Function to call when configuration changes
        """
        self._watchers.append(callback)
    
    def remove_watcher(self, callback: callable) -> None:
        """
        Remove configuration change watcher.
        
        Args:
            callback: Function to remove
        """
        if callback in self._watchers:
            self._watchers.remove(callback)
    
    def get_all(self) -> Dict[str, Any]:
        """Get entire configuration"""
        return self._config.copy()
    
    def validate(self) -> bool:
        """
        Validate configuration.
        
        Returns:
            bool: True if valid, False otherwise
        """
        try:
            # Check required sections
            required_sections = ['system', 'modules', 'logging']
            for section in required_sections:
                if section not in self._config:
                    logger.error(f"Missing required configuration section: {section}")
                    return False
            
            # Validate module configurations
            modules = self.get('modules', {})
            for module_name, module_config in modules.items():
                if not isinstance(module_config, dict):
                    logger.error(f"Invalid module configuration for {module_name}")
                    return False
            
            logger.info("Configuration validation passed")
            return True
            
        except Exception as e:
            logger.error(f"Configuration validation failed: {e}")
            return False


# Global configuration instance
_config_instance: Optional[Configuration] = None


def get_config() -> Configuration:
    """Get global configuration instance"""
    global _config_instance
    if _config_instance is None:
        _config_instance = Configuration()
    return _config_instance


def set_config(config: Configuration) -> None:
    """Set global configuration instance"""
    global _config_instance
    _config_instance = config