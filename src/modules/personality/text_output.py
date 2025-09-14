"""
Text Output Module for R2 Astromech

This module handles text output for scan events, providing human-readable
descriptions of R2's activities.
"""

import asyncio
from typing import Dict, Any, List
from datetime import datetime
import logging

from ...core.interfaces import IModule, ModuleStatus
from ...core.events import EventBus, create_event, R2Events
from ...utils.logging import get_module_logger

logger = get_module_logger("personality.text_output")


class TextOutputModule(IModule):
    """
    Text Output Module
    
    Provides human-readable text output for R2's activities,
    including scan events and device discoveries.
    """
    
    def __init__(self, event_bus: EventBus, config: Dict[str, Any]):
        """
        Initialize the text output module.
        
        Args:
            event_bus: Event bus for communication
            config: Configuration
        """
        self.event_bus = event_bus
        self.config = config
        self.logger = logger
        
        # Module state
        self.is_running = False
        self.output_enabled = config.get('enabled', True)
        
        # Statistics
        self.stats = {
            'events_processed': 0,
            'devices_reported': 0,
            'scans_reported': 0
        }
        
        self.logger.info("Text Output Module initialized")
    
    @property
    def module_name(self) -> str:
        """Get module name"""
        return "personality.text_output"
    
    async def initialize(self) -> bool:
        """Initialize the text output module"""
        try:
            self.logger.info("Initializing text output module...")
            
            # Subscribe to relevant events
            await self.event_bus.subscribe(R2Events.NETWORK_SCAN_STARTED, self._on_scan_started)
            await self.event_bus.subscribe(R2Events.DEVICE_DISCOVERED, self._on_device_discovered)
            await self.event_bus.subscribe(R2Events.NETWORK_SCAN_COMPLETED, self._on_scan_completed)
            await self.event_bus.subscribe(R2Events.NETWORK_SCAN_ERROR, self._on_scan_error)
            await self.event_bus.subscribe(R2Events.DEVICE_ANALYZED, self._on_device_analyzed)
            
            self.logger.info("Text output module initialized successfully")
            return True
            
        except Exception as e:
            self.logger.error("Failed to initialize text output module", error=str(e))
            return False
    
    async def start(self) -> bool:
        """Start the text output module"""
        try:
            self.logger.info("Starting text output module...")
            self.is_running = True
            
            # Display startup message
            self._display_message("🤖 R2-D2 Text Output System Online", "system")
            
            # Publish module started event
            await self.event_bus.publish(create_event(
                R2Events.MODULE_STARTED,
                {"module": self.module_name, "capabilities": ["text_output", "event_reporting"]},
                self.module_name
            ))
            
            self.logger.info("Text output module started successfully")
            return True
            
        except Exception as e:
            self.logger.error("Failed to start text output module", error=str(e))
            return False
    
    async def stop(self) -> bool:
        """Stop the text output module"""
        try:
            self.logger.info("Stopping text output module...")
            
            # Display shutdown message
            self._display_message("👋 R2-D2 Text Output System Offline", "system")
            
            self.is_running = False
            
            # Publish module stopped event
            await self.event_bus.publish(create_event(
                R2Events.MODULE_STOPPED,
                {"module": self.module_name, "stats": self.stats},
                self.module_name
            ))
            
            self.logger.info("Text output module stopped successfully")
            return True
            
        except Exception as e:
            self.logger.error("Failed to stop text output module", error=str(e))
            return False
    
    async def get_status(self) -> ModuleStatus:
        """Get module status"""
        return ModuleStatus(
            name=self.module_name,
            status='running' if self.is_running else 'stopped',
            health_score=1.0 if self.is_running else 0.0,
            last_heartbeat=datetime.now(),
            uptime_seconds=0.0,
            memory_usage_mb=None
        )
    
    async def health_check(self) -> bool:
        """Perform health check"""
        return self.is_running
    
    async def cleanup(self) -> bool:
        """Cleanup module resources"""
        try:
            self.logger.info("Cleaning up text output module...")
            self.logger.info("Text output module cleanup complete")
            return True
            
        except Exception as e:
            self.logger.error("Cleanup failed", error=str(e))
            return False
    
    def _display_message(self, message: str, category: str = "info") -> None:
        """
        Display a message to the user.
        
        Args:
            message: Message to display
            category: Message category (info, warning, error, success)
        """
        if not self.output_enabled:
            return
        
        timestamp = datetime.now().strftime("%H:%M:%S")
        
        # Color coding based on category
        colors = {
            "info": "\033[94m",      # Blue
            "warning": "\033[93m",   # Yellow
            "error": "\033[91m",     # Red
            "success": "\033[92m",   # Green
            "system": "\033[96m",    # Cyan
            "device": "\033[95m",    # Magenta
            "scan": "\033[97m"       # White
        }
        
        color = colors.get(category, "")
        reset = "\033[0m"
        
        print(f"{color}[{timestamp}] {message}{reset}")
    
    # Event handlers
    async def _on_scan_started(self, event) -> None:
        """Handle network scan started event"""
        data = event.data
        scan_id = data.get('scan_id', 'unknown')
        target_network = data.get('target_network', 'unknown')
        
        self._display_message(f"🔍 R2-D2 Beginning Network Discovery Mission", "scan")
        self._display_message(f"📡 Target Network: {target_network}", "scan")
        self._display_message(f"🆔 Scan ID: {scan_id}", "scan")
        self._display_message("=" * 60, "scan")
        
        self.stats['events_processed'] += 1
        self.stats['scans_reported'] += 1
    
    async def _on_device_discovered(self, event) -> None:
        """Handle device discovered event"""
        data = event.data
        
        # Handle different types of device discovery events
        if 'device' in data:
            # Full device object
            device = data['device']
            ip = device.get('ip', 'unknown')
            method = device.get('discovery_method', 'unknown')
            device_number = data.get('device_number', 0)
            total_devices = data.get('total_devices', 0)
        else:
            # Simple IP discovery
            ip = data.get('ip', 'unknown')
            method = data.get('discovery_method', 'unknown')
            device_number = data.get('host_number', 0)
            total_devices = 0
        
        self._display_message(f"📡 Device #{device_number} Found: {ip}", "device")
        self._display_message(f"🔍 Discovery Method: {method}", "device")
        
        if total_devices > 0:
            self._display_message(f"📊 Progress: {device_number}/{total_devices} devices", "device")
        
        self.stats['events_processed'] += 1
        self.stats['devices_reported'] += 1
    
    async def _on_scan_completed(self, event) -> None:
        """Handle network scan completed event"""
        data = event.data
        scan_id = data.get('scan_id', 'unknown')
        devices_found = data.get('devices_found', 0)
        stats = data.get('stats', {})
        
        self._display_message("=" * 60, "scan")
        self._display_message(f"🎯 R2-D2 Discovery Mission Complete!", "success")
        self._display_message(f"📊 Total Devices Discovered: {devices_found}", "success")
        self._display_message(f"🆔 Scan ID: {scan_id}", "success")
        
        if stats:
            self._display_message(f"📈 Scanner Statistics:", "info")
            for key, value in stats.items():
                self._display_message(f"   • {key}: {value}", "info")
        
        self.stats['events_processed'] += 1
    
    async def _on_scan_error(self, event) -> None:
        """Handle network scan error event"""
        data = event.data
        scan_id = data.get('scan_id', 'unknown')
        error = data.get('error', 'unknown error')
        reason = data.get('reason', 'unknown')
        
        if reason == 'user_cancelled':
            self._display_message("🛑 Network Scan Cancelled by User", "warning")
        else:
            self._display_message("❌ R2-D2 Network Scan Failed", "error")
            self._display_message(f"🔍 Error: {error}", "error")
            self._display_message(f"🆔 Scan ID: {scan_id}", "error")
        
        self.stats['events_processed'] += 1
    
    async def _on_device_analyzed(self, event) -> None:
        """Handle device analyzed event"""
        data = event.data
        analysis_type = data.get('analysis_type', 'unknown')
        
        if analysis_type == 'port_scan':
            host = data.get('host', 'unknown')
            port = data.get('port', 'unknown')
            service = data.get('service', 'unknown')
            
            self._display_message(f"🔍 Port Analysis: {host}:{port} ({service})", "device")
            
        elif analysis_type == 'port_discovery':
            # This is handled by the port_scan case above
            pass
        
        self.stats['events_processed'] += 1