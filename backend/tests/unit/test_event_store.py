# Tests for Event Store

import pytest
from datetime import datetime, timedelta
from backend.core.events import DomainEvent, EventStore


class TestDomainEvent:
    """Test DomainEvent class."""
    
    def test_create_event(self):
        """Test creating a domain event."""
        event = DomainEvent(
            aggregate_id="workflow-123",
            aggregate_type="Workflow",
            event_type="WorkflowCreated",
            event_data={"name": "Test Workflow"},
            user_id=1
        )
        
        assert event.aggregate_id == "workflow-123"
        assert event.aggregate_type == "Workflow"
        assert event.event_type == "WorkflowCreated"
        assert event.event_data == {"name": "Test Workflow"}
        assert event.user_id == 1
        assert event.version == 1
        assert isinstance(event.timestamp, datetime)
    
    def test_event_to_dict(self):
        """Test converting event to dictionary."""
        event = DomainEvent(
            aggregate_id="workflow-123",
            aggregate_type="Workflow",
            event_type="WorkflowCreated",
            event_data={"name": "Test Workflow"},
            user_id=1,
            metadata={"source": "api"}
        )
        
        event_dict = event.to_dict()
        
        assert event_dict["aggregate_id"] == "workflow-123"
        assert event_dict["aggregate_type"] == "Workflow"
        assert event_dict["event_type"] == "WorkflowCreated"
        assert event_dict["event_data"] == {"name": "Test Workflow"}
        assert event_dict["user_id"] == 1
        assert event_dict["metadata"] == {"source": "api"}
        assert "timestamp" in event_dict
        assert event_dict["version"] == 1
    
    def test_event_from_dict(self):
        """Test creating event from dictionary."""
        event_dict = {
            "aggregate_id": "workflow-123",
            "aggregate_type": "Workflow",
            "event_type": "WorkflowCreated",
            "event_data": {"name": "Test Workflow"},
            "user_id": 1,
            "metadata": {"source": "api"},
            "timestamp": datetime.utcnow().isoformat(),
            "version": 1
        }
        
        event = DomainEvent.from_dict(event_dict)
        
        assert event.aggregate_id == "workflow-123"
        assert event.aggregate_type == "Workflow"
        assert event.event_type == "WorkflowCreated"
        assert event.user_id == 1


class TestEventStore:
    """Test EventStore class."""
    
    @pytest.mark.asyncio
    async def test_append_event(self, db_session):
        """Test appending an event to the store."""
        store = EventStore(db_session)
        
        event = DomainEvent(
            aggregate_id="workflow-123",
            aggregate_type="Workflow",
            event_type="WorkflowCreated",
            event_data={"name": "Test Workflow"},
            user_id=1
        )
        
        event_id = await store.append(event)
        
        assert event_id is not None
        assert event_id > 0
    
    @pytest.mark.asyncio
    async def test_get_events(self, db_session):
        """Test retrieving events for an aggregate."""
        store = EventStore(db_session)
        
        # Append multiple events
        events = [
            DomainEvent(
                aggregate_id="workflow-123",
                aggregate_type="Workflow",
                event_type="WorkflowCreated",
                event_data={"name": "Test Workflow"},
                user_id=1
            ),
            DomainEvent(
                aggregate_id="workflow-123",
                aggregate_type="Workflow",
                event_type="WorkflowUpdated",
                event_data={"name": "Updated Workflow"},
                user_id=1
            )
        ]
        
        for event in events:
            await store.append(event)
        
        # Retrieve events
        retrieved_events = await store.get_events("workflow-123")
        
        assert len(retrieved_events) == 2
        assert retrieved_events[0].event_type == "WorkflowCreated"
        assert retrieved_events[1].event_type == "WorkflowUpdated"
    
    @pytest.mark.asyncio
    async def test_replay_events(self, db_session):
        """Test replaying events up to a version."""
        store = EventStore(db_session)
        
        # Append events with versions
        for i in range(5):
            event = DomainEvent(
                aggregate_id="workflow-123",
                aggregate_type="Workflow",
                event_type=f"Event{i}",
                event_data={"version": i},
                user_id=1
            )
            event.version = i + 1
            await store.append(event)
        
        # Replay up to version 3
        replayed_events = await store.replay(
            aggregate_id="workflow-123",
            aggregate_type="Workflow",
            to_version=3
        )
        
        assert len(replayed_events) == 3
        assert replayed_events[0].event_type == "Event0"
        assert replayed_events[2].event_type == "Event2"
    
    @pytest.mark.asyncio
    async def test_get_audit_log(self, db_session):
        """Test getting audit log with filters."""
        store = EventStore(db_session)
        
        # Append events for different users
        for user_id in [1, 2]:
            for i in range(3):
                event = DomainEvent(
                    aggregate_id=f"workflow-{user_id}-{i}",
                    aggregate_type="Workflow",
                    event_type="WorkflowCreated",
                    event_data={"name": f"Workflow {i}"},
                    user_id=user_id
                )
                await store.append(event)
        
        # Get audit log for user 1
        audit_log = await store.get_audit_log(user_id=1)
        
        assert len(audit_log) == 3
        assert all(event.user_id == 1 for event in audit_log)
    
    @pytest.mark.asyncio
    async def test_get_audit_log_with_date_filter(self, db_session):
        """Test getting audit log with date filters."""
        store = EventStore(db_session)
        
        # Append event
        event = DomainEvent(
            aggregate_id="workflow-123",
            aggregate_type="Workflow",
            event_type="WorkflowCreated",
            event_data={"name": "Test Workflow"},
            user_id=1
        )
        await store.append(event)
        
        # Get audit log from yesterday
        from_date = datetime.utcnow() - timedelta(days=1)
        audit_log = await store.get_audit_log(from_date=from_date)
        
        assert len(audit_log) >= 1
    
    @pytest.mark.asyncio
    async def test_get_audit_log_with_type_filter(self, db_session):
        """Test getting audit log with type filters."""
        store = EventStore(db_session)
        
        # Append different event types
        event_types = ["WorkflowCreated", "WorkflowUpdated", "WorkflowDeleted"]
        for event_type in event_types:
            event = DomainEvent(
                aggregate_id="workflow-123",
                aggregate_type="Workflow",
                event_type=event_type,
                event_data={"name": "Test Workflow"},
                user_id=1
            )
            await store.append(event)
        
        # Get only WorkflowCreated events
        audit_log = await store.get_audit_log(event_type="WorkflowCreated")
        
        assert len(audit_log) >= 1
        assert all(event.event_type == "WorkflowCreated" for event in audit_log)
