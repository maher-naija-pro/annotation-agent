#!/usr/bin/env python3
"""
Main script to connect to Ollama server and interact with gpt-oss:20b model.
This script uses the llm_server library to establish connection and perform queries.
"""

from llm_server import setup_inference_server_connection, query_llm




def main():
    """
    Main function to run the Ollama client application.

    Args:
        model_name: Name of the model to use (default: "gpt-oss:20b")
    """
    print("=" * 60)


    try:
        # Setup connection with specified model
        connection_gpt = setup_inference_server_connection("gpt-oss:20b")
        connection_vl = setup_inference_server_connection("qwen2.5vl:32b")

        # Run single query
        prompt = "What is artificial intelligence?"
        query_llm(connection_gpt, prompt)

    except Exception as e:
        print(f"Application error: {str(e)}")
        print("Please check your configuration and try again.")


if __name__ == "__main__":
    main()
