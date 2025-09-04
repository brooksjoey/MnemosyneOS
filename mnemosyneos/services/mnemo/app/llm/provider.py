"""
Abstract LLM Provider for MnemosyneOS.

This module defines the interface for LLM providers and factory methods
to get the appropriate provider based on configuration.
"""
from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional, Union

from app import logging_setup
from app.config import settings

# Initialize logger
logger = logging_setup.get_logger()

class LLMProvider(ABC):
    """Abstract base class for LLM providers"""
    
    @abstractmethod
    def generate_text(
        self,
        prompt: str,
        max_tokens: Optional[int] = None,
        temperature: float = 0.7,
        top_p: float = 1.0,
        stop_sequences: Optional[List[str]] = None
    ) -> str:
        """
        Generate text from the LLM.
        
        Args:
            prompt: The input prompt
            max_tokens: Maximum number of tokens to generate
            temperature: Sampling temperature (0.0 to 1.0)
            top_p: Nucleus sampling parameter
            stop_sequences: List of sequences that stop generation
            
        Returns:
            Generated text
        """
        pass
    
    @abstractmethod
    def generate_chat(
        self,
        messages: List[Dict[str, str]],
        max_tokens: Optional[int] = None,
        temperature: float = 0.7,
        top_p: float = 1.0,
        stop_sequences: Optional[List[str]] = None
    ) -> str:
        """
        Generate chat response from the LLM.
        
        Args:
            messages: List of message dictionaries with 'role' and 'content'
            max_tokens: Maximum number of tokens to generate
            temperature: Sampling temperature (0.0 to 1.0)
            top_p: Nucleus sampling parameter
            stop_sequences: List of sequences that stop generation
            
        Returns:
            Generated text
        """
        pass
    
    @abstractmethod
    def get_embedding(self, text: str) -> List[float]:
        """
        Get embedding vector for text.
        
        Args:
            text: The input text
            
        Returns:
            Embedding vector as list of floats
        """
        pass
    
    @abstractmethod
    def get_model_name(self) -> str:
        """
        Get the name of the currently used model.
        
        Returns:
            Model name
        """
        pass

def get_llm() -> LLMProvider:
    """
    Get the appropriate LLM provider based on configuration.
    
    Returns:
        LLM provider instance
    """
    provider_name = settings.LVC_PROVIDER.lower()
    
    if provider_name == "openai":
        from app.llm.openai import OpenAIProvider
        return OpenAIProvider()
    elif provider_name == "anthropic":
        from app.llm.anthropic import AnthropicProvider
        return AnthropicProvider()
    elif provider_name == "deepseek":
        from app.llm.deepseek import DeepSeekProvider
        return DeepSeekProvider()
    else:
        logger.warning(f"Unknown LLM provider: {provider_name}, falling back to OpenAI")
        from app.llm.openai import OpenAIProvider
        return OpenAIProvider()

def get_embedding_provider() -> LLMProvider:
    """
    Get the appropriate embedding provider.
    Currently uses the same provider as the LLM.
    
    Returns:
        LLM provider instance for embeddings
    """
    return get_llm()

def chat_to_text(messages: List[Dict[str, str]], system_prompt: Optional[str] = None) -> str:
    """
    Convert chat messages to a single text prompt.
    Useful for providers that don't support chat format.
    
    Args:
        messages: List of message dictionaries with 'role' and 'content'
        system_prompt: Optional system prompt to prepend
        
    Returns:
        Single text prompt
    """
    prompt = ""
    
    # Add system prompt if provided
    if system_prompt:
        prompt += f"System: {system_prompt}\n\n"
    
    # Add messages
    for message in messages:
        role = message.get("role", "user").capitalize()
        content = message.get("content", "")
        prompt += f"{role}: {content}\n\n"
    
    # Add assistant prompt
    prompt += "Assistant: "
    
    return prompt

def text_to_chat(prompt: str) -> List[Dict[str, str]]:
    """
    Convert a text prompt to chat messages.
    Simplistic conversion, assumes the prompt is from the user.
    
    Args:
        prompt: Text prompt
        
    Returns:
        List with a single user message
    """
    return [{"role": "user", "content": prompt}]
