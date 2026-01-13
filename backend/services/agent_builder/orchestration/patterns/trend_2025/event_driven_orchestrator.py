"""
Event-Driven Orchestrator - 2025 Trend Pattern

Implements event-driven coordination where agents react to specific events
and triggers, enabling real-time responsive systems.
"""

import asyncio
import logging
from typing import Dict, List, Any, Optional, Callable, Set
from datetime import datetime, timedelta
import json
from dataclasses import dataclass, field
from enum import Enum
import uuid

from ..base_orchestrator import BaseOrchestrator
from ....domain.entities.agent import Agent
from ....domain.entities.workflow import Workflow
from ....domain.value_objects.orchestration_config import OrchestrationConfig
from .....core.event_bus import EventBus

logger = logging.getLogger(__name__)

class EventType(Enum):
    """Event types for orchestration"""
    AGENT_COMPLETED = "agent_completed"
    AGENT_FAILED = "agent_failed"
    THRESHOLD_REACHED = "threshold_reached"
    TIME_ELAPSED = "time_elapsed"
    DATA_AVAILABLE = "data_available"
    USER_INPUT = "user_input"
    EXTERNAL_TRIGGER = "external_trigger"
    CONDITION_MET = "condition_met"
    RESOURCE_AVAILABLE = "resource_available"
    ERROR_OCCURRED = "error_occurred"

class TriggerCondition(Enum):
    """Trigger condition types"""
    IMMEDIATE = "immediate"
    DELAYED = "delayed"
    CONDITIONAL = "conditional"
    PERIODIC = "periodic"
    THRESHOLD_BASED = "threshold_based"

@dataclass
class EventTrigger:
    """Event trigger configuration"""
    id: str
    event_type: EventType
    condition: TriggerCondition
    target_agents: List[str]
    parameters: Dict[str, Any] = field(default_factory=dict)
    delay_seconds: float = 0.0
    max_triggers: Optional[int] = None
    trigger_count: int = 0
    is_active: bool = True
    created_at: datetime = field(default_factory=datetime.now)

@dataclass
class EventInstance:
    """Individual event instance"""
    id: str
    event_type: EventType
    source_agent: Optional[str]
    data: Dict[str, Any]
    timestamp: datetime = field(default_factory=datetime.now)
    processed: bool = False
    processing_results: List[Dict[str, Any]] = field(default_factory=list)

@dataclass
class EventListener:
    """Event listener configuration"""
    id: str
    event_types: Set[EventType]
    agent_id: str
    handler_function: str
    filter_conditions: Dict[str, Any] = field(default_factory=dict)
    priority: int = 1
    is_active: bool = True

class EventDrivenOrchestrator(BaseOrchestrator):
    """
    Event-Driven Orchestrator
    
    Coordinates agents based on events and triggers:
    - Real-time event processing
    - Trigger-based agent activation
    - Event filtering and routing
    - Asynchronous event handling
    """
    
    def __init__(self, config: OrchestrationConfig, event_bus: EventBus):
        super().__init__(config, event_bus)
        self.event_triggers: Dict[str, EventTrigger] = {}
        self.event_listeners: Dict[str, EventListener] = {}
        self.event_history: List[EventInstance] = []
        self.active_events: Dict[str, EventInstance] = {}
        
        # Event processing parameters
        self.max_event_history = config.get_parameter("max_event_history", 1000)
        self.event_timeout = config.get_parameter("event_timeout", 300)  # 5 minutes
        self.max_concurrent_events = config.get_parameter("max_concurrent_events", 50)
        self.event_processing_delay = config.get_parameter("event_processing_delay", 0.1)
        
        # Performance monitoring
        self.event_processing_times: List[float] = []
        self.trigger_success_rates: Dict[str, float] = {}
        
        self._setup_event_handlers()
        self._start_event_processor()
    
    def _setup_event_handlers(self):
        """Setup internal event handlers"""
        self.event_bus.subscribe("agent_execution_completed", self._handle_agent_completed)
        self.event_bus.subscribe("agent_execution_failed", self._handle_agent_failed)
        self.event_bus.subscribe("external_event", self._handle_external_event)
        self.event_bus.subscribe("user_input_received", self._handle_user_input)
    
    def _start_event_processor(self):
        """Start the background event processor"""
        asyncio.create_task(self._event_processing_loop())
    
    async def orchestrate(self, workflow: Workflow, agents: List[Agent], context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Orchestrate agents using event-driven coordination
        
        Args:
            workflow: The workflow to execute
            agents: List of available agents
            context: Execution context
            
        Returns:
            Orchestration results with event metrics
        """
        try:
            logger.info(f"Starting event-driven orchestration for workflow {workflow.id}")
            
            # Initialize event system
            await self._initialize_event_system(agents, context)
            
            # Setup triggers and listeners
            await self._setup_triggers_and_listeners(workflow, agents, context)
            
            # Start initial events
            initial_results = await self._trigger_initial_events(context)
            
            # Monitor and process events
            final_results = await self._monitor_event_execution(workflow, context)
            
            # Collect event metrics
            event_metrics = await self._collect_event_metrics()
            
            return {
                "status": "completed",
                "results": final_results,
                "initial_results": initial_results,
                "event_metrics": event_metrics,
                "execution_time": (datetime.now() - self.start_time).total_seconds()
            }
            
        except Exception as e:
            logger.error(f"Event-driven orchestration failed: {str(e)}")
            return {
                "status": "failed",
                "error": str(e),
                "event_state": self._get_current_event_state()
            }
    
    async def _initialize_event_system(self, agents: List[Agent], context: Dict[str, Any]):
        """Initialize the event-driven system"""
        logger.info(f"Initializing event system with {len(agents)} agents")
        
        # Clear previous state
        self.event_triggers.clear()
        self.event_listeners.clear()
        self.event_history.clear()
        self.active_events.clear()
        
        # Create default triggers for each agent
        for agent in agents:
            # Completion trigger
            completion_trigger = EventTrigger(
                id=f"completion_{agent.id}",
                event_type=EventType.AGENT_COMPLETED,
                condition=TriggerCondition.IMMEDIATE,
                target_agents=[],  # Will be set based on workflow
                parameters={"source_agent": agent.id}
            )
            self.event_triggers[completion_trigger.id] = completion_trigger
            
            # Failure trigger
            failure_trigger = EventTrigger(
                id=f"failure_{agent.id}",
                event_type=EventType.AGENT_FAILED,
                condition=TriggerCondition.IMMEDIATE,
                target_agents=[],  # Will be set based on workflow
                parameters={"source_agent": agent.id}
            )
            self.event_triggers[failure_trigger.id] = failure_trigger
        
        await self.event_bus.publish("event_system_initialized", {
            "agent_count": len(agents),
            "trigger_count": len(self.event_triggers)
        })
    
    async def _setup_triggers_and_listeners(self, workflow: Workflow, agents: List[Agent], context: Dict[str, Any]):
        """Setup workflow-specific triggers and listeners"""
        workflow_config = context.get("workflow_config", {})
        
        # Setup custom triggers from configuration
        custom_triggers = workflow_config.get("event_triggers", [])
        for trigger_config in custom_triggers:
            trigger = EventTrigger(
                id=trigger_config.get("id", str(uuid.uuid4())),
                event_type=EventType(trigger_config["event_type"]),
                condition=TriggerCondition(trigger_config.get("condition", "immediate")),
                target_agents=trigger_config.get("target_agents", []),
                parameters=trigger_config.get("parameters", {}),
                delay_seconds=trigger_config.get("delay_seconds", 0.0),
                max_triggers=trigger_config.get("max_triggers")
            )
            self.event_triggers[trigger.id] = trigger
        
        # Setup event listeners
        custom_listeners = workflow_config.get("event_listeners", [])
        for listener_config in custom_listeners:
            listener = EventListener(
                id=listener_config.get("id", str(uuid.uuid4())),
                event_types=set(EventType(et) for et in listener_config["event_types"]),
                agent_id=listener_config["agent_id"],
                handler_function=listener_config.get("handler_function", "default_handler"),
                filter_conditions=listener_config.get("filter_conditions", {}),
                priority=listener_config.get("priority", 1)
            )
            self.event_listeners[listener.id] = listener
        
        # Setup time-based triggers
        time_triggers = workflow_config.get("time_triggers", [])
        for time_config in time_triggers:
            trigger = EventTrigger(
                id=f"time_{time_config['name']}",
                event_type=EventType.TIME_ELAPSED,
                condition=TriggerCondition.DELAYED,
                target_agents=time_config.get("target_agents", []),
                delay_seconds=time_config["delay_seconds"],
                parameters=time_config.get("parameters", {})
            )
            self.event_triggers[trigger.id] = trigger
            
            # Schedule the time trigger
            asyncio.create_task(self._schedule_time_trigger(trigger))
    
    async def _trigger_initial_events(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Trigger initial events to start the orchestration"""
        initial_events = context.get("initial_events", [])
        results = {}
        
        for event_config in initial_events:
            event = EventInstance(
                id=str(uuid.uuid4()),
                event_type=EventType(event_config["event_type"]),
                source_agent=event_config.get("source_agent"),
                data=event_config.get("data", {})
            )
            
            result = await self._process_event(event)
            results[event.id] = result
        
        # If no initial events, trigger a default start event
        if not initial_events:
            start_event = EventInstance(
                id="orchestration_start",
                event_type=EventType.EXTERNAL_TRIGGER,
                source_agent=None,
                data={"trigger": "orchestration_start"}
            )
            results["orchestration_start"] = await self._process_event(start_event)
        
        return results
    
    async def _monitor_event_execution(self, workflow: Workflow, context: Dict[str, Any]) -> Dict[str, Any]:
        """Monitor and coordinate event-driven execution"""
        max_execution_time = context.get("max_execution_time", 300)  # 5 minutes
        start_time = datetime.now()
        results = {}
        
        while (datetime.now() - start_time).total_seconds() < max_execution_time:
            # Check for completion conditions
            if await self._check_completion_conditions(workflow, context):
                logger.info("Event-driven orchestration completed successfully")
                break
            
            # Process pending events
            await self._process_pending_events()
            
            # Check for timeout events
            await self._check_timeout_events()
            
            # Brief pause to prevent busy waiting
            await asyncio.sleep(self.event_processing_delay)
        
        # Collect final results
        for event in self.event_history:
            if event.processed and event.processing_results:
                results[event.id] = event.processing_results
        
        return results
    
    async def _process_event(self, event: EventInstance) -> Dict[str, Any]:
        """Process a single event"""
        start_time = datetime.now()
        
        try:
            logger.info(f"Processing event {event.id} of type {event.event_type.value}")
            
            # Add to active events
            self.active_events[event.id] = event
            
            # Find matching triggers
            matching_triggers = self._find_matching_triggers(event)
            
            # Execute triggered actions
            results = []
            for trigger in matching_triggers:
                if trigger.is_active and self._should_trigger(trigger, event):
                    result = await self._execute_trigger(trigger, event)
                    results.append(result)
                    trigger.trigger_count += 1
                    
                    # Deactivate if max triggers reached
                    if trigger.max_triggers and trigger.trigger_count >= trigger.max_triggers:
                        trigger.is_active = False
            
            # Update event
            event.processed = True
            event.processing_results = results
            
            # Move to history
            self.event_history.append(event)
            if event.id in self.active_events:
                del self.active_events[event.id]
            
            # Trim history if needed
            if len(self.event_history) > self.max_event_history:
                self.event_history = self.event_history[-self.max_event_history:]
            
            processing_time = (datetime.now() - start_time).total_seconds()
            self.event_processing_times.append(processing_time)
            
            await self.event_bus.publish("event_processed", {
                "event_id": event.id,
                "event_type": event.event_type.value,
                "processing_time": processing_time,
                "results_count": len(results)
            })
            
            return {
                "event_id": event.id,
                "status": "processed",
                "results": results,
                "processing_time": processing_time
            }
            
        except Exception as e:
            logger.error(f"Error processing event {event.id}: {str(e)}")
            event.processed = True
            event.processing_results = [{"status": "failed", "error": str(e)}]
            
            return {
                "event_id": event.id,
                "status": "failed",
                "error": str(e)
            }
    
    def _find_matching_triggers(self, event: EventInstance) -> List[EventTrigger]:
        """Find triggers that match the given event"""
        matching_triggers = []
        
        for trigger in self.event_triggers.values():
            if trigger.event_type == event.event_type:
                # Check additional parameters
                if self._trigger_matches_event(trigger, event):
                    matching_triggers.append(trigger)
        
        return matching_triggers
    
    def _trigger_matches_event(self, trigger: EventTrigger, event: EventInstance) -> bool:
        """Check if trigger parameters match event data"""
        for key, value in trigger.parameters.items():
            if key == "source_agent":
                if event.source_agent != value:
                    return False
            elif key in event.data:
                if event.data[key] != value:
                    return False
            else:
                return False
        
        return True
    
    def _should_trigger(self, trigger: EventTrigger, event: EventInstance) -> bool:
        """Determine if trigger should fire for this event"""
        if not trigger.is_active:
            return False
        
        if trigger.condition == TriggerCondition.IMMEDIATE:
            return True
        elif trigger.condition == TriggerCondition.CONDITIONAL:
            return self._evaluate_trigger_condition(trigger, event)
        elif trigger.condition == TriggerCondition.THRESHOLD_BASED:
            return self._check_threshold_condition(trigger, event)
        
        return False
    
    def _evaluate_trigger_condition(self, trigger: EventTrigger, event: EventInstance) -> bool:
        """Evaluate conditional trigger logic"""
        condition_expr = trigger.parameters.get("condition_expression", "true")
        
        # Simple condition evaluation (can be extended)
        try:
            # Create safe evaluation context
            context = {
                "event_data": event.data,
                "trigger_count": trigger.trigger_count,
                "event_type": event.event_type.value
            }
            
            # Basic condition evaluation (extend as needed)
            if condition_expr == "true":
                return True
            elif "trigger_count" in condition_expr:
                return eval(condition_expr.replace("trigger_count", str(trigger.trigger_count)))
            
            return True
        except Exception as e:
            logger.warning(f"Error evaluating trigger condition: {str(e)}")
            return False
    
    def _check_threshold_condition(self, trigger: EventTrigger, event: EventInstance) -> bool:
        """Check threshold-based trigger condition"""
        threshold_key = trigger.parameters.get("threshold_key", "value")
        threshold_value = trigger.parameters.get("threshold_value", 0)
        comparison = trigger.parameters.get("comparison", ">=")
        
        if threshold_key not in event.data:
            return False
        
        event_value = event.data[threshold_key]
        
        if comparison == ">=":
            return event_value >= threshold_value
        elif comparison == "<=":
            return event_value <= threshold_value
        elif comparison == "==":
            return event_value == threshold_value
        elif comparison == ">":
            return event_value > threshold_value
        elif comparison == "<":
            return event_value < threshold_value
        
        return False
    
    async def _execute_trigger(self, trigger: EventTrigger, event: EventInstance) -> Dict[str, Any]:
        """Execute actions for a triggered event"""
        logger.info(f"Executing trigger {trigger.id} for event {event.id}")
        
        results = []
        
        # Execute target agents
        for agent_id in trigger.target_agents:
            try:
                # Create agent execution context
                agent_context = {
                    "trigger_event": event.data,
                    "trigger_id": trigger.id,
                    "event_type": event.event_type.value
                }
                
                # Execute agent (mock implementation)
                agent_result = await self._execute_triggered_agent(agent_id, agent_context)
                results.append(agent_result)
                
            except Exception as e:
                logger.error(f"Error executing agent {agent_id} for trigger {trigger.id}: {str(e)}")
                results.append({
                    "agent_id": agent_id,
                    "status": "failed",
                    "error": str(e)
                })
        
        return {
            "trigger_id": trigger.id,
            "event_id": event.id,
            "agent_results": results,
            "execution_time": datetime.now().isoformat()
        }
    
    async def _execute_triggered_agent(self, agent_id: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Execute an agent triggered by an event"""
        # Mock implementation - replace with actual agent execution
        await asyncio.sleep(0.5)  # Simulate execution time
        
        return {
            "agent_id": agent_id,
            "status": "completed",
            "output": f"Response from {agent_id} to event trigger",
            "execution_time": 0.5,
            "context": context
        }
    
    async def _schedule_time_trigger(self, trigger: EventTrigger):
        """Schedule a time-based trigger"""
        await asyncio.sleep(trigger.delay_seconds)
        
        if trigger.is_active:
            time_event = EventInstance(
                id=f"time_event_{trigger.id}",
                event_type=EventType.TIME_ELAPSED,
                source_agent=None,
                data={"trigger_id": trigger.id, **trigger.parameters}
            )
            
            await self._process_event(time_event)
    
    async def _event_processing_loop(self):
        """Background event processing loop"""
        while True:
            try:
                await self._process_pending_events()
                await self._cleanup_expired_events()
                await asyncio.sleep(self.event_processing_delay)
            except Exception as e:
                logger.error(f"Error in event processing loop: {str(e)}")
                await asyncio.sleep(1.0)  # Longer delay on error
    
    async def _process_pending_events(self):
        """Process any pending events"""
        # Check for events that need processing
        current_time = datetime.now()
        
        for event in list(self.active_events.values()):
            if not event.processed:
                # Check if event has timed out
                if (current_time - event.timestamp).total_seconds() > self.event_timeout:
                    logger.warning(f"Event {event.id} timed out")
                    event.processed = True
                    event.processing_results = [{"status": "timeout"}]
    
    async def _cleanup_expired_events(self):
        """Clean up expired events"""
        current_time = datetime.now()
        expired_events = []
        
        for event_id, event in self.active_events.items():
            if (current_time - event.timestamp).total_seconds() > self.event_timeout:
                expired_events.append(event_id)
        
        for event_id in expired_events:
            del self.active_events[event_id]
    
    async def _check_timeout_events(self):
        """Check for and handle timeout events"""
        current_time = datetime.now()
        
        for event in list(self.active_events.values()):
            if (current_time - event.timestamp).total_seconds() > self.event_timeout:
                timeout_event = EventInstance(
                    id=f"timeout_{event.id}",
                    event_type=EventType.ERROR_OCCURRED,
                    source_agent=event.source_agent,
                    data={"original_event": event.id, "error": "timeout"}
                )
                
                await self._process_event(timeout_event)
    
    async def _check_completion_conditions(self, workflow: Workflow, context: Dict[str, Any]) -> bool:
        """Check if orchestration completion conditions are met"""
        completion_conditions = context.get("completion_conditions", {})
        
        # Default completion: no active events and all triggers processed
        if not completion_conditions:
            return len(self.active_events) == 0 and all(
                not trigger.is_active or trigger.trigger_count > 0 
                for trigger in self.event_triggers.values()
            )
        
        # Custom completion conditions
        if "min_events_processed" in completion_conditions:
            min_events = completion_conditions["min_events_processed"]
            if len(self.event_history) < min_events:
                return False
        
        if "required_event_types" in completion_conditions:
            required_types = set(completion_conditions["required_event_types"])
            processed_types = set(event.event_type.value for event in self.event_history)
            if not required_types.issubset(processed_types):
                return False
        
        return True
    
    async def _collect_event_metrics(self) -> Dict[str, Any]:
        """Collect event processing metrics"""
        total_events = len(self.event_history)
        successful_events = sum(1 for event in self.event_history 
                              if event.processed and not any(
                                  result.get("status") == "failed" 
                                  for result in event.processing_results
                              ))
        
        avg_processing_time = (sum(self.event_processing_times) / len(self.event_processing_times) 
                             if self.event_processing_times else 0)
        
        trigger_stats = {}
        for trigger_id, trigger in self.event_triggers.items():
            trigger_stats[trigger_id] = {
                "trigger_count": trigger.trigger_count,
                "is_active": trigger.is_active,
                "event_type": trigger.event_type.value
            }
        
        return {
            "total_events": total_events,
            "successful_events": successful_events,
            "failed_events": total_events - successful_events,
            "success_rate": successful_events / total_events if total_events > 0 else 0,
            "average_processing_time": avg_processing_time,
            "active_triggers": sum(1 for t in self.event_triggers.values() if t.is_active),
            "trigger_statistics": trigger_stats,
            "event_types_processed": list(set(event.event_type.value for event in self.event_history))
        }
    
    def _get_current_event_state(self) -> Dict[str, Any]:
        """Get current event system state"""
        return {
            "active_events": len(self.active_events),
            "total_triggers": len(self.event_triggers),
            "active_triggers": sum(1 for t in self.event_triggers.values() if t.is_active),
            "events_processed": len(self.event_history),
            "listeners_active": sum(1 for l in self.event_listeners.values() if l.is_active)
        }
    
    # Event handlers
    async def _handle_agent_completed(self, event_data: Dict[str, Any]):
        """Handle agent completion events"""
        completion_event = EventInstance(
            id=str(uuid.uuid4()),
            event_type=EventType.AGENT_COMPLETED,
            source_agent=event_data.get("agent_id"),
            data=event_data
        )
        
        await self._process_event(completion_event)
    
    async def _handle_agent_failed(self, event_data: Dict[str, Any]):
        """Handle agent failure events"""
        failure_event = EventInstance(
            id=str(uuid.uuid4()),
            event_type=EventType.AGENT_FAILED,
            source_agent=event_data.get("agent_id"),
            data=event_data
        )
        
        await self._process_event(failure_event)
    
    async def _handle_external_event(self, event_data: Dict[str, Any]):
        """Handle external events"""
        external_event = EventInstance(
            id=str(uuid.uuid4()),
            event_type=EventType.EXTERNAL_TRIGGER,
            source_agent=None,
            data=event_data
        )
        
        await self._process_event(external_event)
    
    async def _handle_user_input(self, event_data: Dict[str, Any]):
        """Handle user input events"""
        user_event = EventInstance(
            id=str(uuid.uuid4()),
            event_type=EventType.USER_INPUT,
            source_agent=None,
            data=event_data
        )
        
        await self._process_event(user_event)