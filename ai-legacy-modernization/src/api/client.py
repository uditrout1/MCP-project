"""
API Client module.
This module provides a client for interacting with APIs through the MCP interface.
"""

from typing import Dict, Any, Optional
import uuid
from ..mcp.message import MCPMessage, Intent


class APIClient:
    """
    Client for interacting with APIs through the MCP interface.
    
    The client provides a simplified interface for sending requests to APIs
    registered in the system.
    """
    
    def __init__(self, source_id: str = None):
        """
        Initialize the API client.
        
        Args:
            source_id: Identifier for the source component, defaults to a generated ID
        """
        self.source_id = source_id or f"client.{uuid.uuid4().hex[:8]}"
    
    def call_api(self, api_name: str, intent: str, parameters: Dict[str, Any] = None,
                data: Dict[str, Any] = None, metadata: Dict[str, Any] = None) -> MCPMessage:
        """
        Call an API through the MCP interface.
        
        Args:
            api_name: Name of the API to call
            intent: Intent of the request
            parameters: Parameters for the request
            data: Data payload for the request
            metadata: Additional metadata
            
        Returns:
            MCPMessage: The response message
        """
        from ..mcp.router import router
        
        # Create the request message
        request = MCPMessage.create_request(
            source=self.source_id,
            destination=f"api.{api_name}",
            intent=intent,
            parameters=parameters or {},
            data=data or {},
            metadata=metadata or {}
        )
        
        # Route the message
        response = router.route(request)
        
        if response is None:
            # Create an error response if routing failed
            response = MCPMessage.create_error(
                request=request,
                error_code="NO_RESPONSE",
                error_message=f"No response received from API '{api_name}'",
                details={}
            )
        
        return response
