"""Email tool executor."""

import os
from typing import Dict, Any, Optional
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

from ..base_executor import BaseToolExecutor, ToolExecutionResult


class EmailExecutor(BaseToolExecutor):
    """Executor for Email tool."""
    
    def __init__(self):
        super().__init__("send_email", "Send Email")
        self.category = "communication"
        self.smtp_host = os.getenv("SMTP_HOST", "smtp.gmail.com")
        self.smtp_port = int(os.getenv("SMTP_PORT", "587"))
        self.smtp_user = os.getenv("SMTP_USER")
        self.smtp_password = os.getenv("SMTP_PASSWORD")
        
        # Define parameter schema with Select Boxes
        self.params_schema = {
            "to": {
                "type": "string",
                "description": "Recipient email address",
                "required": True,
                "placeholder": "recipient@example.com",
                "pattern": r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$",
                "helpText": "Email address of the recipient"
            },
            "subject": {
                "type": "string",
                "description": "Email subject",
                "required": True,
                "placeholder": "Subject line",
                "helpText": "Subject line of the email"
            },
            "body": {
                "type": "textarea",
                "description": "Email body content",
                "required": True,
                "placeholder": "Enter your message here...",
                "helpText": "Main content of the email"
            },
            "content_type": {
                "type": "select",  # ✅ Select Box
                "description": "Email content type",
                "required": False,
                "default": "plain",
                "enum": ["plain", "html"],
                "helpText": "Plain text or HTML formatted email"
            },
            "cc": {
                "type": "string",
                "description": "CC email addresses (comma-separated)",
                "required": False,
                "placeholder": "cc1@example.com, cc2@example.com",
                "helpText": "Carbon copy recipients"
            },
            "bcc": {
                "type": "string",
                "description": "BCC email addresses (comma-separated)",
                "required": False,
                "placeholder": "bcc1@example.com",
                "helpText": "Blind carbon copy recipients"
            },
            "priority": {
                "type": "select",  # ✅ Select Box
                "description": "Email priority",
                "required": False,
                "default": "normal",
                "enum": ["low", "normal", "high"],
                "helpText": "Priority level of the email"
            },
            "from": {
                "type": "string",
                "description": "Sender email address (optional)",
                "required": False,
                "placeholder": "sender@example.com",
                "helpText": "Override default sender address"
            }
        }
    
    async def execute(
        self,
        params: Dict[str, Any],
        credentials: Optional[Dict[str, str]] = None
    ) -> ToolExecutionResult:
        """Send email."""
        
        self.validate_params(params, ["to", "subject", "body"])
        
        to_email = params.get("to")
        subject = params.get("subject")
        body = params.get("body")
        from_email = params.get("from", self.smtp_user)
        
        # Get credentials
        smtp_user = credentials.get("smtp_user") if credentials else self.smtp_user
        smtp_password = credentials.get("smtp_password") if credentials else self.smtp_password
        
        if not smtp_user or not smtp_password:
            return ToolExecutionResult(
                success=False,
                output=None,
                error="SMTP credentials not configured"
            )
        
        try:
            # Create message
            msg = MIMEMultipart()
            msg["From"] = from_email
            msg["To"] = to_email
            msg["Subject"] = subject
            msg.attach(MIMEText(body, "plain"))
            
            # Send email
            with smtplib.SMTP(self.smtp_host, self.smtp_port) as server:
                server.starttls()
                server.login(smtp_user, smtp_password)
                server.send_message(msg)
            
            return ToolExecutionResult(
                success=True,
                output={
                    "sent": True,
                    "to": to_email,
                    "subject": subject
                }
            )
            
        except Exception as e:
            return ToolExecutionResult(
                success=False,
                output=None,
                error=f"Failed to send email: {str(e)}"
            )
