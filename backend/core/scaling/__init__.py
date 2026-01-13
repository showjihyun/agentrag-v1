"""
Core Scaling Module

자동 스케일링 및 리소스 관리 관련 핵심 컴포넌트들
"""

from .auto_scaling_manager import AutoScalingManager, ScalingPolicy

__all__ = [
    'AutoScalingManager',
    'ScalingPolicy'
]