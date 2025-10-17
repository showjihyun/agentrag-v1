"""
Export API

Provides endpoints for exporting conversations in various formats.
"""

import logging
from fastapi import APIRouter, HTTPException, Depends
from fastapi.responses import StreamingResponse, Response
from typing import Optional
from datetime import datetime
import json
import io

from backend.services.conversation_service import ConversationService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/export", tags=["Export"])


@router.post("/pdf")
async def export_conversation_pdf(
    conversation_id: str,
    title: str,
    messages: list,
    include_sources: bool = True,
    include_timestamps: bool = True,
):
    """
    Export conversation as PDF.

    Note: This is a placeholder. For production, use a library like:
    - reportlab
    - weasyprint
    - pdfkit
    """
    try:
        # TODO: Implement actual PDF generation
        # For now, return a simple text-based PDF placeholder

        from reportlab.lib.pagesizes import letter
        from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
        from reportlab.lib.styles import getSampleStyleSheet

        buffer = io.BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=letter)
        styles = getSampleStyleSheet()
        story = []

        # Title
        story.append(Paragraph(f"<b>{title}</b>", styles["Title"]))
        story.append(Spacer(1, 12))

        # Metadata
        story.append(Paragraph(f"Conversation ID: {conversation_id}", styles["Normal"]))
        story.append(
            Paragraph(
                f"Exported: {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')}",
                styles["Normal"],
            )
        )
        story.append(Paragraph(f"Total Messages: {len(messages)}", styles["Normal"]))
        story.append(Spacer(1, 24))

        # Messages
        for msg in messages:
            role = "User" if msg.get("role") == "user" else "Assistant"
            story.append(Paragraph(f"<b>{role}</b>", styles["Heading2"]))

            if include_timestamps and msg.get("timestamp"):
                story.append(Paragraph(f"<i>{msg['timestamp']}</i>", styles["Normal"]))

            story.append(Paragraph(msg.get("content", ""), styles["Normal"]))

            if include_sources and msg.get("sources"):
                story.append(Paragraph("<b>Sources:</b>", styles["Heading3"]))
                for idx, source in enumerate(msg["sources"], 1):
                    story.append(
                        Paragraph(
                            f"{idx}. {source.get('title', 'Unknown')}", styles["Normal"]
                        )
                    )

            story.append(Spacer(1, 12))

        doc.build(story)
        buffer.seek(0)

        return StreamingResponse(
            buffer,
            media_type="application/pdf",
            headers={
                "Content-Disposition": f"attachment; filename={title.replace(' ', '_')}.pdf"
            },
        )

    except Exception as e:
        logger.error(f"Failed to export PDF: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to export PDF: {str(e)}")


@router.post("/markdown")
async def export_conversation_markdown(
    conversation_id: str,
    title: str,
    messages: list,
    include_sources: bool = True,
    include_timestamps: bool = True,
):
    """Export conversation as Markdown."""
    try:
        markdown = f"# {title}\n\n"
        markdown += f"**Conversation ID:** {conversation_id}\n"
        markdown += f"**Exported:** {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')}\n"
        markdown += f"**Total Messages:** {len(messages)}\n\n"
        markdown += "---\n\n"

        for msg in messages:
            role = "👤 User" if msg.get("role") == "user" else "🤖 Assistant"
            markdown += f"## {role}\n\n"

            if include_timestamps and msg.get("timestamp"):
                markdown += f"*{msg['timestamp']}*\n\n"

            markdown += f"{msg.get('content', '')}\n\n"

            if include_sources and msg.get("sources"):
                markdown += "### Sources\n\n"
                for idx, source in enumerate(msg["sources"], 1):
                    markdown += f"{idx}. **{source.get('title', 'Unknown')}**\n"
                    if source.get("content"):
                        markdown += f"   {source['content'][:200]}...\n\n"

            markdown += "---\n\n"

        return Response(
            content=markdown,
            media_type="text/markdown",
            headers={
                "Content-Disposition": f"attachment; filename={title.replace(' ', '_')}.md"
            },
        )

    except Exception as e:
        logger.error(f"Failed to export Markdown: {e}")
        raise HTTPException(
            status_code=500, detail=f"Failed to export Markdown: {str(e)}"
        )


@router.post("/json")
async def export_conversation_json(
    conversation_id: str, title: str, messages: list, include_sources: bool = True
):
    """Export conversation as JSON."""
    try:
        data = {
            "conversationId": conversation_id,
            "title": title,
            "exportedAt": datetime.utcnow().isoformat(),
            "messageCount": len(messages),
            "messages": [
                {
                    "id": msg.get("id"),
                    "role": msg.get("role"),
                    "content": msg.get("content"),
                    "timestamp": msg.get("timestamp"),
                    **(
                        {"sources": msg["sources"]}
                        if include_sources and msg.get("sources")
                        else {}
                    ),
                }
                for msg in messages
            ],
        }

        json_str = json.dumps(data, indent=2, ensure_ascii=False)

        return Response(
            content=json_str,
            media_type="application/json",
            headers={
                "Content-Disposition": f"attachment; filename={title.replace(' ', '_')}.json"
            },
        )

    except Exception as e:
        logger.error(f"Failed to export JSON: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to export JSON: {str(e)}")
