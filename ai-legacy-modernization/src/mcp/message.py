"""
Message Control Protocol (MCP) message module.
This module defines the standard message format for communication between components.
"""

import uuid
import time
from typing import Dict, Any, Optional, List, Union
from enum import Enum
from pydantic import BaseModel, Field


class MessageType(str, Enum):
    """Enum for message types in the MCP protocol."""
    REQUEST = "request"
    RESPONSE = "response"
    ERROR = "error"
    EVENT = "event"
    NOTIFICATION = "notification"


class Intent(str, Enum):
    """Enum for common intents in the MCP protocol."""
    QUERY = "query"
    CREATE = "create"
    UPDATE = "update"
    DELETE = "delete"
    LIST = "list"
    AUTHENTICATE = "authenticate"
    CRAWL = "crawl"
    EXTRACT = "extract"
    ENRICH = "enrich"
    TRANSFORM = "transform"
    CUSTOM = "custom"


class MCPPayload(BaseModel):
    """Payload model for MCP messages."""
    intent: str = Field(..., description="Action intent of the message")
    parameters: Dict[str, Any] = Field(default_factory=dict, description="Parameters for the action")
    data: Dict[str, Any] = Field(default_factory=dict, description="Data payload")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")


class MCPMessage(BaseModel):
    """Standard message format for the Message Control Protocol (MCP)."""
    message_id: str = Field(default_factory=lambda: str(uuid.uuid4()), description="Unique identifier for the message")
    message_type: MessageType = Field(..., description="Type of message")
    source: str = Field(..., description="Source component identifier")
    destination: str = Field(..., description="Destination component identifier")
    timestamp: float = Field(default_factory=time.time, description="Message creation timestamp")
    correlation_id: Optional[str] = Field(None, description="ID for correlating related messages")
    payload: MCPPayload = Field(..., description="Message payload")

    @classmethod
    def create_request(cls, source: str, destination: str, intent: str, 
                      parameters: Dict[str, Any] = None, 
                      data: Dict[str, Any] = None,
                      metadata: Dict[str, Any] = None,
                      correlation_id: str = None) -> "MCPMessage":
        """
        Create a request message.
        
        Args:
            source: Source component identifier
            destination: Destination component identifier
            intent: Action intent
            parameters: Parameters for the action
            data: Data payload
            metadata: Additional metadata
            correlation_id: ID for correlating related messages
            
        Returns:
            MCPMessage: A new request message
        """
        return cls(
            message_type=MessageType.REQUEST,
            source=source,
            destination=destination,
            correlation_id=correlation_id,
            payload=MCPPayload(
                intent=intent,
                parameters=parameters or {},
                data=data or {},
                metadata=metadata or {}
            )
        )
    
    @classmethod
    def create_response(cls, request: "MCPMessage", data: Dict[str, Any] = None, 
                       metadata: Dict[str, Any] = None) -> "MCPMessage":
        """
        Create a response message based on a request message.
        
        Args:
            request: The original request message
            data: Response data
            metadata: Additional metadata
            
        Returns:
            MCPMessage: A new response message
        """
        return cls(
            message_type=MessageType.RESPONSE,
            source=request.destination,
            destination=request.source,
            correlation_id=request.message_id,
            payload=MCPPayload(
                intent=request.payload.intent,
                parameters=request.payload.parameters,
                data=data or {},
                metadata=metadata or {}
            )
        )
    
    @classmethod
    def create_error(cls, request: "MCPMessage", error_code: str, error_message: str,
                    details: Dict[str, Any] = None) -> "MCPMessage":
        """
        Create an error message based on a request message.
        
        Args:
            request: The original request message
            error_code: Error code
            error_message: Error message
            details: Additional error details
            
        Returns:
            MCPMessage: A new error message
        """
        return cls(
            message_type=MessageType.ERROR,
            source=request.destination,
            destination=request.source,
            correlation_id=request.message_id,
            payload=MCPPayload(
                intent=request.payload.intent,
                parameters=request.payload.parameters,
                data={
                    "error_code": error_code,
                    "error_message": error_message,
                    "details": details or {}
                },
                metadata={}
            )
        )
