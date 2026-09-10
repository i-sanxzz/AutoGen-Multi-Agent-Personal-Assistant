import os
from typing import Optional
from dotenv import load_dotenv
from autogen_core.models import ModelFamily
from autogen_ext.models.openai import OpenAIChatCompletionClient


def get_model_client(
    model: Optional[str] = None,
    api_key: Optional[str] = None,
    base_url: Optional[str] = None,
    max_tokens: Optional[int] = None,
) -> OpenAIChatCompletionClient:
    """Creates an OpenAIChatCompletionClient with proper model_info and endpoint configuration.
    
    Compatible with:
      - OpenAI (default)
      - OpenRouter (https://openrouter.ai/api/v1)
      - Google Gemini (https://generativelanguage.googleapis.com/v1beta/openai/)
      - Groq, Together, Ollama, etc.
    """
    load_dotenv()

    api_key = api_key or os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise ValueError(
            "API key not found. Please set OPENAI_API_KEY in your .env file or environment."
        )

    base_url = base_url or os.getenv("OPENAI_BASE_URL")
    
    if not model:
        model = os.getenv("OPENAI_MODEL")
        if not model:
            if base_url and "openrouter.ai" in base_url:
                model = "openai/gpt-4o-mini"
            else:
                model = "gpt-4o-mini"

    if max_tokens is None:
        max_tokens_env = os.getenv("OPENAI_MAX_TOKENS")
        if max_tokens_env:
            try:
                max_tokens = int(max_tokens_env)
            except ValueError:
                max_tokens = 1000
        else:
            max_tokens = 1000

    client_args = {
        "model": model,
        "api_key": api_key,
        "max_tokens": max_tokens,
    }

    if base_url:
        client_args["base_url"] = base_url

    # autogen-ext requires model_info when using custom model names (like OpenRouter's 'openai/gpt-4o-mini'
    # or 'meta-llama/llama-3.3-70b-instruct')
    client_args["model_info"] = {
        "vision": True,
        "function_calling": True,
        "json_output": True,
        "family": ModelFamily.UNKNOWN,
        "structured_output": True,
    }

    return OpenAIChatCompletionClient(**client_args)

