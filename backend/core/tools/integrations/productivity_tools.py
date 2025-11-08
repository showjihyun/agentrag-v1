"""Productivity and collaboration tool integrations.

This module provides integrations for productivity services including:
- Notion
- Google Sheets
- Airtable
- Trello
"""

import logging

from backend.core.tools.registry import ToolRegistry
from backend.core.tools.base import ParamConfig, OutputConfig, RequestConfig
from backend.core.tools.response_transformer import ResponseTransformer

logger = logging.getLogger(__name__)


# Notion
@ToolRegistry.register(
    tool_id="notion",
    name="Notion",
    description="Create and update Notion pages",
    category="productivity",
    params={
        "parent_page_id": ParamConfig(
            type="string",
            description="Parent page ID",
            required=True
        ),
        "title": ParamConfig(
            type="string",
            description="Page title",
            required=True
        ),
        "content": ParamConfig(
            type="array",
            description="Page content blocks"
        )
    },
    outputs={
        "id": OutputConfig(type="string", description="Created page ID"),
        "url": OutputConfig(type="string", description="Page URL")
    },
    request=RequestConfig(
        method="POST",
        url="https://api.notion.com/v1/pages",
        headers={
            "Content-Type": "application/json",
            "Authorization": "Bearer {{api_key}}",
            "Notion-Version": "2022-06-28"
        },
        body_template={
            "parent": {"page_id": "{{parent_page_id}}"},
            "properties": {
                "title": {
                    "title": [{"text": {"content": "{{title}}"}}]
                }
            },
            "children": "{{content}}"
        }
    ),
    api_key_env="NOTION_API_KEY",
    transform_response=ResponseTransformer.create_transformer(
        field_mapping={"id": "id", "url": "url"}
    ),
    icon="file-text",
    bg_color="#000000",
    docs_link="https://developers.notion.com/reference/post-page"
)
class NotionTool:
    pass


# Google Sheets
@ToolRegistry.register(
    tool_id="google_sheets",
    name="Google Sheets",
    description="Read and write Google Sheets data",
    category="productivity",
    params={
        "spreadsheet_id": ParamConfig(
            type="string",
            description="Spreadsheet ID",
            required=True
        ),
        "range": ParamConfig(
            type="string",
            description="A1 notation range (e.g., Sheet1!A1:B10)",
            required=True
        ),
        "values": ParamConfig(
            type="array",
            description="2D array of values to write"
        ),
        "action": ParamConfig(
            type="string",
            description="Action to perform",
            enum=["read", "write", "append"],
            default="read"
        )
    },
    outputs={
        "values": OutputConfig(type="array", description="Cell values"),
        "updated_cells": OutputConfig(type="number", description="Number of updated cells")
    },
    request=RequestConfig(
        method="POST",
        url="https://sheets.googleapis.com/v4/spreadsheets/{{spreadsheet_id}}/values/{{range}}:{{action}}",
        headers={
            "Content-Type": "application/json",
            "Authorization": "Bearer {{api_key}}"
        },
        query_params={"valueInputOption": "USER_ENTERED"},
        body_template={"values": "{{values}}"}
    ),
    api_key_env="GOOGLE_SHEETS_API_KEY",
    transform_response=ResponseTransformer.create_transformer(
        field_mapping={
            "values": "values",
            "updated_cells": "updatedCells"
        }
    ),
    icon="table",
    bg_color="#0F9D58",
    docs_link="https://developers.google.com/sheets/api/reference/rest"
)
class GoogleSheetsTool:
    pass


# Airtable
@ToolRegistry.register(
    tool_id="airtable",
    name="Airtable",
    description="Manage Airtable records",
    category="productivity",
    params={
        "base_id": ParamConfig(
            type="string",
            description="Base ID",
            required=True
        ),
        "table_name": ParamConfig(
            type="string",
            description="Table name",
            required=True
        ),
        "fields": ParamConfig(
            type="object",
            description="Record fields",
            required=True
        ),
        "action": ParamConfig(
            type="string",
            description="Action",
            enum=["create", "update", "list"],
            default="create"
        ),
        "record_id": ParamConfig(
            type="string",
            description="Record ID (for update)"
        )
    },
    outputs={
        "id": OutputConfig(type="string", description="Record ID"),
        "fields": OutputConfig(type="object", description="Record fields")
    },
    request=RequestConfig(
        method="POST",
        url="https://api.airtable.com/v0/{{base_id}}/{{table_name}}",
        headers={
            "Content-Type": "application/json",
            "Authorization": "Bearer {{api_key}}"
        },
        body_template={"fields": "{{fields}}"}
    ),
    api_key_env="AIRTABLE_API_KEY",
    transform_response=ResponseTransformer.create_transformer(
        field_mapping={"id": "id", "fields": "fields"}
    ),
    icon="database",
    bg_color="#18BFFF",
    docs_link="https://airtable.com/developers/web/api/introduction"
)
class AirtableTool:
    pass


# Trello
@ToolRegistry.register(
    tool_id="trello",
    name="Trello",
    description="Manage Trello cards",
    category="productivity",
    params={
        "list_id": ParamConfig(
            type="string",
            description="List ID",
            required=True
        ),
        "name": ParamConfig(
            type="string",
            description="Card name",
            required=True
        ),
        "desc": ParamConfig(
            type="string",
            description="Card description"
        ),
        "due": ParamConfig(
            type="string",
            description="Due date (ISO 8601)"
        ),
        "labels": ParamConfig(
            type="array",
            description="Label IDs"
        )
    },
    outputs={
        "id": OutputConfig(type="string", description="Card ID"),
        "url": OutputConfig(type="string", description="Card URL")
    },
    request=RequestConfig(
        method="POST",
        url="https://api.trello.com/1/cards",
        query_params={
            "key": "{{api_key}}",
            "token": "{{api_token}}",
            "idList": "{{list_id}}",
            "name": "{{name}}",
            "desc": "{{desc}}",
            "due": "{{due}}"
        }
    ),
    api_key_env="TRELLO_API_KEY",
    transform_response=ResponseTransformer.create_transformer(
        field_mapping={"id": "id", "url": "url"}
    ),
    icon="trello",
    bg_color="#0079BF",
    docs_link="https://developer.atlassian.com/cloud/trello/rest/api-group-cards/"
)
class TrelloTool:
    pass


logger.info("Registered 4 productivity tools")
