"""
MCP Router module.
This module provides the routing functionality for MCP messages between components.
"""

from typing import Dict, Callable, Any, Optional, List
from .message import MCPMessage, MessageType


class MCPRouter:
    """
    Router for MCP messages.
    
    The router is responsible for routing messages between components based on
    the destination and intent of the message.
    """
    
    def __init__(self):
        """Initialize the router with empty route tables."""
        # Routes are organized by destination and intent
        self._routes: Dict[str, Dict[str, Callable]] = {}
        # Global middleware that applies to all messages
        self._middleware: List[Callable] = []
    
    def register_handler(self, destination: str, intent: str, handler: Callable[[MCPMessage], MCPMessage]):
        """
        Register a handler for a specific destination and intent.
        
        Args:
            destination: Destination component identifier
            intent: Action intent
            handler: Function that processes the message and returns a response
        """
        if destination not in self._routes:
            self._routes[destination] = {}
        
        self._routes[destination][intent] = handler
    
    def register_middleware(self, middleware: Callable[[MCPMessage], Optional[MCPMessage]]):
        """
        Register middleware that processes messages before they are routed.
        
        Args:
            middleware: Function that processes the message and returns it or None
                       If None is returned, the message is not processed further.
        """
        self._middleware.append(middleware)
    
    def route(self, message: MCPMessage) -> Optional[MCPMessage]:
        """
        Route a message to its destination handler.
        
        Args:
            message: The message to route
            
        Returns:
            Optional[MCPMessage]: The response message, or None if no handler was found
                                 or if middleware blocked the message
        """
        # Apply middleware
        for mw in self._middleware:
            result = mw(message)
            if result is None:
                return None
            message = result
        
        # Find the appropriate handler
        destination = message.destination
        intent = message.payload.intent
        
        if destination not in self._routes or intent not in self._routes[destination]:
            # No handler found
            if message.message_type == MessageType.REQUEST:
                # Create an error response for requests
                return MCPMessage.create_error(
                    request=message,
                    error_code="ROUTE_NOT_FOUND",
                    error_message=f"No handler found for destination '{destination}' and intent '{intent}'",
                    details={"available_destinations": list(self._routes.keys())}
                )
            return None
        
        # Call the handler
        handler = self._routes[destination][intent]
        return handler(message)


# Global router instance
router = MCPRouter()
