import os
from adapters.openai_adapter import OpenAIAdapter
from adapters.gemini_adapter import GeminiAdapter
from adapters.groq_adapter import GroqAdapter
from adapters.hf_adapter import HuggingFaceAdapter
from adapters.ollama_adapter import OllamaAdapter


ADAPTERS = {
    "openai": OpenAIAdapter(),
    "gemini": GeminiAdapter(),
    "groq": GroqAdapter(),
    "huggingface": HuggingFaceAdapter(),
    "ollama": OllamaAdapter(),
}


def call_llm(provider: str, model: str, api_key: str, prompt: str, temperature: float = 0.2) -> str:
    provider_key = (provider or "").lower()
    if provider_key not in ADAPTERS:
        raise ValueError(f"Unsupported provider: {provider}")
    adapter = ADAPTERS[provider_key]
    return adapter.generate(model=model, api_key=api_key, prompt=prompt, temperature=temperature)


def redact_key(api_key: str) -> str:
    if not api_key:
        return ""
    if len(api_key) <= 6:
        return "*" * len(api_key)
    return f"{api_key[:3]}***{api_key[-3:]}"
