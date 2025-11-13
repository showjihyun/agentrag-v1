"""
Email Integration Service

Provides methods to send emails via SMTP.
"""

import logging
from typing import List, Optional, Dict, Any
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
import asyncio
from functools import partial

logger = logging.getLogger(__name__)


class EmailService:
    """Service for sending emails via SMTP."""
    
    def __init__(
        self,
        smtp_host: str,
        smtp_port: int,
        username: str,
        password: str,
        use_tls: bool = True,
    ):
        """
        Initialize Email service.
        
        Args:
            smtp_host: SMTP server hostname
            smtp_port: SMTP server port
            username: SMTP username (usually email address)
            password: SMTP password or app password
            use_tls: Whether to use TLS encryption
        """
        self.smtp_host = smtp_host
        self.smtp_port = smtp_port
        self.username = username
        self.password = password
        self.use_tls = use_tls
    
    async def send_email(
        self,
        to: List[str],
        subject: str,
        body: str,
        body_type: str = "text",
        cc: Optional[List[str]] = None,
        bcc: Optional[List[str]] = None,
        attachments: Optional[List[Dict[str, Any]]] = None,
        from_name: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Send an email.
        
        Args:
            to: List of recipient email addresses
            subject: Email subject
            body: Email body content
            body_type: 'text' or 'html'
            cc: List of CC recipients
            bcc: List of BCC recipients
            attachments: List of attachment dicts with 'filename' and 'content'
            from_name: Display name for sender
            
        Returns:
            Result dict with success status
        """
        try:
            # Run blocking SMTP operations in thread pool
            loop = asyncio.get_event_loop()
            result = await loop.run_in_executor(
                None,
                partial(
                    self._send_email_sync,
                    to=to,
                    subject=subject,
                    body=body,
                    body_type=body_type,
                    cc=cc,
                    bcc=bcc,
                    attachments=attachments,
                    from_name=from_name,
                ),
            )
            return result
            
        except Exception as e:
            logger.error(f"Failed to send email: {e}")
            raise
    
    def _send_email_sync(
        self,
        to: List[str],
        subject: str,
        body: str,
        body_type: str = "text",
        cc: Optional[List[str]] = None,
        bcc: Optional[List[str]] = None,
        attachments: Optional[List[Dict[str, Any]]] = None,
        from_name: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Synchronous email sending (runs in thread pool)."""
        
        # Create message
        msg = MIMEMultipart("alternative")
        msg["Subject"] = subject
        
        if from_name:
            msg["From"] = f"{from_name} <{self.username}>"
        else:
            msg["From"] = self.username
        
        msg["To"] = ", ".join(to)
        
        if cc:
            msg["Cc"] = ", ".join(cc)
        
        # Attach body
        if body_type == "html":
            msg.attach(MIMEText(body, "html"))
        else:
            msg.attach(MIMEText(body, "plain"))
        
        # Attach files
        if attachments:
            for attachment in attachments:
                part = MIMEBase("application", "octet-stream")
                part.set_payload(attachment["content"])
                encoders.encode_base64(part)
                part.add_header(
                    "Content-Disposition",
                    f"attachment; filename= {attachment['filename']}",
                )
                msg.attach(part)
        
        # Send email
        try:
            with smtplib.SMTP(self.smtp_host, self.smtp_port) as server:
                if self.use_tls:
                    server.starttls()
                
                server.login(self.username, self.password)
                
                # Combine all recipients
                all_recipients = to + (cc or []) + (bcc or [])
                
                server.sendmail(self.username, all_recipients, msg.as_string())
                
                logger.info(f"Email sent to {len(all_recipients)} recipients")
                
                return {
                    "success": True,
                    "recipients": len(all_recipients),
                    "to": to,
                    "cc": cc,
                    "bcc": bcc,
                }
                
        except smtplib.SMTPAuthenticationError:
            logger.error("SMTP authentication failed")
            raise Exception("SMTP authentication failed. Check username and password.")
        except smtplib.SMTPException as e:
            logger.error(f"SMTP error: {e}")
            raise Exception(f"SMTP error: {str(e)}")
    
    async def test_connection(self) -> bool:
        """
        Test SMTP connection.
        
        Returns:
            True if connection is successful
        """
        try:
            loop = asyncio.get_event_loop()
            result = await loop.run_in_executor(
                None,
                self._test_connection_sync,
            )
            return result
        except Exception as e:
            logger.error(f"SMTP connection test failed: {e}")
            return False
    
    def _test_connection_sync(self) -> bool:
        """Synchronous connection test."""
        try:
            with smtplib.SMTP(self.smtp_host, self.smtp_port, timeout=10) as server:
                if self.use_tls:
                    server.starttls()
                server.login(self.username, self.password)
                return True
        except Exception:
            return False


# Common SMTP configurations
SMTP_CONFIGS = {
    "gmail": {
        "smtp_host": "smtp.gmail.com",
        "smtp_port": 587,
        "use_tls": True,
    },
    "outlook": {
        "smtp_host": "smtp-mail.outlook.com",
        "smtp_port": 587,
        "use_tls": True,
    },
    "yahoo": {
        "smtp_host": "smtp.mail.yahoo.com",
        "smtp_port": 587,
        "use_tls": True,
    },
    "sendgrid": {
        "smtp_host": "smtp.sendgrid.net",
        "smtp_port": 587,
        "use_tls": True,
    },
}
