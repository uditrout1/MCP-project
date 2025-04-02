"""
Natural Language Processing module.
This module provides functionality for processing natural language queries and converting them to API calls.
"""

from typing import Dict, Any, List, Optional, Union, Tuple
import json
import logging
from ..mcp.message import MCPMessage, Intent
from ..api.client import APIClient
from .models import LLMProvider, create_llm_provider

logger = logging.getLogger(__name__)


class NLProcessor:
    """
    Natural Language Processor for converting user queries to API calls.
    
    This class handles the conversion of natural language queries to structured
    API calls using LLMs, and formats API responses into natural language.
    """
    
    def __init__(self, llm_provider: LLMProvider = None, api_client: APIClient = None):
        """
        Initialize the Natural Language Processor.
        
        Args:
            llm_provider: LLM provider to use, defaults to OpenAI
            api_client: API client to use for making API calls
        """
        self.llm_provider = llm_provider or create_llm_provider("openai")
        self.api_client = api_client or APIClient(source_id="nl_processor")
        
        # Load prompt templates
        self.system_prompt = self._load_system_prompt()
    
    def _load_system_prompt(self) -> str:
        """
        Load the system prompt template.
        
        Returns:
            str: The system prompt template
        """
        # This would typically load from a file, but for simplicity we'll define it here
        return """
        You are an AI assistant that helps users interact with APIs using natural language.
        Your task is to convert natural language queries into structured API calls.
        
        For each user query, you should:
        1. Identify the intent of the query
        2. Determine which API should be called
        3. Extract relevant parameters from the query
        4. Format the extracted information into a JSON structure
        
        Your response should be a valid JSON object with the following structure:
        {
            "api_name": "name of the API to call",
            "intent": "intent of the API call (e.g., query, create, update, delete)",
            "parameters": {
                "param1": "value1",
                "param2": "value2",
                ...
            },
            "confidence": 0.95  // Your confidence in the interpretation (0.0 to 1.0)
        }
        
        If you cannot determine the API or intent with reasonable confidence, respond with:
        {
            "error": "Unable to determine API or intent",
            "message": "Please provide more specific information about what you're looking for."
        }
        
        Available APIs and their capabilities:
        {{AVAILABLE_APIS}}
        """
    
    def update_system_prompt(self, available_apis: Dict[str, Any]):
        """
        Update the system prompt with information about available APIs.
        
        Args:
            available_apis: Dictionary of available APIs and their capabilities
        """
        api_descriptions = []
        for api_name, api_info in available_apis.items():
            description = f"- {api_name}: {api_info.get('description', 'No description')}"
            
            # Add endpoints if available
            if 'endpoints' in api_info:
                description += "\n  Endpoints:"
                for intent, endpoint_info in api_info['endpoints'].items():
                    params = ", ".join(endpoint_info.get('params', []))
                    description += f"\n  - {intent}: {endpoint_info.get('description', '')} (Parameters: {params})"
            
            api_descriptions.append(description)
        
        # Join all API descriptions
        api_description_text = "\n".join(api_descriptions)
        
        # Update the system prompt
        self.system_prompt = self.system_prompt.replace("{{AVAILABLE_APIS}}", api_description_text)
    
    def process_query(self, query: str) -> Dict[str, Any]:
        """
        Process a natural language query and convert it to an API call.
        
        Args:
            query: The natural language query
            
        Returns:
            Dict[str, Any]: The result of the API call or an error message
        """
        try:
            # Extract API call information from the query
            api_info = self._extract_api_info(query)
            
            # Check if extraction was successful
            if "error" in api_info:
                return api_info
            
            # Make the API call
            response = self._make_api_call(api_info)
            
            # Format the response
            return self._format_response(response, query, api_info)
            
        except Exception as e:
            logger.exception(f"Error processing query: {e}")
            return {
                "error": "Processing Error",
                "message": f"An error occurred while processing your query: {str(e)}"
            }
    
    def _extract_api_info(self, query: str) -> Dict[str, Any]:
        """
        Extract API call information from a natural language query.
        
        Args:
            query: The natural language query
            
        Returns:
            Dict[str, Any]: The extracted API information
        """
        # Prepare the messages for the LLM
        messages = [
            {"role": "system", "content": self.system_prompt},
            {"role": "user", "content": query}
        ]
        
        # Generate a response from the LLM
        response_text = self.llm_provider.generate_chat_response(
            messages,
            temperature=0.2  # Lower temperature for more deterministic responses
        )
        
        # Parse the JSON response
        try:
            # Extract JSON from the response (in case there's additional text)
            json_start = response_text.find('{')
            json_end = response_text.rfind('}') + 1
            if json_start >= 0 and json_end > json_start:
                json_str = response_text[json_start:json_end]
                return json.loads(json_str)
            else:
                return {
                    "error": "Invalid Response",
                    "message": "The LLM did not return a valid JSON response."
                }
        except json.JSONDecodeError:
            return {
                "error": "Invalid JSON",
                "message": "The LLM returned a response that could not be parsed as JSON."
            }
    
    def _make_api_call(self, api_info: Dict[str, Any]) -> MCPMessage:
        """
        Make an API call based on the extracted information.
        
        Args:
            api_info: The extracted API information
            
        Returns:
            MCPMessage: The API response
        """
        api_name = api_info.get("api_name")
        intent = api_info.get("intent")
        parameters = api_info.get("parameters", {})
        
        # Make the API call
        return self.api_client.call_api(
            api_name=api_name,
            intent=intent,
            parameters=parameters
        )
    
    def _format_response(self, response: MCPMessage, original_query: str, api_info: Dict[str, Any]) -> Dict[str, Any]:
        """
        Format the API response into a user-friendly format.
        
        Args:
            response: The API response
            original_query: The original natural language query
            api_info: The API information used for the call
            
        Returns:
            Dict[str, Any]: The formatted response
        """
        # Check if the response is an error
        if response.message_type == "error":
            return {
                "error": response.payload.data.get("error_code", "API Error"),
                "message": response.payload.data.get("error_message", "An error occurred while calling the API.")
            }
        
        # Prepare the prompt for formatting the response
        format_prompt = f"""
        The user asked: "{original_query}"
        
        I called the {api_info['api_name']} API with the intent {api_info['intent']} and received the following response:
        {json.dumps(response.payload.data, indent=2)}
        
        Please format this response in a natural, conversational way that directly answers the user's question.
        Focus on the most relevant information and present it in a clear, concise manner.
        """
        
        # Generate a formatted response
        formatted_text = self.llm_provider.generate_text(format_prompt, temperature=0.7)
        
        # Return the formatted response along with the raw data
        return {
            "formatted_response": formatted_text,
            "raw_data": response.payload.data,
            "api_called": api_info['api_name'],
            "intent": api_info['intent']
        }
    
    def explain_api_capabilities(self) -> str:
        """
        Generate an explanation of the available API capabilities.
        
        Returns:
            str: A natural language explanation of available APIs
        """
        prompt = """
        Based on the available APIs described below, please provide a clear, concise explanation
        of what kinds of questions or tasks a user could ask the system to perform.
        Include a few example queries that would work well with these APIs.
        
        Available APIs:
        """ + self.system_prompt.split("Available APIs and their capabilities:")[1]
        
        return self.llm_provider.generate_text(prompt, temperature=0.7)
