#!/usr/bin/env python3
"""
Main script to connect to Ollama server and interact with gpt-oss:20b model.
This script uses the client module to establish connection and perform queries.
"""

import sys
import os
from typing import Dict, Any

# Add the client directory to the Python path
sys.path.append(os.path.join(os.path.dirname(__file__), 'client'))

from llm_client import create_client, simple_query



def setup_ollama_connection() -> Dict[str, Any]:
    """
    Setup connection to the Ollama server at 148.253.83.132.
    
    Returns:
        Dict containing client and configuration information
    """
    # Configure for Ollama server - using the exact endpoint that works with curl
    endpoint_url = "http://148.253.83.132:11434/v1"  # OpenAI-compatible endpoint
    model_name = "gpt-oss:20b"
    api_key = ""  # Empty string for Ollama (no API key required)
    
    print(f"Connecting to Ollama server...")

    
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




def run_single_query(connection_info: Dict[str, Any]):
    """
    Run a single query with the Ollama model.
    
    Args:
        connection_info: Dictionary containing client and config info
    """
    print("Running single query...")
    print("-" * 40)
    
    # Single prompt - you can modify this as needed
    prompt = "What is artificial intelligence?"
    
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
        
    except Exception as e:
        print(f"Error: {str(e)}")




def main():
    """
    Main function to run the Ollama client application.
    """
    print("=" * 60)
    print("Ollama GPT-OSS:20B Client Application")
    print("=" * 60)
    
    try:
        # Setup connection
        connection_info = setup_ollama_connection()
        
        
        # Run single query
        run_single_query(connection_info)
                
    except Exception as e:
        print(f"Application error: {str(e)}")
        print("Please check your configuration and try again.")


if __name__ == "__main__":
    main()
