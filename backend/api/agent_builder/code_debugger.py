"""
Code Debugger API endpoints for Enhanced Code Block.
Phase 2: Interactive Debugger
"""
import uuid
import asyncio
import sys
import traceback
from typing import Any, Dict, List, Optional
from datetime import datetime
from io import StringIO
import threading

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from backend.core.auth_dependencies import get_current_user
from backend.db.models.user import User
from backend.db.database import get_db
from backend.models.error import ErrorResponse

router = APIRouter(prefix="/api/workflow/debug", tags=["code-debugger"])


# ============== In-Memory Debug Sessions ==============
debug_sessions: Dict[str, Dict[str, Any]] = {}


# ============== Request/Response Models ==============

class DebugStartRequest(BaseModel):
    """디버그 세션 시작 요청."""
    code: str
    language: str = "python"
    input: Any = None
    breakpoints: List[int] = Field(default_factory=list)


class DebugResponse(BaseModel):
    """디버그 응답."""
    session_id: Optional[str] = None
    status: str = "idle"
    current_line: Optional[int] = None
    variables: List[Dict[str, Any]] = Field(default_factory=list)
    call_stack: List[Dict[str, Any]] = Field(default_factory=list)
    output: List[str] = Field(default_factory=list)
    error: Optional[str] = None


class DebugSessionRequest(BaseModel):
    """디버그 세션 요청."""
    session_id: str


# ============== Debug Session Manager ==============

class DebugSession:
    """디버그 세션 관리 클래스."""
    
    def __init__(self, session_id: str, code: str, language: str, input_data: Any, breakpoints: List[int]):
        self.session_id = session_id
        self.code = code
        self.language = language
        self.input_data = input_data
        self.breakpoints = set(breakpoints)
        self.status = "idle"
        self.current_line = 0
        self.variables: Dict[str, Any] = {}
        self.call_stack: List[Dict[str, Any]] = []
        self.output: List[str] = []
        self.error: Optional[str] = None
        self.lines = code.split('\n')
        self._step_event = threading.Event()
        self._stop_flag = False
    
    def get_variables_list(self) -> List[Dict[str, Any]]:
        """변수 목록 반환."""
        result = []
        for name, value in self.variables.items():
            if not name.startswith('_'):
                result.append({
                    "name": name,
                    "value": self._serialize_value(value),
                    "type": type(value).__name__
                })
        return result
    
    def _serialize_value(self, value: Any, max_depth: int = 3) -> Any:
        """값 직렬화."""
        if max_depth <= 0:
            return str(value)[:100]
        
        if isinstance(value, (str, int, float, bool, type(None))):
            return value
        elif isinstance(value, (list, tuple)):
            return [self._serialize_value(v, max_depth - 1) for v in value[:10]]
        elif isinstance(value, dict):
            return {k: self._serialize_value(v, max_depth - 1) for k, v in list(value.items())[:10]}
        else:
            return str(value)[:100]
    
    def to_response(self) -> DebugResponse:
        """응답 객체 생성."""
        return DebugResponse(
            session_id=self.session_id,
            status=self.status,
            current_line=self.current_line,
            variables=self.get_variables_list(),
            call_stack=self.call_stack,
            output=self.output,
            error=self.error
        )


def simulate_debug_execution(session: DebugSession) -> DebugResponse:
    """
    디버그 실행 시뮬레이션.
    실제 Python 디버거 대신 간단한 시뮬레이션 제공.
    """
    try:
        # 코드 파싱 및 실행 준비
        lines = session.lines
        session.status = "running"
        
        # 간단한 변수 추적을 위한 globals/locals
        exec_globals = {
            '__builtins__': __builtins__,
            'input': session.input_data,
            'context': {'timestamp': datetime.utcnow().isoformat()},
        }
        exec_locals = {}
        
        # 출력 캡처
        output_capture = StringIO()
        
        # 첫 번째 breakpoint 또는 첫 줄에서 멈춤
        if session.breakpoints:
            session.current_line = min(session.breakpoints)
        else:
            session.current_line = 1
        
        session.status = "paused"
        
        # 초기 변수 설정
        session.variables = {
            'input': session.input_data,
            'context': exec_globals['context'],
        }
        
        # 콜 스택 초기화
        session.call_stack = [
            {"function": "<module>", "line": session.current_line}
        ]
        
        return session.to_response()
        
    except Exception as e:
        session.status = "error"
        session.error = str(e)
        return session.to_response()


def step_execution(session: DebugSession, step_type: str = "over") -> DebugResponse:
    """
    스텝 실행.
    step_type: 'over', 'into', 'out'
    """
    try:
        if session.status != "paused":
            return session.to_response()
        
        # 다음 라인으로 이동
        next_line = session.current_line + 1
        
        # 코드 끝 체크
        if next_line > len(session.lines):
            session.status = "finished"
            session.output.append("=== 실행 완료 ===")
            return session.to_response()
        
        # 현재 라인 실행 시뮬레이션
        current_code = session.lines[session.current_line - 1] if session.current_line > 0 else ""
        
        # 간단한 변수 할당 파싱
        if '=' in current_code and not current_code.strip().startswith('#'):
            parts = current_code.split('=', 1)
            if len(parts) == 2:
                var_name = parts[0].strip()
                if var_name.isidentifier():
                    try:
                        # 안전한 eval 시도
                        value = eval(parts[1].strip(), {"__builtins__": {}}, session.variables)
                        session.variables[var_name] = value
                    except:
                        session.variables[var_name] = f"<{parts[1].strip()[:20]}>"
        
        # print 문 감지
        if 'print(' in current_code:
            session.output.append(f"[Line {session.current_line}] print 실행")
        
        # 다음 라인으로 이동
        session.current_line = next_line
        
        # breakpoint 체크
        if next_line in session.breakpoints:
            session.status = "paused"
        elif step_type == "over":
            session.status = "paused"
        
        # 콜 스택 업데이트
        if session.call_stack:
            session.call_stack[0]["line"] = session.current_line
        
        return session.to_response()
        
    except Exception as e:
        session.status = "error"
        session.error = str(e)
        return session.to_response()


def continue_execution(session: DebugSession) -> DebugResponse:
    """다음 breakpoint까지 실행."""
    try:
        if session.status != "paused":
            return session.to_response()
        
        session.status = "running"
        
        # 다음 breakpoint 찾기
        current = session.current_line
        next_bp = None
        
        for bp in sorted(session.breakpoints):
            if bp > current:
                next_bp = bp
                break
        
        if next_bp:
            # breakpoint까지 실행
            while session.current_line < next_bp and session.current_line <= len(session.lines):
                step_execution(session, "over")
            session.current_line = next_bp
            session.status = "paused"
        else:
            # 끝까지 실행
            session.current_line = len(session.lines)
            session.status = "finished"
            session.output.append("=== 실행 완료 ===")
        
        return session.to_response()
        
    except Exception as e:
        session.status = "error"
        session.error = str(e)
        return session.to_response()


# ============== API Endpoints ==============

@router.post("/start", response_model=DebugResponse)
async def start_debug(
    request: DebugStartRequest,
    current_user: User = Depends(get_current_user),
) -> DebugResponse:
    """디버그 세션 시작."""
    if request.language != "python":
        raise HTTPException(
            status_code=400,
            detail="현재 Python만 디버깅을 지원합니다."
        )
    
    session_id = str(uuid.uuid4())
    session = DebugSession(
        session_id=session_id,
        code=request.code,
        language=request.language,
        input_data=request.input,
        breakpoints=request.breakpoints
    )
    
    debug_sessions[session_id] = session
    
    # 디버그 실행 시작
    return simulate_debug_execution(session)


@router.post("/continue", response_model=DebugResponse)
async def debug_continue(
    request: DebugSessionRequest,
    current_user: User = Depends(get_current_user),
) -> DebugResponse:
    """다음 breakpoint까지 실행."""
    session = debug_sessions.get(request.session_id)
    if not session:
        raise HTTPException(status_code=404, detail="세션을 찾을 수 없습니다.")
    
    return continue_execution(session)


@router.post("/step-over", response_model=DebugResponse)
async def debug_step_over(
    request: DebugSessionRequest,
    current_user: User = Depends(get_current_user),
) -> DebugResponse:
    """Step Over 실행."""
    session = debug_sessions.get(request.session_id)
    if not session:
        raise HTTPException(status_code=404, detail="세션을 찾을 수 없습니다.")
    
    return step_execution(session, "over")


@router.post("/step-into", response_model=DebugResponse)
async def debug_step_into(
    request: DebugSessionRequest,
    current_user: User = Depends(get_current_user),
) -> DebugResponse:
    """Step Into 실행."""
    session = debug_sessions.get(request.session_id)
    if not session:
        raise HTTPException(status_code=404, detail="세션을 찾을 수 없습니다.")
    
    return step_execution(session, "into")


@router.post("/step-out", response_model=DebugResponse)
async def debug_step_out(
    request: DebugSessionRequest,
    current_user: User = Depends(get_current_user),
) -> DebugResponse:
    """Step Out 실행."""
    session = debug_sessions.get(request.session_id)
    if not session:
        raise HTTPException(status_code=404, detail="세션을 찾을 수 없습니다.")
    
    return step_execution(session, "out")


@router.post("/stop", response_model=Dict[str, str])
async def debug_stop(
    request: DebugSessionRequest,
    current_user: User = Depends(get_current_user),
) -> Dict[str, str]:
    """디버그 세션 중지."""
    session = debug_sessions.pop(request.session_id, None)
    if session:
        session.status = "idle"
    
    return {"message": "디버그 세션이 종료되었습니다."}


@router.get("/sessions")
async def list_debug_sessions(
    current_user: User = Depends(get_current_user),
) -> Dict[str, Any]:
    """활성 디버그 세션 목록."""
    return {
        "sessions": [
            {
                "session_id": sid,
                "status": s.status,
                "current_line": s.current_line
            }
            for sid, s in debug_sessions.items()
        ]
    }
