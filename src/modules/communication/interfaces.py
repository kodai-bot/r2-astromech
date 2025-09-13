"""
Communication Module Interfaces

This module defines the interfaces for communication functionality
including message bus, API server, and protocol handlers.
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, Union, Callable
from datetime import datetime

from ...core.interfaces import IModule, Event


class IMessageBus(IModule):
    """Internal Message Bus interface"""
    
    @abstractmethod
    async def send_message(self, target_module: str, message_type: str, data: Dict[str, Any]) -> bool:
        """
        Send message to specific module.
        
        Args:
            target_module: Target module name
            message_type: Type of message
            data: Message data
            
        Returns:
            bool: True if message sent successfully
        """
        pass
    
    @abstractmethod
    async def broadcast_message(self, message_type: str, data: Dict[str, Any]) -> bool:
        """
        Broadcast message to all modules.
        
        Args:
            message_type: Type of message
            data: Message data
            
        Returns:
            bool: True if message broadcast successfully
        """
        pass
    
    @abstractmethod
    async def register_message_handler(self, message_type: str, handler: Callable) -> None:
        """
        Register message handler.
        
        Args:
            message_type: Type of message to handle
            handler: Handler function
        """
        pass
    
    @abstractmethod
    async def unregister_message_handler(self, message_type: str, handler: Callable) -> None:
        """
        Unregister message handler.
        
        Args:
            message_type: Type of message
            handler: Handler function to remove
        """
        pass
    
    @abstractmethod
    async def get_message_history(self, limit: int = 100) -> List[Dict[str, Any]]:
        """
        Get message history.
        
        Args:
            limit: Maximum number of messages to return
            
        Returns:
            List[Dict[str, Any]]: Message history
        """
        pass


class IAPIServer(IModule):
    """API Server interface"""
    
    @abstractmethod
    async def start_server(self, host: str = "0.0.0.0", port: int = 8080) -> bool:
        """
        Start the API server.
        
        Args:
            host: Host address
            port: Port number
            
        Returns:
            bool: True if server started successfully
        """
        pass
    
    @abstractmethod
    async def stop_server(self) -> bool:
        """
        Stop the API server.
        
        Returns:
            bool: True if server stopped successfully
        """
        pass
    
    @abstractmethod
    async def add_route(self, method: str, path: str, handler: Callable) -> None:
        """
        Add API route.
        
        Args:
            method: HTTP method (GET, POST, etc.)
            path: URL path
            handler: Handler function
        """
        pass
    
    @abstractmethod
    async def remove_route(self, method: str, path: str) -> None:
        """
        Remove API route.
        
        Args:
            method: HTTP method
            path: URL path
        """
        pass
    
    @abstractmethod
    async def get_server_status(self) -> Dict[str, Any]:
        """
        Get server status.
        
        Returns:
            Dict[str, Any]: Server status information
        """
        pass
    
    @abstractmethod
    async def get_active_connections(self) -> int:
        """
        Get number of active connections.
        
        Returns:
            int: Number of active connections
        """
        pass


class IWebSocketServer(IModule):
    """WebSocket Server interface"""
    
    @abstractmethod
    async def start_server(self, host: str = "0.0.0.0", port: int = 8081) -> bool:
        """
        Start the WebSocket server.
        
        Args:
            host: Host address
            port: Port number
            
        Returns:
            bool: True if server started successfully
        """
        pass
    
    @abstractmethod
    async def stop_server(self) -> bool:
        """
        Stop the WebSocket server.
        
        Returns:
            bool: True if server stopped successfully
        """
        pass
    
    @abstractmethod
    async def broadcast_event(self, event: Event) -> int:
        """
        Broadcast event to all connected clients.
        
        Args:
            event: Event to broadcast
            
        Returns:
            int: Number of clients that received the event
        """
        pass
    
    @abstractmethod
    async def send_to_client(self, client_id: str, data: Dict[str, Any]) -> bool:
        """
        Send data to specific client.
        
        Args:
            client_id: Client identifier
            data: Data to send
            
        Returns:
            bool: True if sent successfully
        """
        pass
    
    @abstractmethod
    async def get_connected_clients(self) -> List[Dict[str, Any]]:
        """
        Get list of connected clients.
        
        Returns:
            List[Dict[str, Any]]: Connected client information
        """
        pass
    
    @abstractmethod
    async def disconnect_client(self, client_id: str) -> bool:
        """
        Disconnect specific client.
        
        Args:
            client_id: Client identifier
            
        Returns:
            bool: True if disconnected successfully
        """
        pass


class IProtocolHandler(IModule):
    """Protocol Handler interface"""
    
    @abstractmethod
    async def handle_request(self, protocol: str, request_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Handle protocol-specific request.
        
        Args:
            protocol: Protocol name
            request_data: Request data
            
        Returns:
            Dict[str, Any]: Response data
        """
        pass
    
    @abstractmethod
    async def register_protocol(self, protocol: str, handler: Callable) -> None:
        """
        Register protocol handler.
        
        Args:
            protocol: Protocol name
            handler: Handler function
        """
        pass
    
    @abstractmethod
    async def unregister_protocol(self, protocol: str) -> None:
        """
        Unregister protocol handler.
        
        Args:
            protocol: Protocol name
        """
        pass
    
    @abstractmethod
    async def get_supported_protocols(self) -> List[str]:
        """
        Get list of supported protocols.
        
        Returns:
            List[str]: Supported protocol names
        """
        pass


class IRateLimiter(IModule):
    """Rate Limiting interface"""
    
    @abstractmethod
    async def check_rate_limit(self, client_id: str, endpoint: str) -> bool:
        """
        Check if client is within rate limits.
        
        Args:
            client_id: Client identifier
            endpoint: API endpoint
            
        Returns:
            bool: True if within limits, False if rate limited
        """
        pass
    
    @abstractmethod
    async def record_request(self, client_id: str, endpoint: str) -> None:
        """
        Record API request for rate limiting.
        
        Args:
            client_id: Client identifier
            endpoint: API endpoint
        """
        pass
    
    @abstractmethod
    async def get_rate_limit_status(self, client_id: str) -> Dict[str, Any]:
        """
        Get rate limit status for client.
        
        Args:
            client_id: Client identifier
            
        Returns:
            Dict[str, Any]: Rate limit status
        """
        pass


class IAuthentication(IModule):
    """Authentication interface"""
    
    @abstractmethod
    async def authenticate_request(self, request_data: Dict[str, Any]) -> Optional[str]:
        """
        Authenticate API request.
        
        Args:
            request_data: Request data including headers/auth
            
        Returns:
            Optional[str]: Client ID if authenticated, None otherwise
        """
        pass
    
    @abstractmethod
    async def generate_token(self, client_id: str) -> str:
        """
        Generate authentication token.
        
        Args:
            client_id: Client identifier
            
        Returns:
            str: Authentication token
        """
        pass
    
    @abstractmethod
    async def validate_token(self, token: str) -> Optional[str]:
        """
        Validate authentication token.
        
        Args:
            token: Token to validate
            
        Returns:
            Optional[str]: Client ID if valid, None otherwise
        """
        pass
    
    @abstractmethod
    async def revoke_token(self, token: str) -> bool:
        """
        Revoke authentication token.
        
        Args:
            token: Token to revoke
            
        Returns:
            bool: True if revoked successfully
        """
        pass


class ICORSHandler(IModule):
    """CORS Handler interface"""
    
    @abstractmethod
    async def handle_cors_request(self, origin: str, method: str, headers: List[str]) -> Dict[str, Any]:
        """
        Handle CORS preflight request.
        
        Args:
            origin: Request origin
            method: HTTP method
            headers: Request headers
            
        Returns:
            Dict[str, Any]: CORS response headers
        """
        pass
    
    @abstractmethod
    async def add_cors_headers(self, response_headers: Dict[str, str], origin: str) -> Dict[str, str]:
        """
        Add CORS headers to response.
        
        Args:
            response_headers: Existing response headers
            origin: Request origin
            
        Returns:
            Dict[str, str]: Updated response headers with CORS
        """
        pass
    
    @abstractmethod
    async def is_origin_allowed(self, origin: str) -> bool:
        """
        Check if origin is allowed.
        
        Args:
            origin: Origin to check
            
        Returns:
            bool: True if origin is allowed
        """
        pass