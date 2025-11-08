"""AI and LLM tools catalog."""

AI_TOOLS = [
    {
        "id": "openai_chat",
        "name": "OpenAI Chat",
        "description": "Chat with OpenAI GPT models (GPT-4, GPT-3.5)",
        "category": "ai",
        "provider": "openai",
        "icon": "🤖",
        "requires_auth": True,
        "auth_type": "api_key",
        "config": {
            "models": ["gpt-4", "gpt-4-turbo", "gpt-3.5-turbo"],
            "max_tokens": 4096,
            "temperature": 0.7,
        }
    },
    {
        "id": "anthropic_claude",
        "name": "Anthropic Claude",
        "description": "Chat with Claude AI models (Claude 3 Opus, Sonnet, Haiku)",
        "category": "ai",
        "provider": "anthropic",
        "icon": "🧠",
        "requires_auth": True,
        "auth_type": "api_key",
        "config": {
            "models": ["claude-3-opus", "claude-3-sonnet", "claude-3-haiku"],
            "max_tokens": 4096,
        }
    },
    {
        "id": "google_gemini",
        "name": "Google Gemini",
        "description": "Access Google's Gemini AI models",
        "category": "ai",
        "provider": "google",
        "icon": "✨",
        "requires_auth": True,
        "auth_type": "api_key",
        "config": {
            "models": ["gemini-pro", "gemini-pro-vision"],
        }
    },
    {
        "id": "mistral_ai",
        "name": "Mistral AI",
        "description": "Use Mistral AI models for chat and completion",
        "category": "ai",
        "provider": "mistral",
        "icon": "🌪️",
        "requires_auth": True,
        "auth_type": "api_key",
    },
    {
        "id": "cohere",
        "name": "Cohere",
        "description": "Cohere language models for generation and embeddings",
        "category": "ai",
        "provider": "cohere",
        "icon": "🔮",
        "requires_auth": True,
        "auth_type": "api_key",
    },
    {
        "id": "huggingface",
        "name": "Hugging Face",
        "description": "Access thousands of models from Hugging Face",
        "category": "ai",
        "provider": "huggingface",
        "icon": "🤗",
        "requires_auth": True,
        "auth_type": "api_key",
    },
    {
        "id": "replicate",
        "name": "Replicate",
        "description": "Run AI models via Replicate API",
        "category": "ai",
        "provider": "replicate",
        "icon": "🔁",
        "requires_auth": True,
        "auth_type": "api_key",
    },
]
