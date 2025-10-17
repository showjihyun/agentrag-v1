"""
Integration tests for LLM provider connections
These tests require actual provider access (Ollama running, API keys set)
"""

import pytest
import os
from backend.services.llm_manager import LLMManager, LLMProvider, LLMConfigurationError


@pytest.mark.integration
class TestOllamaIntegration:
    """Integration tests for Ollama provider"""

    @pytest.mark.skipif(
        not os.getenv("TEST_OLLAMA", "false").lower() == "true",
        reason="Ollama integration tests disabled. Set TEST_OLLAMA=true to enable",
    )
    async def test_ollama_connection(self):
        """Test Ollama connection and basic generation"""
        try:
            manager = LLMManager(provider=LLMProvider.OLLAMA, model="llama3.1")

            # Test basic generation
            response = await manager.generate(
                messages=[{"role": "user", "content": "Say 'Hello' and nothing else."}],
                max_tokens=10,
            )

            assert response is not None
            assert len(response) > 0
            print(f"Ollama response: {response}")

        except LLMConfigurationError as e:
            pytest.skip(f"Ollama not available: {e}")

    @pytest.mark.skipif(
        not os.getenv("TEST_OLLAMA", "false").lower() == "true",
        reason="Ollama integration tests disabled. Set TEST_OLLAMA=true to enable",
    )
    async def test_ollama_streaming(self):
        """Test Ollama streaming responses"""
        try:
            manager = LLMManager(provider=LLMProvider.OLLAMA, model="llama3.1")

            # Test streaming
            chunks = []
            async for chunk in await manager.generate(
                messages=[{"role": "user", "content": "Count from 1 to 3."}],
                stream=True,
                max_tokens=20,
            ):
                chunks.append(chunk)

            assert len(chunks) > 0
            full_response = "".join(chunks)
            assert len(full_response) > 0
            print(f"Ollama streaming response: {full_response}")

        except LLMConfigurationError as e:
            pytest.skip(f"Ollama not available: {e}")


@pytest.mark.integration
class TestOpenAIIntegration:
    """Integration tests for OpenAI provider"""

    @pytest.mark.skipif(
        not os.getenv("OPENAI_API_KEY"),
        reason="OpenAI API key not set. Set OPENAI_API_KEY to enable",
    )
    async def test_openai_connection(self):
        """Test OpenAI connection and basic generation"""
        manager = LLMManager(provider=LLMProvider.OPENAI, model="gpt-3.5-turbo")

        # Test basic generation
        response = await manager.generate(
            messages=[{"role": "user", "content": "Say 'Hello' and nothing else."}],
            max_tokens=10,
        )

        assert response is not None
        assert len(response) > 0
        print(f"OpenAI response: {response}")

    @pytest.mark.skipif(
        not os.getenv("OPENAI_API_KEY"),
        reason="OpenAI API key not set. Set OPENAI_API_KEY to enable",
    )
    async def test_openai_streaming(self):
        """Test OpenAI streaming responses"""
        manager = LLMManager(provider=LLMProvider.OPENAI, model="gpt-3.5-turbo")

        # Test streaming
        chunks = []
        async for chunk in await manager.generate(
            messages=[{"role": "user", "content": "Count from 1 to 3."}],
            stream=True,
            max_tokens=20,
        ):
            chunks.append(chunk)

        assert len(chunks) > 0
        full_response = "".join(chunks)
        assert len(full_response) > 0
        print(f"OpenAI streaming response: {full_response}")

    @pytest.mark.skipif(
        not os.getenv("OPENAI_API_KEY"),
        reason="OpenAI API key not set. Set OPENAI_API_KEY to enable",
    )
    async def test_openai_with_system_prompt(self):
        """Test OpenAI with system prompt convenience method"""
        manager = LLMManager(provider=LLMProvider.OPENAI, model="gpt-3.5-turbo")

        response = await manager.generate_with_system(
            system_prompt="You are a helpful assistant that responds concisely.",
            user_message="What is 2+2?",
            max_tokens=10,
        )

        assert response is not None
        assert len(response) > 0
        print(f"OpenAI with system prompt: {response}")


@pytest.mark.integration
class TestClaudeIntegration:
    """Integration tests for Claude provider"""

    @pytest.mark.skipif(
        not os.getenv("ANTHROPIC_API_KEY"),
        reason="Anthropic API key not set. Set ANTHROPIC_API_KEY to enable",
    )
    async def test_claude_connection(self):
        """Test Claude connection and basic generation"""
        manager = LLMManager(
            provider=LLMProvider.CLAUDE, model="claude-3-haiku-20240307"
        )

        # Test basic generation
        response = await manager.generate(
            messages=[{"role": "user", "content": "Say 'Hello' and nothing else."}],
            max_tokens=10,
        )

        assert response is not None
        assert len(response) > 0
        print(f"Claude response: {response}")

    @pytest.mark.skipif(
        not os.getenv("ANTHROPIC_API_KEY"),
        reason="Anthropic API key not set. Set ANTHROPIC_API_KEY to enable",
    )
    async def test_claude_streaming(self):
        """Test Claude streaming responses"""
        manager = LLMManager(
            provider=LLMProvider.CLAUDE, model="claude-3-haiku-20240307"
        )

        # Test streaming
        chunks = []
        async for chunk in await manager.generate(
            messages=[{"role": "user", "content": "Count from 1 to 3."}],
            stream=True,
            max_tokens=20,
        ):
            chunks.append(chunk)

        assert len(chunks) > 0
        full_response = "".join(chunks)
        assert len(full_response) > 0
        print(f"Claude streaming response: {full_response}")


@pytest.mark.integration
class TestProviderFallback:
    """Integration tests for provider fallback functionality"""

    @pytest.mark.skipif(
        not (
            os.getenv("OPENAI_API_KEY")
            and os.getenv("TEST_OLLAMA", "false").lower() == "true"
        ),
        reason="Both Ollama and OpenAI needed for fallback test",
    )
    async def test_fallback_from_invalid_to_valid(self):
        """Test fallback from unavailable provider to available one"""
        # This test would need to simulate Ollama being down
        # For now, we'll test the configuration aspect

        manager = LLMManager(provider=LLMProvider.OPENAI, enable_fallback=True)

        info = manager.get_provider_info()
        assert info["provider"] in ["openai", "ollama"]
        print(f"Active provider: {info['provider']}")


@pytest.mark.integration
class TestProviderInfo:
    """Test provider information retrieval"""

    async def test_get_provider_info_ollama(self):
        """Test getting provider info for Ollama"""
        try:
            manager = LLMManager(provider=LLMProvider.OLLAMA, enable_fallback=False)
            info = manager.get_provider_info()

            assert info["provider"] == "ollama"
            assert info["model"] is not None
            assert info["base_url"] is not None
            assert "formatted_model_name" in info
            assert info["formatted_model_name"].startswith("ollama/")

            print(f"Ollama provider info: {info}")

        except LLMConfigurationError:
            pytest.skip("Ollama not available")

    @pytest.mark.skipif(
        not os.getenv("OPENAI_API_KEY"), reason="OpenAI API key not set"
    )
    async def test_get_provider_info_openai(self):
        """Test getting provider info for OpenAI"""
        manager = LLMManager(provider=LLMProvider.OPENAI, enable_fallback=False)
        info = manager.get_provider_info()

        assert info["provider"] == "openai"
        assert info["model"] is not None
        assert info["has_api_key"] is True
        assert "formatted_model_name" in info

        print(f"OpenAI provider info: {info}")
