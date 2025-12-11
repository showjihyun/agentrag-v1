"""
Embed Widget API

Provides endpoints for creating and managing embeddable chat widgets
for Chatflows. Includes public endpoints for widget rendering.
"""

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from fastapi.responses import HTMLResponse, JSONResponse
from sqlalchemy.orm import Session
from typing import Optional, List
from pydantic import BaseModel, Field
from datetime import datetime
import uuid
import secrets
import logging

from backend.db.database import get_db
from backend.core.auth_dependencies import get_current_user
from backend.db.models.user import User
from backend.db.models.flows import Chatflow, EmbedConfig, ChatSession, ChatMessage
from backend.services.agent_builder.chatflow_service import ChatflowService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/agent-builder/embed", tags=["Embed Widget"])


# ============ Pydantic Models ============

class EmbedConfigRequest(BaseModel):
    """Request to create/update embed configuration."""
    chatflow_id: str
    theme: str = "light"
    primary_color: str = "#6366f1"
    position: str = "bottom-right"
    widget_title: Optional[str] = None
    welcome_message: Optional[str] = None
    placeholder_text: str = "메시지를 입력하세요..."
    show_branding: bool = True
    custom_css: Optional[str] = None
    allowed_domains: List[str] = []
    rate_limit_per_ip: int = 100


class EmbedConfigResponse(BaseModel):
    """Embed configuration response."""
    id: str
    chatflow_id: str
    embed_token: str
    theme: str
    primary_color: str
    position: str
    widget_title: Optional[str]
    welcome_message: Optional[str]
    placeholder_text: str
    show_branding: bool
    custom_css: Optional[str]
    allowed_domains: List[str]
    rate_limit_per_ip: int
    is_active: bool
    created_at: datetime
    updated_at: datetime
    # Generated URLs
    embed_url: str
    script_tag: str

    class Config:
        from_attributes = True


class PublicChatRequest(BaseModel):
    """Public chat request for embedded widget."""
    message: str
    session_id: Optional[str] = None


# ============ Helper Functions ============

def generate_embed_token() -> str:
    """Generate a unique embed token."""
    return f"emb_{secrets.token_urlsafe(32)}"


def get_embed_script(embed_token: str, base_url: str) -> str:
    """Generate the embed script tag."""
    return f'''<script src="{base_url}/api/agent-builder/embed/widget.js" data-token="{embed_token}"></script>'''


def get_embed_url(embed_token: str, base_url: str) -> str:
    """Generate the embed iframe URL."""
    return f"{base_url}/api/agent-builder/embed/widget/{embed_token}"


# ============ Authenticated Endpoints ============

@router.post("", response_model=EmbedConfigResponse)
async def create_embed_config(
    request: EmbedConfigRequest,
    req: Request,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Create embed configuration for a Chatflow."""
    try:
        chatflow_uuid = uuid.UUID(request.chatflow_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid chatflow ID format")
    
    try:
        # Verify chatflow ownership
        chatflow = db.query(Chatflow).filter(
            Chatflow.id == chatflow_uuid,
            Chatflow.user_id == current_user.id,
            Chatflow.deleted_at.is_(None)
        ).first()
        
        if not chatflow:
            raise HTTPException(status_code=404, detail="Chatflow not found or access denied")
        
        # Check for existing config
        existing = db.query(EmbedConfig).filter(
            EmbedConfig.chatflow_id == chatflow_uuid,
            EmbedConfig.user_id == current_user.id
        ).first()
        
        if existing:
            # Update existing
            existing.theme = request.theme
            existing.primary_color = request.primary_color
            existing.position = request.position
            existing.widget_title = request.widget_title
            existing.welcome_message = request.welcome_message
            existing.placeholder_text = request.placeholder_text
            existing.show_branding = request.show_branding
            existing.custom_css = request.custom_css
            existing.allowed_domains = request.allowed_domains
            existing.rate_limit_per_ip = request.rate_limit_per_ip
            existing.updated_at = datetime.utcnow()
            
            db.commit()
            db.refresh(existing)
            config = existing
        else:
            # Create new
            config = EmbedConfig(
                chatflow_id=chatflow_uuid,
                user_id=current_user.id,
                embed_token=generate_embed_token(),
                theme=request.theme,
                primary_color=request.primary_color,
                position=request.position,
                widget_title=request.widget_title or chatflow.name,
                welcome_message=request.welcome_message or chatflow.chat_config.get("welcome_message", "안녕하세요! 무엇을 도와드릴까요?"),
                placeholder_text=request.placeholder_text,
                show_branding=request.show_branding,
                custom_css=request.custom_css,
                allowed_domains=request.allowed_domains,
                rate_limit_per_ip=request.rate_limit_per_ip,
                is_active=True,
            )
            
            db.add(config)
            db.commit()
            db.refresh(config)
        
        base_url = str(req.base_url).rstrip("/")
        
        return EmbedConfigResponse(
            id=str(config.id),
            chatflow_id=str(config.chatflow_id),
            embed_token=config.embed_token,
            theme=config.theme,
            primary_color=config.primary_color,
            position=config.position,
            widget_title=config.widget_title,
            welcome_message=config.welcome_message,
            placeholder_text=config.placeholder_text,
            show_branding=config.show_branding,
            custom_css=config.custom_css,
            allowed_domains=config.allowed_domains or [],
            rate_limit_per_ip=config.rate_limit_per_ip,
            is_active=config.is_active,
            created_at=config.created_at,
            updated_at=config.updated_at,
            embed_url=get_embed_url(config.embed_token, base_url),
            script_tag=get_embed_script(config.embed_token, base_url),
        )
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Failed to create embed config: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{chatflow_id}", response_model=EmbedConfigResponse)
async def get_embed_config(
    chatflow_id: str,
    req: Request,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Get embed configuration for a Chatflow."""
    try:
        chatflow_uuid = uuid.UUID(chatflow_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid chatflow ID format")
    
    try:
        config = db.query(EmbedConfig).filter(
            EmbedConfig.chatflow_id == chatflow_uuid,
            EmbedConfig.user_id == current_user.id
        ).first()
        
        if not config:
            raise HTTPException(status_code=404, detail="Embed configuration not found")
        
        base_url = str(req.base_url).rstrip("/")
        
        return EmbedConfigResponse(
            id=str(config.id),
            chatflow_id=str(config.chatflow_id),
            embed_token=config.embed_token,
            theme=config.theme,
            primary_color=config.primary_color,
            position=config.position,
            widget_title=config.widget_title,
            welcome_message=config.welcome_message,
            placeholder_text=config.placeholder_text,
            show_branding=config.show_branding,
            custom_css=config.custom_css,
            allowed_domains=config.allowed_domains or [],
            rate_limit_per_ip=config.rate_limit_per_ip,
            is_active=config.is_active,
            created_at=config.created_at,
            updated_at=config.updated_at,
            embed_url=get_embed_url(config.embed_token, base_url),
            script_tag=get_embed_script(config.embed_token, base_url),
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get embed config: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/{chatflow_id}")
async def delete_embed_config(
    chatflow_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Delete embed configuration."""
    try:
        chatflow_uuid = uuid.UUID(chatflow_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid chatflow ID format")
    
    try:
        config = db.query(EmbedConfig).filter(
            EmbedConfig.chatflow_id == chatflow_uuid,
            EmbedConfig.user_id == current_user.id
        ).first()
        
        if not config:
            raise HTTPException(status_code=404, detail="Embed configuration not found")
        
        db.delete(config)
        db.commit()
        
        return {"success": True, "message": "Embed configuration deleted"}
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Failed to delete embed config: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{chatflow_id}/regenerate-token")
async def regenerate_embed_token(
    chatflow_id: str,
    req: Request,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Regenerate the embed token for security."""
    try:
        chatflow_uuid = uuid.UUID(chatflow_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid chatflow ID format")
    
    try:
        config = db.query(EmbedConfig).filter(
            EmbedConfig.chatflow_id == chatflow_uuid,
            EmbedConfig.user_id == current_user.id
        ).first()
        
        if not config:
            raise HTTPException(status_code=404, detail="Embed configuration not found")
        
        config.embed_token = generate_embed_token()
        config.updated_at = datetime.utcnow()
        
        db.commit()
        db.refresh(config)
        
        base_url = str(req.base_url).rstrip("/")
        
        return {
            "success": True,
            "embed_token": config.embed_token,
            "embed_url": get_embed_url(config.embed_token, base_url),
            "script_tag": get_embed_script(config.embed_token, base_url),
        }
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Failed to regenerate token: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============ Public Endpoints (No Auth Required) ============

@router.get("/widget/{embed_token}", response_class=HTMLResponse)
async def get_widget_html(
    embed_token: str,
    req: Request,
    db: Session = Depends(get_db),
):
    """Get the embeddable widget HTML."""
    config = db.query(EmbedConfig).filter(
        EmbedConfig.embed_token == embed_token,
        EmbedConfig.is_active == True
    ).first()
    
    if not config:
        return HTMLResponse(content="<html><body>Widget not found</body></html>", status_code=404)
    
    # Check domain restrictions
    origin = req.headers.get("origin", "")
    if config.allowed_domains and origin:
        domain = origin.replace("http://", "").replace("https://", "").split("/")[0]
        if domain not in config.allowed_domains and "*" not in config.allowed_domains:
            return HTMLResponse(content="<html><body>Domain not allowed</body></html>", status_code=403)
    
    chatflow = db.query(Chatflow).filter(Chatflow.id == config.chatflow_id).first()
    if not chatflow:
        return HTMLResponse(content="<html><body>Chatflow not found</body></html>", status_code=404)
    
    base_url = str(req.base_url).rstrip("/")
    
    html = f'''<!DOCTYPE html>
<html lang="ko">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{config.widget_title or chatflow.name}</title>
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; }}
        .chat-container {{
            display: flex;
            flex-direction: column;
            height: 100vh;
            background: {config.theme == 'dark' and '#1f2937' or '#ffffff'};
            color: {config.theme == 'dark' and '#f9fafb' or '#1f2937'};
        }}
        .chat-header {{
            padding: 16px;
            background: {config.primary_color};
            color: white;
            font-weight: 600;
        }}
        .chat-messages {{
            flex: 1;
            overflow-y: auto;
            padding: 16px;
        }}
        .message {{
            margin-bottom: 12px;
            padding: 10px 14px;
            border-radius: 12px;
            max-width: 80%;
        }}
        .message.user {{
            background: {config.primary_color};
            color: white;
            margin-left: auto;
        }}
        .message.assistant {{
            background: {config.theme == 'dark' and '#374151' or '#f3f4f6'};
        }}
        .chat-input-container {{
            padding: 16px;
            border-top: 1px solid {config.theme == 'dark' and '#374151' or '#e5e7eb'};
            display: flex;
            gap: 8px;
        }}
        .chat-input {{
            flex: 1;
            padding: 10px 14px;
            border: 1px solid {config.theme == 'dark' and '#4b5563' or '#d1d5db'};
            border-radius: 8px;
            background: {config.theme == 'dark' and '#374151' or '#ffffff'};
            color: {config.theme == 'dark' and '#f9fafb' or '#1f2937'};
            outline: none;
        }}
        .chat-input:focus {{ border-color: {config.primary_color}; }}
        .send-button {{
            padding: 10px 20px;
            background: {config.primary_color};
            color: white;
            border: none;
            border-radius: 8px;
            cursor: pointer;
        }}
        .send-button:hover {{ opacity: 0.9; }}
        .branding {{
            text-align: center;
            padding: 8px;
            font-size: 12px;
            color: {config.theme == 'dark' and '#9ca3af' or '#6b7280'};
        }}
        {config.custom_css or ''}
    </style>
</head>
<body>
    <div class="chat-container">
        <div class="chat-header">{config.widget_title or chatflow.name}</div>
        <div class="chat-messages" id="messages">
            <div class="message assistant">{config.welcome_message or '안녕하세요! 무엇을 도와드릴까요?'}</div>
        </div>
        <div class="chat-input-container">
            <input type="text" class="chat-input" id="messageInput" placeholder="{config.placeholder_text}" />
            <button class="send-button" onclick="sendMessage()">전송</button>
        </div>
        {'<div class="branding">Powered by AgenticRAG</div>' if config.show_branding else ''}
    </div>
    <script>
        const API_URL = '{base_url}/api/agent-builder/embed/public/{embed_token}/chat';
        let sessionId = localStorage.getItem('chat_session_{embed_token}') || null;
        
        async function sendMessage() {{
            const input = document.getElementById('messageInput');
            const message = input.value.trim();
            if (!message) return;
            
            // Add user message
            addMessage(message, 'user');
            input.value = '';
            
            try {{
                const response = await fetch(API_URL, {{
                    method: 'POST',
                    headers: {{ 'Content-Type': 'application/json' }},
                    body: JSON.stringify({{ message, session_id: sessionId }})
                }});
                
                const data = await response.json();
                if (data.session_id) {{
                    sessionId = data.session_id;
                    localStorage.setItem('chat_session_{embed_token}', sessionId);
                }}
                
                addMessage(data.response, 'assistant');
            }} catch (error) {{
                addMessage('죄송합니다. 오류가 발생했습니다.', 'assistant');
            }}
        }}
        
        function addMessage(text, role) {{
            const messages = document.getElementById('messages');
            const div = document.createElement('div');
            div.className = 'message ' + role;
            div.textContent = text;
            messages.appendChild(div);
            messages.scrollTop = messages.scrollHeight;
        }}
        
        document.getElementById('messageInput').addEventListener('keypress', (e) => {{
            if (e.key === 'Enter') sendMessage();
        }});
    </script>
</body>
</html>'''
    
    return HTMLResponse(content=html)


@router.get("/widget.js")
async def get_widget_script(
    req: Request,
    db: Session = Depends(get_db),
):
    """Get the widget loader script."""
    base_url = str(req.base_url).rstrip("/")
    
    script = f'''(function() {{
    const script = document.currentScript;
    const token = script.getAttribute('data-token');
    if (!token) {{ console.error('AgenticRAG: Missing data-token'); return; }}
    
    const iframe = document.createElement('iframe');
    iframe.src = '{base_url}/api/agent-builder/embed/widget/' + token;
    iframe.style.cssText = 'position:fixed;bottom:20px;right:20px;width:380px;height:600px;border:none;border-radius:12px;box-shadow:0 4px 20px rgba(0,0,0,0.15);z-index:9999;';
    
    const toggle = document.createElement('button');
    toggle.innerHTML = '💬';
    toggle.style.cssText = 'position:fixed;bottom:20px;right:20px;width:60px;height:60px;border-radius:50%;border:none;background:#6366f1;color:white;font-size:24px;cursor:pointer;z-index:10000;box-shadow:0 4px 12px rgba(0,0,0,0.15);';
    
    let isOpen = false;
    iframe.style.display = 'none';
    
    toggle.onclick = function() {{
        isOpen = !isOpen;
        iframe.style.display = isOpen ? 'block' : 'none';
        toggle.innerHTML = isOpen ? '✕' : '💬';
    }};
    
    document.body.appendChild(iframe);
    document.body.appendChild(toggle);
}})();'''
    
    return HTMLResponse(content=script, media_type="application/javascript")


@router.post("/public/{embed_token}/chat")
async def public_chat(
    embed_token: str,
    request: PublicChatRequest,
    req: Request,
    db: Session = Depends(get_db),
):
    """Public chat endpoint for embedded widgets."""
    config = db.query(EmbedConfig).filter(
        EmbedConfig.embed_token == embed_token,
        EmbedConfig.is_active == True
    ).first()
    
    if not config:
        raise HTTPException(status_code=404, detail="Widget not found")
    
    # Check domain restrictions
    origin = req.headers.get("origin", "")
    if config.allowed_domains and origin:
        domain = origin.replace("http://", "").replace("https://", "").split("/")[0]
        if domain not in config.allowed_domains and "*" not in config.allowed_domains:
            raise HTTPException(status_code=403, detail="Domain not allowed")
    
    chatflow = db.query(Chatflow).filter(
        Chatflow.id == config.chatflow_id,
        Chatflow.deleted_at.is_(None)
    ).first()
    
    if not chatflow:
        raise HTTPException(status_code=404, detail="Chatflow not found")
    
    try:
        # Get or create session
        session = None
        if request.session_id:
            try:
                session_uuid = uuid.UUID(request.session_id)
                session = db.query(ChatSession).filter(
                    ChatSession.id == session_uuid,
                    ChatSession.chatflow_id == chatflow.id
                ).first()
            except ValueError:
                pass
        
        if not session:
            session = ChatSession(
                chatflow_id=chatflow.id,
                session_token=secrets.token_urlsafe(16),
                message_count=0,
            )
            db.add(session)
            db.flush()
        
        # Save user message
        user_message = ChatMessage(
            session_id=session.id,
            role="user",
            content=request.message,
        )
        db.add(user_message)
        session.message_count = (session.message_count or 0) + 1
        session.last_message_at = datetime.utcnow()
        
        # Extract LLM configuration from chatflow
        llm_config = chatflow.llm_config or {}
        chat_config = {
            "provider": llm_config.get("provider", "ollama"),
            "model": llm_config.get("model", "llama3.3:70b"),
            "system_prompt": chatflow.system_prompt or "",
            "temperature": llm_config.get("temperature", 0.7),
            "max_tokens": llm_config.get("max_tokens", 1000),
        }
        
        # Use ChatflowService for actual LLM chat
        chatflow_service = ChatflowService(db)
        result = await chatflow_service.chat(
            session_id=str(session.id),
            user_message=request.message,
            config=chat_config,
            workflow_id=str(chatflow.id),
        )
        
        if result.get("success"):
            response_text = result.get("response", "")
        else:
            response_text = f"죄송합니다. 오류가 발생했습니다: {result.get('error', '알 수 없는 오류')}"
        
        # Save assistant message
        assistant_message = ChatMessage(
            session_id=session.id,
            role="assistant",
            content=response_text,
        )
        db.add(assistant_message)
        session.message_count = (session.message_count or 0) + 1
        
        db.commit()
        
        return {
            "response": response_text,
            "session_id": str(session.id),
            "timestamp": datetime.utcnow().isoformat(),
            "usage": result.get("usage"),
        }
        
    except Exception as e:
        db.rollback()
        logger.error(f"Public chat error: {e}")
        raise HTTPException(status_code=500, detail="Chat error")


@router.get("/public/{embed_token}/config")
async def get_public_config(
    embed_token: str,
    db: Session = Depends(get_db),
):
    """Get public widget configuration."""
    config = db.query(EmbedConfig).filter(
        EmbedConfig.embed_token == embed_token,
        EmbedConfig.is_active == True
    ).first()
    
    if not config:
        raise HTTPException(status_code=404, detail="Widget not found")
    
    chatflow = db.query(Chatflow).filter(Chatflow.id == config.chatflow_id).first()
    
    return {
        "theme": config.theme,
        "primary_color": config.primary_color,
        "position": config.position,
        "widget_title": config.widget_title or (chatflow.name if chatflow else "Chat"),
        "welcome_message": config.welcome_message,
        "placeholder_text": config.placeholder_text,
        "show_branding": config.show_branding,
    }
