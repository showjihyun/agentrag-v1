"""
Email Service

Provides email sending capabilities using multiple providers:
- SendGrid
- AWS SES
- SMTP
"""

import logging
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum
import os

logger = logging.getLogger(__name__)

# Try to import email libraries
try:
    from sendgrid import SendGridAPIClient
    from sendgrid.helpers.mail import Mail, Email, To, Content, Attachment, FileContent, FileName, FileType
    SENDGRID_AVAILABLE = True
except ImportError:
    SENDGRID_AVAILABLE = False

try:
    import boto3
    from botocore.exceptions import ClientError
    AWS_AVAILABLE = True
except ImportError:
    AWS_AVAILABLE = False


class EmailProvider(str, Enum):
    """Email provider options."""
    SENDGRID = "sendgrid"
    AWS_SES = "aws_ses"
    SMTP = "smtp"


class EmailService:
    """Multi-provider email service."""
    
    def __init__(
        self,
        provider: EmailProvider = EmailProvider.SENDGRID,
        sendgrid_api_key: Optional[str] = None,
        aws_region: str = "us-east-1",
        smtp_host: Optional[str] = None,
        smtp_port: int = 587,
        smtp_user: Optional[str] = None,
        smtp_password: Optional[str] = None,
    ):
        self.provider = provider
        self._sendgrid_key = sendgrid_api_key or os.getenv("SENDGRID_API_KEY")
        self._aws_region = aws_region
        self._smtp_config = {
            "host": smtp_host or os.getenv("SMTP_HOST"),
            "port": smtp_port,
            "user": smtp_user or os.getenv("SMTP_USER"),
            "password": smtp_password or os.getenv("SMTP_PASSWORD"),
        }
        self._from_email = os.getenv("EMAIL_FROM", "noreply@example.com")
        self._from_name = os.getenv("EMAIL_FROM_NAME", "Agentic RAG System")

    async def send_email(
        self,
        to_email: str,
        subject: str,
        html_content: str,
        text_content: Optional[str] = None,
        attachments: Optional[List[Dict[str, Any]]] = None,
        reply_to: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Send an email using the configured provider.
        
        Returns:
            dict with 'success', 'message_id', and 'error' keys
        """
        if self.provider == EmailProvider.SENDGRID:
            return await self._send_via_sendgrid(
                to_email, subject, html_content, text_content, attachments, reply_to
            )
        elif self.provider == EmailProvider.AWS_SES:
            return await self._send_via_ses(
                to_email, subject, html_content, text_content, attachments, reply_to
            )
        elif self.provider == EmailProvider.SMTP:
            return await self._send_via_smtp(
                to_email, subject, html_content, text_content, attachments, reply_to
            )
        else:
            return {"success": False, "error": f"Unknown provider: {self.provider}"}
    
    async def _send_via_sendgrid(
        self,
        to_email: str,
        subject: str,
        html_content: str,
        text_content: Optional[str],
        attachments: Optional[List[Dict[str, Any]]],
        reply_to: Optional[str],
    ) -> Dict[str, Any]:
        """Send email via SendGrid."""
        if not SENDGRID_AVAILABLE:
            return {"success": False, "error": "SendGrid library not installed"}
        
        if not self._sendgrid_key:
            return {"success": False, "error": "SendGrid API key not configured"}
        
        try:
            message = Mail(
                from_email=Email(self._from_email, self._from_name),
                to_emails=To(to_email),
                subject=subject,
                html_content=Content("text/html", html_content),
            )
            
            if text_content:
                message.add_content(Content("text/plain", text_content))
            
            if reply_to:
                message.reply_to = Email(reply_to)
            
            # Add attachments
            if attachments:
                for att in attachments:
                    attachment = Attachment(
                        FileContent(att.get("content", "")),
                        FileName(att.get("filename", "attachment")),
                        FileType(att.get("type", "application/octet-stream")),
                    )
                    message.add_attachment(attachment)
            
            sg = SendGridAPIClient(self._sendgrid_key)
            response = sg.send(message)
            
            logger.info(f"Email sent via SendGrid to {to_email}, status: {response.status_code}")
            
            return {
                "success": response.status_code in [200, 201, 202],
                "message_id": response.headers.get("X-Message-Id"),
                "status_code": response.status_code,
            }
            
        except Exception as e:
            logger.error(f"SendGrid send failed: {e}")
            return {"success": False, "error": str(e)}

    async def _send_via_ses(
        self,
        to_email: str,
        subject: str,
        html_content: str,
        text_content: Optional[str],
        attachments: Optional[List[Dict[str, Any]]],
        reply_to: Optional[str],
    ) -> Dict[str, Any]:
        """Send email via AWS SES."""
        if not AWS_AVAILABLE:
            return {"success": False, "error": "boto3 library not installed"}
        
        try:
            client = boto3.client('ses', region_name=self._aws_region)
            
            body = {"Html": {"Charset": "UTF-8", "Data": html_content}}
            if text_content:
                body["Text"] = {"Charset": "UTF-8", "Data": text_content}
            
            message = {
                "Subject": {"Charset": "UTF-8", "Data": subject},
                "Body": body,
            }
            
            kwargs = {
                "Source": f"{self._from_name} <{self._from_email}>",
                "Destination": {"ToAddresses": [to_email]},
                "Message": message,
            }
            
            if reply_to:
                kwargs["ReplyToAddresses"] = [reply_to]
            
            response = client.send_email(**kwargs)
            
            logger.info(f"Email sent via SES to {to_email}, MessageId: {response['MessageId']}")
            
            return {
                "success": True,
                "message_id": response["MessageId"],
            }
            
        except ClientError as e:
            logger.error(f"SES send failed: {e}")
            return {"success": False, "error": str(e)}
        except Exception as e:
            logger.error(f"SES send failed: {e}")
            return {"success": False, "error": str(e)}
    
    async def _send_via_smtp(
        self,
        to_email: str,
        subject: str,
        html_content: str,
        text_content: Optional[str],
        attachments: Optional[List[Dict[str, Any]]],
        reply_to: Optional[str],
    ) -> Dict[str, Any]:
        """Send email via SMTP."""
        import smtplib
        from email.mime.multipart import MIMEMultipart
        from email.mime.text import MIMEText
        from email.mime.base import MIMEBase
        from email import encoders
        import base64
        
        if not self._smtp_config["host"]:
            return {"success": False, "error": "SMTP host not configured"}
        
        try:
            msg = MIMEMultipart('alternative')
            msg['Subject'] = subject
            msg['From'] = f"{self._from_name} <{self._from_email}>"
            msg['To'] = to_email
            
            if reply_to:
                msg['Reply-To'] = reply_to
            
            if text_content:
                msg.attach(MIMEText(text_content, 'plain'))
            msg.attach(MIMEText(html_content, 'html'))
            
            # Add attachments
            if attachments:
                for att in attachments:
                    part = MIMEBase('application', 'octet-stream')
                    content = att.get("content", "")
                    if isinstance(content, str):
                        content = base64.b64decode(content)
                    part.set_payload(content)
                    encoders.encode_base64(part)
                    part.add_header(
                        'Content-Disposition',
                        f'attachment; filename="{att.get("filename", "attachment")}"'
                    )
                    msg.attach(part)
            
            with smtplib.SMTP(self._smtp_config["host"], self._smtp_config["port"]) as server:
                server.starttls()
                if self._smtp_config["user"] and self._smtp_config["password"]:
                    server.login(self._smtp_config["user"], self._smtp_config["password"])
                server.send_message(msg)
            
            logger.info(f"Email sent via SMTP to {to_email}")
            return {"success": True, "message_id": None}
            
        except Exception as e:
            logger.error(f"SMTP send failed: {e}")
            return {"success": False, "error": str(e)}


# Global instance
_email_service: Optional[EmailService] = None


def get_email_service() -> EmailService:
    """Get or create email service instance."""
    global _email_service
    if _email_service is None:
        provider = os.getenv("EMAIL_PROVIDER", "sendgrid").lower()
        _email_service = EmailService(provider=EmailProvider(provider))
    return _email_service
