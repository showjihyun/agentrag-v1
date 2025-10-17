#!/usr/bin/env python3
"""
Configuration Validation Script

This script validates your environment configuration and checks
if all required services are accessible.

Usage:
    python validate_config.py
"""

import sys
import os
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent))


def check_ollama_connection():
    """Check if Ollama is accessible"""
    try:
        import requests

        response = requests.get("http://localhost:11434/api/tags", timeout=5)
        if response.status_code == 200:
            models = response.json().get("models", [])
            return True, f"Connected. {len(models)} model(s) installed."
        return False, f"Unexpected response: {response.status_code}"
    except requests.exceptions.ConnectionError:
        return False, "Cannot connect. Is Ollama running? Run 'ollama serve'"
    except Exception as e:
        return False, f"Error: {str(e)}"


def check_milvus_connection(host: str, port: int):
    """Check if Milvus is accessible"""
    try:
        from pymilvus import connections

        connections.connect(alias="validation", host=host, port=port, timeout=5)
        connections.disconnect("validation")
        return True, "Connected successfully"
    except Exception as e:
        return False, f"Cannot connect: {str(e)}"


def check_redis_connection(host: str, port: int, password: str = None):
    """Check if Redis is accessible"""
    try:
        import redis

        client = redis.Redis(
            host=host,
            port=port,
            password=password if password else None,
            socket_connect_timeout=5,
        )
        client.ping()
        return True, "Connected successfully"
    except Exception as e:
        return False, f"Cannot connect: {str(e)}"


def check_embedding_model(model_name: str):
    """Check if embedding model can be loaded"""
    try:
        from sentence_transformers import SentenceTransformer

        print(f"    Loading model '{model_name}'... ", end="", flush=True)
        model = SentenceTransformer(model_name)
        dim = model.get_sentence_embedding_dimension()
        return True, f"Loaded successfully (dimension: {dim})"
    except Exception as e:
        return False, f"Cannot load: {str(e)}"


def main():
    print("\n" + "=" * 70)
    print("AGENTIC RAG SYSTEM - CONFIGURATION VALIDATOR")
    print("=" * 70 + "\n")

    # Load configuration
    try:
        from config import settings

        print("✓ Configuration loaded successfully\n")
    except Exception as e:
        print(f"✗ Failed to load configuration: {e}\n")
        print("Please check your .env file and ensure all required variables are set.")
        print("See .env.example for a template.\n")
        return 1

    # Print configuration summary
    settings.print_config_summary()

    # Validate configuration
    print("=" * 70)
    print("VALIDATING CONFIGURATION")
    print("=" * 70 + "\n")

    is_valid, errors = settings.validate_required_config()

    if not is_valid:
        print("✗ Configuration validation failed:\n")
        for error in errors:
            print(f"  - {error}")
        print()
        return 1

    print("✓ Configuration validation passed\n")

    # Check service connectivity
    print("=" * 70)
    print("CHECKING SERVICE CONNECTIVITY")
    print("=" * 70 + "\n")

    all_ok = True

    # Check LLM provider
    print(f"[1] Checking {settings.LLM_PROVIDER.upper()} connectivity...")

    if settings.LLM_PROVIDER == "ollama":
        is_ok, message = check_ollama_connection()
        if is_ok:
            print(f"    ✓ {message}")
        else:
            print(f"    ✗ {message}")
            all_ok = False
    elif settings.LLM_PROVIDER == "openai":
        if settings.OPENAI_API_KEY:
            print(f"    ✓ API key configured")
        else:
            print(f"    ✗ API key not configured")
            all_ok = False
    elif settings.LLM_PROVIDER == "claude":
        if settings.ANTHROPIC_API_KEY:
            print(f"    ✓ API key configured")
        else:
            print(f"    ✗ API key not configured")
            all_ok = False

    print()

    # Check Milvus
    print("[2] Checking Milvus connectivity...")
    is_ok, message = check_milvus_connection(settings.MILVUS_HOST, settings.MILVUS_PORT)
    if is_ok:
        print(f"    ✓ {message}")
    else:
        print(f"    ✗ {message}")
        print(f"    → Start Milvus: docker-compose up -d milvus")
        all_ok = False

    print()

    # Check Redis
    print("[3] Checking Redis connectivity...")
    is_ok, message = check_redis_connection(
        settings.REDIS_HOST, settings.REDIS_PORT, settings.REDIS_PASSWORD
    )
    if is_ok:
        print(f"    ✓ {message}")
    else:
        print(f"    ✗ {message}")
        print(f"    → Start Redis: docker-compose up -d redis")
        all_ok = False

    print()

    # Check embedding model
    print("[4] Checking embedding model...")
    is_ok, message = check_embedding_model(settings.EMBEDDING_MODEL)
    if is_ok:
        print(f"    ✓ {message}")
    else:
        print(f"    ✗ {message}")
        all_ok = False

    print()

    # Summary
    print("=" * 70)
    print("VALIDATION SUMMARY")
    print("=" * 70 + "\n")

    if all_ok:
        print("✓ All checks passed! Your system is ready to use.\n")
        print("Next steps:")
        print("  1. Start the backend: uvicorn main:app --reload --port 8000")
        print("  2. Start the frontend: cd frontend && npm run dev")
        print("  3. Open http://localhost:3000 in your browser\n")
        return 0
    else:
        print("✗ Some checks failed. Please fix the issues above.\n")
        print("Common solutions:")
        print("  - Start services: docker-compose up -d")
        print("  - Install Ollama: https://ollama.ai")
        print("  - Pull Ollama model: ollama pull llama3.1")
        print("  - Check .env configuration\n")
        return 1


if __name__ == "__main__":
    sys.exit(main())
