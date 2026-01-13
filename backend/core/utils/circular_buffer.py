"""
순환 버퍼 구현 - 메모리 사용량 제한
"""
from typing import Generic, TypeVar, List, Optional, Iterator
from collections import deque
from threading import Lock
import time

T = TypeVar('T')

class CircularBuffer(Generic[T]):
    """
    고정 크기 순환 버퍼
    메모리 사용량을 제한하면서 최신 데이터를 유지
    """
    
    def __init__(self, max_size: int = 1000):
        self.max_size = max_size
        self.buffer: deque = deque(maxlen=max_size)
        self.lock = Lock()
        self._total_added = 0
    
    def add(self, item: T) -> None:
        """아이템 추가"""
        with self.lock:
            self.buffer.append(item)
            self._total_added += 1
    
    def get_latest(self, count: int = 10) -> List[T]:
        """최신 N개 아이템 반환"""
        with self.lock:
            return list(self.buffer)[-count:]
    
    def get_all(self) -> List[T]:
        """모든 아이템 반환"""
        with self.lock:
            return list(self.buffer)
    
    def clear(self) -> None:
        """버퍼 비우기"""
        with self.lock:
            self.buffer.clear()
    
    def size(self) -> int:
        """현재 크기"""
        return len(self.buffer)
    
    def is_full(self) -> bool:
        """버퍼가 가득 찼는지 확인"""
        return len(self.buffer) >= self.max_size
    
    def total_added(self) -> int:
        """총 추가된 아이템 수"""
        return self._total_added
    
    def __iter__(self) -> Iterator[T]:
        with self.lock:
            return iter(list(self.buffer))
    
    def __len__(self) -> int:
        return len(self.buffer)

class TimedCircularBuffer(CircularBuffer[T]):
    """
    시간 기반 순환 버퍼
    일정 시간이 지난 아이템은 자동으로 제거
    """
    
    def __init__(self, max_size: int = 1000, max_age_seconds: int = 3600):
        super().__init__(max_size)
        self.max_age_seconds = max_age_seconds
    
    def add(self, item: T) -> None:
        """타임스탬프와 함께 아이템 추가"""
        timestamped_item = {
            'data': item,
            'timestamp': time.time()
        }
        super().add(timestamped_item)
        self._cleanup_old_items()
    
    def get_latest(self, count: int = 10) -> List[T]:
        """최신 N개 아이템 반환 (데이터만)"""
        self._cleanup_old_items()
        with self.lock:
            items = list(self.buffer)[-count:]
            return [item['data'] for item in items]
    
    def get_all(self) -> List[T]:
        """모든 유효한 아이템 반환 (데이터만)"""
        self._cleanup_old_items()
        with self.lock:
            return [item['data'] for item in self.buffer]
    
    def _cleanup_old_items(self) -> None:
        """오래된 아이템 제거"""
        current_time = time.time()
        cutoff_time = current_time - self.max_age_seconds
        
        with self.lock:
            # 오래된 아이템들을 앞에서부터 제거
            while self.buffer and self.buffer[0]['timestamp'] < cutoff_time:
                self.buffer.popleft()

class ExecutionHistoryBuffer:
    """
    Agent 실행 이력 관리용 특화 버퍼
    """
    
    def __init__(self, max_size: int = 1000, max_age_hours: int = 24):
        self.buffer = TimedCircularBuffer(max_size, max_age_hours * 3600)
        self.success_count = 0
        self.error_count = 0
    
    def add_execution(self, execution_data: dict) -> None:
        """실행 이력 추가"""
        self.buffer.add(execution_data)
        
        # 성공/실패 카운트 업데이트
        if execution_data.get('success', False):
            self.success_count += 1
        else:
            self.error_count += 1
    
    def get_success_rate(self) -> float:
        """성공률 계산"""
        total = self.success_count + self.error_count
        if total == 0:
            return 0.0
        return (self.success_count / total) * 100
    
    def get_recent_executions(self, count: int = 10) -> List[dict]:
        """최근 실행 이력 반환"""
        return self.buffer.get_latest(count)
    
    def get_statistics(self) -> dict:
        """통계 정보 반환"""
        executions = self.buffer.get_all()
        
        if not executions:
            return {
                'total_executions': 0,
                'success_rate': 0.0,
                'average_duration': 0.0,
                'error_rate': 0.0
            }
        
        total_duration = sum(
            exec_data.get('duration', 0) 
            for exec_data in executions
        )
        
        return {
            'total_executions': len(executions),
            'success_rate': self.get_success_rate(),
            'average_duration': total_duration / len(executions) if executions else 0.0,
            'error_rate': (self.error_count / (self.success_count + self.error_count)) * 100 if (self.success_count + self.error_count) > 0 else 0.0
        }