"""
PDF Export Service

Provides PDF generation capabilities for:
- Chat conversations
- Workflow reports
- Dashboard exports
- Document summaries
"""

import logging
from typing import Optional, List, Dict, Any
from datetime import datetime
from io import BytesIO
import base64

logger = logging.getLogger(__name__)

# Try to import PDF libraries
try:
    from reportlab.lib import colors
    from reportlab.lib.pagesizes import A4, letter
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.units import inch, cm
    from reportlab.platypus import (
        SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
        PageBreak, Image, ListFlowable, ListItem
    )
    from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_RIGHT
    REPORTLAB_AVAILABLE = True
except ImportError:
    REPORTLAB_AVAILABLE = False
    logger.warning("reportlab not installed. PDF export will be limited.")


class PDFExportService:
    """
    Service for generating PDF exports.
    """
    
    def __init__(self):
        self.page_size = A4 if REPORTLAB_AVAILABLE else None
        self._styles = None
    
    @property
    def styles(self):
        """Get or create styles."""
        if not REPORTLAB_AVAILABLE:
            return None
        
        if self._styles is None:
            self._styles = getSampleStyleSheet()
            
            # Custom styles
            self._styles.add(ParagraphStyle(
                name='ChatUser',
                parent=self._styles['Normal'],
                fontSize=10,
                textColor=colors.HexColor('#1a1a2e'),
                backColor=colors.HexColor('#e8f4f8'),
                borderPadding=8,
                spaceBefore=6,
                spaceAfter=6,
            ))
            
            self._styles.add(ParagraphStyle(
                name='ChatAssistant',
                parent=self._styles['Normal'],
                fontSize=10,
                textColor=colors.HexColor('#1a1a2e'),
                backColor=colors.HexColor('#f0f0f5'),
                borderPadding=8,
                spaceBefore=6,
                spaceAfter=6,
            ))
            
            self._styles.add(ParagraphStyle(
                name='ReportTitle',
                parent=self._styles['Heading1'],
                fontSize=24,
                textColor=colors.HexColor('#4F46E5'),
                spaceAfter=20,
                alignment=TA_CENTER,
            ))
            
            self._styles.add(ParagraphStyle(
                name='SectionHeader',
                parent=self._styles['Heading2'],
                fontSize=14,
                textColor=colors.HexColor('#1e293b'),
                spaceBefore=16,
                spaceAfter=8,
            ))
            
            self._styles.add(ParagraphStyle(
                name='MetaInfo',
                parent=self._styles['Normal'],
                fontSize=9,
                textColor=colors.HexColor('#64748b'),
            ))
        
        return self._styles
    
    def export_chat_history(
        self,
        messages: List[Dict[str, Any]],
        title: str = "Chat Export",
        metadata: Optional[Dict[str, Any]] = None,
    ) -> bytes:
        """Export chat history to PDF."""
        if not REPORTLAB_AVAILABLE:
            raise RuntimeError("reportlab library not installed")
        
        buffer = BytesIO()
        doc = SimpleDocTemplate(
            buffer,
            pagesize=self.page_size,
            rightMargin=72,
            leftMargin=72,
            topMargin=72,
            bottomMargin=72,
        )
        
        story = []
        
        # Title
        story.append(Paragraph(title, self.styles['ReportTitle']))
        
        # Metadata
        if metadata:
            meta_text = f"Generated: {datetime.utcnow().strftime('%Y-%m-%d %H:%M UTC')}"
            if metadata.get("session_id"):
                meta_text += f" | Session: {metadata['session_id'][:8]}..."
            story.append(Paragraph(meta_text, self.styles['MetaInfo']))
        
        story.append(Spacer(1, 20))
        
        # Messages
        for msg in messages:
            role = msg.get("role", "user")
            content = msg.get("content", "")
            timestamp = msg.get("created_at", "")
            
            # Role label
            role_label = "You" if role == "user" else "Assistant"
            style = self.styles['ChatUser'] if role == "user" else self.styles['ChatAssistant']
            
            # Format message
            formatted_content = f"<b>{role_label}</b><br/>{self._escape_html(content)}"
            if timestamp:
                formatted_content += f"<br/><font size='8' color='#94a3b8'>{timestamp}</font>"
            
            story.append(Paragraph(formatted_content, style))
        
        # Build PDF
        doc.build(story)
        
        buffer.seek(0)
        return buffer.getvalue()
    
    def export_workflow_report(
        self,
        workflow: Dict[str, Any],
        executions: List[Dict[str, Any]],
        include_details: bool = True,
    ) -> bytes:
        """Export workflow execution report to PDF."""
        if not REPORTLAB_AVAILABLE:
            raise RuntimeError("reportlab library not installed")
        
        buffer = BytesIO()
        doc = SimpleDocTemplate(
            buffer,
            pagesize=self.page_size,
            rightMargin=72,
            leftMargin=72,
            topMargin=72,
            bottomMargin=72,
        )
        
        story = []
        
        # Title
        workflow_name = workflow.get("name", "Workflow Report")
        story.append(Paragraph(f"Workflow Report: {workflow_name}", self.styles['ReportTitle']))
        
        # Summary section
        story.append(Paragraph("Summary", self.styles['SectionHeader']))
        
        total = len(executions)
        successful = sum(1 for e in executions if e.get("status") == "completed")
        failed = sum(1 for e in executions if e.get("status") == "failed")
        
        summary_data = [
            ["Metric", "Value"],
            ["Total Executions", str(total)],
            ["Successful", str(successful)],
            ["Failed", str(failed)],
            ["Success Rate", f"{(successful/total*100):.1f}%" if total > 0 else "N/A"],
        ]
        
        summary_table = Table(summary_data, colWidths=[200, 200])
        summary_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#4F46E5')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 11),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.HexColor('#f8fafc')),
            ('GRID', (0, 0), (-1, -1), 1, colors.HexColor('#e2e8f0')),
            ('FONTSIZE', (0, 1), (-1, -1), 10),
            ('PADDING', (0, 0), (-1, -1), 8),
        ]))
        
        story.append(summary_table)
        story.append(Spacer(1, 20))
        
        # Execution details
        if include_details and executions:
            story.append(Paragraph("Execution History", self.styles['SectionHeader']))
            
            exec_data = [["ID", "Status", "Duration", "Started At"]]
            
            for exec in executions[:20]:  # Limit to 20 most recent
                exec_id = exec.get("id", "")[:8] + "..."
                status = exec.get("status", "unknown")
                duration = exec.get("duration_ms", 0)
                started = exec.get("started_at", "")[:19] if exec.get("started_at") else ""
                
                exec_data.append([
                    exec_id,
                    status.upper(),
                    f"{duration}ms" if duration else "N/A",
                    started,
                ])
            
            exec_table = Table(exec_data, colWidths=[80, 80, 80, 160])
            exec_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1e293b')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, -1), 9),
                ('GRID', (0, 0), (-1, -1), 1, colors.HexColor('#e2e8f0')),
                ('PADDING', (0, 0), (-1, -1), 6),
                ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f8fafc')]),
            ]))
            
            story.append(exec_table)
        
        # Footer
        story.append(Spacer(1, 30))
        story.append(Paragraph(
            f"Generated by Agentic RAG System on {datetime.utcnow().strftime('%Y-%m-%d %H:%M UTC')}",
            self.styles['MetaInfo']
        ))
        
        doc.build(story)
        
        buffer.seek(0)
        return buffer.getvalue()
    
    def export_dashboard(
        self,
        dashboard_data: Dict[str, Any],
        charts_base64: Optional[List[str]] = None,
    ) -> bytes:
        """Export dashboard to PDF."""
        if not REPORTLAB_AVAILABLE:
            raise RuntimeError("reportlab library not installed")
        
        buffer = BytesIO()
        doc = SimpleDocTemplate(
            buffer,
            pagesize=self.page_size,
            rightMargin=50,
            leftMargin=50,
            topMargin=50,
            bottomMargin=50,
        )
        
        story = []
        
        # Title
        story.append(Paragraph("Dashboard Report", self.styles['ReportTitle']))
        story.append(Paragraph(
            f"Generated: {datetime.utcnow().strftime('%Y-%m-%d %H:%M UTC')}",
            self.styles['MetaInfo']
        ))
        story.append(Spacer(1, 20))
        
        # Metrics summary
        if "metrics" in dashboard_data:
            story.append(Paragraph("Key Metrics", self.styles['SectionHeader']))
            
            metrics = dashboard_data["metrics"]
            metrics_data = [["Metric", "Value", "Change"]]
            
            for metric in metrics:
                metrics_data.append([
                    metric.get("name", ""),
                    str(metric.get("value", "")),
                    metric.get("change", ""),
                ])
            
            if len(metrics_data) > 1:
                metrics_table = Table(metrics_data, colWidths=[180, 120, 100])
                metrics_table.setStyle(TableStyle([
                    ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#4F46E5')),
                    ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
                    ('GRID', (0, 0), (-1, -1), 1, colors.HexColor('#e2e8f0')),
                    ('PADDING', (0, 0), (-1, -1), 8),
                ]))
                story.append(metrics_table)
                story.append(Spacer(1, 20))
        
        # Charts (if provided as base64 images)
        if charts_base64:
            story.append(Paragraph("Charts", self.styles['SectionHeader']))
            
            for i, chart_b64 in enumerate(charts_base64):
                try:
                    chart_data = base64.b64decode(chart_b64)
                    chart_buffer = BytesIO(chart_data)
                    img = Image(chart_buffer, width=400, height=250)
                    story.append(img)
                    story.append(Spacer(1, 10))
                except Exception as e:
                    logger.warning(f"Failed to add chart {i}: {e}")
        
        doc.build(story)
        
        buffer.seek(0)
        return buffer.getvalue()
    
    def _escape_html(self, text: str) -> str:
        """Escape HTML special characters."""
        return (
            text
            .replace("&", "&amp;")
            .replace("<", "&lt;")
            .replace(">", "&gt;")
            .replace("\n", "<br/>")
        )


# Global instance
_pdf_service: Optional[PDFExportService] = None


def get_pdf_export_service() -> PDFExportService:
    """Get or create PDF export service instance."""
    global _pdf_service
    if _pdf_service is None:
        _pdf_service = PDFExportService()
    return _pdf_service
