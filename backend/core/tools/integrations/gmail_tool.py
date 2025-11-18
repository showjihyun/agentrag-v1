"""
Gmail Integration Tool - n8n level functionality.
Supports sending, reading, searching, and managing emails.
"""

import logging
from typing import Dict, Any, List, Optional
import base64
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
import httpx
from datetime import datetime

from backend.core.tools.registry import ToolRegistry

logger = logging.getLogger(__name__)


class GmailTool:
    """Gmail integration with comprehensive n8n-level features."""
    
    BASE_URL = "https://gmail.googleapis.com/gmail/v1"
    
    @staticmethod
    def _get_headers(access_token: str) -> Dict[str, str]:
        """Get authorization headers."""
        return {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json"
        }
    
    @staticmethod
    def _create_message(
        to: str,
        subject: str,
        body: str,
        body_type: str = "Plain Text",
        cc: Optional[str] = None,
        bcc: Optional[str] = None,
        attachments: Optional[List[Dict]] = None
    ) -> str:
        """Create a MIME message."""
        if body_type == "HTML":
            message = MIMEMultipart()
            message.attach(MIMEText(body, "html"))
        else:
            message = MIMEText(body, "plain")
        
        message["to"] = to
        message["subject"] = subject
        
        if cc:
            message["cc"] = cc
        if bcc:
            message["bcc"] = bcc
        
        # Add attachments
        if attachments:
            if not isinstance(message, MIMEMultipart):
                # Convert to multipart
                text_part = message
                message = MIMEMultipart()
                message.attach(text_part)
            
            for attachment in attachments:
                part = MIMEBase("application", "octet-stream")
                part.set_payload(base64.b64decode(attachment["data"]))
                encoders.encode_base64(part)
                part.add_header(
                    "Content-Disposition",
                    f"attachment; filename= {attachment['filename']}"
                )
                message.attach(part)
        
        # Encode message
        raw_message = base64.urlsafe_b64encode(message.as_bytes()).decode()
        return raw_message
    
    @staticmethod
    async def send_email(
        access_token: str,
        to: str,
        subject: str,
        body: str,
        body_type: str = "Plain Text",
        cc: Optional[str] = None,
        bcc: Optional[str] = None,
        attachments: Optional[List[Dict]] = None
    ) -> Dict[str, Any]:
        """Send an email via Gmail."""
        raw_message = GmailTool._create_message(
            to=to,
            subject=subject,
            body=body,
            body_type=body_type,
            cc=cc,
            bcc=bcc,
            attachments=attachments
        )
        
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{GmailTool.BASE_URL}/users/me/messages/send",
                headers=GmailTool._get_headers(access_token),
                json={"raw": raw_message}
            )
            
            if response.status_code != 200:
                raise Exception(f"Gmail API error: {response.text}")
            
            result = response.json()
            return {
                "success": True,
                "message_id": result.get("id"),
                "thread_id": result.get("threadId"),
                "label_ids": result.get("labelIds")
            }
    
    @staticmethod
    async def get_email(
        access_token: str,
        message_id: str,
        format: str = "full"
    ) -> Dict[str, Any]:
        """Get a specific email."""
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{GmailTool.BASE_URL}/users/me/messages/{message_id}",
                headers=GmailTool._get_headers(access_token),
                params={"format": format}
            )
            
            if response.status_code != 200:
                raise Exception(f"Gmail API error: {response.text}")
            
            message = response.json()
            
            # Parse headers
            headers = {}
            for header in message.get("payload", {}).get("headers", []):
                headers[header["name"]] = header["value"]
            
            # Get body
            body = ""
            if "parts" in message.get("payload", {}):
                for part in message["payload"]["parts"]:
                    if part.get("mimeType") == "text/plain":
                        body_data = part.get("body", {}).get("data", "")
                        if body_data:
                            body = base64.urlsafe_b64decode(body_data).decode()
                            break
            else:
                body_data = message.get("payload", {}).get("body", {}).get("data", "")
                if body_data:
                    body = base64.urlsafe_b64decode(body_data).decode()
            
            return {
                "id": message.get("id"),
                "thread_id": message.get("threadId"),
                "label_ids": message.get("labelIds"),
                "snippet": message.get("snippet"),
                "from": headers.get("From"),
                "to": headers.get("To"),
                "subject": headers.get("Subject"),
                "date": headers.get("Date"),
                "body": body
            }
    
    @staticmethod
    async def search_emails(
        access_token: str,
        query: str,
        max_results: int = 10,
        label_ids: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """Search emails with Gmail query syntax."""
        params = {
            "q": query,
            "maxResults": max_results
        }
        
        if label_ids:
            params["labelIds"] = label_ids
        
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{GmailTool.BASE_URL}/users/me/messages",
                headers=GmailTool._get_headers(access_token),
                params=params
            )
            
            if response.status_code != 200:
                raise Exception(f"Gmail API error: {response.text}")
            
            result = response.json()
            messages = result.get("messages", [])
            
            # Get full details for each message
            detailed_messages = []
            for msg in messages:
                try:
                    detailed = await GmailTool.get_email(access_token, msg["id"])
                    detailed_messages.append(detailed)
                except Exception as e:
                    logger.error(f"Failed to get message {msg['id']}: {e}")
            
            return {
                "result_size_estimate": result.get("resultSizeEstimate"),
                "messages": detailed_messages
            }
    
    @staticmethod
    async def delete_email(
        access_token: str,
        message_id: str
    ) -> Dict[str, Any]:
        """Delete an email (move to trash)."""
        async with httpx.AsyncClient() as client:
            response = await client.delete(
                f"{GmailTool.BASE_URL}/users/me/messages/{message_id}",
                headers=GmailTool._get_headers(access_token)
            )
            
            if response.status_code != 204:
                raise Exception(f"Gmail API error: {response.text}")
            
            return {"success": True}
    
    @staticmethod
    async def add_labels(
        access_token: str,
        message_id: str,
        label_ids: List[str]
    ) -> Dict[str, Any]:
        """Add labels to an email."""
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{GmailTool.BASE_URL}/users/me/messages/{message_id}/modify",
                headers=GmailTool._get_headers(access_token),
                json={"addLabelIds": label_ids}
            )
            
            if response.status_code != 200:
                raise Exception(f"Gmail API error: {response.text}")
            
            result = response.json()
            return {
                "success": True,
                "label_ids": result.get("labelIds")
            }
    
    @staticmethod
    async def remove_labels(
        access_token: str,
        message_id: str,
        label_ids: List[str]
    ) -> Dict[str, Any]:
        """Remove labels from an email."""
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{GmailTool.BASE_URL}/users/me/messages/{message_id}/modify",
                headers=GmailTool._get_headers(access_token),
                json={"removeLabelIds": label_ids}
            )
            
            if response.status_code != 200:
                raise Exception(f"Gmail API error: {response.text}")
            
            result = response.json()
            return {
                "success": True,
                "label_ids": result.get("labelIds")
            }
    
    @staticmethod
    async def create_draft(
        access_token: str,
        to: str,
        subject: str,
        body: str,
        body_type: str = "Plain Text",
        cc: Optional[str] = None,
        bcc: Optional[str] = None
    ) -> Dict[str, Any]:
        """Create a draft email."""
        raw_message = GmailTool._create_message(
            to=to,
            subject=subject,
            body=body,
            body_type=body_type,
            cc=cc,
            bcc=bcc
        )
        
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{GmailTool.BASE_URL}/users/me/drafts",
                headers=GmailTool._get_headers(access_token),
                json={"message": {"raw": raw_message}}
            )
            
            if response.status_code != 200:
                raise Exception(f"Gmail API error: {response.text}")
            
            result = response.json()
            return {
                "success": True,
                "draft_id": result.get("id"),
                "message_id": result.get("message", {}).get("id")
            }
    
    @staticmethod
    async def send_draft(
        access_token: str,
        draft_id: str
    ) -> Dict[str, Any]:
        """Send a draft email."""
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{GmailTool.BASE_URL}/users/me/drafts/send",
                headers=GmailTool._get_headers(access_token),
                json={"id": draft_id}
            )
            
            if response.status_code != 200:
                raise Exception(f"Gmail API error: {response.text}")
            
            result = response.json()
            return {
                "success": True,
                "message_id": result.get("id"),
                "thread_id": result.get("threadId")
            }
    
    @staticmethod
    async def get_labels(
        access_token: str
    ) -> Dict[str, Any]:
        """Get all labels."""
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{GmailTool.BASE_URL}/users/me/labels",
                headers=GmailTool._get_headers(access_token)
            )
            
            if response.status_code != 200:
                raise Exception(f"Gmail API error: {response.text}")
            
            result = response.json()
            return {
                "labels": result.get("labels", [])
            }


async def execute_gmail_tool(parameters: Dict[str, Any]) -> Dict[str, Any]:
    """Execute Gmail tool operations."""
    operation = parameters.get("operation", "Send Email")
    credentials = parameters.get("credentials", {})
    access_token = credentials.get("access_token") or credentials.get("refresh_token")
    
    if not access_token:
        raise ValueError("Gmail access token is required")
    
    try:
        if operation == "Send Email":
            return await GmailTool.send_email(
                access_token=access_token,
                to=parameters.get("to"),
                subject=parameters.get("subject"),
                body=parameters.get("body"),
                body_type=parameters.get("body_type", "Plain Text"),
                cc=parameters.get("cc"),
                bcc=parameters.get("bcc"),
                attachments=parameters.get("attachments")
            )
        
        elif operation == "Get Email":
            return await GmailTool.get_email(
                access_token=access_token,
                message_id=parameters.get("message_id")
            )
        
        elif operation == "Search Emails":
            return await GmailTool.search_emails(
                access_token=access_token,
                query=parameters.get("query"),
                max_results=parameters.get("max_results", 10),
                label_ids=parameters.get("label_ids")
            )
        
        elif operation == "Delete Email":
            return await GmailTool.delete_email(
                access_token=access_token,
                message_id=parameters.get("message_id")
            )
        
        elif operation == "Add Label":
            return await GmailTool.add_labels(
                access_token=access_token,
                message_id=parameters.get("message_id"),
                label_ids=parameters.get("label_ids")
            )
        
        elif operation == "Remove Label":
            return await GmailTool.remove_labels(
                access_token=access_token,
                message_id=parameters.get("message_id"),
                label_ids=parameters.get("label_ids")
            )
        
        elif operation == "Create Draft":
            return await GmailTool.create_draft(
                access_token=access_token,
                to=parameters.get("to"),
                subject=parameters.get("subject"),
                body=parameters.get("body"),
                body_type=parameters.get("body_type", "Plain Text"),
                cc=parameters.get("cc"),
                bcc=parameters.get("bcc")
            )
        
        elif operation == "Send Draft":
            return await GmailTool.send_draft(
                access_token=access_token,
                draft_id=parameters.get("draft_id")
            )
        
        elif operation == "Get Labels":
            return await GmailTool.get_labels(
                access_token=access_token
            )
        
        else:
            raise ValueError(f"Unknown operation: {operation}")
    
    except Exception as e:
        logger.error(f"Gmail tool error: {e}")
        return {
            "success": False,
            "error": str(e)
        }
