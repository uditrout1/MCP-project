"""
Prompt templates module.
This module provides prompt templates for different LLM tasks.
"""

from typing import Dict, Any, List

# System prompt for API extraction
API_EXTRACTION_PROMPT = """
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
{available_apis}
"""

# Prompt for formatting API responses
RESPONSE_FORMATTING_PROMPT = """
The user asked: "{original_query}"

I called the {api_name} API with the intent {intent} and received the following response:
{api_response}

Please format this response in a natural, conversational way that directly answers the user's question.
Focus on the most relevant information and present it in a clear, concise manner.
"""

# Prompt for explaining API capabilities
API_CAPABILITIES_PROMPT = """
Based on the available APIs described below, please provide a clear, concise explanation
of what kinds of questions or tasks a user could ask the system to perform.
Include a few example queries that would work well with these APIs.

Available APIs:
{available_apis}
"""

# Prompt for handling ambiguous queries
AMBIGUOUS_QUERY_PROMPT = """
The user's query: "{original_query}"

This query is ambiguous and could be interpreted in multiple ways. Please ask clarifying questions
to better understand what the user is looking for. Consider the following possible interpretations:

{possible_interpretations}

Generate 2-3 specific questions that would help clarify the user's intent.
"""

# Prompt for generating few-shot examples
FEW_SHOT_EXAMPLES_PROMPT = """
Here are some examples of natural language queries and their corresponding API calls:

Query: "Show me the weather in New York"
API Call: {{"api_name": "weather", "intent": "query", "parameters": {{"location": "New York"}}}}

Query: "What's the current price of Apple stock?"
API Call: {{"api_name": "stocks", "intent": "query", "parameters": {{"symbol": "AAPL"}}}}

Query: "Book a meeting with John on Friday at 2pm"
API Call: {{"api_name": "calendar", "intent": "create", "parameters": {{"attendee": "John", "day": "Friday", "time": "14:00"}}}}

Now, convert the following query into an API call:
{user_query}
"""

def get_api_extraction_prompt(available_apis: Dict[str, Any]) -> str:
    """
    Get the API extraction prompt with available APIs information.
    
    Args:
        available_apis: Dictionary of available APIs and their capabilities
        
    Returns:
        str: The formatted prompt
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
    
    # Return the formatted prompt
    return API_EXTRACTION_PROMPT.format(available_apis=api_description_text)

def get_response_formatting_prompt(original_query: str, api_name: str, intent: str, api_response: str) -> str:
    """
    Get the response formatting prompt.
    
    Args:
        original_query: The original user query
        api_name: The name of the API that was called
        intent: The intent of the API call
        api_response: The API response as a string
        
    Returns:
        str: The formatted prompt
    """
    return RESPONSE_FORMATTING_PROMPT.format(
        original_query=original_query,
        api_name=api_name,
        intent=intent,
        api_response=api_response
    )

def get_api_capabilities_prompt(available_apis: str) -> str:
    """
    Get the API capabilities explanation prompt.
    
    Args:
        available_apis: Description of available APIs
        
    Returns:
        str: The formatted prompt
    """
    return API_CAPABILITIES_PROMPT.format(available_apis=available_apis)

def get_ambiguous_query_prompt(original_query: str, possible_interpretations: List[str]) -> str:
    """
    Get the ambiguous query handling prompt.
    
    Args:
        original_query: The original user query
        possible_interpretations: List of possible interpretations
        
    Returns:
        str: The formatted prompt
    """
    interpretations_text = "\n".join([f"- {interp}" for interp in possible_interpretations])
    return AMBIGUOUS_QUERY_PROMPT.format(
        original_query=original_query,
        possible_interpretations=interpretations_text
    )

def get_few_shot_examples_prompt(user_query: str) -> str:
    """
    Get the few-shot examples prompt.
    
    Args:
        user_query: The user query to convert
        
    Returns:
        str: The formatted prompt
    """
    return FEW_SHOT_EXAMPLES_PROMPT.format(user_query=user_query)
