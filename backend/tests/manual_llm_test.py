"""
Manual test script for LLM providers
Run this to verify your LLM provider configuration
"""

import asyncio
import sys
import os

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from backend.services.llm_manager import LLMManager, LLMProvider, LLMConfigurationError
from config import settings


async def test_provider(provider: LLMProvider, model: str = None):
    """Test a specific provider"""
    print(f"\n{'='*60}")
    print(f"Testing {provider.value.upper()} Provider")
    print(f"{'='*60}")

    try:
        # Initialize manager
        manager = LLMManager(provider=provider, model=model, enable_fallback=False)

        # Get provider info
        info = manager.get_provider_info()
        print(f"\n✓ Provider initialized successfully")
        print(f"  Model: {info['model']}")
        print(f"  Formatted name: {info['formatted_model_name']}")
        print(f"  Has API key: {info['has_api_key']}")
        if info.get("base_url"):
            print(f"  Base URL: {info['base_url']}")

        # Test basic generation
        print(f"\n→ Testing basic generation...")
        response = await manager.generate(
            messages=[
                {"role": "user", "content": "Say 'Hello from LLM!' and nothing else."}
            ],
            max_tokens=20,
        )
        print(f"✓ Response: {response}")

        # Test streaming
        print(f"\n→ Testing streaming generation...")
        chunks = []
        async for chunk in await manager.generate(
            messages=[{"role": "user", "content": "Count: 1, 2, 3"}],
            stream=True,
            max_tokens=30,
        ):
            chunks.append(chunk)
            print(chunk, end="", flush=True)
        print()  # New line
        print(f"✓ Received {len(chunks)} chunks")

        print(f"\n✓ All tests passed for {provider.value}!")
        return True

    except LLMConfigurationError as e:
        print(f"\n✗ Configuration error: {e}")
        return False

    except Exception as e:
        print(f"\n✗ Error: {e}")
        import traceback

        traceback.print_exc()
        return False


async def test_all_providers():
    """Test all configured providers"""
    print("\n" + "=" * 60)
    print("LLM Provider Configuration Test")
    print("=" * 60)

    # Show configuration status
    status = settings.get_provider_config_status()
    print(f"\nPrimary provider: {status['primary_provider']}")
    print(f"Primary model: {status['primary_model']}")
    print(
        f"Fallback providers: {', '.join(status['fallback_providers']) if status['fallback_providers'] else 'none'}"
    )

    print(f"\nProvider Configuration Status:")
    for provider, details in status["providers"].items():
        if details["configured"]:
            print(f"  ✓ {provider}: configured")
        else:
            print(f"  ✗ {provider}: {details['error']}")

    # Test each provider
    results = {}

    # Test Ollama
    if status["providers"]["ollama"]["configured"]:
        results["ollama"] = await test_provider(LLMProvider.OLLAMA)

    # Test OpenAI
    if status["providers"]["openai"]["configured"]:
        results["openai"] = await test_provider(LLMProvider.OPENAI, "gpt-3.5-turbo")

    # Test Claude
    if status["providers"]["claude"]["configured"]:
        results["claude"] = await test_provider(
            LLMProvider.CLAUDE, "claude-3-haiku-20240307"
        )

    # Summary
    print(f"\n{'='*60}")
    print("Test Summary")
    print(f"{'='*60}")
    for provider, success in results.items():
        status_icon = "✓" if success else "✗"
        print(f"{status_icon} {provider}: {'PASSED' if success else 'FAILED'}")

    if not results:
        print("No providers configured. Please set up at least one provider:")
        print(
            "  - Ollama: Install from https://ollama.ai and run 'ollama pull llama3.1'"
        )
        print("  - OpenAI: Set OPENAI_API_KEY environment variable")
        print("  - Claude: Set ANTHROPIC_API_KEY environment variable")


async def test_fallback():
    """Test fallback functionality"""
    print("\n" + "=" * 60)
    print("Testing Fallback Functionality")
    print("=" * 60)

    try:
        # Try to initialize with fallback enabled
        manager = LLMManager(enable_fallback=True)

        info = manager.get_provider_info()
        print(f"\n✓ Initialized with provider: {info['provider']}")
        print(f"  Model: {info['model']}")

        # Test generation
        response = await manager.generate(
            messages=[{"role": "user", "content": "Say 'Fallback works!'"}],
            max_tokens=10,
        )
        print(f"✓ Response: {response}")

    except Exception as e:
        print(f"\n✗ Fallback test failed: {e}")


def main():
    """Main entry point"""
    import argparse

    parser = argparse.ArgumentParser(description="Test LLM provider configuration")
    parser.add_argument(
        "--provider",
        choices=["ollama", "openai", "claude", "all", "fallback"],
        default="all",
        help="Which provider to test",
    )
    parser.add_argument("--model", help="Model name to use (optional)")

    args = parser.parse_args()

    if args.provider == "all":
        asyncio.run(test_all_providers())
    elif args.provider == "fallback":
        asyncio.run(test_fallback())
    else:
        provider = LLMProvider(args.provider)
        asyncio.run(test_provider(provider, args.model))


if __name__ == "__main__":
    main()
