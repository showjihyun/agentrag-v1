"""Communication and messaging tool integrations.

This module provides integrations for communication services including:
- Slack (full n8n-level integration)
- Gmail (full n8n-level integration)
- Discord
- Telegram
- SendGrid (Email)
"""

import logging

from backend.core.tools.registry import ToolRegistry
from backend.core.tools.base import ParamConfig, OutputConfig, RequestConfig
from backend.core.tools.response_transformer import ResponseTransformer

# Import full-featured tools
from backend.core.tools.integrations.slack_tool import execute_slack_tool
from backend.core.tools.integrations.gmail_tool import execute_gmail_tool

logger = logging.getLogger(__name__)


# Note: Slack and Gmail are now registered in their respective modules
# (slack_tool.py and gmail_tool.py) with full n8n-level functionality


# Discord
@ToolRegistry.register(
    tool_id="discord",
    name="Discord",
    description="Send messages to Discord channels via webhook",
    category="communication",
    params={
        "webhook_url": ParamConfig(
            type="string",
            description="Discord webhook URL",
            required=True
        ),
        "content": ParamConfig(
            type="string",
            description="Message content",
            required=True
        ),
        "username": ParamConfig(
            type="string",
            description="Override username"
        ),
        "avatar_url": ParamConfig(
            type="string",
            description="Override avatar URL"
        ),
        "embeds": ParamConfig(
            type="array",
            description="Rich embeds"
        )
    },
    outputs={
        "success": OutputConfig(type="boolean", description="Success status")
    },
    request=RequestConfig(
        method="POST",
        url="{{webhook_url}}",
        headers={"Content-Type": "application/json"},
        body_template={
            "content": "{{content}}",
            "username": "{{username}}",
            "avatar_url": "{{avatar_url}}",
            "embeds": "{{embeds}}"
        }
    ),
    transform_response=lambda x: {"success": True},
    icon="message-circle",
    bg_color="#5865F2",
    docs_link="https://discord.com/developers/docs/resources/webhook"
)
class DiscordTool:
    pass


# Telegram
@ToolRegistry.register(
    tool_id="telegram",
    name="Telegram",
    description="Send messages via Telegram bot",
    category="communication",
    params={
        "chat_id": ParamConfig(
            type="string",
            description="Chat ID or username",
            required=True
        ),
        "text": ParamConfig(
            type="string",
            description="Message text",
            required=True
        ),
        "parse_mode": ParamConfig(
            type="string",
            description="Parse mode",
            enum=["Markdown", "MarkdownV2", "HTML"],
            default="Markdown"
        ),
        "disable_notification": ParamConfig(
            type="boolean",
            description="Send silently",
            default=False
        )
    },
    outputs={
        "message_id": OutputConfig(type="number", description="Message ID"),
        "success": OutputConfig(type="boolean", description="Success status")
    },
    request=RequestConfig(
        method="POST",
        url="https://api.telegram.org/bot{{api_key}}/sendMessage",
        headers={"Content-Type": "application/json"},
        body_template={
            "chat_id": "{{chat_id}}",
            "text": "{{text}}",
            "parse_mode": "{{parse_mode}}",
            "disable_notification": "{{disable_notification}}"
        }
    ),
    api_key_env="TELEGRAM_BOT_TOKEN",
    transform_response=ResponseTransformer.create_transformer(
        field_mapping={
            "message_id": "result.message_id",
            "success": "ok"
        }
    ),
    icon="send",
    bg_color="#0088CC",
    docs_link="https://core.telegram.org/bots/api#sendmessage"
)
class TelegramTool:
    pass


# SendGrid Email
@ToolRegistry.register(
    tool_id="sendgrid",
    name="SendGrid",
    description="Send emails via SendGrid API",
    category="communication",
    params={
        "to": ParamConfig(
            type="string",
            description="Recipient email",
            required=True
        ),
        "from": ParamConfig(
            type="string",
            description="Sender email",
            required=True
        ),
        "subject": ParamConfig(
            type="string",
            description="Email subject",
            required=True
        ),
        "text": ParamConfig(
            type="string",
            description="Plain text content"
        ),
        "html": ParamConfig(
            type="string",
            description="HTML content"
        )
    },
    outputs={
        "success": OutputConfig(type="boolean", description="Success status")
    },
    request=RequestConfig(
        method="POST",
        url="https://api.sendgrid.com/v3/mail/send",
        headers={
            "Content-Type": "application/json",
            "Authorization": "Bearer {{api_key}}"
        },
        body_template={
            "personalizations": [{
                "to": [{"email": "{{to}}"}]
            }],
            "from": {"email": "{{from}}"},
            "subject": "{{subject}}",
            "content": [
                {"type": "text/plain", "value": "{{text}}"},
                {"type": "text/html", "value": "{{html}}"}
            ]
        }
    ),
    api_key_env="SENDGRID_API_KEY",
    transform_response=lambda x: {"success": True},
    icon="mail",
    bg_color="#1A82E2",
    docs_link="https://docs.sendgrid.com/api-reference/mail-send/mail-send"
)
class SendGridTool:
    pass


logger.info("Registered 6 communication tools (including Slack and Gmail with n8n-level features)")
