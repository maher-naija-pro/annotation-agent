#!/usr/bin/env python3
"""
Simple Python script to interact with OpenAI-compatible LLM endpoints.
Supports configurable endpoint URL and model name using functional programming.
"""

import os
import base64
from typing import Optional, Dict, Any, List, Union
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


def encode_image_to_base64(image_path: str) -> str:
    """
    Encode an image file to base64 string for API transmission.
    
    Args:
        image_path (str): Path to the image file
        
    Returns:
        str: Base64 encoded image string
        
    Raises:
        FileNotFoundError: If the image file doesn't exist
        ValueError: If the file is not a valid image format
    """
    if not os.path.exists(image_path):
        raise FileNotFoundError(f"Image file not found: {image_path}")
    
    # Check if it's a valid image file
    valid_extensions = {'.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp'}
    file_ext = os.path.splitext(image_path)[1].lower()
    if file_ext not in valid_extensions:
        raise ValueError(f"Unsupported image format: {file_ext}. Supported formats: {valid_extensions}")
    
    with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode('utf-8')


def create_image_message(image_path: str, text: str = "", detail: str = "auto") -> Dict[str, Any]:
    """
    Create a message dictionary with image content for multimodal conversations.
    
    Args:
        image_path (str): Path to the image file
        text (str): Optional text content to accompany the image
        detail (str): Level of detail for image analysis ("low", "high", or "auto")
        
    Returns:
        Dict: Message dictionary with image content
    """
    base64_image = encode_image_to_base64(image_path)
    
    content = []
    
    # Add text content if provided
    if text:
        content.append({
            "type": "text",
            "text": text
        })
    
    # Add image content
    content.append({
        "type": "image_url",
        "image_url": {
            "url": f"data:image/jpeg;base64,{base64_image}",
            "detail": detail
        }
    })
    
    return {
        "role": "user",
        "content": content
    }


def multimodal_chat_completion(client: OpenAI, 
                             model_name: str,
                             messages: List[Dict[str, Any]], 
                             temperature: float = 0.7, 
                             max_tokens: int = 1000,
                             **kwargs) -> Dict[str, Any]:
    """
    Send a multimodal chat completion request to the LLM with support for images and text.
    
    Args:
        client (OpenAI): The OpenAI client instance
        model_name (str): The name of the model to use
        messages (List[Dict]): List of message dictionaries with 'role' and 'content'
                              Content can include text and/or images
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


def analyze_image(client: OpenAI, model_name: str, image_path: str, prompt: str = "Describe this image in detail.", **kwargs) -> str:
    """
    Analyze an image with a text prompt using the LLM.
    
    Args:
        client (OpenAI): The OpenAI client instance
        model_name (str): The name of the model to use
        image_path (str): Path to the image file
        prompt (str): Text prompt for image analysis
        **kwargs: Additional parameters for multimodal_chat_completion
        
    Returns:
        str: The response content from the LLM, or error message
    """
    try:
        # Create image message
        image_message = create_image_message(image_path, prompt)
        messages = [image_message]
        
        # Send multimodal request
        response = multimodal_chat_completion(client, model_name, messages, **kwargs)
        
        if response['success']:
            return response['content']
        else:
            return f"Error: {response['error']}"
            
    except Exception as e:
        return f"Error processing image: {str(e)}"


def get_config() -> Dict[str, str]:
    """
    Get configuration with default endpoint IP 148.253.83.132.
    Updated to use Qwen 2.5 VL model.
    
    Returns:
        Dict containing endpoint_url, model_name, and api_key
    """
    return {
        'endpoint_url': os.getenv('LLM_ENDPOINT_URL', 'http://148.253.83.132:11434/v1'),
        'model_name': os.getenv('LLM_MODEL_NAME', 'qwen2.5vl:32b'),
        'api_key': os.getenv('OPENAI_API_KEY')
    }


def main():
    """
    Example usage of the LLM functions including image analysis.
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
    print(f"  API Key: {'***' + config['api_key'][-4:] if config['api_key'] else 'Not set (using default endpoint)'}")
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
    print()
    
    # Example 3: Image analysis (if image files exist)
    print("Example 3: Image analysis")
    print("-" * 30)
    
    # Look for sample images in the data-images directory
    sample_images = []
    data_images_dir = "data-images/output_advanced"
    
    if os.path.exists(data_images_dir):
        for root, dirs, files in os.walk(data_images_dir):
            for file in files:
                if file.lower().endswith(('.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp')):
                    sample_images.append(os.path.join(root, file))
                    if len(sample_images) >= 2:  # Limit to 2 examples
                        break
            if len(sample_images) >= 2:
                break
    
    if sample_images:
        for i, image_path in enumerate(sample_images[:2], 1):
            print(f"Analyzing image {i}: {os.path.basename(image_path)}")
            try:
                # Analyze the image
                analysis = analyze_image(
                    client, 
                    config['model_name'], 
                    image_path, 
                    "Describe what you see in this image. What type of document or content is this?"
                )
                print(f"Analysis: {analysis}")
                print()
            except Exception as e:
                print(f"Error analyzing image: {e}")
                print()
    else:
        print("No sample images found in data-images directory.")
        print("To test image analysis, place some image files in the data-images directory.")
        print()
    
    # Example 4: Multimodal conversation
    print("Example 4: Multimodal conversation")
    print("-" * 30)
    
    if sample_images:
        try:
            # Create a multimodal conversation with text and image
            multimodal_messages = [
                {
                    "role": "system", 
                    "content": "You are an expert document analyzer. Analyze the provided images and text carefully."
                },
                create_image_message(
                    sample_images[0], 
                    "What type of document is this? Please provide a detailed analysis."
                )
            ]
            
            response = multimodal_chat_completion(client, config['model_name'], multimodal_messages)
            
            if response['success']:
                print(f"Multimodal Response: {response['content']}")
                print(f"Tokens used: {response['usage']['total_tokens']}")
            else:
                print(f"Error: {response['error']}")
        except Exception as e:
            print(f"Error in multimodal conversation: {e}")
    else:
        print("Skipping multimodal example - no sample images available.")


if __name__ == "__main__":
    main()
