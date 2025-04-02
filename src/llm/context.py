"""
Conversation Context Manager module.
This module provides functionality for managing conversation context.
"""

from typing import Dict, Any, List, Optional, Deque
from collections import deque
import json
import time


class ConversationContext:
    """
    Manager for conversation context.
    
    This class maintains the context of a conversation, including message history,
    extracted entities, and user preferences.
    """
    
    def __init__(self, max_history: int = 10):
        """
        Initialize the conversation context.
        
        Args:
            max_history: Maximum number of messages to keep in history
        """
        self.messages: Deque[Dict[str, Any]] = deque(maxlen=max_history)
        self.entities: Dict[str, Any] = {}
        self.preferences: Dict[str, Any] = {}
        self.session_data: Dict[str, Any] = {
            "session_id": str(int(time.time())),
            "start_time": time.time(),
            "last_activity": time.time()
        }
    
    def add_message(self, role: str, content: str, metadata: Dict[str, Any] = None):
        """
        Add a message to the conversation history.
        
        Args:
            role: Role of the message sender ("user", "assistant", or "system")
            content: Content of the message
            metadata: Additional metadata for the message
        """
        message = {
            "role": role,
            "content": content,
            "timestamp": time.time(),
            "metadata": metadata or {}
        }
        self.messages.append(message)
        self.session_data["last_activity"] = time.time()
    
    def add_entity(self, entity_type: str, entity_value: Any, confidence: float = 1.0):
        """
        Add an extracted entity to the context.
        
        Args:
            entity_type: Type of the entity
            entity_value: Value of the entity
            confidence: Confidence score for the extraction
        """
        if entity_type not in self.entities:
            self.entities[entity_type] = []
        
        self.entities[entity_type].append({
            "value": entity_value,
            "confidence": confidence,
            "timestamp": time.time()
        })
    
    def set_preference(self, key: str, value: Any):
        """
        Set a user preference.
        
        Args:
            key: Preference key
            value: Preference value
        """
        self.preferences[key] = {
            "value": value,
            "timestamp": time.time()
        }
    
    def get_messages(self, count: int = None) -> List[Dict[str, Any]]:
        """
        Get the conversation history.
        
        Args:
            count: Number of most recent messages to return, or None for all
            
        Returns:
            List[Dict[str, Any]]: The conversation history
        """
        if count is None:
            return list(self.messages)
        return list(self.messages)[-count:]
    
    def get_formatted_messages(self, count: int = None) -> List[Dict[str, str]]:
        """
        Get the conversation history formatted for LLM input.
        
        Args:
            count: Number of most recent messages to return, or None for all
            
        Returns:
            List[Dict[str, str]]: The formatted conversation history
        """
        messages = self.get_messages(count)
        return [{"role": msg["role"], "content": msg["content"]} for msg in messages]
    
    def get_entity(self, entity_type: str, most_recent: bool = True) -> Optional[Any]:
        """
        Get an extracted entity.
        
        Args:
            entity_type: Type of the entity
            most_recent: Whether to return only the most recent entity
            
        Returns:
            Optional[Any]: The entity value, or None if not found
        """
        if entity_type not in self.entities:
            return None
        
        if most_recent:
            # Sort by timestamp and return the most recent
            sorted_entities = sorted(self.entities[entity_type], key=lambda e: e["timestamp"], reverse=True)
            return sorted_entities[0]["value"] if sorted_entities else None
        
        # Return all entities of this type
        return [e["value"] for e in self.entities[entity_type]]
    
    def get_preference(self, key: str) -> Optional[Any]:
        """
        Get a user preference.
        
        Args:
            key: Preference key
            
        Returns:
            Optional[Any]: The preference value, or None if not set
        """
        if key not in self.preferences:
            return None
        return self.preferences[key]["value"]
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Convert the context to a dictionary.
        
        Returns:
            Dict[str, Any]: The context as a dictionary
        """
        return {
            "messages": list(self.messages),
            "entities": self.entities,
            "preferences": self.preferences,
            "session_data": self.session_data
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ConversationContext":
        """
        Create a context from a dictionary.
        
        Args:
            data: The dictionary to create the context from
            
        Returns:
            ConversationContext: The created context
        """
        context = cls()
        
        # Restore messages
        context.messages = deque(data.get("messages", []), maxlen=context.messages.maxlen)
        context.entities = data.get("entities", {})
        context.preferences = data.get("preferences", {})
        context.session_data = data.get("session_data", {
            "session_id": str(int(time.time())),
            "start_time": time.time(),
            "last_activity": time.time()
        })
        
        return context
    
    def save_to_file(self, filepath: str):
        """
        Save the context to a file.
        
        Args:
            filepath: Path to save the context to
        """
        with open(filepath, 'w') as f:
            json.dump(self.to_dict(), f, indent=2)
    
    @classmethod
    def load_from_file(cls, filepath: str) -> "ConversationContext":
        """
        Load a context from a file.
        
        Args:
            filepath: Path to load the context from
            
        Returns:
            ConversationContext: The loaded context
        """
        with open(filepath, 'r') as f:
            data = json.load(f)
        return cls.from_dict(data)
