"""
Core Event Bus Module

이벤트 기반 아키텍처를 위한 핵심 컴포넌트들
"""

# Import EventBus from the main module to make it available at package level
import sys
import os

# Add the parent directory to sys.path to import the main event_bus module
parent_dir = os.path.dirname(__file__)
sys.path.insert(0, parent_dir)

try:
    from event_bus import EventBus
except ImportError:
    # Fallback to absolute import
    import importlib.util
    event_bus_path = os.path.join(parent_dir, '..', 'event_bus.py')
    spec = importlib.util.spec_from_file_location("event_bus_module", event_bus_path)
    event_bus_module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(event_bus_module)
    EventBus = event_bus_module.EventBus

from .validated_event_bus import ValidatedEventBus, EventType
from .event_schema import EventSchema

__all__ = [
    'EventBus',
    'ValidatedEventBus',
    'EventType',
    'EventSchema'
]