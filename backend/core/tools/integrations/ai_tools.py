"""AI and LLM tool integrations.

This module provides integrations for AI services including:
- OpenAI (GPT-4, GPT-3.5)
- Anthropic Claude
- Google Gemini
- Mistral AI
- Cohere
"""

import logging

from backend.core.tools.registry import ToolRegistry
from backend.core.tools.base import ParamConfig, OutputConfig, RequestConfig
from backend.core.tools.response_transformer import ResponseTransformer

logger = logging.getLogger(__name__)


# OpenAI Chat
@ToolRegistry.register(
    tool_id="openai_chat",
    name="OpenAI Chat",
    description="Chat with OpenAI GPT models (GPT-4, GPT-3.5)",
    category="ai",
    params={
        "messages": ParamConfig(
            type="array",
            description="Array of message objects with role and content",
            required=True
        ),
        "model": ParamConfig(
            type="string",
            description="Model to use",
            enum=["gpt-4", "gpt-4-turbo", "gpt-3.5-turbo"],
            default="gpt-4"
        ),
        "temperature": ParamConfig(
            type="number",
            description="Sampling temperature (0-2)",
            default=0.7
        ),
        "max_tokens": ParamConfig(
            type="number",
            description="Maximum tokens to generate",
            default=1000
        )
    },
    outputs={
        "content": OutputConfig(type="string", description="Generated response"),
        "usage": OutputConfig(type="object", description="Token usage information")
    },
    request=RequestConfig(
        method="POST",
        url="https://api.openai.com/v1/chat/completions",
        headers={
            "Content-Type": "application/json",
            "Authorization": "Bearer {{api_key}}"
        },
        body_template={
            "model": "{{model}}",
            "messages": "{{messages}}",
            "temperature": "{{temperature}}",
            "max_tokens": "{{max_tokens}}"
        }
    ),
    api_key_env="OPENAI_API_KEY",
    transform_response=ResponseTransformer.create_transformer(
        field_mapping={
            "content": "choices[0].message.content",
            "usage": "usage"
        }
    ),
    icon="bot",
    bg_color="#10A37F",
    docs_link="https://platform.openai.com/docs/api-reference/chat"
)
class OpenAIChatTool:
    pass


# Anthropic Claude
@ToolRegistry.register(
    tool_id="anthropic_claude",
    name="Anthropic Claude",
    description="Chat with Claude AI models",
    category="ai",
    params={
        "messages": ParamConfig(
            type="array",
            description="Array of message objects",
            required=True
        ),
        "model": ParamConfig(
            type="string",
            description="Claude model to use",
            enum=["claude-3-opus-20240229", "claude-3-sonnet-20240229", "claude-3-haiku-20240307"],
            default="claude-3-sonnet-20240229"
        ),
        "max_tokens": ParamConfig(
            type="number",
            description="Maximum tokens to generate",
            default=1024
        ),
        "temperature": ParamConfig(
            type="number",
            description="Sampling temperature (0-1)",
            default=1.0
        )
    },
    outputs={
        "content": OutputConfig(type="string", description="Generated response"),
        "usage": OutputConfig(type="object", description="Token usage")
    },
    request=RequestConfig(
        method="POST",
        url="https://api.anthropic.com/v1/messages",
        headers={
            "Content-Type": "application/json",
            "x-api-key": "{{api_key}}",
            "anthropic-version": "2023-06-01"
        },
        body_template={
            "model": "{{model}}",
            "messages": "{{messages}}",
            "max_tokens": "{{max_tokens}}",
            "temperature": "{{temperature}}"
        }
    ),
    api_key_env="ANTHROPIC_API_KEY",
    transform_response=ResponseTransformer.create_transformer(
        field_mapping={
            "content": "content[0].text",
            "usage": "usage"
        }
    ),
    icon="brain",
    bg_color="#D97757",
    docs_link="https://docs.anthropic.com/claude/reference/messages_post"
)
class AnthropicClaudeTool:
    pass


# Google Gemini
@ToolRegistry.register(
    tool_id="google_gemini",
    name="Google Gemini",
    description="Access Google's Gemini AI models",
    category="ai",
    params={
        "contents": ParamConfig(
            type="array",
            description="Array of content objects",
            required=True
        ),
        "model": ParamConfig(
            type="string",
            description="Gemini model",
            enum=["gemini-pro", "gemini-pro-vision"],
            default="gemini-pro"
        ),
        "temperature": ParamConfig(
            type="number",
            description="Temperature (0-1)",
            default=0.9
        )
    },
    outputs={
        "text": OutputConfig(type="string", description="Generated text")
    },
    request=RequestConfig(
        method="POST",
        url="https://generativelanguage.googleapis.com/v1/models/{{model}}:generateContent",
        headers={"Content-Type": "application/json"},
        query_params={"key": "{{api_key}}"},
        body_template={
            "contents": "{{contents}}",
            "generationConfig": {
                "temperature": "{{temperature}}"
            }
        }
    ),
    api_key_env="GOOGLE_API_KEY",
    transform_response=ResponseTransformer.create_transformer(
        field_mapping={"text": "candidates[0].content.parts[0].text"}
    ),
    icon="sparkles",
    bg_color="#4285F4",
    docs_link="https://ai.google.dev/docs"
)
class GoogleGeminiTool:
    pass


# Mistral AI
@ToolRegistry.register(
    tool_id="mistral_ai",
    name="Mistral AI",
    description="Use Mistral AI models for chat",
    category="ai",
    params={
        "messages": ParamConfig(
            type="array",
            description="Chat messages",
            required=True
        ),
        "model": ParamConfig(
            type="string",
            description="Mistral model",
            enum=["mistral-large-latest", "mistral-medium-latest", "mistral-small-latest"],
            default="mistral-small-latest"
        ),
        "temperature": ParamConfig(
            type="number",
            description="Temperature",
            default=0.7
        )
    },
    outputs={
        "content": OutputConfig(type="string", description="Response")
    },
    request=RequestConfig(
        method="POST",
        url="https://api.mistral.ai/v1/chat/completions",
        headers={
            "Content-Type": "application/json",
            "Authorization": "Bearer {{api_key}}"
        },
        body_template={
            "model": "{{model}}",
            "messages": "{{messages}}",
            "temperature": "{{temperature}}"
        }
    ),
    api_key_env="MISTRAL_API_KEY",
    transform_response=ResponseTransformer.create_transformer(
        field_mapping={"content": "choices[0].message.content"}
    ),
    icon="wind",
    bg_color="#FF7000",
    docs_link="https://docs.mistral.ai/"
)
class MistralAITool:
    pass


# Cohere
@ToolRegistry.register(
    tool_id="cohere",
    name="Cohere",
    description="Cohere language models for generation",
    category="ai",
    params={
        "message": ParamConfig(
            type="string",
            description="User message",
            required=True
        ),
        "model": ParamConfig(
            type="string",
            description="Cohere model",
            enum=["command", "command-light", "command-nightly"],
            default="command"
        ),
        "temperature": ParamConfig(
            type="number",
            description="Temperature",
            default=0.75
        )
    },
    outputs={
        "text": OutputConfig(type="string", description="Generated text")
    },
    request=RequestConfig(
        method="POST",
        url="https://api.cohere.ai/v1/chat",
        headers={
            "Content-Type": "application/json",
            "Authorization": "Bearer {{api_key}}"
        },
        body_template={
            "message": "{{message}}",
            "model": "{{model}}",
            "temperature": "{{temperature}}"
        }
    ),
    api_key_env="COHERE_API_KEY",
    transform_response=ResponseTransformer.create_transformer(
        field_mapping={"text": "text"}
    ),
    icon="message-circle",
    bg_color="#39594D",
    docs_link="https://docs.cohere.com/"
)
class CohereTool:
    pass


logger.info("Registered 5 AI tools")
