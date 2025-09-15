"""
Configuration functions for the LLM client.
You can modify these settings or use environment variables.
"""

import os
from typing import Optional, Dict


# Default configuration values
DEFAULT_ENDPOINT_URL = "https://api.openai.com/v1"
DEFAULT_MODEL_NAME = "gpt-3.5-turbo"
DEFAULT_API_KEY: Optional[str] = None


def get_endpoint_url() -> str:
    """Get the endpoint URL from environment or use default."""
    return os.getenv('LLM_ENDPOINT_URL', DEFAULT_ENDPOINT_URL)


def get_model_name() -> str:
    """Get the model name from environment or use default."""
    return os.getenv('LLM_MODEL_NAME', DEFAULT_MODEL_NAME)


def get_api_key() -> Optional[str]:
    """Get the API key from environment or use default."""
    return os.getenv('OPENAI_API_KEY', DEFAULT_API_KEY)


def get_all_config() -> Dict[str, str]:
    """Get all configuration as a dictionary."""
    return {
        'endpoint_url': get_endpoint_url(),
        'model_name': get_model_name(),
        'api_key': get_api_key()
    }


def get_config_by_provider(provider: str) -> Dict[str, str]:
    """
    Get configuration for a specific provider.
    
    Args:
        provider (str): Provider name ('openai', 'anthropic', 'local_ollama', 'local_lmstudio')
        
    Returns:
        Dict containing endpoint_url, model_name, and api_key
    """
    configs = {
        'openai': {
            'endpoint_url': 'https://api.openai.com/v1',
            'model_name': 'gpt-3.5-turbo',
            'api_key': 'your-openai-api-key'
        },
        'anthropic': {
            'endpoint_url': 'https://api.anthropic.com/v1',
            'model_name': 'claude-3-sonnet-20240229',
            'api_key': 'your-anthropic-api-key'
        },
        'local_ollama': {
            'endpoint_url': 'http://localhost:11434/v1',
            'model_name': 'llama2',
            'api_key': None  # Ollama typically doesn't require API key
        },
        'local_lmstudio': {
            'endpoint_url': 'http://localhost:1234/v1',
            'model_name': 'your-model-name',
            'api_key': None  # LM Studio typically doesn't require API key
        }
    }
    
    return configs.get(provider, configs['openai'])


# Example configurations for different providers
EXAMPLE_CONFIGS = {
    'openai': get_config_by_provider('openai'),
    'anthropic': get_config_by_provider('anthropic'),
    'local_ollama': get_config_by_provider('local_ollama'),
    'local_lmstudio': get_config_by_provider('local_lmstudio')
}
