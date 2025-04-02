"""
LLM Provider module.
This module provides interfaces for different LLM providers.
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional, Union
import os
import logging
import openai
from langchain.llms import OpenAI as LangchainOpenAI
from langchain.chat_models import ChatOpenAI
from langchain.schema import HumanMessage, SystemMessage, AIMessage

logger = logging.getLogger(__name__)


class LLMProvider(ABC):
    """
    Abstract base class for LLM providers.
    
    This class defines the interface for interacting with different LLM providers.
    """
    
    @abstractmethod
    def generate_text(self, prompt: str, **kwargs) -> str:
        """
        Generate text based on a prompt.
        
        Args:
            prompt: The input prompt
            **kwargs: Additional parameters for the LLM
            
        Returns:
            str: The generated text
        """
        pass
    
    @abstractmethod
    def generate_chat_response(self, messages: List[Dict[str, str]], **kwargs) -> str:
        """
        Generate a response in a chat context.
        
        Args:
            messages: List of messages in the conversation
            **kwargs: Additional parameters for the LLM
            
        Returns:
            str: The generated response
        """
        pass


class OpenAIProvider(LLMProvider):
    """
    Provider for OpenAI's language models.
    """
    
    def __init__(self, api_key: str = None, model: str = "gpt-4"):
        """
        Initialize the OpenAI provider.
        
        Args:
            api_key: OpenAI API key, defaults to environment variable
            model: Model to use, defaults to gpt-4
        """
        self.api_key = api_key or os.environ.get("OPENAI_API_KEY")
        if not self.api_key:
            logger.warning("No OpenAI API key provided. Set OPENAI_API_KEY environment variable.")
        
        self.model = model
        openai.api_key = self.api_key
    
    def generate_text(self, prompt: str, **kwargs) -> str:
        """
        Generate text using OpenAI's completion API.
        
        Args:
            prompt: The input prompt
            **kwargs: Additional parameters for the API
            
        Returns:
            str: The generated text
        """
        try:
            # Set default parameters
            params = {
                "model": self.model,
                "temperature": 0.7,
                "max_tokens": 1000,
            }
            # Update with any provided parameters
            params.update(kwargs)
            
            # Create messages for the chat completion API
            messages = [{"role": "user", "content": prompt}]
            
            # Call the API
            response = openai.chat.completions.create(
                messages=messages,
                **params
            )
            
            # Extract and return the generated text
            return response.choices[0].message.content.strip()
            
        except Exception as e:
            logger.error(f"Error generating text with OpenAI: {e}")
            return f"Error: {str(e)}"
    
    def generate_chat_response(self, messages: List[Dict[str, str]], **kwargs) -> str:
        """
        Generate a response using OpenAI's chat completion API.
        
        Args:
            messages: List of messages in the conversation
            **kwargs: Additional parameters for the API
            
        Returns:
            str: The generated response
        """
        try:
            # Set default parameters
            params = {
                "model": self.model,
                "temperature": 0.7,
                "max_tokens": 1000,
            }
            # Update with any provided parameters
            params.update(kwargs)
            
            # Format messages for the API
            formatted_messages = []
            for msg in messages:
                role = msg.get("role", "user")
                content = msg.get("content", "")
                formatted_messages.append({"role": role, "content": content})
            
            # Call the API
            response = openai.chat.completions.create(
                messages=formatted_messages,
                **params
            )
            
            # Extract and return the generated text
            return response.choices[0].message.content.strip()
            
        except Exception as e:
            logger.error(f"Error generating chat response with OpenAI: {e}")
            return f"Error: {str(e)}"


class LangchainProvider(LLMProvider):
    """
    Provider that uses Langchain for LLM integration.
    """
    
    def __init__(self, api_key: str = None, model: str = "gpt-4"):
        """
        Initialize the Langchain provider.
        
        Args:
            api_key: OpenAI API key, defaults to environment variable
            model: Model to use, defaults to gpt-4
        """
        self.api_key = api_key or os.environ.get("OPENAI_API_KEY")
        if not self.api_key:
            logger.warning("No OpenAI API key provided. Set OPENAI_API_KEY environment variable.")
        
        self.model = model
        os.environ["OPENAI_API_KEY"] = self.api_key
        
        # Initialize Langchain models
        self.llm = LangchainOpenAI(model_name=model, temperature=0.7)
        self.chat_model = ChatOpenAI(model_name=model, temperature=0.7)
    
    def generate_text(self, prompt: str, **kwargs) -> str:
        """
        Generate text using Langchain's LLM interface.
        
        Args:
            prompt: The input prompt
            **kwargs: Additional parameters for the LLM
            
        Returns:
            str: The generated text
        """
        try:
            # Update parameters if provided
            if kwargs:
                # Create a new instance with updated parameters
                temp_llm = LangchainOpenAI(model_name=self.model, **kwargs)
                return temp_llm.predict(prompt)
            
            # Use the default instance
            return self.llm.predict(prompt)
            
        except Exception as e:
            logger.error(f"Error generating text with Langchain: {e}")
            return f"Error: {str(e)}"
    
    def generate_chat_response(self, messages: List[Dict[str, str]], **kwargs) -> str:
        """
        Generate a response using Langchain's chat model.
        
        Args:
            messages: List of messages in the conversation
            **kwargs: Additional parameters for the chat model
            
        Returns:
            str: The generated response
        """
        try:
            # Convert messages to Langchain format
            langchain_messages = []
            for msg in messages:
                role = msg.get("role", "user")
                content = msg.get("content", "")
                
                if role == "system":
                    langchain_messages.append(SystemMessage(content=content))
                elif role == "user":
                    langchain_messages.append(HumanMessage(content=content))
                elif role == "assistant":
                    langchain_messages.append(AIMessage(content=content))
            
            # Update parameters if provided
            if kwargs:
                # Create a new instance with updated parameters
                temp_chat_model = ChatOpenAI(model_name=self.model, **kwargs)
                return temp_chat_model.predict_messages(langchain_messages).content
            
            # Use the default instance
            return self.chat_model.predict_messages(langchain_messages).content
            
        except Exception as e:
            logger.error(f"Error generating chat response with Langchain: {e}")
            return f"Error: {str(e)}"


# Factory function to create LLM providers
def create_llm_provider(provider_type: str = "openai", **kwargs) -> LLMProvider:
    """
    Create an LLM provider of the specified type.
    
    Args:
        provider_type: Type of provider ("openai" or "langchain")
        **kwargs: Additional parameters for the provider
        
    Returns:
        LLMProvider: The created provider
    """
    if provider_type.lower() == "openai":
        return OpenAIProvider(**kwargs)
    elif provider_type.lower() == "langchain":
        return LangchainProvider(**kwargs)
    else:
        raise ValueError(f"Unsupported provider type: {provider_type}")
