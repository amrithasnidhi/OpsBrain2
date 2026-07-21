#!/usr/bin/env python3
"""
Quick check of available LLM providers.

Run with: python -m rag_engine.check_llm
"""

import sys
import os

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from rag_engine.llm import check_available_providers, get_llm


def main():
    print("\n" + "="*60)
    print("LLM Provider Status Check")
    print("="*60)

    providers = check_available_providers()

    print("\nAvailable Providers:")
    for name, available in providers.items():
        status = "[OK]" if available else "[--]"
        print(f"  {status} {name}")

    print("\n" + "-"*60)

    # Test the active provider
    llm = get_llm()
    print(f"\nActive Provider: {llm.provider_name}")

    print("\nTesting with a simple prompt...")
    try:
        response = llm.generate("What is 2+2? Answer with just the number.", max_tokens=10)
        print(f"Response: {response.strip()}")
        print("\n[OK] LLM is working!")
    except Exception as e:
        print(f"[ERROR] {e}")

    print("\n" + "="*60)
    print("\nTo enable a provider:")
    print("  - Groq (FREE): export GROQ_API_KEY=your-key")
    print("  - Ollama (FREE): ollama serve")
    print("  - Claude: export ANTHROPIC_API_KEY=your-key")
    print("="*60 + "\n")


if __name__ == "__main__":
    main()
