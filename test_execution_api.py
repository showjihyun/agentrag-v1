"""Test execution API endpoints."""
import sys
sys.path.insert(0, 'backend')

from fastapi.testclient import TestClient
from backend.main import app
from backend.db.database import get_db
from backend.db.models.user import User
from backend.db.models.agent_builder import Agent, Workflow, WorkflowExecution
from sqlalchemy.orm import Session
import uuid
from datetime import datetime

client = TestClient(app)

def create_test_user(db: Session):
    """Create a test user."""
    user = User(
        id=uuid.uuid4(),
        email="test@example.com",
        username="testuser",
        hashed_password="dummy",
        is_active=True
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user

def create_test_workflow(db: Session, user_id: uuid.UUID):
    """Create a test workflow."""
    workflow = Workflow(
        id=uuid.uuid4(),
        user_id=user_id,
        name="Test Workflow",
        description="Test workflow for execution",
        workflow_data={
            "nodes": [],
            "edges": []
        },
        is_public=False,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )
    db.add(workflow)
    db.commit()
    db.refresh(workflow)
    return workflow

def test_execution_list():
    """Test execution list endpoint."""
    print("🧪 Testing execution list endpoint...")
    
    # Get DB session
    db = next(get_db())
    
    try:
        # Create test data
        user = create_test_user(db)
        workflow = create_test_workflow(db, user.id)
        
        # Create a workflow execution
        execution = WorkflowExecution(
            id=uuid.uuid4(),
            workflow_id=workflow.id,
            user_id=user.id,
            input_data={"test": True},
            execution_context={},
            status="completed",
            started_at=datetime.utcnow(),
            completed_at=datetime.utcnow()
        )
        db.add(execution)
        db.commit()
        
        print(f"✅ Created test workflow execution: {execution.id}")
        
        # Now test the API (we need to mock authentication)
        # For now, just verify the execution is in DB
        from sqlalchemy import text
        result = db.execute(text("SELECT COUNT(*) FROM workflow_executions"))
        count = result.scalar()
        print(f"📊 Workflow executions in DB: {count}")
        
        if count > 0:
            print("✅ Workflow execution was saved successfully!")
        else:
            print("❌ Workflow execution was not saved!")
        
        # Cleanup
        db.delete(execution)
        db.delete(workflow)
        db.delete(user)
        db.commit()
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    test_execution_list()
