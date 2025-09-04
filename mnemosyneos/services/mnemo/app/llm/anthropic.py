"""
Anthropic Provider for MnemosyneOS.

This module implements the LLMProvider interface for Anthropic Claude models,
supporting text generation and adapting to the embeddings interface.
"""
import os
import time
from typing import List, Dict, Any, Optional, Union

import httpx
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

from app import logging_setup
from app.config import settings
from app.llm.provider import LLMProvider

# Initialize logger
logger = logging_setup.get_logger()

class AnthropicProvider(LLMProvider):
    """Anthropic implementation of LLMProvider"""
    
    def __init__(self):
        """Initialize the Anthropic provider"""
        self.api_key = settings.ANTHROPIC_API_KEY
        
        if not self.api_key:
            logger.warning("Anthropic API key not set, some functionality may be limited")
            
        # Set base URL for API requests
        self.api_base = "https://api.anthropic.com/v1"
        
        # Default model names - Claude 3 is the default
        self.default_model = "claude-3-opus-20240229"
        
        # Since Anthropic doesn't have an embeddings model,
        # we'll need to use OpenAI for that part
        self.use_openai_for_embeddings = True
        
        logger.info(f"Initialized Anthropic provider with model: {self.default_model}")
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=4, max=10)
    )
    def generate_text(
        self,
        prompt: str,
        max_tokens: Optional[int] = None,
        temperature: float = 0.7,
        top_p: float = 1.0,
        stop_sequences: Optional[List[str]] = None
    ) -> str:
        """
        Generate text from the Anthropic model.
        
        Args:
            prompt: The input prompt
            max_tokens: Maximum number of tokens to generate
            temperature: Sampling temperature (0.0 to 1.0)
            top_p: Nucleus sampling parameter
            stop_sequences: List of sequences that stop generation
            
        Returns:
            Generated text
        """
        try:
            # For Anthropic, convert to a simple message format
            messages = [
                {"role": "user", "content": prompt}
            ]
            
            # Call generate_chat with the message format
            return self.generate_chat(
                messages=messages,
                max_tokens=max_tokens,
                temperature=temperature,
                top_p=top_p,
                stop_sequences=stop_sequences
            )
            
        except Exception as e:
            logger.error(f"Error generating text with Anthropic: {str(e)}")
            return f"Error generating text: {str(e)}"
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=4, max=10)
    )
    def generate_chat(
        self,
        messages: List[Dict[str, str]],
        max_tokens: Optional[int] = None,
        temperature: float = 0.7,
        top_p: float = 1.0,
        stop_sequences: Optional[List[str]] = None
    ) -> str:
        """
        Generate chat response from the Anthropic model.
        
        Args:
            messages: List of message dictionaries with 'role' and 'content'
            max_tokens: Maximum number of tokens to generate
            temperature: Sampling temperature (0.0 to 1.0)
            top_p: Nucleus sampling parameter
            stop_sequences: List of sequences that stop generation
            
        Returns:
            Generated text
        """
        try:
            # Set default max tokens if not provided
            if max_tokens is None:
                max_tokens = 4096
                
            # Convert messages to Anthropic format
            # Anthropic uses "user" and "assistant" roles
            anthropic_messages = []
            for message in messages:
                role = message.get("role", "user")
                if role == "system":
                    # Anthropic handles system messages differently
                    # We'll incorporate it into the first user message
                    continue
                elif role == "user":
                    anthropic_messages.append({"role": "user", "content": message["content"]})
                elif role == "assistant":
                    anthropic_messages.append({"role": "assistant", "content": message["content"]})
                    
            # Prepare the request data
            data = {
                "model": self.default_model,
                "messages": anthropic_messages,
                "max_tokens": max_tokens,
                "temperature": temperature,
                "top_p": top_p
            }
            
            # Add stop sequences if provided
            if stop_sequences:
                data["stop_sequences"] = stop_sequences
                
            # Make the API request
            headers = {
                "Content-Type": "application/json",
                "X-API-Key": self.api_key,
                "anthropic-version": "2023-06-01"
            }
            
            with httpx.Client(timeout=60.0) as client:
                response = client.post(
                    f"{self.api_base}/messages",
                    json=data,
                    headers=headers
                )
                response.raise_for_status()
                
            # Parse the response
            result = response.json()
            
            # Extract the generated text
            generated_text = result.get("content", [{"text": "No response generated"}])[0].get("text", "")
            
            logger.info(f"Generated {len(generated_text)} characters with Anthropic model")
            return generated_text
            
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 429:
                logger.warning(f"Anthropic rate limit exceeded: {e}")
                # Wait and retry (handled by tenacity)
                raise
                
            logger.error(f"HTTP error with Anthropic API: {e.response.status_code} - {e.response.text}")
            return f"Error generating chat response: HTTP {e.response.status_code}"
            
        except httpx.TimeoutException as e:
            logger.warning(f"Anthropic API timeout: {e}")
            # Wait and retry (handled by tenacity)
            raise
            
        except Exception as e:
            logger.error(f"Error generating chat with Anthropic: {str(e)}")
            return f"Error generating chat response: {str(e)}"
    
    def get_embedding(self, text: str) -> List[float]:
        """
        Get embedding vector for text using Anthropic.
        
        Note: Anthropic doesn't provide embeddings directly, so this method
        falls back to OpenAI's embedding API or a local alternative.
        
        Args:
            text: The input text
            
        Returns:
            Embedding vector as list of floats
        """
        try:
            # If OpenAI fallback is enabled, use it
            if self.use_openai_for_embeddings and settings.OPENAI_API_KEY:
                # Import here to avoid circular dependencies
                from app.llm.openai import OpenAIProvider
                openai_provider = OpenAIProvider()
                return openai_provider.get_embedding(text)
                
            # If no OpenAI fallback, try to use a local alternative
            # For now, return a zero vector as placeholder
            logger.warning("No embedding provider available for Anthropic - returning zero vector")
            return [0.0] * 1536  # Standard size compatible with OpenAI embeddings
            
        except Exception as e:
            logger.error(f"Error generating embedding: {str(e)}")
            # Return zero vector on error
            return [0.0] * 1536
    
    def get_model_name(self) -> str:
        """
        Get the name of the currently used model.
        
        Returns:
            Model name
        """
        return self.default_model
    
    def get_token_estimate(self, text: str) -> int:
        """
        Estimate the number of tokens in a text.
        This is a rough approximation based on words.
        
        Args:
            text: The input text
            
        Returns:
            Estimated token count
        """
        # Rough estimate: 1 token ≈ 0.75 words (similar to OpenAI)
        word_count = len(text.split())
        return int(word_count / 0.75)
