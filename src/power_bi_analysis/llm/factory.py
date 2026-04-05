"""
LLM client factory for multiple providers.
"""

import os
from typing import Optional, Dict, Any
from .base import BaseLLMClient
from .anthropic_client import AnthropicClient
from .openai_client import OpenAIClient
try:
    from .gemini_client import GeminiClient
except ImportError:
    GeminiClient = None

# Registry of available LLM clients
_LLM_CLIENTS: Dict[str, type] = {
    "anthropic": AnthropicClient,
    "openai": OpenAIClient,
}
if GeminiClient is not None:
    _LLM_CLIENTS["gemini"] = GeminiClient

def create_llm_client(
    provider: str = "anthropic",
    api_key: Optional[str] = None,
    model: Optional[str] = None,
    **kwargs
) -> BaseLLMClient:
    """
    Create an LLM client for the specified provider.

    Args:
        provider: LLM provider name ("anthropic", "openai", "gemini")
        api_key: API key for the provider (default: from environment variable)
        model: Model name to use (default: provider's default)
        **kwargs: Additional provider-specific arguments

    Returns:
        LLM client instance

    Raises:
        ValueError: If provider is not supported
    """
    if provider not in _LLM_CLIENTS:
        supported = ", ".join(_LLM_CLIENTS.keys())
        raise ValueError(f"Unsupported LLM provider: {provider}. Supported: {supported}")

    client_class = _LLM_CLIENTS[provider]

    # Set default API key from environment if not provided
    if api_key is None:
        env_var = _get_api_key_env_var(provider)
        api_key = os.environ.get(env_var)

    # Set default model if not provided
    if model is None:
        model = _get_default_model(provider)

    # Create client instance
    return client_class(api_key=api_key, model=model, **kwargs)

def _get_api_key_env_var(provider: str) -> str:
    """Get environment variable name for provider API key."""
    mapping = {
        "anthropic": "ANTHROPIC_API_KEY",
        "openai": "OPENAI_API_KEY",
        "gemini": "GOOGLE_API_KEY",
    }
    return mapping.get(provider, f"{provider.upper()}_API_KEY")

def _get_default_model(provider: str) -> str:
    """Get default model for provider."""
    defaults = {
        "anthropic": "claude-3-5-sonnet-20241022",
        "openai": "gpt-4-turbo-preview",
        "gemini": "gemini-2.0-flash-exp",
    }
    return defaults.get(provider, "")

def register_llm_client(provider: str, client_class: type) -> None:
    """
    Register a new LLM client class.

    Args:
        provider: Provider name
        client_class: LLM client class (subclass of BaseLLMClient)
    """
    if not issubclass(client_class, BaseLLMClient):
        raise TypeError(f"Client class must be a subclass of BaseLLMClient")
    _LLM_CLIENTS[provider] = client_class

def list_supported_providers() -> list:
    """Get list of supported LLM providers."""
    return list(_LLM_CLIENTS.keys())