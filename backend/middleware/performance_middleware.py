"""
Performance Middleware
성능 최적화 미들웨어
"""

import time
import json
from typing import Callable
from fastapi import Request, Response
from fastapi.responses import JSONResponse
import logging

from backend.core.performance_optimizer import get_performance_optimizer
from backend.core.structured_logging import get_logger

logger = get_logger(__name__)

class PerformanceMiddleware:
    """성능 최적화 미들웨어"""
    
    def __init__(self, app):
        self.app = app
        self.optimizer = get_performance_optimizer()
    
    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return
        
        request = Request(scope, receive)
        
        # 성능 측정 시작
        start_time = time.time()
        
        # 캐시 확인
        cache_key = self._generate_cache_key(request)
        cached_response = None
        
        if request.method == "GET" and self._is_cacheable(request):
            cached_response = self.optimizer.get_cache(cache_key)
        
        if cached_response:
            # 캐시된 응답 반환
            response = JSONResponse(content=cached_response)
            response.headers["X-Cache"] = "HIT"
            
            await self._send_response(response, send)
            
            # 메트릭 업데이트
            duration = time.time() - start_time
            self.optimizer.metrics.request_count += 1
            self.optimizer.metrics.total_response_time += duration
            
            return
        
        # 배치 처리 확인
        if self._should_batch(request):
            self.optimizer.add_batch_request(
                str(request.url.path),
                {
                    "method": request.method,
                    "path": str(request.url.path),
                    "query_params": dict(request.query_params)
                }
            )
        
        # 원본 요청 처리
        response_data = None
        
        async def capture_response(message):
            nonlocal response_data
            if message["type"] == "http.response.body":
                if response_data is None:
                    response_data = message.get("body", b"")
                else:
                    response_data += message.get("body", b"")
            await send(message)
        
        await self.app(scope, receive, capture_response)
        
        # 성능 메트릭 업데이트
        duration = time.time() - start_time
        self.optimizer.metrics.request_count += 1
        self.optimizer.metrics.total_response_time += duration
        
        # 응답 캐싱
        if (request.method == "GET" and 
            self._is_cacheable(request) and 
            response_data and 
            duration < 5.0):  # 5초 이하의 응답만 캐싱
            
            try:
                # JSON 응답인 경우에만 캐싱
                parsed_data = json.loads(response_data.decode())
                
                # 응답 최적화
                optimized_data = await self.optimizer.optimize_response(parsed_data)
                
                # 캐시 저장
                ttl = self._get_cache_ttl(request)
                self.optimizer.set_cache(cache_key, optimized_data, ttl)
                
            except (json.JSONDecodeError, UnicodeDecodeError):
                # JSON이 아닌 응답은 캐싱하지 않음
                pass
    
    async def _send_response(self, response: Response, send: Callable):
        """응답 전송"""
        await send({
            "type": "http.response.start",
            "status": response.status_code,
            "headers": [
                [key.encode(), value.encode()]
                for key, value in response.headers.items()
            ]
        })
        
        if hasattr(response, 'body'):
            body = response.body
        else:
            body = json.dumps(response.content).encode() if response.content else b""
        
        await send({
            "type": "http.response.body",
            "body": body
        })
    
    def _generate_cache_key(self, request: Request) -> str:
        """캐시 키 생성"""
        # URL 경로와 쿼리 파라미터를 기반으로 키 생성
        path = str(request.url.path)
        query_params = sorted(request.query_params.items())
        query_string = "&".join([f"{k}={v}" for k, v in query_params])
        
        cache_key = f"{path}?{query_string}" if query_string else path
        
        # 사용자별 캐시가 필요한 경우
        if self._requires_user_cache(request):
            user_id = self._extract_user_id(request)
            if user_id:
                cache_key = f"user:{user_id}:{cache_key}"
        
        return cache_key
    
    def _is_cacheable(self, request: Request) -> bool:
        """캐시 가능 여부 확인"""
        path = str(request.url.path)
        
        # 캐시 가능한 엔드포인트
        cacheable_patterns = [
            "/api/agent-builder/agent-olympics/leaderboard",
            "/api/agent-builder/agent-olympics/agents",
            "/api/agent-builder/agent-olympics/competitions",
            "/api/agent-builder/emotional-ai/emotion-types",
            "/api/agent-builder/workflow-dna/gene-types",
            "/api/agent-builder/workflow-dna/experiments",
        ]
        
        # 캐시 불가능한 패턴
        non_cacheable_patterns = [
            "/progress",  # 실시간 진행률
            "/analyze",   # 분석 요청
            "/start",     # 시작 요청
            "/stop",      # 중단 요청
        ]
        
        # 캐시 불가능한 패턴 확인
        for pattern in non_cacheable_patterns:
            if pattern in path:
                return False
        
        # 캐시 가능한 패턴 확인
        for pattern in cacheable_patterns:
            if path.startswith(pattern):
                return True
        
        return False
    
    def _requires_user_cache(self, request: Request) -> bool:
        """사용자별 캐시 필요 여부"""
        path = str(request.url.path)
        
        user_specific_patterns = [
            "/api/agent-builder/emotional-ai/users/",
            "/api/agent-builder/workflow-dna/experiments/"
        ]
        
        return any(pattern in path for pattern in user_specific_patterns)
    
    def _extract_user_id(self, request: Request) -> str:
        """요청에서 사용자 ID 추출"""
        # Authorization 헤더에서 추출하거나 경로에서 추출
        path_parts = str(request.url.path).split('/')
        
        # /users/{user_id}/ 패턴에서 추출
        if 'users' in path_parts:
            try:
                user_index = path_parts.index('users')
                if user_index + 1 < len(path_parts):
                    return path_parts[user_index + 1]
            except (ValueError, IndexError):
                pass
        
        return "anonymous"
    
    def _get_cache_ttl(self, request: Request) -> int:
        """캐시 TTL 결정"""
        path = str(request.url.path)
        
        # 경로별 TTL 설정
        ttl_config = {
            "leaderboard": 30,      # 30초
            "agents": 60,           # 1분
            "competitions": 120,    # 2분
            "experiments": 300,     # 5분
            "emotion-types": 3600,  # 1시간
            "gene-types": 3600,     # 1시간
        }
        
        for pattern, ttl in ttl_config.items():
            if pattern in path:
                return ttl
        
        return 300  # 기본 5분
    
    def _should_batch(self, request: Request) -> bool:
        """배치 처리 여부 확인"""
        path = str(request.url.path)
        
        # 배치 처리 가능한 엔드포인트
        batch_patterns = [
            "/progress",
            "/emotion",
            "/population"
        ]
        
        return any(pattern in path for pattern in batch_patterns)

def add_performance_middleware(app):
    """성능 미들웨어 추가"""
    app.add_middleware(PerformanceMiddleware)
    logger.info("Performance middleware added")