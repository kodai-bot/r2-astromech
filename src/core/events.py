"""
Event System for R2 Astromech

This module implements the event bus for inter-module communication,
allowing modules to communicate without direct dependencies.
"""

import asyncio
from typing import Dict, List, Callable, Any
from datetime import datetime
from collections import deque
import logging

from .interfaces import IEventBus, Event

logger = logging.getLogger(__name__)


class EventBus(IEventBus):
    """Event bus implementation for inter-module communication"""
    
    def __init__(self, max_history: int = 1000):
        """
        Initialize the event bus.
        
        Args:
            max_history: Maximum number of events to keep in history
        """
        self._subscribers: Dict[str, List[Callable]] = {}
        self._event_history: deque = deque(maxlen=max_history)
        self._lock = asyncio.Lock()
        self._stats = {
            'events_published': 0,
            'events_processed': 0,
            'subscribers_count': 0
        }
    
    async def publish(self, event: Event) -> None:
        """
        Publish an event to the bus.
        
        Args:
            event: Event to publish
        """
        async with self._lock:
            # Add to history
            self._event_history.append(event)
            self._stats['events_published'] += 1
            
            # Notify subscribers
            if event.name in self._subscribers:
                subscribers = self._subscribers[event.name].copy()
                
                # Process subscribers concurrently
                tasks = []
                for handler in subscribers:
                    task = asyncio.create_task(self._safe_handler_call(handler, event))
                    tasks.append(task)
                
                if tasks:
                    await asyncio.gather(*tasks, return_exceptions=True)
                    self._stats['events_processed'] += len(tasks)
            
            logger.debug(f"Published event '{event.name}' from {event.source}")
    
    async def _safe_handler_call(self, handler: Callable, event: Event) -> None:
        """Safely call event handler with error handling"""
        try:
            if asyncio.iscoroutinefunction(handler):
                await handler(event)
            else:
                handler(event)
        except Exception as e:
            logger.error(f"Error in event handler for '{event.name}': {e}")
    
    async def subscribe(self, event_name: str, handler: Callable) -> None:
        """
        Subscribe to an event.
        
        Args:
            event_name: Name of event to subscribe to
            handler: Function to call when event occurs
        """
        async with self._lock:
            if event_name not in self._subscribers:
                self._subscribers[event_name] = []
            
            if handler not in self._subscribers[event_name]:
                self._subscribers[event_name].append(handler)
                self._stats['subscribers_count'] += 1
                logger.debug(f"Subscribed handler to event '{event_name}'")
    
    async def unsubscribe(self, event_name: str, handler: Callable) -> None:
        """
        Unsubscribe from an event.
        
        Args:
            event_name: Name of event to unsubscribe from
            handler: Handler function to remove
        """
        async with self._lock:
            if event_name in self._subscribers:
                try:
                    self._subscribers[event_name].remove(handler)
                    self._stats['subscribers_count'] -= 1
                    logger.debug(f"Unsubscribed handler from event '{event_name}'")
                except ValueError:
                    logger.warning(f"Handler not found in subscribers for '{event_name}'")
    
    async def get_event_history(self, limit: int = 100) -> List[Event]:
        """
        Get recent event history.
        
        Args:
            limit: Maximum number of events to return
            
        Returns:
            List[Event]: Recent events
        """
        async with self._lock:
            return list(self._event_history)[-limit:]
    
    def get_stats(self) -> Dict[str, Any]:
        """Get event bus statistics"""
        return {
            **self._stats,
            'active_subscriptions': len(self._subscribers),
            'history_size': len(self._event_history)
        }
    
    async def clear_history(self) -> None:
        """Clear event history"""
        async with self._lock:
            self._event_history.clear()
            logger.info("Event history cleared")


# Predefined event types for common R2 operations
class R2Events:
    """Common R2 event types"""
    
    # System events
    SYSTEM_STARTUP = "system.startup"
    SYSTEM_SHUTDOWN = "system.shutdown"
    SYSTEM_ERROR = "system.error"
    
    # Module events
    MODULE_STARTED = "module.started"
    MODULE_STOPPED = "module.stopped"
    MODULE_ERROR = "module.error"
    MODULE_HEALTH_CHECK = "module.health_check"
    
    # Network events
    NETWORK_SCAN_STARTED = "network.scan_started"
    NETWORK_SCAN_COMPLETED = "network.scan_completed"
    NETWORK_SCAN_ERROR = "network.scan_error"
    DEVICE_DISCOVERED = "network.device_discovered"
    DEVICE_ANALYZED = "network.device_analyzed"
    
    # AI events
    AI_MODEL_LOADED = "ai.model_loaded"
    AI_MODEL_UNLOADED = "ai.model_unloaded"
    AI_ANALYSIS_STARTED = "ai.analysis_started"
    AI_ANALYSIS_COMPLETED = "ai.analysis_completed"
    AI_RESPONSE_GENERATED = "ai.response_generated"
    
    # Personality events
    AUDIO_PLAYED = "personality.audio_played"
    PERSONALITY_RESPONSE = "personality.response"
    EMOTION_EXPRESSED = "personality.emotion_expressed"
    
    # Communication events
    API_REQUEST_RECEIVED = "communication.api_request_received"
    API_RESPONSE_SENT = "communication.api_response_sent"
    WEBSOCKET_CONNECTED = "communication.websocket_connected"
    WEBSOCKET_DISCONNECTED = "communication.websocket_disconnected"


def create_event(name: str, data: Dict[str, Any], source: str, 
                correlation_id: str = None, priority: int = 0) -> Event:
    """
    Helper function to create events.
    
    Args:
        name: Event name
        data: Event data
        source: Source module name
        correlation_id: Optional correlation ID
        priority: Event priority (0=normal, 1=high, 2=critical)
        
    Returns:
        Event: Created event
    """
    return Event(
        name=name,
        data=data,
        timestamp=datetime.now(),
        source=source,
        correlation_id=correlation_id,
        priority=priority
    )