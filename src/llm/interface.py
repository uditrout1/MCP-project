"""
Natural Language Interface module.
This module provides the main interface for natural language processing.
"""

from typing import Dict, Any, List, Optional, Union
import logging
from .models import LLMProvider, create_llm_provider
from .processors import NLProcessor
from .context import ConversationContext
from ..api.client import APIClient
from ..api.registry import registry

logger = logging.getLogger(__name__)


class NLInterface:
    """
    Natural Language Interface for the application.
    
    This class provides the main interface for processing natural language
    queries and interacting with APIs.
    """
    
    def __init__(self, llm_provider: LLMProvider = None, api_client: APIClient = None):
        """
        Initialize the Natural Language Interface.
        
        Args:
            llm_provider: LLM provider to use, defaults to OpenAI
            api_client: API client to use for making API calls
        """
        self.llm_provider = llm_provider or create_llm_provider("openai")
        self.api_client = api_client or APIClient(source_id="nl_interface")
        self.processor = NLProcessor(self.llm_provider, self.api_client)
        self.context = ConversationContext()
        
        # Update the processor with available APIs
        self._update_available_apis()
    
    def _update_available_apis(self):
        """Update the processor with information about available APIs."""
        available_apis = {}
        
        # Get the list of registered connectors
        connector_names = registry.list_connectors()
        
        for name in connector_names:
            connector = registry.get_connector(name)
            if connector:
                api_info = {
                    "description": f"{connector.api_type.value.upper()} API",
                    "endpoints": {}
                }
                
                # Add endpoint information if available
                if hasattr(connector, 'endpoints'):
                    for intent, endpoint_info in connector.endpoints.items():
                        api_info["endpoints"][intent] = {
                            "description": f"Endpoint for {intent}",
                            "params": list(endpoint_info.get('params_mapping', {}).keys())
                        }
                
                available_apis[name] = api_info
        
        # Update the processor
        self.processor.update_system_prompt(available_apis)
    
    def process_query(self, query: str) -> Dict[str, Any]:
        """
        Process a natural language query.
        
        Args:
            query: The natural language query
            
        Returns:
            Dict[str, Any]: The result of processing the query
        """
        # Add the query to the conversation context
        self.context.add_message("user", query)
        
        # Process the query
        result = self.processor.process_query(query)
        
        # Add the response to the conversation context
        if "error" in result:
            response_text = result["message"]
        else:
            response_text = result.get("formatted_response", str(result.get("raw_data", "")))
        
        self.context.add_message("assistant", response_text, metadata=result)
        
        # Extract entities if available
        if "api_called" in result and "raw_data" in result:
            # This is a simplified entity extraction - in a real system,
            # you would have more sophisticated entity extraction logic
            for key, value in result["raw_data"].items():
                if isinstance(value, (str, int, float, bool)):
                    self.context.add_entity(key, value)
        
        return result
    
    def get_conversation_history(self, count: int = None) -> List[Dict[str, Any]]:
        """
        Get the conversation history.
        
        Args:
            count: Number of most recent messages to return, or None for all
            
        Returns:
            List[Dict[str, Any]]: The conversation history
        """
        return self.context.get_messages(count)
    
    def explain_capabilities(self) -> str:
        """
        Generate an explanation of the system's capabilities.
        
        Returns:
            str: A natural language explanation of the system's capabilities
        """
        return self.processor.explain_api_capabilities()
    
    def save_context(self, filepath: str):
        """
        Save the conversation context to a file.
        
        Args:
            filepath: Path to save the context to
        """
        self.context.save_to_file(filepath)
    
    def load_context(self, filepath: str):
        """
        Load the conversation context from a file.
        
        Args:
            filepath: Path to load the context from
        """
        self.context = ConversationContext.load_from_file(filepath)
