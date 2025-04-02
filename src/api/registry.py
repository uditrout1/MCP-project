"""
API Registry module.
This module provides a registry for API connectors and handles their registration with the MCP router.
"""

from typing import Dict, Any, List, Optional
import logging
from ..mcp.router import router
from ..mcp.message import MCPMessage, Intent
from .connector import APIConnector, RESTConnector, GraphQLConnector, APIType, AuthType

logger = logging.getLogger(__name__)


class APIRegistry:
    """
    Registry for API connectors.
    
    The registry maintains a collection of API connectors and handles
    their registration with the MCP router.
    """
    
    def __init__(self):
        """Initialize the registry with an empty connector dictionary."""
        self._connectors: Dict[str, APIConnector] = {}
    
    def register_connector(self, connector: APIConnector):
        """
        Register an API connector.
        
        Args:
            connector: The API connector to register
        """
        if connector.name in self._connectors:
            logger.warning(f"Overwriting existing connector with name '{connector.name}'")
        
        self._connectors[connector.name] = connector
        
        # Register the connector with the MCP router
        router.register_handler(
            destination=f"api.{connector.name}",
            intent="*",  # Wildcard to handle all intents
            handler=self._create_handler(connector)
        )
        
        logger.info(f"Registered API connector '{connector.name}' of type {connector.api_type}")
    
    def get_connector(self, name: str) -> Optional[APIConnector]:
        """
        Get an API connector by name.
        
        Args:
            name: Name of the connector
            
        Returns:
            Optional[APIConnector]: The connector, or None if not found
        """
        return self._connectors.get(name)
    
    def list_connectors(self) -> List[str]:
        """
        List all registered connector names.
        
        Returns:
            List[str]: List of connector names
        """
        return list(self._connectors.keys())
    
    def _create_handler(self, connector: APIConnector):
        """
        Create a message handler for the connector.
        
        Args:
            connector: The API connector
            
        Returns:
            Callable: A function that handles MCP messages for this connector
        """
        def handler(message: MCPMessage) -> MCPMessage:
            return connector.process_request(message)
        
        return handler


# Global API registry instance
registry = APIRegistry()


def create_rest_connector(name: str, base_url: str, auth_type: AuthType = AuthType.NONE, 
                         auth_params: Dict[str, Any] = None) -> RESTConnector:
    """
    Create and register a REST API connector.
    
    Args:
        name: Name of the connector
        base_url: Base URL for the API
        auth_type: Type of authentication
        auth_params: Authentication parameters
        
    Returns:
        RESTConnector: The created connector
    """
    connector = RESTConnector(name, base_url, auth_type)
    
    if auth_params:
        connector.set_auth(**auth_params)
    
    registry.register_connector(connector)
    return connector


def create_graphql_connector(name: str, base_url: str, auth_type: AuthType = AuthType.NONE,
                           auth_params: Dict[str, Any] = None) -> GraphQLConnector:
    """
    Create and register a GraphQL API connector.
    
    Args:
        name: Name of the connector
        base_url: Base URL for the API
        auth_type: Type of authentication
        auth_params: Authentication parameters
        
    Returns:
        GraphQLConnector: The created connector
    """
    connector = GraphQLConnector(name, base_url, auth_type)
    
    if auth_params:
        connector.set_auth(**auth_params)
    
    registry.register_connector(connector)
    return connector
