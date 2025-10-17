"""
Unit tests for LLM configuration validation
"""

import pytest
from unittest.mock import patch, MagicMock
from backend.config import Settings
from backend.services.llm_manager import (
    LLMManager,
    LLMProvider,
    LLMConfigurationError,
    LLMConnectionError,
)


class TestSettingsValidation:
    """Test Settings configuration validation"""

    def test_validate_provider_config_openai_missing_key(self):
        """Test OpenAI validation fails without API key"""
        with patch.dict("os.environ", {"OPENAI_API_KEY": ""}, clear=True):
            settings = Settings()
            is_valid, error = settings.validate_provider_config("openai")

            assert not is_valid
            assert "OPENAI_API_KEY" in error
            assert "https://platform.openai.com/api-keys" in error

    def test_validate_provider_config_openai_with_key(self):
        """Test OpenAI validation succeeds with API key"""
        with patch.dict("os.environ", {"OPENAI_API_KEY": "sk-test123"}, clear=True):
            settings = Settings()
            is_valid, error = settings.validate_provider_config("openai")

            assert is_valid
            assert error is None

    def test_validate_provider_config_claude_missing_key(self):
        """Test Claude validation fails without API key"""
        with patch.dict("os.environ", {"ANTHROPIC_API_KEY": ""}, clear=True):
            settings = Settings()
            is_valid, error = settings.validate_provider_config("claude")

            assert not is_valid
            assert "ANTHROPIC_API_KEY" in error
            assert "https://console.anthropic.com/settings/keys" in error

    def test_validate_provider_config_claude_with_key(self):
        """Test Claude validation succeeds with API key"""
        with patch.dict(
            "os.environ", {"ANTHROPIC_API_KEY": "sk-ant-test123"}, clear=True
        ):
            settings = Settings()
            is_valid, error = settings.validate_provider_config("claude")

            assert is_valid
            assert error is None

    def test_validate_provider_config_ollama(self):
        """Test Ollama validation (always valid if URL is set)"""
        settings = Settings()
        is_valid, error = settings.validate_provider_config("ollama")

        assert is_valid
        assert error is None

    def test_get_fallback_providers_empty(self):
        """Test fallback providers when none configured"""
        settings = Settings()
        fallbacks = settings.get_fallback_providers()

        assert fallbacks == []

    def test_get_fallback_providers_valid(self):
        """Test fallback providers parsing"""
        with patch.dict(
            "os.environ",
            {
                "LLM_FALLBACK_PROVIDERS": "openai,claude",
                "OPENAI_API_KEY": "sk-test",
                "ANTHROPIC_API_KEY": "sk-ant-test",
            },
            clear=True,
        ):
            settings = Settings()
            fallbacks = settings.get_fallback_providers()

            assert "openai" in fallbacks
            assert "claude" in fallbacks

    def test_get_fallback_providers_filters_invalid(self):
        """Test fallback providers filters out invalid entries"""
        with patch.dict(
            "os.environ",
            {
                "LLM_FALLBACK_PROVIDERS": "openai,invalid,claude",
                "OPENAI_API_KEY": "sk-test",
                "ANTHROPIC_API_KEY": "sk-ant-test",
            },
            clear=True,
        ):
            settings = Settings()
            fallbacks = settings.get_fallback_providers()

            assert "openai" in fallbacks
            assert "claude" in fallbacks
            assert "invalid" not in fallbacks

    def test_get_available_providers(self):
        """Test getting list of available providers"""
        with patch.dict(
            "os.environ",
            {"OPENAI_API_KEY": "sk-test", "ANTHROPIC_API_KEY": ""},
            clear=True,
        ):
            settings = Settings()
            available = settings.get_available_providers()

            assert "ollama" in available
            assert "openai" in available
            assert "claude" not in available

    def test_get_provider_config_status(self):
        """Test getting detailed provider status"""
        with patch.dict(
            "os.environ",
            {"OPENAI_API_KEY": "sk-test", "ANTHROPIC_API_KEY": ""},
            clear=True,
        ):
            settings = Settings()
            status = settings.get_provider_config_status()

            assert status["primary_provider"] == "ollama"
            assert "providers" in status
            assert status["providers"]["openai"]["configured"] is True
            assert status["providers"]["claude"]["configured"] is False
            assert status["providers"]["claude"]["error"] is not None


class TestLLMManagerFallback:
    """Test LLMManager fallback functionality"""

    @patch("backend.services.llm_manager.httpx.get")
    def test_ollama_connection_success(self, mock_get):
        """Test successful Ollama connection validation"""
        mock_response = MagicMock()
        mock_response.raise_for_status = MagicMock()
        mock_get.return_value = mock_response

        manager = LLMManager(provider=LLMProvider.OLLAMA)

        assert manager.provider == LLMProvider.OLLAMA
        mock_get.assert_called_once()

    @patch("backend.services.llm_manager.httpx.get")
    def test_ollama_connection_failure_no_fallback(self, mock_get):
        """Test Ollama connection failure without fallback"""
        mock_get.side_effect = Exception("Connection refused")

        with pytest.raises(LLMConfigurationError) as exc_info:
            LLMManager(provider=LLMProvider.OLLAMA, enable_fallback=False)

        # Check for either error message format
        error_msg = str(exc_info.value)
        assert "Ollama" in error_msg and (
            "Connection" in error_msg or "connection" in error_msg
        )

    @patch("backend.services.llm_manager.httpx.get")
    def test_ollama_connection_failure_with_fallback(self, mock_get):
        """Test Ollama connection failure with fallback to OpenAI"""
        mock_get.side_effect = Exception("Connection refused")

        with patch.dict(
            "os.environ",
            {"LLM_FALLBACK_PROVIDERS": "openai", "OPENAI_API_KEY": "sk-test123"},
            clear=True,
        ):
            # Recreate settings to pick up env vars
            from backend.config import Settings

            settings = Settings()

            with patch("backend.services.llm_manager.settings", settings):
                manager = LLMManager(provider=LLMProvider.OLLAMA, enable_fallback=True)

                # Should have fallen back to OpenAI
                assert manager.provider == LLMProvider.OPENAI
                assert manager.api_key == "sk-test123"

    def test_openai_missing_key_no_fallback(self):
        """Test OpenAI without API key and no fallback"""
        with patch.dict("os.environ", {"OPENAI_API_KEY": ""}, clear=True):
            from backend.config import Settings

            settings = Settings()

            with patch("backend.services.llm_manager.settings", settings):
                with pytest.raises(LLMConfigurationError) as exc_info:
                    LLMManager(provider=LLMProvider.OPENAI, enable_fallback=False)

                assert "OPENAI_API_KEY" in str(exc_info.value)

    @patch("backend.services.llm_manager.httpx.get")
    def test_openai_missing_key_with_ollama_fallback(self, mock_get):
        """Test OpenAI without API key falls back to Ollama"""
        mock_response = MagicMock()
        mock_response.raise_for_status = MagicMock()
        mock_get.return_value = mock_response

        with patch.dict(
            "os.environ",
            {
                "LLM_PROVIDER": "openai",
                "OPENAI_API_KEY": "",
                "LLM_FALLBACK_PROVIDERS": "ollama",
            },
            clear=True,
        ):
            from backend.config import Settings

            settings = Settings()

            with patch("backend.services.llm_manager.settings", settings):
                manager = LLMManager(enable_fallback=True)

                # Should have fallen back to Ollama
                assert manager.provider == LLMProvider.OLLAMA

    def test_get_provider_info(self):
        """Test getting provider information"""
        with patch.dict("os.environ", {"OPENAI_API_KEY": "sk-test"}, clear=True):
            from backend.config import Settings

            settings = Settings()

            with patch("backend.services.llm_manager.settings", settings):
                manager = LLMManager(provider=LLMProvider.OPENAI, enable_fallback=False)
                info = manager.get_provider_info()

                assert info["provider"] == "openai"
                assert info["has_api_key"] is True
                assert "formatted_model_name" in info

    def test_invalid_provider_name(self):
        """Test invalid provider name raises error"""
        from pydantic import ValidationError

        with pytest.raises(ValidationError) as exc_info:
            with patch.dict(
                "os.environ", {"LLM_PROVIDER": "invalid_provider"}, clear=True
            ):
                from backend.config import Settings

                Settings()

        assert "Invalid LLM_PROVIDER" in str(exc_info.value)
