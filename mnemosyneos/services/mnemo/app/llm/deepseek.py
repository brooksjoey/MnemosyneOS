"""
DeepSeek Provider for MnemosyneOS.

This module implements the LLMProvider interface for DeepSeek AI models,
supporting text generation and adapting to the embeddings interface.
"""
import os
import time
import json
from typing import List, Dict, Any, Optional, Union

import httpx
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

from app import logging_setup
from app.config import settings
from app.llm.provider import LLMProvider

# Initialize logger
logger = logging_setup.get_logger()

class DeepSeekProvider(LLMProvider):
    """DeepSeek implementation of LLMProvider"""
    
    def __init__(self):
        """Initialize the DeepSeek provider"""
        self.api_key = settings.DEEPSEEK_API_KEY
        
        if not self.api_key:
            logger.warning("DeepSeek API key not set, some functionality may be limited")
            
        # Set base URL for API requests
        self.api_base = "https://api.deepseek.com/v1"
        
        # Default model names
        self.default_model = "deepseek-chat"
        
        # Like Anthropic, DeepSeek doesn't have a dedicated embeddings model,
        # so we'll need a fallback for that
        self.use_openai_for_embeddings = True
        
        logger.info(f"Initialized DeepSeek provider with model: {self.default_model}")
    
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
        Generate text from the DeepSeek model.
        
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
            # For DeepSeek, convert to a simple message format
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
            logger.error(f"Error generating text with DeepSeek: {str(e)}")
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
        Generate chat response from the DeepSeek model.
        
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
                max_tokens = 2048
                
            # DeepSeek uses similar message format to OpenAI
            # with "user", "assistant", and "system" roles
            deepseek_messages = []
            
            # Extract system message if present
            system_message = None
            for message in messages:
                if message.get("role") == "system":
                    system_message = message["content"]
                    break
                    
            # Add system message if found
            if system_message:
                deepseek_messages.append({"role": "system", "content": system_message})
                
            # Add other messages
            for message in messages:
                role = message.get("role", "user")
                if role != "system":  # Skip system messages as we've already handled them
                    deepseek_messages.append({"role": role, "content": message["content"]})
                    
            # Prepare the request data
            data = {
                "model": self.default_model,
                "messages": deepseek_messages,
                "max_tokens": max_tokens,
                "temperature": temperature,
                "top_p": top_p
            }
            
            # Add stop sequences if provided
            if stop_sequences:
                data["stop"] = stop_sequences
                
            # Make the API request
            headers = {
                "Content-Type": "application/json",
                "Authorization": f"Bearer {self.api_key}"
            }
            
            with httpx.Client(timeout=60.0) as client:
                response = client.post(
                    f"{self.api_base}/chat/completions",
                    json=data,
                    headers=headers
                )
                response.raise_for_status()
                
            # Parse the response
            result = response.json()
            
            # Extract the generated text
            generated_text = result.get("choices", [{}])[0].get("message", {}).get("content", "")
            
            logger.info(f"Generated {len(generated_text)} characters with DeepSeek model")
            return generated_text
            
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 429:
                logger.warning(f"DeepSeek rate limit exceeded: {e}")
                # Wait and retry (handled by tenacity)
                raise
                
            logger.error(f"HTTP error with DeepSeek API: {e.response.status_code} - {e.response.text}")
            return f"Error generating chat response: HTTP {e.response.status_code}"
            
        except httpx.TimeoutException as e:
            logger.warning(f"DeepSeek API timeout: {e}")
            # Wait and retry (handled by tenacity)
            raise
            
        except Exception as e:
            logger.error(f"Error generating chat with DeepSeek: {str(e)}")
            return f"Error generating chat response: {str(e)}"
    
    def get_embedding(self, text: str) -> List[float]:
        """
        Get embedding vector for text using DeepSeek.
        
        Note: DeepSeek may not provide embeddings directly, so this method
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
                
            # If DeepSeek adds embedding support in the future, implement it here
            
            # If no OpenAI fallback, try to use a local alternative
            # For now, return a zero vector as placeholder
            logger.warning("No embedding provider available for DeepSeek - returning zero vector")
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
