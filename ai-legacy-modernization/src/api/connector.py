"""
API Connector Framework module.
This module provides the base classes and interfaces for API connectors.
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List, Union
from enum import Enum
import requests
import aiohttp
import json
import logging
from ..mcp.message import MCPMessage, MCPPayload, Intent

logger = logging.getLogger(__name__)


class APIType(str, Enum):
    """Enum for supported API types."""
    REST = "rest"
    SOAP = "soap"
    GRAPHQL = "graphql"
    CUSTOM = "custom"


class AuthType(str, Enum):
    """Enum for supported authentication types."""
    NONE = "none"
    API_KEY = "api_key"
    BASIC = "basic"
    OAUTH = "oauth"
    BEARER = "bearer"
    CUSTOM = "custom"


class APIConnector(ABC):
    """
    Abstract base class for API connectors.
    
    API connectors are responsible for communicating with external APIs
    and translating between the MCP format and the API-specific format.
    """
    
    def __init__(self, name: str, base_url: str, api_type: APIType, auth_type: AuthType = AuthType.NONE):
        """
        Initialize the API connector.
        
        Args:
            name: Name of the API connector
            base_url: Base URL for the API
            api_type: Type of API
            auth_type: Type of authentication
        """
        self.name = name
        self.base_url = base_url
        self.api_type = api_type
        self.auth_type = auth_type
        self.session = requests.Session()
        self.headers = {}
        self.auth_params = {}
    
    @abstractmethod
    def process_request(self, message: MCPMessage) -> MCPMessage:
        """
        Process an MCP request message and return a response.
        
        Args:
            message: The MCP request message
            
        Returns:
            MCPMessage: The MCP response message
        """
        pass
    
    @abstractmethod
    def format_request(self, message: MCPMessage) -> Dict[str, Any]:
        """
        Format an MCP message into an API-specific request.
        
        Args:
            message: The MCP message
            
        Returns:
            Dict[str, Any]: The API-specific request
        """
        pass
    
    @abstractmethod
    def format_response(self, api_response: Any, original_message: MCPMessage) -> MCPMessage:
        """
        Format an API response into an MCP message.
        
        Args:
            api_response: The API response
            original_message: The original MCP request message
            
        Returns:
            MCPMessage: The MCP response message
        """
        pass
    
    def set_auth(self, **kwargs):
        """
        Set authentication parameters.
        
        Args:
            **kwargs: Authentication parameters
        """
        self.auth_params.update(kwargs)
        
        # Configure authentication based on type
        if self.auth_type == AuthType.API_KEY:
            key_name = kwargs.get('key_name', 'api_key')
            key_value = kwargs.get('key_value', '')
            key_location = kwargs.get('key_location', 'header')
            
            if key_location == 'header':
                self.headers[key_name] = key_value
            # Other locations handled in request formatting
            
        elif self.auth_type == AuthType.BASIC:
            username = kwargs.get('username', '')
            password = kwargs.get('password', '')
            self.session.auth = (username, password)
            
        elif self.auth_type == AuthType.BEARER:
            token = kwargs.get('token', '')
            self.headers['Authorization'] = f'Bearer {token}'
            
        # OAuth and custom auth handled in subclasses


class RESTConnector(APIConnector):
    """
    Connector for REST APIs.
    """
    
    def __init__(self, name: str, base_url: str, auth_type: AuthType = AuthType.NONE):
        """
        Initialize the REST connector.
        
        Args:
            name: Name of the API connector
            base_url: Base URL for the API
            auth_type: Type of authentication
        """
        super().__init__(name, base_url, APIType.REST, auth_type)
        self.endpoints = {}
    
    def register_endpoint(self, intent: str, endpoint: str, method: str = 'GET', 
                         params_mapping: Dict[str, str] = None):
        """
        Register an endpoint for a specific intent.
        
        Args:
            intent: The intent to register
            endpoint: The API endpoint (relative to base_url)
            method: The HTTP method to use
            params_mapping: Mapping from MCP parameters to API parameters
        """
        self.endpoints[intent] = {
            'endpoint': endpoint,
            'method': method.upper(),
            'params_mapping': params_mapping or {}
        }
    
    def format_request(self, message: MCPMessage) -> Dict[str, Any]:
        """
        Format an MCP message into a REST API request.
        
        Args:
            message: The MCP message
            
        Returns:
            Dict[str, Any]: The REST API request
        """
        intent = message.payload.intent
        
        if intent not in self.endpoints:
            raise ValueError(f"No endpoint registered for intent '{intent}'")
        
        endpoint_info = self.endpoints[intent]
        endpoint = endpoint_info['endpoint']
        method = endpoint_info['method']
        params_mapping = endpoint_info['params_mapping']
        
        # Apply parameter mapping
        params = {}
        for mcp_param, api_param in params_mapping.items():
            if mcp_param in message.payload.parameters:
                params[api_param] = message.payload.parameters[mcp_param]
        
        # Add any unmapped parameters
        for param, value in message.payload.parameters.items():
            if param not in params_mapping:
                params[param] = value
        
        # Handle path parameters
        for param, value in list(params.items()):
            placeholder = f"{{{param}}}"
            if placeholder in endpoint:
                endpoint = endpoint.replace(placeholder, str(value))
                del params[param]
        
        # Prepare request
        request = {
            'method': method,
            'url': f"{self.base_url.rstrip('/')}/{endpoint.lstrip('/')}",
            'headers': self.headers.copy(),
        }
        
        # Add parameters based on method
        if method in ['GET', 'DELETE']:
            request['params'] = params
        else:
            request['json'] = params
        
        # Add auth parameters if needed
        if self.auth_type == AuthType.API_KEY and self.auth_params.get('key_location') == 'query':
            key_name = self.auth_params.get('key_name', 'api_key')
            key_value = self.auth_params.get('key_value', '')
            if 'params' not in request:
                request['params'] = {}
            request['params'][key_name] = key_value
        
        return request
    
    def process_request(self, message: MCPMessage) -> MCPMessage:
        """
        Process an MCP request message and return a response.
        
        Args:
            message: The MCP request message
            
        Returns:
            MCPMessage: The MCP response message
        """
        try:
            # Format the request
            request = self.format_request(message)
            
            # Send the request
            method = request.pop('method')
            response = self.session.request(method, **request)
            
            # Check for errors
            response.raise_for_status()
            
            # Parse the response
            try:
                api_response = response.json()
            except json.JSONDecodeError:
                api_response = {'text': response.text}
            
            # Format the response
            return self.format_response(api_response, message)
            
        except requests.exceptions.RequestException as e:
            # Handle request errors
            return MCPMessage.create_error(
                request=message,
                error_code="API_REQUEST_ERROR",
                error_message=str(e),
                details={
                    'status_code': getattr(e.response, 'status_code', None),
                    'response_text': getattr(e.response, 'text', None)
                } if hasattr(e, 'response') else {}
            )
        except Exception as e:
            # Handle other errors
            logger.exception(f"Error processing request: {e}")
            return MCPMessage.create_error(
                request=message,
                error_code="PROCESSING_ERROR",
                error_message=str(e),
                details={'exception_type': type(e).__name__}
            )
    
    def format_response(self, api_response: Any, original_message: MCPMessage) -> MCPMessage:
        """
        Format a REST API response into an MCP message.
        
        Args:
            api_response: The API response
            original_message: The original MCP request message
            
        Returns:
            MCPMessage: The MCP response message
        """
        return MCPMessage.create_response(
            request=original_message,
            data=api_response,
            metadata={'api_name': self.name, 'api_type': self.api_type}
        )


class GraphQLConnector(APIConnector):
    """
    Connector for GraphQL APIs.
    """
    
    def __init__(self, name: str, base_url: str, auth_type: AuthType = AuthType.NONE):
        """
        Initialize the GraphQL connector.
        
        Args:
            name: Name of the API connector
            base_url: Base URL for the API
            auth_type: Type of authentication
        """
        super().__init__(name, base_url, APIType.GRAPHQL, auth_type)
        self.queries = {}
        self.mutations = {}
    
    def register_query(self, intent: str, query: str, params_mapping: Dict[str, str] = None):
        """
        Register a GraphQL query for a specific intent.
        
        Args:
            intent: The intent to register
            query: The GraphQL query
            params_mapping: Mapping from MCP parameters to GraphQL variables
        """
        self.queries[intent] = {
            'query': query,
            'params_mapping': params_mapping or {}
        }
    
    def register_mutation(self, intent: str, mutation: str, params_mapping: Dict[str, str] = None):
        """
        Register a GraphQL mutation for a specific intent.
        
        Args:
            intent: The intent to register
            mutation: The GraphQL mutation
            params_mapping: Mapping from MCP parameters to GraphQL variables
        """
        self.mutations[intent] = {
            'mutation': mutation,
            'params_mapping': params_mapping or {}
        }
    
    def format_request(self, message: MCPMessage) -> Dict[str, Any]:
        """
        Format an MCP message into a GraphQL API request.
        
        Args:
            message: The MCP message
            
        Returns:
            Dict[str, Any]: The GraphQL API request
        """
        intent = message.payload.intent
        
        # Determine if this is a query or mutation based on intent
        operation_type = None
        operation_data = None
        
        if intent in self.queries:
            operation_type = 'query'
            operation_data = self.queries[intent]
        elif intent in self.mutations:
            operation_type = 'mutation'
            operation_data = self.mutations[intent]
        else:
            raise ValueError(f"No query or mutation registered for intent '{intent}'")
        
        # Get the query/mutation and params mapping
        gql_operation = operation_data[operation_type] if operation_type == 'mutation' else operation_data['query']
        params_mapping = operation_data['params_mapping']
        
        # Apply parameter mapping
        variables = {}
        for mcp_param, gql_param in params_mapping.items():
            if mcp_param in message.payload.parameters:
                variables[gql_param] = message.payload.parameters[mcp_param]
        
        # Add any unmapped parameters
        for param, value in message.payload.parameters.items():
            if param not in params_mapping:
                variables[param] = value
        
        # Prepare request
        request = {
            'method': 'POST',
            'url': self.base_url,
            'headers': {**self.headers, 'Content-Type': 'application/json'},
            'json': {
                'query': gql_operation,
                'variables': variables
            }
        }
        
        return request
    
    def process_request(self, message: MCPMessage) -> MCPMessage:
        """
        Process an MCP request message and return a response.
        
        Args:
            message: The MCP request message
            
        Returns:
            MCPMessage: The MCP response message
        """
        try:
            # Format the request
            request = self.format_request(message)
            
            # Send the request
            method = request.pop('method')
            response = self.session.request(method, **request)
            
            # Check for errors
            response.raise_for_status()
            
            # Parse the response
            api_response = response.json()
            
            # Check for GraphQL errors
            if 'errors' in api_response:
                return MCPMessage.create_error(
                    request=message,
                    error_code="GRAPHQL_ERROR",
                    error_message="GraphQL operation failed",
                    details={'errors': api_response['errors']}
                )
            
            # Format the response
            return self.format_response(api_response, message)
            
        except requests.exceptions.RequestException as e:
            # Handle request errors
            return MCPMessage.create_error(
                request=message,
                error_code="API_REQUEST_ERROR",
                error_message=str(e),
                details={
                    'status_code': getattr(e.response, 'status_code', None),
                    'response_text': getattr(e.response, 'text', None)
                } if hasattr(e, 'response') else {}
            )
        except Exception as e:
            # Handle other errors
            logger.exception(f"Error processing request: {e}")
            return MCPMessage.create_error(
                request=message,
                error_code="PROCESSING_ERROR",
                error_message=str(e),
                details={'exception_type': type(e).__name__}
            )
    
    def format_response(self, api_response: Any, original_message: MCPMessage) -> MCPMessage:
        """
        Format a GraphQL API response into an MCP message.
        
        Args:
            api_response: The API response
            original_message: The original MCP request message
            
        Returns:
            MCPMessage: The MCP response message
        """
        # Extract data from GraphQL response
        data = api_response.get('data', {})
        
        return MCPMessage.create_response(
            request=original_message,
            data=data,
            metadata={'api_name': self.name, 'api_type': self.api_type}
        )
