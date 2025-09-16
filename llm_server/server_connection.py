"""
Server Connection Module

This module provides functions for setting up connections to LLM inference servers
and executing queries against them.
"""

import sys
import os
from typing import Dict, Any

# Add the client directory to the Python path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'client'))

from llm_client import create_client, simple_query


def setup_inference_server_connection(model_name: str = "gpt-oss:20b") -> Dict[str, Any]:
    """
    Setup connection to the inference server at 148.253.83.132.

    Args:
        model_name: Name of the model to use (default: "gpt-oss:20b")

    Returns:
        Dict containing client and configuration information
    """
    # Configure for inference server - using the exact endpoint that works with curl
    endpoint_url = "http://148.253.83.132:11434/v1"  # OpenAI-compatible endpoint
    api_key = ""  # Empty string for inference server (no API key required)

    print(f"Connecting to inference server with model '{model_name}'...")

    # Create the client with proper API key handling for Ollama
    client = create_client(
        endpoint_url=endpoint_url,
        model_name=model_name,
        api_key=""  # Empty string for Ollama
    )
    
    return {
        'client': client,
        'endpoint_url': endpoint_url,
        'model_name': model_name,
        'api_key': api_key
    }


def query_llm(connection_info: Dict[str, Any], prompt: str) -> str:
    """
    Run a single query with the Ollama model.

    Args:
        connection_info: Dictionary containing client and config info
        prompt: The prompt text to send to the model
        
    Returns:
        The response from the LLM model
    """
    print("Running query...")
    print("-" * 40)
    
    print(f"Prompt: {prompt}")
    print("-" * 40)

    try:
        response = simple_query(
            client=connection_info['client'],
            model_name=connection_info['model_name'],
            prompt=prompt,
            temperature=0.7,
            max_tokens=500
        )
        
        print(response)
        print("-" * 40)
        
        return response
        
    except Exception as e:
        print(f"Error: {str(e)}")
        raise e
