"""Communication and messaging tool integrations.

This module provides integrations for communication services including:
- Slack
- Discord
- Telegram
- SendGrid (Email)
"""

import logging

from backend.core.tools.registry import ToolRegistry
from backend.core.tools.base import ParamConfig, OutputConfig, RequestConfig
from backend.core.tools.response_transformer import ResponseTransformer

logger = logging.getLogger(__name__)


# Slack
@ToolRegistry.register(
    tool_id="slack",
    name="Slack",
    description="Send messages to Slack channels",
    category="communication",
    params={
        "channel": ParamConfig(
            type="string",
            description="Channel ID or name",
            required=True
        ),
        "text": ParamConfig(
            type="string",
            description="Message text",
            required=True
        ),
        "blocks": ParamConfig(
            type="array",
            description="Rich message blocks (optional)"
        ),
        "thread_ts": ParamConfig(
            type="string",
            description="Thread timestamp for replies"
        )
    },
    outputs={
        "ok": OutputConfig(type="boolean", description="Success status"),
        "ts": OutputConfig(type="string", description="Message timestamp")
    },
    request=RequestConfig(
        method="POST",
        url="https://slack.com/api/chat.postMessage",
        headers={
            "Content-Type": "application/json",
            "Authorization": "Bearer {{api_key}}"
        },
        body_template={
            "channel": "{{channel}}",
            "text": "{{text}}",
            "blocks": "{{blocks}}",
            "thread_ts": "{{thread_ts}}"
        }
    ),
    api_key_env="SLACK_BOT_TOKEN",
    transform_response=ResponseTransformer.create_transformer(
        field_mapping={"ok": "ok", "ts": "ts"}
    ),
    icon="message-square",
    bg_color="#4A154B",
    docs_link="https://api.slack.com/methods/chat.postMessage"
)
class SlackTool:
    pass


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


logger.info("Registered 4 communication tools")
