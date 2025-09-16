#!/usr/bin/env python3
"""
 python main.py Main script to connect to LLM server and interact with Qwen 2.5 VL model.
This script uses the simplified client configuration with default endpoint IP 148.253.83.132.
Updated to use Qwen 2.5 VL (Vision-Language) model for enhanced multimodal capabilities.
"""

from client.llm_client import create_client, simple_query, get_config




def main():
    """
    Main function to run the LLM client application.
    Uses the simplified configuration with default endpoint IP 148.253.83.132.
    Updated to use Qwen 2.5 VL model for enhanced multimodal capabilities.
    """
    print("=" * 60)
    print("🤖 LLM Client Application")
    print("=" * 60)

    try:
        # Get configuration with default endpoint IP 148.253.83.132
        config = get_config()
        
        # Create LLM client
        client = create_client(
            endpoint_url=config['endpoint_url'],
            model_name=config['model_name'],
            api_key=config['api_key']
        )
        
        print(f"✅ Connected to LLM server:")
        print(f"   Endpoint: {config['endpoint_url']}")
        print(f"   Model: {config['model_name']} (Qwen 2.5 VL - Vision-Language)")
        print(f"   API Key: {'Set' if config['api_key'] else 'Not required (default endpoint)'}")
        print()

        # Test query
        prompt = "What is artificial intelligence?"
        print(f"🔍 Query: {prompt}")
        print("-" * 40)
        
        response = simple_query(client, config['model_name'], prompt)
        print(f"🤖 Response: {response}")
        print()

    except Exception as e:
        print(f"❌ Application error: {str(e)}")
        print("Please check your configuration and try again.")


if __name__ == "__main__":
    main()
