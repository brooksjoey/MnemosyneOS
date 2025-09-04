"""
OpenAI Provider for MnemosyneOS.

This module implements the LLMProvider interface for OpenAI models,
supporting both text generation and embeddings.
"""
import os
import time
from typing import List, Dict, Any, Optional, Union

import openai
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

from app import logging_setup
from app.config import settings
from app.llm.provider import LLMProvider

# Initialize logger
logger = logging_setup.get_logger()

class OpenAIProvider(LLMProvider):
    """OpenAI implementation of LLMProvider"""
    
    def __init__(self):
        """Initialize the OpenAI provider"""
        self.api_key = settings.OPENAI_API_KEY
        
        if not self.api_key:
            logger.warning("OpenAI API key not set, some functionality may be limited")
            
        # Set API key for the OpenAI client
        openai.api_key = self.api_key
        
        # Default model names
        self.default_model = settings.DEFAULT_MODEL
        self.embedding_model = "text-embedding-3-large"
        
        logger.info(f"Initialized OpenAI provider with model: {self.default_model}")
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=4, max=10),
        retry=retry_if_exception_type((openai.RateLimitError, openai.APITimeoutError))
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
        Generate text from the OpenAI model.
        
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
            # Convert to chat format for newer models
            messages = [{"role": "user", "content": prompt}]
            
            # Call the OpenAI API
            response = openai.chat.completions.create(
                model=self.default_model,
                messages=messages,
                max_tokens=max_tokens,
                temperature=temperature,
                top_p=top_p,
                stop=stop_sequences
            )
            
            # Extract the generated text
            generated_text = response.choices[0].message.content
            
            logger.info(f"Generated {len(generated_text)} characters with OpenAI model")
            return generated_text
            
        except openai.RateLimitError as e:
            logger.warning(f"OpenAI rate limit exceeded: {e}")
            # Wait and retry (handled by tenacity)
            raise
            
        except openai.APITimeoutError as e:
            logger.warning(f"OpenAI API timeout: {e}")
            # Wait and retry (handled by tenacity)
            raise
            
        except Exception as e:
            logger.error(f"Error generating text with OpenAI: {str(e)}")
            # For other errors, return an error message
            return f"Error generating text: {str(e)}"
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=4, max=10),
        retry=retry_if_exception_type((openai.RateLimitError, openai.APITimeoutError))
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
        Generate chat response from the OpenAI model.
        
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
            # Call the OpenAI API
            response = openai.chat.completions.create(
                model=self.default_model,
                messages=messages,
                max_tokens=max_tokens,
                temperature=temperature,
                top_p=top_p,
                stop=stop_sequences
            )
            
            # Extract the generated text
            generated_text = response.choices[0].message.content
            
            logger.info(f"Generated {len(generated_text)} characters with OpenAI chat model")
            return generated_text
            
        except openai.RateLimitError as e:
            logger.warning(f"OpenAI rate limit exceeded: {e}")
            # Wait and retry (handled by tenacity)
            raise
            
        except openai.APITimeoutError as e:
            logger.warning(f"OpenAI API timeout: {e}")
            # Wait and retry (handled by tenacity)
            raise
            
        except Exception as e:
            logger.error(f"Error generating chat with OpenAI: {str(e)}")
            # For other errors, return an error message
            return f"Error generating chat response: {str(e)}"
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=4, max=10),
        retry=retry_if_exception_type((openai.RateLimitError, openai.APITimeoutError))
    )
    def get_embedding(self, text: str) -> List[float]:
        """
        Get embedding vector for text using OpenAI.
        
        Args:
            text: The input text
            
        Returns:
            Embedding vector as list of floats
        """
        try:
            # Truncate long texts (OpenAI has an 8K token limit for embeddings)
            if len(text) > 20000:  # Rough approximation
                logger.warning(f"Truncating long text for embedding ({len(text)} chars)")
                text = text[:20000]
                
            # Call the OpenAI API
            response = openai.embeddings.create(
                model=self.embedding_model,
                input=text
            )
            
            # Extract the embedding
            embedding = response.data[0].embedding
            
            logger.info(f"Generated embedding with {len(embedding)} dimensions")
            return embedding
            
        except openai.RateLimitError as e:
            logger.warning(f"OpenAI rate limit exceeded for embedding: {e}")
            # Wait and retry (handled by tenacity)
            raise
            
        except openai.APITimeoutError as e:
            logger.warning(f"OpenAI API timeout for embedding: {e}")
            # Wait and retry (handled by tenacity)
            raise
            
        except Exception as e:
            logger.error(f"Error generating embedding with OpenAI: {str(e)}")
            # For embedding errors, return a zero vector of standard size
            return [0.0] * 1536  # Default size for OpenAI embeddings
    
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
        # Rough estimate: 1 token ≈ 0.75 words
        word_count = len(text.split())
        return int(word_count / 0.75)
