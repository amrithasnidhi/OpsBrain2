# rag_engine/llm.py
"""
LLM Provider Abstraction with Free Fallbacks.

Priority order:
1. Anthropic Claude (paid, best quality)
2. Groq (free tier, very fast - uses Llama/Mixtral)
3. Ollama (local, completely free - requires local install)
4. Mock responses (no API needed, for testing)

Set environment variables:
- ANTHROPIC_API_KEY: For Claude (paid)
- GROQ_API_KEY: For Groq free tier
- OLLAMA_BASE_URL: For local Ollama (default: http://localhost:11434)
"""

import os
import logging
from typing import Optional, Tuple
from abc import ABC, abstractmethod

logger = logging.getLogger(__name__)


class LLMProvider(ABC):
    """Abstract base class for LLM providers."""

    @abstractmethod
    def generate(self, prompt: str, system: Optional[str] = None, max_tokens: int = 1500) -> str:
        """Generate a response from the LLM."""
        pass

    @abstractmethod
    def is_available(self) -> bool:
        """Check if this provider is available."""
        pass

    @property
    @abstractmethod
    def name(self) -> str:
        """Provider name for logging."""
        pass


# ---------------------------------------------------------------------------
# Anthropic Claude (Paid - Best Quality)
# ---------------------------------------------------------------------------

class AnthropicProvider(LLMProvider):
    """Anthropic Claude API provider."""

    def __init__(self):
        self._client = None
        self._checked = False
        self._available = False

    @property
    def name(self) -> str:
        return "Anthropic Claude"

    def is_available(self) -> bool:
        if self._checked:
            return self._available

        self._checked = True
        api_key = os.environ.get("ANTHROPIC_API_KEY")
        if not api_key:
            self._available = False
            return False

        try:
            from anthropic import Anthropic
            self._client = Anthropic(api_key=api_key)
            self._available = True
            return True
        except ImportError:
            logger.debug("anthropic package not installed")
            self._available = False
            return False

    def generate(self, prompt: str, system: Optional[str] = None, max_tokens: int = 1500) -> str:
        if not self._client:
            raise RuntimeError("Anthropic client not initialized")

        messages = [{"role": "user", "content": prompt}]
        kwargs = {
            "model": "claude-sonnet-4-20250514",
            "max_tokens": max_tokens,
            "messages": messages
        }
        if system:
            kwargs["system"] = system

        response = self._client.messages.create(**kwargs)
        return response.content[0].text


# ---------------------------------------------------------------------------
# Groq (Free Tier - Very Fast)
# ---------------------------------------------------------------------------

class GroqProvider(LLMProvider):
    """Groq API provider - free tier available."""

    def __init__(self):
        self._client = None
        self._checked = False
        self._available = False

    @property
    def name(self) -> str:
        return "Groq (Free)"

    def is_available(self) -> bool:
        if self._checked:
            return self._available

        self._checked = True
        api_key = os.environ.get("GROQ_API_KEY")
        if not api_key:
            self._available = False
            return False

        try:
            from groq import Groq
            self._client = Groq(api_key=api_key)
            self._available = True
            return True
        except ImportError:
            logger.debug("groq package not installed. Install with: pip install groq")
            self._available = False
            return False

    def generate(self, prompt: str, system: Optional[str] = None, max_tokens: int = 1500) -> str:
        if not self._client:
            raise RuntimeError("Groq client not initialized")

        messages = []
        if system:
            messages.append({"role": "system", "content": system})
        messages.append({"role": "user", "content": prompt})

        response = self._client.chat.completions.create(
            model="llama-3.1-70b-versatile",  # Free, very capable
            messages=messages,
            max_tokens=max_tokens,
            temperature=0.3
        )
        return response.choices[0].message.content


# ---------------------------------------------------------------------------
# Ollama (Local - Completely Free)
# ---------------------------------------------------------------------------

class OllamaProvider(LLMProvider):
    """Ollama local provider - completely free, runs on your machine."""

    def __init__(self):
        self._base_url = os.environ.get("OLLAMA_BASE_URL", "http://localhost:11434")
        self._model = os.environ.get("OLLAMA_MODEL", "llama3.1")  # or mistral, mixtral
        self._checked = False
        self._available = False

    @property
    def name(self) -> str:
        return f"Ollama ({self._model})"

    def is_available(self) -> bool:
        if self._checked:
            return self._available

        self._checked = True
        try:
            import requests
            response = requests.get(f"{self._base_url}/api/tags", timeout=2)
            if response.status_code == 200:
                # Check if our model is available
                models = response.json().get("models", [])
                model_names = [m.get("name", "").split(":")[0] for m in models]
                self._available = self._model in model_names or any(self._model in n for n in model_names)
                if not self._available:
                    logger.debug(f"Ollama running but model '{self._model}' not found. Available: {model_names}")
                return self._available
        except Exception as e:
            logger.debug(f"Ollama not available: {e}")
            self._available = False
        return False

    def generate(self, prompt: str, system: Optional[str] = None, max_tokens: int = 1500) -> str:
        import requests

        full_prompt = prompt
        if system:
            full_prompt = f"{system}\n\n{prompt}"

        response = requests.post(
            f"{self._base_url}/api/generate",
            json={
                "model": self._model,
                "prompt": full_prompt,
                "stream": False,
                "options": {
                    "num_predict": max_tokens,
                    "temperature": 0.3
                }
            },
            timeout=120
        )
        response.raise_for_status()
        return response.json()["response"]


# ---------------------------------------------------------------------------
# Mock Provider (No API - For Testing)
# ---------------------------------------------------------------------------

class MockProvider(LLMProvider):
    """Mock provider for testing without any API."""

    @property
    def name(self) -> str:
        return "Mock (No API)"

    def is_available(self) -> bool:
        return True  # Always available as last resort

    def generate(self, prompt: str, system: Optional[str] = None, max_tokens: int = 1500) -> str:
        # Return a placeholder response
        return "[Mock response - configure ANTHROPIC_API_KEY, GROQ_API_KEY, or run Ollama for real LLM responses]"


# ---------------------------------------------------------------------------
# LLM Manager - Handles Fallback
# ---------------------------------------------------------------------------

class LLMManager:
    """
    Manages LLM providers with automatic fallback.

    Usage:
        llm = get_llm()
        response = llm.generate("What is 2+2?", system="You are a math tutor")
    """

    _instance = None
    _providers = None
    _active_provider = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._providers = [
                AnthropicProvider(),
                GroqProvider(),
                OllamaProvider(),
                MockProvider()
            ]
            cls._active_provider = None
        return cls._instance

    def get_provider(self) -> LLMProvider:
        """Get the best available provider."""
        if self._active_provider and self._active_provider.is_available():
            return self._active_provider

        for provider in self._providers:
            if provider.is_available():
                self._active_provider = provider
                logger.info(f"Using LLM provider: {provider.name}")
                return provider

        # Should never reach here since MockProvider is always available
        raise RuntimeError("No LLM provider available")

    def generate(self, prompt: str, system: Optional[str] = None, max_tokens: int = 1500) -> str:
        """Generate a response using the best available provider."""
        provider = self.get_provider()
        try:
            return provider.generate(prompt, system, max_tokens)
        except Exception as e:
            logger.error(f"Provider {provider.name} failed: {e}")
            # Try next provider
            self._active_provider = None
            for p in self._providers:
                if p != provider and p.is_available():
                    try:
                        return p.generate(prompt, system, max_tokens)
                    except Exception:
                        continue
            raise

    @property
    def provider_name(self) -> str:
        """Get the name of the current provider."""
        return self.get_provider().name


# Global instance
_llm_manager = None


def get_llm() -> LLMManager:
    """Get the global LLM manager instance."""
    global _llm_manager
    if _llm_manager is None:
        _llm_manager = LLMManager()
    return _llm_manager


def check_available_providers() -> dict:
    """Check which providers are available. Useful for debugging."""
    manager = LLMManager()
    return {
        provider.name: provider.is_available()
        for provider in manager._providers
    }
