"""
LLM Server Library

This package provides utilities for connecting to and querying LLM inference servers.
"""

from .server_connection import setup_inference_server_connection, query_llm

__all__ = [
    'setup_inference_server_connection',
    'query_llm'
]

__version__ = '1.0.0'
