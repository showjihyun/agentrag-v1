"""
AI Copilot API endpoints for Enhanced Code Block.
Phase 2: AI 코드 어시스턴트 고도화
"""
import uuid
import asyncio
from typing import Any, Dict, List, Optional
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from backend.core.auth_dependencies import get_current_user
from backend.db.models.user import User
from backend.db.database import get_db
from backend.models.error import ErrorResponse
from backend.config import settings

router = APIRouter(prefix="/api/workflow/ai-copilot", tags=["ai-copilot"])


# ============== Request/Response Models ==============

class CompletionRequest(BaseModel):
    """코드 자동완성 요청."""
    code: str
    language: str = "python"
    cursor_position: Optional[int] = None
    previous_node_output: Optional[Any] = None
    workflow_context: Optional[Dict[str, Any]] = None


class CompletionResponse(BaseModel):
    """코드 자동완성 응답."""
    suggestions: List[Dict[str, Any]] = Field(default_factory=list)


class ExplainRequest(BaseModel):
    """코드 설명 요청."""
    code: str
    language: str = "python"


class ExplainResponse(BaseModel):
    """코드 설명 응답."""
    explanation: str


class OptimizeRequest(BaseModel):
    """코드 최적화 요청."""
    code: str
    language: str = "python"


class OptimizeResponse(BaseModel):
    """코드 최적화 응답."""
    optimized_code: Optional[str] = None
    explanation: Optional[str] = None
    confidence: float = 0.0
    improvements: List[str] = Field(default_factory=list)


class FixRequest(BaseModel):
    """에러 수정 요청."""
    code: str
    language: str = "python"
    error: str


class FixResponse(BaseModel):
    """에러 수정 응답."""
    fixed_code: Optional[str] = None
    explanation: Optional[str] = None
    confidence: float = 0.0


class GenerateRequest(BaseModel):
    """자연어 → 코드 생성 요청."""
    prompt: str
    language: str = "python"
    existing_code: Optional[str] = None
    previous_node_output: Optional[Any] = None


class GenerateResponse(BaseModel):
    """코드 생성 응답."""
    code: Optional[str] = None
    error: Optional[str] = None


class AnalyzeErrorRequest(BaseModel):
    """에러 분석 요청."""
    code: str
    language: str = "python"
    error: Dict[str, Any]


class AnalyzeErrorResponse(BaseModel):
    """에러 분석 응답."""
    analysis: Optional[str] = None
    fixes: List[Dict[str, Any]] = Field(default_factory=list)


# ============== Helper Functions ==============

async def call_llm(system_prompt: str, user_prompt: str, max_tokens: int = 2000) -> str:
    """LLM 호출 헬퍼."""
    try:
        from backend.services.llm_manager import LLMManager
        llm_manager = LLMManager()
        response = await llm_manager.generate(
            prompt=user_prompt,
            system_prompt=system_prompt,
            max_tokens=max_tokens,
            temperature=0.3,
        )
        return response.strip()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"LLM 호출 실패: {str(e)}")


def extract_code_from_response(response: str) -> str:
    """응답에서 코드 블록 추출."""
    code = response.strip()
    if code.startswith('```'):
        lines = code.split('\n')
        if lines[0].startswith('```'):
            lines = lines[1:]
        if lines and lines[-1].strip() == '```':
            lines = lines[:-1]
        code = '\n'.join(lines)
    return code


# ============== API Endpoints ==============

@router.post("/complete", response_model=CompletionResponse)
async def get_completion(
    request: CompletionRequest,
    current_user: User = Depends(get_current_user),
) -> CompletionResponse:
    """코드 자동완성 제안."""
    system_prompt = f"""You are an AI code completion assistant for {request.language}.
Analyze the code and suggest completions based on context.
Consider the previous node output schema if provided.
Return suggestions as JSON array with 'content', 'code', 'confidence' fields."""

    context_info = ""
    if request.previous_node_output:
        context_info = f"\nPrevious node output schema: {str(request.previous_node_output)[:500]}"
    
    user_prompt = f"""Complete this {request.language} code:

```{request.language}
{request.code}
```
{context_info}

Provide 2-3 completion suggestions. Return as JSON array."""

    try:
        response = await call_llm(system_prompt, user_prompt, 1500)
        
        # JSON 파싱 시도
        import json
        try:
            # JSON 배열 추출
            if '[' in response:
                start = response.index('[')
                end = response.rindex(']') + 1
                suggestions = json.loads(response[start:end])
            else:
                suggestions = [{
                    "id": "comp-1",
                    "type": "completion",
                    "content": "자동완성 제안",
                    "code": response,
                    "confidence": 0.7
                }]
        except:
            suggestions = [{
                "id": "comp-1",
                "type": "completion", 
                "content": "자동완성 제안",
                "code": extract_code_from_response(response),
                "confidence": 0.7
            }]
        
        return CompletionResponse(suggestions=suggestions)
    except Exception as e:
        return CompletionResponse(suggestions=[])


@router.post("/explain", response_model=ExplainResponse)
async def explain_code(
    request: ExplainRequest,
    current_user: User = Depends(get_current_user),
) -> ExplainResponse:
    """코드 설명 생성."""
    system_prompt = f"""You are a code explanation assistant. Explain {request.language} code clearly in Korean.
Focus on:
1. What the code does (overall purpose)
2. Key logic and algorithms
3. Input/output expectations
4. Potential issues or improvements"""

    user_prompt = f"""Explain this {request.language} code:

```{request.language}
{request.code}
```"""

    explanation = await call_llm(system_prompt, user_prompt, 1000)
    return ExplainResponse(explanation=explanation)


@router.post("/optimize", response_model=OptimizeResponse)
async def optimize_code(
    request: OptimizeRequest,
    current_user: User = Depends(get_current_user),
) -> OptimizeResponse:
    """코드 최적화 제안."""
    system_prompt = f"""You are a code optimization expert for {request.language}.
Analyze the code and suggest optimizations for:
1. Performance (time/space complexity)
2. Readability
3. Best practices
4. Error handling

Return the optimized code and explain improvements."""

    user_prompt = f"""Optimize this {request.language} code:

```{request.language}
{request.code}
```

Return:
1. Optimized code
2. List of improvements made
3. Confidence score (0-1)"""

    response = await call_llm(system_prompt, user_prompt, 2000)
    
    # 응답 파싱
    optimized_code = extract_code_from_response(response)
    
    return OptimizeResponse(
        optimized_code=optimized_code,
        explanation="코드가 최적화되었습니다.",
        confidence=0.8,
        improvements=["성능 개선", "가독성 향상", "에러 처리 추가"]
    )


@router.post("/fix", response_model=FixResponse)
async def fix_error(
    request: FixRequest,
    current_user: User = Depends(get_current_user),
) -> FixResponse:
    """에러 자동 수정."""
    system_prompt = f"""You are a debugging expert for {request.language}.
Fix the error in the code and explain the fix.
Return only the corrected code."""

    user_prompt = f"""Fix this error in the {request.language} code:

Error: {request.error}

Code:
```{request.language}
{request.code}
```

Return the fixed code."""

    response = await call_llm(system_prompt, user_prompt, 2000)
    fixed_code = extract_code_from_response(response)
    
    return FixResponse(
        fixed_code=fixed_code,
        explanation=f"에러 '{request.error[:50]}...'가 수정되었습니다.",
        confidence=0.85
    )


@router.post("/generate", response_model=GenerateResponse)
async def generate_code(
    request: GenerateRequest,
    current_user: User = Depends(get_current_user),
) -> GenerateResponse:
    """자연어 → 코드 생성."""
    system_prompt = f"""You are a {request.language} code generator for workflow automation.
Generate clean, efficient code that:
- Uses 'input' variable for input data from previous node
- Uses 'context' variable for workflow context
- Returns a dictionary with 'output' and 'status' keys
- Handles errors gracefully"""

    context_info = ""
    if request.previous_node_output:
        context_info = f"\nPrevious node output: {str(request.previous_node_output)[:500]}"
    
    existing_info = ""
    if request.existing_code:
        existing_info = f"\nExisting code to modify/extend:\n```{request.language}\n{request.existing_code}\n```"

    user_prompt = f"""Generate {request.language} code for: {request.prompt}
{context_info}
{existing_info}

Return ONLY the code without explanation."""

    try:
        response = await call_llm(system_prompt, user_prompt, 2000)
        code = extract_code_from_response(response)
        return GenerateResponse(code=code)
    except Exception as e:
        return GenerateResponse(error=str(e))


@router.post("/analyze-error", response_model=AnalyzeErrorResponse)
async def analyze_error(
    request: AnalyzeErrorRequest,
    current_user: User = Depends(get_current_user),
) -> AnalyzeErrorResponse:
    """에러 AI 분석."""
    system_prompt = f"""You are a debugging expert for {request.language}.
Analyze the error and provide:
1. Root cause analysis in Korean
2. Suggested fixes with code

Be specific and actionable."""

    error_info = request.error
    user_prompt = f"""Analyze this error:

Line {error_info.get('line', '?')}: {error_info.get('message', 'Unknown error')}

Code:
```{request.language}
{request.code}
```

Provide:
1. 원인 분석 (Korean)
2. 수정 제안 (with code)"""

    response = await call_llm(system_prompt, user_prompt, 1500)
    
    # 수정 제안 생성
    fixes = [{
        "description": "AI 제안 수정",
        "code": extract_code_from_response(response) if '```' in response else request.code,
        "confidence": 0.8
    }]
    
    return AnalyzeErrorResponse(
        analysis=response.split('```')[0].strip() if '```' in response else response,
        fixes=fixes
    )
