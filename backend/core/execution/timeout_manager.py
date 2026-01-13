"""
Timeout Manager
실행 타임아웃 및 강제 종료 관리
"""
import asyncio
import signal
import threading
import time
from typing import Dict, Any, Optional, Callable, Set
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from enum import Enum
import logging
import psutil
import os

from backend.core.error_handling.plugin_errors import (
    PluginTimeoutError,
    PluginResourceError,
    PluginErrorCode
)

logger = logging.getLogger(__name__)


class TimeoutType(Enum):
    """타임아웃 타입"""
    EXECUTION = "execution"
    NETWORK = "network"
    DATABASE = "database"
    FILE_IO = "file_io"
    CUSTOM = "custom"


class ExecutionStatus(Enum):
    """실행 상태"""
    RUNNING = "running"
    COMPLETED = "completed"
    TIMEOUT = "timeout"
    CANCELLED = "cancelled"
    FAILED = "failed"


@dataclass
class ExecutionContext:
    """실행 컨텍스트"""
    execution_id: str
    timeout_seconds: int
    timeout_type: TimeoutType
    start_time: datetime
    process_id: Optional[int] = None
    thread_id: Optional[int] = None
    task: Optional[asyncio.Task] = None
    callback: Optional[Callable] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    # 리소스 제한
    max_memory_mb: Optional[int] = None
    max_cpu_percent: Optional[float] = None
    
    # 상태
    status: ExecutionStatus = ExecutionStatus.RUNNING
    end_time: Optional[datetime] = None
    error: Optional[str] = None


class ResourceMonitor:
    """리소스 모니터링"""
    
    def __init__(self, check_interval: float = 1.0):
        self.check_interval = check_interval
        self.monitoring_tasks: Dict[str, asyncio.Task] = {}
        self.resource_violations: Dict[str, List[str]] = {}
    
    async def start_monitoring(self, context: ExecutionContext) -> None:
        """리소스 모니터링 시작"""
        if not (context.max_memory_mb or context.max_cpu_percent):
            return
        
        task = asyncio.create_task(self._monitor_resources(context))
        self.monitoring_tasks[context.execution_id] = task
    
    async def stop_monitoring(self, execution_id: str) -> None:
        """리소스 모니터링 중지"""
        if execution_id in self.monitoring_tasks:
            task = self.monitoring_tasks[execution_id]
            task.cancel()
            try:
                await task
            except asyncio.CancelledError:
                pass
            del self.monitoring_tasks[execution_id]
    
    async def _monitor_resources(self, context: ExecutionContext) -> None:
        """리소스 모니터링 루프"""
        violations = []
        
        try:
            while context.status == ExecutionStatus.RUNNING:
                try:
                    # 프로세스 정보 가져오기
                    if context.process_id:
                        process = psutil.Process(context.process_id)
                    else:
                        process = psutil.Process(os.getpid())
                    
                    # 메모리 사용량 확인
                    if context.max_memory_mb:
                        memory_mb = process.memory_info().rss / 1024 / 1024
                        if memory_mb > context.max_memory_mb:
                            violation = f"Memory usage {memory_mb:.1f}MB exceeds limit {context.max_memory_mb}MB"
                            violations.append(violation)
                            logger.warning(f"Resource violation for {context.execution_id}: {violation}")
                    
                    # CPU 사용률 확인
                    if context.max_cpu_percent:
                        cpu_percent = process.cpu_percent(interval=0.1)
                        if cpu_percent > context.max_cpu_percent:
                            violation = f"CPU usage {cpu_percent:.1f}% exceeds limit {context.max_cpu_percent}%"
                            violations.append(violation)
                            logger.warning(f"Resource violation for {context.execution_id}: {violation}")
                    
                    # 위반이 3회 이상 발생하면 강제 종료
                    if len(violations) >= 3:
                        context.status = ExecutionStatus.FAILED
                        context.error = f"Resource limit violations: {violations[-3:]}"
                        
                        # 강제 종료
                        if context.task:
                            context.task.cancel()
                        elif context.process_id:
                            try:
                                process.terminate()
                                # 5초 후에도 종료되지 않으면 강제 kill
                                await asyncio.sleep(5)
                                if process.is_running():
                                    process.kill()
                            except psutil.NoSuchProcess:
                                pass
                        
                        break
                    
                    await asyncio.sleep(self.check_interval)
                    
                except psutil.NoSuchProcess:
                    # 프로세스가 이미 종료됨
                    break
                except Exception as e:
                    logger.error(f"Error monitoring resources for {context.execution_id}: {e}")
                    break
        
        except asyncio.CancelledError:
            pass
        finally:
            self.resource_violations[context.execution_id] = violations


class TimeoutManager:
    """타임아웃 관리자"""
    
    def __init__(self):
        self.active_executions: Dict[str, ExecutionContext] = {}
        self.timeout_tasks: Dict[str, asyncio.Task] = {}
        self.resource_monitor = ResourceMonitor()
        
        # 기본 타임아웃 설정
        self.default_timeouts = {
            TimeoutType.EXECUTION: 300,  # 5분
            TimeoutType.NETWORK: 30,     # 30초
            TimeoutType.DATABASE: 60,    # 1분
            TimeoutType.FILE_IO: 120,    # 2분
            TimeoutType.CUSTOM: 300      # 5분
        }
        
        # 통계
        self.stats = {
            "total_executions": 0,
            "completed": 0,
            "timeout": 0,
            "cancelled": 0,
            "failed": 0
        }
    
    async def start_execution(
        self,
        execution_id: str,
        timeout_seconds: Optional[int] = None,
        timeout_type: TimeoutType = TimeoutType.EXECUTION,
        max_memory_mb: Optional[int] = None,
        max_cpu_percent: Optional[float] = None,
        callback: Optional[Callable] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> ExecutionContext:
        """실행 시작 및 타임아웃 설정"""
        
        if execution_id in self.active_executions:
            raise ValueError(f"Execution {execution_id} is already running")
        
        # 타임아웃 설정
        if timeout_seconds is None:
            timeout_seconds = self.default_timeouts[timeout_type]
        
        # 실행 컨텍스트 생성
        context = ExecutionContext(
            execution_id=execution_id,
            timeout_seconds=timeout_seconds,
            timeout_type=timeout_type,
            start_time=datetime.now(),
            process_id=os.getpid(),
            thread_id=threading.get_ident(),
            callback=callback,
            metadata=metadata or {},
            max_memory_mb=max_memory_mb,
            max_cpu_percent=max_cpu_percent
        )
        
        self.active_executions[execution_id] = context
        
        # 타임아웃 태스크 시작
        timeout_task = asyncio.create_task(self._timeout_handler(context))
        self.timeout_tasks[execution_id] = timeout_task
        
        # 리소스 모니터링 시작
        await self.resource_monitor.start_monitoring(context)
        
        self.stats["total_executions"] += 1
        
        logger.info(f"Started execution {execution_id} with {timeout_seconds}s timeout")
        
        return context
    
    async def complete_execution(
        self,
        execution_id: str,
        success: bool = True,
        error: Optional[str] = None
    ) -> None:
        """실행 완료"""
        
        if execution_id not in self.active_executions:
            logger.warning(f"Execution {execution_id} not found")
            return
        
        context = self.active_executions[execution_id]
        context.end_time = datetime.now()
        
        if success:
            context.status = ExecutionStatus.COMPLETED
            self.stats["completed"] += 1
        else:
            context.status = ExecutionStatus.FAILED
            context.error = error
            self.stats["failed"] += 1
        
        # 정리
        await self._cleanup_execution(execution_id)
        
        # 콜백 호출
        if context.callback:
            try:
                await context.callback(context)
            except Exception as e:
                logger.error(f"Error in completion callback for {execution_id}: {e}")
        
        logger.info(f"Completed execution {execution_id} with status {context.status.value}")
    
    async def cancel_execution(self, execution_id: str, reason: str = "User cancelled") -> bool:
        """실행 취소"""
        
        if execution_id not in self.active_executions:
            return False
        
        context = self.active_executions[execution_id]
        context.status = ExecutionStatus.CANCELLED
        context.error = reason
        context.end_time = datetime.now()
        
        # 강제 종료
        await self._force_terminate(context)
        
        # 정리
        await self._cleanup_execution(execution_id)
        
        self.stats["cancelled"] += 1
        
        logger.info(f"Cancelled execution {execution_id}: {reason}")
        
        return True
    
    async def _timeout_handler(self, context: ExecutionContext) -> None:
        """타임아웃 핸들러"""
        try:
            await asyncio.sleep(context.timeout_seconds)
            
            # 아직 실행 중이면 타임아웃 처리
            if context.status == ExecutionStatus.RUNNING:
                context.status = ExecutionStatus.TIMEOUT
                context.end_time = datetime.now()
                context.error = f"Execution timed out after {context.timeout_seconds} seconds"
                
                logger.warning(f"Execution {context.execution_id} timed out")
                
                # 강제 종료
                await self._force_terminate(context)
                
                # 콜백 호출
                if context.callback:
                    try:
                        await context.callback(context)
                    except Exception as e:
                        logger.error(f"Error in timeout callback for {context.execution_id}: {e}")
                
                self.stats["timeout"] += 1
        
        except asyncio.CancelledError:
            # 정상적으로 완료되어 타임아웃 태스크가 취소됨
            pass
    
    async def _force_terminate(self, context: ExecutionContext) -> None:
        """강제 종료"""
        try:
            # asyncio 태스크 취소
            if context.task and not context.task.done():
                context.task.cancel()
                try:
                    await context.task
                except asyncio.CancelledError:
                    pass
            
            # 프로세스 종료 (별도 프로세스인 경우)
            if context.process_id and context.process_id != os.getpid():
                try:
                    process = psutil.Process(context.process_id)
                    
                    # SIGTERM으로 정상 종료 시도
                    process.terminate()
                    
                    # 5초 대기
                    try:
                        process.wait(timeout=5)
                    except psutil.TimeoutExpired:
                        # 강제 종료
                        process.kill()
                        logger.warning(f"Force killed process {context.process_id}")
                
                except psutil.NoSuchProcess:
                    # 프로세스가 이미 종료됨
                    pass
                except Exception as e:
                    logger.error(f"Error terminating process {context.process_id}: {e}")
        
        except Exception as e:
            logger.error(f"Error in force terminate for {context.execution_id}: {e}")
    
    async def _cleanup_execution(self, execution_id: str) -> None:
        """실행 정리"""
        try:
            # 타임아웃 태스크 취소
            if execution_id in self.timeout_tasks:
                task = self.timeout_tasks[execution_id]
                if not task.done():
                    task.cancel()
                    try:
                        await task
                    except asyncio.CancelledError:
                        pass
                del self.timeout_tasks[execution_id]
            
            # 리소스 모니터링 중지
            await self.resource_monitor.stop_monitoring(execution_id)
            
            # 실행 컨텍스트 제거
            if execution_id in self.active_executions:
                del self.active_executions[execution_id]
        
        except Exception as e:
            logger.error(f"Error cleaning up execution {execution_id}: {e}")
    
    def get_execution_status(self, execution_id: str) -> Optional[ExecutionContext]:
        """실행 상태 조회"""
        return self.active_executions.get(execution_id)
    
    def get_active_executions(self) -> Dict[str, ExecutionContext]:
        """활성 실행 목록"""
        return self.active_executions.copy()
    
    def get_statistics(self) -> Dict[str, Any]:
        """통계 정보"""
        return {
            **self.stats,
            "active_executions": len(self.active_executions),
            "resource_violations": len(self.resource_monitor.resource_violations)
        }
    
    async def cleanup_all(self) -> None:
        """모든 실행 정리"""
        execution_ids = list(self.active_executions.keys())
        
        for execution_id in execution_ids:
            try:
                await self.cancel_execution(execution_id, "System shutdown")
            except Exception as e:
                logger.error(f"Error cancelling execution {execution_id}: {e}")
        
        logger.info(f"Cleaned up {len(execution_ids)} active executions")


# 컨텍스트 매니저
class TimeoutContext:
    """타임아웃 컨텍스트 매니저"""
    
    def __init__(
        self,
        timeout_manager: TimeoutManager,
        execution_id: str,
        timeout_seconds: Optional[int] = None,
        timeout_type: TimeoutType = TimeoutType.EXECUTION,
        max_memory_mb: Optional[int] = None,
        max_cpu_percent: Optional[float] = None
    ):
        self.timeout_manager = timeout_manager
        self.execution_id = execution_id
        self.timeout_seconds = timeout_seconds
        self.timeout_type = timeout_type
        self.max_memory_mb = max_memory_mb
        self.max_cpu_percent = max_cpu_percent
        self.context: Optional[ExecutionContext] = None
    
    async def __aenter__(self) -> ExecutionContext:
        self.context = await self.timeout_manager.start_execution(
            execution_id=self.execution_id,
            timeout_seconds=self.timeout_seconds,
            timeout_type=self.timeout_type,
            max_memory_mb=self.max_memory_mb,
            max_cpu_percent=self.max_cpu_percent
        )
        return self.context
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.context:
            if exc_type is None:
                await self.timeout_manager.complete_execution(self.execution_id, success=True)
            else:
                error_msg = str(exc_val) if exc_val else "Unknown error"
                await self.timeout_manager.complete_execution(
                    self.execution_id, 
                    success=False, 
                    error=error_msg
                )


# 데코레이터
def with_timeout(
    timeout_seconds: Optional[int] = None,
    timeout_type: TimeoutType = TimeoutType.EXECUTION,
    max_memory_mb: Optional[int] = None,
    max_cpu_percent: Optional[float] = None
):
    """타임아웃 데코레이터"""
    def decorator(func):
        async def wrapper(*args, **kwargs):
            execution_id = f"{func.__name__}_{int(time.time())}"
            
            async with TimeoutContext(
                timeout_manager,
                execution_id,
                timeout_seconds,
                timeout_type,
                max_memory_mb,
                max_cpu_percent
            ) as context:
                # 태스크 등록
                task = asyncio.current_task()
                if task:
                    context.task = task
                
                return await func(*args, **kwargs)
        
        return wrapper
    return decorator


# 전역 인스턴스
timeout_manager = TimeoutManager()