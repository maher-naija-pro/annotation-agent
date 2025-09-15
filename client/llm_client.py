#!/usr/bin/env python3
"""
Simple Python script to interact with OpenAI-compatible LLM endpoints.
Supports configurable endpoint URL and model name using functional programming.
"""

import os
from typing import Optional, Dict, Any, List
from openai import OpenAI


def create_client(endpoint_url: str, model_name: str, api_key: Optional[str] = None) -> OpenAI:
    """
    Create an OpenAI client with custom endpoint configuration.
    
    Args:
        endpoint_url (str): The base URL of the OpenAI-compatible endpoint
        model_name (str): The name of the model to use
        api_key (str, optional): API key for authentication. If None, will try to get from environment
        
    Returns:
        OpenAI: Configured OpenAI client
    """
    # Clean endpoint URL
    clean_endpoint = endpoint_url.rstrip('/')
    
    # Get API key from parameter or environment
    final_api_key = api_key or os.getenv('OPENAI_API_KEY')
    
    # For Ollama and other local servers, we might not need an API key
    # If no API key is provided and we're connecting to a local server, use empty string
    if final_api_key is None and ('localhost' in clean_endpoint or '127.0.0.1' in clean_endpoint or '148.253.83.132' in clean_endpoint):
        final_api_key = ""
    
    # Create and return the client
    return OpenAI(
        base_url=clean_endpoint,
        api_key=final_api_key
    )


def chat_completion(client: OpenAI, 
                   model_name: str,
                   messages: List[Dict[str, str]], 
                   temperature: float = 0.7, 
                   max_tokens: int = 1000,
                   **kwargs) -> Dict[str, Any]:
    """
    Send a chat completion request to the LLM.
    
    Args:
        client (OpenAI): The OpenAI client instance
        model_name (str): The name of the model to use
        messages (List[Dict]): List of message dictionaries with 'role' and 'content'
        temperature (float): Sampling temperature (0.0 to 2.0)
        max_tokens (int): Maximum number of tokens to generate
        **kwargs: Additional parameters to pass to the API
        
    Returns:
        Dict containing the response from the LLM
    """
    try:
        response = client.chat.completions.create(
            model=model_name,
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,
            **kwargs
        )
        
        return {
            'success': True,
            'content': response.choices[0].message.content,
            'usage': {
                'prompt_tokens': response.usage.prompt_tokens,
                'completion_tokens': response.usage.completion_tokens,
                'total_tokens': response.usage.total_tokens
            },
            'model': response.model,
            'finish_reason': response.choices[0].finish_reason
        }
        
    except Exception as e:
        return {
            'success': False,
            'error': str(e),
            'content': None
        }


def simple_query(client: OpenAI, model_name: str, prompt: str, **kwargs) -> str:
    """
    Send a simple text query and return just the response content.
    
    Args:
        client (OpenAI): The OpenAI client instance
        model_name (str): The name of the model to use
        prompt (str): The text prompt to send
        **kwargs: Additional parameters for chat_completion
        
    Returns:
        str: The response content from the LLM, or error message
    """
    messages = [{"role": "user", "content": prompt}]
    response = chat_completion(client, model_name, messages, **kwargs)
    
    if response['success']:
        return response['content']
    else:
        return f"Error: {response['error']}"


def get_config() -> Dict[str, str]:
    """
    Get configuration from environment variables with defaults.
    
    Returns:
        Dict containing endpoint_url, model_name, and api_key
    """
    return {
        'endpoint_url': os.getenv('LLM_ENDPOINT_URL', 'https://api.openai.com/v1'),
        'model_name': os.getenv('LLM_MODEL_NAME', 'gpt-3.5-turbo'),
        'api_key': os.getenv('OPENAI_API_KEY')
    }


def main():
    """
    Example usage of the LLM functions.
    """
    # Get configuration
    config = get_config()
    
    # Check if API key is provided
    if not config['api_key']:
        print("Warning: No API key found. Set OPENAI_API_KEY environment variable.")
        print("You can also set LLM_ENDPOINT_URL and LLM_MODEL_NAME environment variables.")
        print()
    
    # Create the client
    client = create_client(
        endpoint_url=config['endpoint_url'],
        model_name=config['model_name'],
        api_key=config['api_key']
    )
    
    print(f"LLM Client initialized:")
    print(f"  Endpoint: {config['endpoint_url']}")
    print(f"  Model: {config['model_name']}")
    print(f"  API Key: {'***' + config['api_key'][-4:] if config['api_key'] else 'Not set'}")
    print()
    
    # Example 1: Simple query
    print("Example 1: Simple query")
    print("-" * 30)
    prompt = "What is the capital of France?"
    response = simple_query(client, config['model_name'], prompt)
    print(f"Prompt: {prompt}")
    print(f"Response: {response}")
    print()
    
    # Example 2: Chat conversation
    print("Example 2: Chat conversation")
    print("-" * 30)
    messages = [
        {"role": "system", "content": "You are a helpful assistant that explains things clearly."},
        {"role": "user", "content": "Explain what machine learning is in simple terms."}
    ]
    
    response = chat_completion(client, config['model_name'], messages, temperature=0.5)
    
    if response['success']:
        print(f"Response: {response['content']}")
        print(f"Tokens used: {response['usage']['total_tokens']}")
    else:
        print(f"Error: {response['error']}")


if __name__ == "__main__":
    main()
