"""
Circuit Breaker Pattern Implementation
서킷 브레이커 패턴으로 시스템 안정성 향상
"""
import asyncio
import time
from typing import Dict, Any, Optional, Callable, Union, List
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from enum import Enum
import logging
import random
import statistics

from backend.core.error_handling.plugin_errors import (
    PluginException,
    PluginErrorCode,
    PluginResourceError
)

logger = logging.getLogger(__name__)


class CircuitState(Enum):
    """서킷 브레이커 상태"""
    CLOSED = "closed"      # 정상 상태
    OPEN = "open"          # 차단 상태
    HALF_OPEN = "half_open"  # 반개방 상태


class RetryStrategy(Enum):
    """재시도 전략"""
    FIXED = "fixed"              # 고정 간격
    EXPONENTIAL = "exponential"  # 지수 백오프
    LINEAR = "linear"            # 선형 증가
    RANDOM = "random"            # 랜덤 지터


@dataclass
class CircuitBreakerConfig:
    """서킷 브레이커 설정"""
    failure_threshold: int = 5          # 실패 임계값
    success_threshold: int = 3          # 성공 임계값 (반개방 상태에서)
    timeout_seconds: int = 60           # 차단 시간
    window_size: int = 100              # 슬라이딩 윈도우 크기
    min_calls: int = 10                 # 최소 호출 수
    failure_rate_threshold: float = 0.5  # 실패율 임계값 (50%)
    slow_call_threshold: float = 5.0    # 느린 호출 임계값 (초)
    slow_call_rate_threshold: float = 0.5  # 느린 호출 비율 임계값


@dataclass
class RetryConfig:
    """재시도 설정"""
    max_attempts: int = 3
    base_delay: float = 1.0
    max_delay: float = 60.0
    strategy: RetryStrategy = RetryStrategy.EXPONENTIAL
    jitter: bool = True
    backoff_multiplier: float = 2.0
    retryable_exceptions: List[type] = field(default_factory=lambda: [Exception])


@dataclass
class CallResult:
    """호출 결과"""
    success: bool
    duration: float
    timestamp: datetime
    error: Optional[Exception] = None
    
    @property
    def is_slow(self) -> bool:
        """느린 호출 여부"""
        return self.duration > 5.0  # 5초 이상


class CircuitBreaker:
    """서킷 브레이커"""
    
    def __init__(self, name: str, config: CircuitBreakerConfig):
        self.name = name
        self.config = config
        self.state = CircuitState.CLOSED
        self.failure_count = 0
        self.success_count = 0
        self.last_failure_time: Optional[datetime] = None
        self.call_history: List[CallResult] = []
        self.state_change_time = datetime.now()
        
        # 통계
        self.stats = {
            "total_calls": 0,
            "successful_calls": 0,
            "failed_calls": 0,
            "rejected_calls": 0,
            "state_changes": 0,
            "average_response_time": 0.0
        }
    
    async def call(self, func: Callable, *args, **kwargs) -> Any:
        """함수 호출 (서킷 브레이커 적용)"""
        
        # 상태 확인 및 업데이트
        await self._update_state()
        
        # OPEN 상태에서는 호출 차단
        if self.state == CircuitState.OPEN:
            self.stats["rejected_calls"] += 1
            raise PluginResourceError(
                message=f"Circuit breaker {self.name} is OPEN",
                resource_type="circuit_breaker",
                limit="open_state",
                current="rejected"
            )
        
        # 호출 실행
        start_time = time.time()
        self.stats["total_calls"] += 1
        
        try:
            if asyncio.iscoroutinefunction(func):
                result = await func(*args, **kwargs)
            else:
                result = func(*args, **kwargs)
            
            # 성공 기록
            duration = time.time() - start_time
            call_result = CallResult(
                success=True,
                duration=duration,
                timestamp=datetime.now()
            )
            
            await self._record_success(call_result)
            return result
            
        except Exception as e:
            # 실패 기록
            duration = time.time() - start_time
            call_result = CallResult(
                success=False,
                duration=duration,
                timestamp=datetime.now(),
                error=e
            )
            
            await self._record_failure(call_result)
            raise
    
    async def _update_state(self) -> None:
        """상태 업데이트"""
        now = datetime.now()
        
        if self.state == CircuitState.OPEN:
            # 타임아웃 확인
            if (now - self.state_change_time).total_seconds() >= self.config.timeout_seconds:
                await self._transition_to_half_open()
        
        elif self.state == CircuitState.HALF_OPEN:
            # 성공 임계값 확인
            if self.success_count >= self.config.success_threshold:
                await self._transition_to_closed()
    
    async def _record_success(self, call_result: CallResult) -> None:
        """성공 기록"""
        self.call_history.append(call_result)
        self._trim_history()
        
        self.stats["successful_calls"] += 1
        self._update_average_response_time()
        
        if self.state == CircuitState.HALF_OPEN:
            self.success_count += 1
        elif self.state == CircuitState.CLOSED:
            # 실패 카운트 리셋
            self.failure_count = 0
    
    async def _record_failure(self, call_result: CallResult) -> None:
        """실패 기록"""
        self.call_history.append(call_result)
        self._trim_history()
        
        self.stats["failed_calls"] += 1
        self._update_average_response_time()
        
        self.failure_count += 1
        self.last_failure_time = datetime.now()
        
        # 상태 전환 확인
        if self.state == CircuitState.CLOSED:
            if await self._should_open():
                await self._transition_to_open()
        elif self.state == CircuitState.HALF_OPEN:
            await self._transition_to_open()
    
    async def _should_open(self) -> bool:
        """OPEN 상태로 전환해야 하는지 확인"""
        # 최소 호출 수 확인
        if len(self.call_history) < self.config.min_calls:
            return False
        
        # 실패 임계값 확인
        if self.failure_count >= self.config.failure_threshold:
            return True
        
        # 실패율 확인
        recent_calls = self.call_history[-self.config.window_size:]
        if len(recent_calls) >= self.config.min_calls:
            failure_rate = sum(1 for call in recent_calls if not call.success) / len(recent_calls)
            if failure_rate >= self.config.failure_rate_threshold:
                return True
        
        # 느린 호출 비율 확인
        slow_calls = sum(1 for call in recent_calls if call.is_slow)
        if len(recent_calls) > 0:
            slow_call_rate = slow_calls / len(recent_calls)
            if slow_call_rate >= self.config.slow_call_rate_threshold:
                return True
        
        return False
    
    async def _transition_to_open(self) -> None:
        """OPEN 상태로 전환"""
        self.state = CircuitState.OPEN
        self.state_change_time = datetime.now()
        self.stats["state_changes"] += 1
        
        logger.warning(f"Circuit breaker {self.name} transitioned to OPEN")
    
    async def _transition_to_half_open(self) -> None:
        """HALF_OPEN 상태로 전환"""
        self.state = CircuitState.HALF_OPEN
        self.state_change_time = datetime.now()
        self.success_count = 0
        self.stats["state_changes"] += 1
        
        logger.info(f"Circuit breaker {self.name} transitioned to HALF_OPEN")
    
    async def _transition_to_closed(self) -> None:
        """CLOSED 상태로 전환"""
        self.state = CircuitState.CLOSED
        self.state_change_time = datetime.now()
        self.failure_count = 0
        self.success_count = 0
        self.stats["state_changes"] += 1
        
        logger.info(f"Circuit breaker {self.name} transitioned to CLOSED")
    
    def _trim_history(self) -> None:
        """히스토리 정리"""
        if len(self.call_history) > self.config.window_size:
            self.call_history = self.call_history[-self.config.window_size:]
    
    def _update_average_response_time(self) -> None:
        """평균 응답 시간 업데이트"""
        if self.call_history:
            durations = [call.duration for call in self.call_history[-100:]]  # 최근 100개
            self.stats["average_response_time"] = statistics.mean(durations)
    
    def get_state(self) -> Dict[str, Any]:
        """상태 정보 반환"""
        return {
            "name": self.name,
            "state": self.state.value,
            "failure_count": self.failure_count,
            "success_count": self.success_count,
            "last_failure_time": self.last_failure_time.isoformat() if self.last_failure_time else None,
            "state_change_time": self.state_change_time.isoformat(),
            "stats": self.stats,
            "config": {
                "failure_threshold": self.config.failure_threshold,
                "timeout_seconds": self.config.timeout_seconds,
                "failure_rate_threshold": self.config.failure_rate_threshold
            }
        }


class RetryManager:
    """재시도 관리자"""
    
    def __init__(self, config: RetryConfig):
        self.config = config
    
    async def retry(self, func: Callable, *args, **kwargs) -> Any:
        """재시도 실행"""
        last_exception = None
        
        for attempt in range(self.config.max_attempts):
            try:
                if asyncio.iscoroutinefunction(func):
                    return await func(*args, **kwargs)
                else:
                    return func(*args, **kwargs)
            
            except Exception as e:
                last_exception = e
                
                # 재시도 가능한 예외인지 확인
                if not self._is_retryable(e):
                    raise
                
                # 마지막 시도면 예외 발생
                if attempt == self.config.max_attempts - 1:
                    raise
                
                # 지연 시간 계산
                delay = self._calculate_delay(attempt)
                
                logger.warning(
                    f"Attempt {attempt + 1} failed, retrying in {delay:.2f}s: {str(e)}"
                )
                
                await asyncio.sleep(delay)
        
        # 모든 시도 실패
        raise last_exception
    
    def _is_retryable(self, exception: Exception) -> bool:
        """재시도 가능한 예외인지 확인"""
        return any(isinstance(exception, exc_type) for exc_type in self.config.retryable_exceptions)
    
    def _calculate_delay(self, attempt: int) -> float:
        """지연 시간 계산"""
        if self.config.strategy == RetryStrategy.FIXED:
            delay = self.config.base_delay
        
        elif self.config.strategy == RetryStrategy.EXPONENTIAL:
            delay = self.config.base_delay * (self.config.backoff_multiplier ** attempt)
        
        elif self.config.strategy == RetryStrategy.LINEAR:
            delay = self.config.base_delay * (attempt + 1)
        
        elif self.config.strategy == RetryStrategy.RANDOM:
            delay = random.uniform(self.config.base_delay, self.config.max_delay)
        
        else:
            delay = self.config.base_delay
        
        # 최대 지연 시간 제한
        delay = min(delay, self.config.max_delay)
        
        # 지터 추가
        if self.config.jitter:
            jitter = delay * 0.1 * random.random()
            delay += jitter
        
        return delay


class ResilienceManager:
    """복원력 관리자 (서킷 브레이커 + 재시도)"""
    
    def __init__(self):
        self.circuit_breakers: Dict[str, CircuitBreaker] = {}
        self.retry_managers: Dict[str, RetryManager] = {}
        
        # 기본 설정
        self.default_circuit_config = CircuitBreakerConfig()
        self.default_retry_config = RetryConfig()
    
    def get_circuit_breaker(
        self, 
        name: str, 
        config: Optional[CircuitBreakerConfig] = None
    ) -> CircuitBreaker:
        """서킷 브레이커 가져오기 (없으면 생성)"""
        if name not in self.circuit_breakers:
            config = config or self.default_circuit_config
            self.circuit_breakers[name] = CircuitBreaker(name, config)
        
        return self.circuit_breakers[name]
    
    def get_retry_manager(
        self, 
        name: str, 
        config: Optional[RetryConfig] = None
    ) -> RetryManager:
        """재시도 관리자 가져오기 (없으면 생성)"""
        if name not in self.retry_managers:
            config = config or self.default_retry_config
            self.retry_managers[name] = RetryManager(config)
        
        return self.retry_managers[name]
    
    async def call_with_resilience(
        self,
        func: Callable,
        circuit_breaker_name: str,
        retry_name: Optional[str] = None,
        circuit_config: Optional[CircuitBreakerConfig] = None,
        retry_config: Optional[RetryConfig] = None,
        *args,
        **kwargs
    ) -> Any:
        """복원력 패턴을 적용한 함수 호출"""
        
        circuit_breaker = self.get_circuit_breaker(circuit_breaker_name, circuit_config)
        
        if retry_name:
            retry_manager = self.get_retry_manager(retry_name, retry_config)
            
            # 재시도 + 서킷 브레이커
            return await retry_manager.retry(
                circuit_breaker.call, func, *args, **kwargs
            )
        else:
            # 서킷 브레이커만
            return await circuit_breaker.call(func, *args, **kwargs)
    
    def get_all_states(self) -> Dict[str, Any]:
        """모든 서킷 브레이커 상태"""
        return {
            name: breaker.get_state() 
            for name, breaker in self.circuit_breakers.items()
        }
    
    def reset_circuit_breaker(self, name: str) -> bool:
        """서킷 브레이커 리셋"""
        if name in self.circuit_breakers:
            breaker = self.circuit_breakers[name]
            breaker.state = CircuitState.CLOSED
            breaker.failure_count = 0
            breaker.success_count = 0
            breaker.state_change_time = datetime.now()
            logger.info(f"Reset circuit breaker {name}")
            return True
        return False


# 데코레이터
def with_circuit_breaker(
    name: str,
    config: Optional[CircuitBreakerConfig] = None
):
    """서킷 브레이커 데코레이터"""
    def decorator(func):
        async def wrapper(*args, **kwargs):
            circuit_breaker = resilience_manager.get_circuit_breaker(name, config)
            return await circuit_breaker.call(func, *args, **kwargs)
        return wrapper
    return decorator


def with_retry(
    name: str,
    config: Optional[RetryConfig] = None
):
    """재시도 데코레이터"""
    def decorator(func):
        async def wrapper(*args, **kwargs):
            retry_manager = resilience_manager.get_retry_manager(name, config)
            return await retry_manager.retry(func, *args, **kwargs)
        return wrapper
    return decorator


def with_resilience(
    circuit_breaker_name: str,
    retry_name: Optional[str] = None,
    circuit_config: Optional[CircuitBreakerConfig] = None,
    retry_config: Optional[RetryConfig] = None
):
    """복원력 패턴 데코레이터"""
    def decorator(func):
        async def wrapper(*args, **kwargs):
            return await resilience_manager.call_with_resilience(
                func,
                circuit_breaker_name,
                retry_name,
                circuit_config,
                retry_config,
                *args,
                **kwargs
            )
        return wrapper
    return decorator


# 전역 인스턴스
resilience_manager = ResilienceManager()