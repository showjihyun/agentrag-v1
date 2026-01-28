"""
Enhanced Execution Logging

명확하고 찾기 쉬운 실행 로그를 제공합니다.
Provides clear and easy-to-find execution logs.
"""

import logging
import sys
from typing import Any, Dict, Optional
from datetime import datetime
from enum import Enum
import json


class ExecutionPhase(Enum):
    """실행 단계 / Execution phases"""
    WORKFLOW_START = "🚀 WORKFLOW_START"
    WORKFLOW_END = "✅ WORKFLOW_END"
    NODE_START = "▶️  NODE_START"
    NODE_END = "⏹️  NODE_END"
    AGENT_START = "🤖 AGENT_START"
    AGENT_END = "🤖 AGENT_END"
    ERROR = "❌ ERROR"
    WARNING = "⚠️  WARNING"
    INFO = "ℹ️  INFO"
    DEBUG = "🔍 DEBUG"


class ExecutionLogger:
    """
    실행 로그를 명확하게 출력하는 로거
    Logger that outputs execution logs clearly
    """
    
    def __init__(self, name: str, enable_colors: bool = True):
        self.logger = logging.getLogger(name)
        self.enable_colors = enable_colors
        self._setup_logger()
    
    def _setup_logger(self):
        """로거 설정 / Setup logger"""
        if not self.logger.handlers:
            handler = logging.StreamHandler(sys.stdout)
            handler.setFormatter(ExecutionLogFormatter(enable_colors=self.enable_colors))
            self.logger.addHandler(handler)
            self.logger.setLevel(logging.DEBUG)
    
    def workflow_start(
        self,
        workflow_id: str,
        workflow_name: str,
        orchestration_type: str,
        **kwargs
    ):
        """워크플로우 시작 로그 / Log workflow start"""
        self.logger.info(
            "",
            extra={
                "phase": ExecutionPhase.WORKFLOW_START,
                "workflow_id": workflow_id,
                "workflow_name": workflow_name,
                "orchestration_type": orchestration_type,
                "timestamp": datetime.utcnow().isoformat(),
                **kwargs
            }
        )
    
    def workflow_end(
        self,
        workflow_id: str,
        workflow_name: str,
        success: bool,
        duration_ms: float,
        **kwargs
    ):
        """워크플로우 종료 로그 / Log workflow end"""
        self.logger.info(
            "",
            extra={
                "phase": ExecutionPhase.WORKFLOW_END,
                "workflow_id": workflow_id,
                "workflow_name": workflow_name,
                "success": success,
                "duration_ms": duration_ms,
                "timestamp": datetime.utcnow().isoformat(),
                **kwargs
            }
        )
    
    def node_start(
        self,
        node_id: str,
        node_name: str,
        node_type: str,
        **kwargs
    ):
        """노드 시작 로그 / Log node start"""
        self.logger.info(
            "",
            extra={
                "phase": ExecutionPhase.NODE_START,
                "node_id": node_id,
                "node_name": node_name,
                "node_type": node_type,
                "timestamp": datetime.utcnow().isoformat(),
                **kwargs
            }
        )
    
    def node_end(
        self,
        node_id: str,
        node_name: str,
        node_type: str,
        success: bool,
        duration_ms: float,
        **kwargs
    ):
        """노드 종료 로그 / Log node end"""
        self.logger.info(
            "",
            extra={
                "phase": ExecutionPhase.NODE_END,
                "node_id": node_id,
                "node_name": node_name,
                "node_type": node_type,
                "success": success,
                "duration_ms": duration_ms,
                "timestamp": datetime.utcnow().isoformat(),
                **kwargs
            }
        )
    
    def agent_start(
        self,
        agent_id: str,
        agent_name: str,
        agent_type: str,
        **kwargs
    ):
        """에이전트 시작 로그 / Log agent start"""
        self.logger.info(
            "",
            extra={
                "phase": ExecutionPhase.AGENT_START,
                "agent_id": agent_id,
                "agent_name": agent_name,
                "agent_type": agent_type,
                "timestamp": datetime.utcnow().isoformat(),
                **kwargs
            }
        )
    
    def agent_end(
        self,
        agent_id: str,
        agent_name: str,
        agent_type: str,
        success: bool,
        duration_ms: float,
        **kwargs
    ):
        """에이전트 종료 로그 / Log agent end"""
        self.logger.info(
            "",
            extra={
                "phase": ExecutionPhase.AGENT_END,
                "agent_id": agent_id,
                "agent_name": agent_name,
                "agent_type": agent_type,
                "success": success,
                "duration_ms": duration_ms,
                "timestamp": datetime.utcnow().isoformat(),
                **kwargs
            }
        )
    
    def error(self, message: str, **kwargs):
        """에러 로그 / Log error"""
        self.logger.error(
            message,
            extra={
                "phase": ExecutionPhase.ERROR,
                "timestamp": datetime.utcnow().isoformat(),
                **kwargs
            }
        )
    
    def warning(self, message: str, **kwargs):
        """경고 로그 / Log warning"""
        self.logger.warning(
            message,
            extra={
                "phase": ExecutionPhase.WARNING,
                "timestamp": datetime.utcnow().isoformat(),
                **kwargs
            }
        )
    
    def info(self, message: str, **kwargs):
        """정보 로그 / Log info"""
        self.logger.info(
            message,
            extra={
                "phase": ExecutionPhase.INFO,
                "timestamp": datetime.utcnow().isoformat(),
                **kwargs
            }
        )
    
    def debug(self, message: str, **kwargs):
        """디버그 로그 / Log debug"""
        self.logger.debug(
            message,
            extra={
                "phase": ExecutionPhase.DEBUG,
                "timestamp": datetime.utcnow().isoformat(),
                **kwargs
            }
        )


class ExecutionLogFormatter(logging.Formatter):
    """
    실행 로그를 명확하게 포맷팅
    Format execution logs clearly
    """
    
    # ANSI 색상 코드 / ANSI color codes
    COLORS = {
        "RESET": "\033[0m",
        "BOLD": "\033[1m",
        "GREEN": "\033[92m",
        "YELLOW": "\033[93m",
        "RED": "\033[91m",
        "BLUE": "\033[94m",
        "CYAN": "\033[96m",
        "MAGENTA": "\033[95m",
    }
    
    def __init__(self, enable_colors: bool = True):
        super().__init__()
        self.enable_colors = enable_colors
    
    def format(self, record: logging.LogRecord) -> str:
        """로그 레코드 포맷팅 / Format log record"""
        
        # 기본 정보 추출 / Extract basic info
        phase = getattr(record, "phase", None)
        timestamp = getattr(record, "timestamp", datetime.utcnow().isoformat())
        
        if not phase:
            # 일반 로그 / Regular log
            return f"[{timestamp}] {record.levelname}: {record.getMessage()}"
        
        # 실행 로그 포맷팅 / Format execution log
        phase_value = phase.value if isinstance(phase, ExecutionPhase) else str(phase)
        
        # 구분선 / Separator
        separator = "=" * 80
        
        # 워크플로우 시작 / Workflow start
        if phase == ExecutionPhase.WORKFLOW_START:
            workflow_id = getattr(record, "workflow_id", "N/A")
            workflow_name = getattr(record, "workflow_name", "N/A")
            orchestration_type = getattr(record, "orchestration_type", "N/A")
            
            lines = [
                "",
                separator,
                f"{phase_value} 워크플로우 실행 시작 / Workflow Execution Started",
                separator,
                f"  📋 워크플로우 ID / Workflow ID: {workflow_id}",
                f"  📝 워크플로우 이름 / Name: {workflow_name}",
                f"  🔄 오케스트레이션 타입 / Orchestration: {orchestration_type}",
                f"  🕐 시작 시간 / Start Time: {timestamp}",
                separator,
                ""
            ]
            
            return self._colorize("\n".join(lines), "CYAN")
        
        # 워크플로우 종료 / Workflow end
        elif phase == ExecutionPhase.WORKFLOW_END:
            workflow_id = getattr(record, "workflow_id", "N/A")
            workflow_name = getattr(record, "workflow_name", "N/A")
            success = getattr(record, "success", False)
            duration_ms = getattr(record, "duration_ms", 0)
            
            status = "✅ 성공 / SUCCESS" if success else "❌ 실패 / FAILED"
            color = "GREEN" if success else "RED"
            
            lines = [
                "",
                separator,
                f"{phase_value} 워크플로우 실행 완료 / Workflow Execution Completed",
                separator,
                f"  📋 워크플로우 ID / Workflow ID: {workflow_id}",
                f"  📝 워크플로우 이름 / Name: {workflow_name}",
                f"  {status}",
                f"  ⏱️  실행 시간 / Duration: {duration_ms:.2f}ms",
                f"  🕐 종료 시간 / End Time: {timestamp}",
                separator,
                ""
            ]
            
            return self._colorize("\n".join(lines), color)
        
        # 노드 시작 / Node start
        elif phase == ExecutionPhase.NODE_START:
            node_id = getattr(record, "node_id", "N/A")
            node_name = getattr(record, "node_name", "N/A")
            node_type = getattr(record, "node_type", "N/A")
            
            lines = [
                "",
                f"{phase_value} 노드 실행 시작 / Node Execution Started",
                f"  🔹 노드 ID / Node ID: {node_id}",
                f"  🔹 노드 이름 / Name: {node_name}",
                f"  🔹 노드 타입 / Type: {node_type}",
                f"  🕐 시작 시간 / Start Time: {timestamp}",
                ""
            ]
            
            return self._colorize("\n".join(lines), "BLUE")
        
        # 노드 종료 / Node end
        elif phase == ExecutionPhase.NODE_END:
            node_id = getattr(record, "node_id", "N/A")
            node_name = getattr(record, "node_name", "N/A")
            node_type = getattr(record, "node_type", "N/A")
            success = getattr(record, "success", False)
            duration_ms = getattr(record, "duration_ms", 0)
            
            status = "✅ 성공 / SUCCESS" if success else "❌ 실패 / FAILED"
            color = "GREEN" if success else "RED"
            
            lines = [
                "",
                f"{phase_value} 노드 실행 완료 / Node Execution Completed",
                f"  🔹 노드 ID / Node ID: {node_id}",
                f"  🔹 노드 이름 / Name: {node_name}",
                f"  🔹 노드 타입 / Type: {node_type}",
                f"  {status}",
                f"  ⏱️  실행 시간 / Duration: {duration_ms:.2f}ms",
                f"  🕐 종료 시간 / End Time: {timestamp}",
                ""
            ]
            
            return self._colorize("\n".join(lines), color)
        
        # 에이전트 시작 / Agent start
        elif phase == ExecutionPhase.AGENT_START:
            agent_id = getattr(record, "agent_id", "N/A")
            agent_name = getattr(record, "agent_name", "N/A")
            agent_type = getattr(record, "agent_type", "N/A")
            
            lines = [
                "",
                f"{phase_value} 에이전트 실행 시작 / Agent Execution Started",
                f"  🤖 에이전트 ID / Agent ID: {agent_id}",
                f"  🤖 에이전트 이름 / Name: {agent_name}",
                f"  🤖 에이전트 타입 / Type: {agent_type}",
                f"  🕐 시작 시간 / Start Time: {timestamp}",
                ""
            ]
            
            return self._colorize("\n".join(lines), "MAGENTA")
        
        # 에이전트 종료 / Agent end
        elif phase == ExecutionPhase.AGENT_END:
            agent_id = getattr(record, "agent_id", "N/A")
            agent_name = getattr(record, "agent_name", "N/A")
            agent_type = getattr(record, "agent_type", "N/A")
            success = getattr(record, "success", False)
            duration_ms = getattr(record, "duration_ms", 0)
            
            status = "✅ 성공 / SUCCESS" if success else "❌ 실패 / FAILED"
            color = "GREEN" if success else "RED"
            
            lines = [
                "",
                f"{phase_value} 에이전트 실행 완료 / Agent Execution Completed",
                f"  🤖 에이전트 ID / Agent ID: {agent_id}",
                f"  🤖 에이전트 이름 / Name: {agent_name}",
                f"  🤖 에이전트 타입 / Type: {agent_type}",
                f"  {status}",
                f"  ⏱️  실행 시간 / Duration: {duration_ms:.2f}ms",
                f"  🕐 종료 시간 / End Time: {timestamp}",
                ""
            ]
            
            return self._colorize("\n".join(lines), color)
        
        # 에러 / Error
        elif phase == ExecutionPhase.ERROR:
            message = record.getMessage()
            error_type = getattr(record, "error_type", "")
            
            lines = [
                "",
                f"{phase_value} 에러 발생 / Error Occurred",
                f"  ❌ 메시지 / Message: {message}",
            ]
            
            if error_type:
                lines.append(f"  ❌ 타입 / Type: {error_type}")
            
            lines.append(f"  🕐 시간 / Time: {timestamp}")
            lines.append("")
            
            return self._colorize("\n".join(lines), "RED")
        
        # 경고 / Warning
        elif phase == ExecutionPhase.WARNING:
            message = record.getMessage()
            
            lines = [
                "",
                f"{phase_value} 경고 / Warning",
                f"  ⚠️  메시지 / Message: {message}",
                f"  🕐 시간 / Time: {timestamp}",
                ""
            ]
            
            return self._colorize("\n".join(lines), "YELLOW")
        
        # 정보 / Info
        elif phase == ExecutionPhase.INFO:
            message = record.getMessage()
            return f"[{timestamp}] {phase_value} {message}"
        
        # 디버그 / Debug
        elif phase == ExecutionPhase.DEBUG:
            message = record.getMessage()
            return f"[{timestamp}] {phase_value} {message}"
        
        # 기본 / Default
        return f"[{timestamp}] {phase_value} {record.getMessage()}"
    
    def _colorize(self, text: str, color: str) -> str:
        """텍스트에 색상 적용 / Apply color to text"""
        if not self.enable_colors:
            return text
        
        color_code = self.COLORS.get(color, "")
        reset_code = self.COLORS["RESET"]
        bold_code = self.COLORS["BOLD"]
        
        return f"{bold_code}{color_code}{text}{reset_code}"


# 전역 로거 인스턴스 / Global logger instances
_execution_loggers: Dict[str, ExecutionLogger] = {}


def get_execution_logger(name: str, enable_colors: bool = True) -> ExecutionLogger:
    """
    실행 로거 가져오기 / Get execution logger
    
    Args:
        name: 로거 이름 / Logger name
        enable_colors: 색상 활성화 / Enable colors
        
    Returns:
        ExecutionLogger 인스턴스 / ExecutionLogger instance
    """
    if name not in _execution_loggers:
        _execution_loggers[name] = ExecutionLogger(name, enable_colors=enable_colors)
    
    return _execution_loggers[name]


# 편의 함수 / Convenience functions

def log_workflow_start(workflow_id: str, workflow_name: str, orchestration_type: str, **kwargs):
    """워크플로우 시작 로그 / Log workflow start"""
    logger = get_execution_logger("workflow")
    logger.workflow_start(workflow_id, workflow_name, orchestration_type, **kwargs)


def log_workflow_end(workflow_id: str, workflow_name: str, success: bool, duration_ms: float, **kwargs):
    """워크플로우 종료 로그 / Log workflow end"""
    logger = get_execution_logger("workflow")
    logger.workflow_end(workflow_id, workflow_name, success, duration_ms, **kwargs)


def log_node_start(node_id: str, node_name: str, node_type: str, **kwargs):
    """노드 시작 로그 / Log node start"""
    logger = get_execution_logger("node")
    logger.node_start(node_id, node_name, node_type, **kwargs)


def log_node_end(node_id: str, node_name: str, node_type: str, success: bool, duration_ms: float, **kwargs):
    """노드 종료 로그 / Log node end"""
    logger = get_execution_logger("node")
    logger.node_end(node_id, node_name, node_type, success, duration_ms, **kwargs)


def log_agent_start(agent_id: str, agent_name: str, agent_type: str, **kwargs):
    """에이전트 시작 로그 / Log agent start"""
    logger = get_execution_logger("agent")
    logger.agent_start(agent_id, agent_name, agent_type, **kwargs)


def log_agent_end(agent_id: str, agent_name: str, agent_type: str, success: bool, duration_ms: float, **kwargs):
    """에이전트 종료 로그 / Log agent end"""
    logger = get_execution_logger("agent")
    logger.agent_end(agent_id, agent_name, agent_type, success, duration_ms, **kwargs)
