#!/usr/bin/env python3
"""
Quick Demo Setup for 30-second Video

Minimal setup script for fast demo preparation.
Creates essential data only for the 30-second video demo.
"""

import asyncio
import sys
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent.parent / "backend"))

from sqlalchemy.orm import Session
from backend.db.database import SessionLocal
from backend.db.models.user import User
from backend.db.models.flows import Agentflow
from backend.db.models.agent_builder import Agent
from datetime import datetime
import json


def create_demo_user(db: Session) -> User:
    """Create demo user for 30s video."""
    demo_user = db.query(User).filter(User.email == "demo@agentbuilder.ai").first()
    
    if not demo_user:
        demo_user = User(
            email="demo@agentbuilder.ai",
            username="demo_user",
            full_name="Demo User",
            hashed_password="$2b$12$demo_hashed_password",
            is_active=True,
            is_verified=True
        )
        db.add(demo_user)
        db.commit()
        db.refresh(demo_user)
        print("✅ Demo user created")
    else:
        print("ℹ️  Demo user exists")
    
    return demo_user


def create_essential_agents(db: Session, user_id: str) -> list:
    """Create minimal agents for 30s demo."""
    agents_data = [
        {
            "name": "Intent Analyzer",
            "description": "Analyzes customer inquiry intent",
            "agent_type": "llm",
            "configuration": {
                "llm_provider": "openai",
                "llm_model": "gpt-4",
                "system_prompt": "Classify intent as: FAQ, Technical, or Other",
                "temperature": 0.3
            }
        }
    ]
    
    created_agents = []
    for agent_data in agents_data:
        existing = db.query(Agent).filter(
            Agent.user_id == user_id,
            Agent.name == agent_data["name"]
        ).first()
        
        if not existing:
            agent = Agent(
                user_id=user_id,
                name=agent_data["name"],
                description=agent_data["description"],
                agent_type=agent_data["agent_type"],
                configuration=agent_data["configuration"],
                is_active=True,
                created_at=datetime.utcnow()
            )
            db.add(agent)
            created_agents.append(agent)
    
    if created_agents:
        db.commit()
        print(f"✅ Created {len(created_agents)} agents")
    else:
        print("ℹ️  Agents already exist")
    
    return db.query(Agent).filter(Agent.user_id == user_id).all()


def create_demo_agentflow(db: Session, user_id: str, agents: list) -> Agentflow:
    """Create the demo agentflow for 30s video."""
    
    existing = db.query(Agentflow).filter(
        Agentflow.user_id == user_id,
        Agentflow.name == "Customer Support Demo"
    ).first()
    
    if existing:
        print("ℹ️  Demo agentflow exists")
        return existing
    
    # Simplified graph for 30s demo
    graph_definition = {
        "nodes": [
            {
                "id": "webhook_trigger",
                "type": "trigger",
                "data": {"label": "Webhook Trigger"},
                "position": {"x": 100, "y": 100}
            },
            {
                "id": "intent_analyzer",
                "type": "agent",
                "data": {"label": "Intent Analysis", "agent_id": agents[0].id if agents else "demo"},
                "position": {"x": 300, "y": 100}
            },
            {
                "id": "condition",
                "type": "condition",
                "data": {"label": "Route by Intent"},
                "position": {"x": 500, "y": 100}
            },
            {
                "id": "slack_notify",
                "type": "integration",
                "data": {"label": "Slack Notification", "integration": "slack"},
                "position": {"x": 700, "y": 50}
            },
            {
                "id": "email_notify",
                "type": "integration",
                "data": {"label": "Email Notification", "integration": "email"},
                "position": {"x": 700, "y": 150}
            }
        ],
        "edges": [
            {"id": "e1", "source": "webhook_trigger", "target": "intent_analyzer"},
            {"id": "e2", "source": "intent_analyzer", "target": "condition"},
            {"id": "e3", "source": "condition", "target": "slack_notify"},
            {"id": "e4", "source": "condition", "target": "email_notify"}
        ]
    }
    
    agentflow = Agentflow(
        user_id=user_id,
        name="Customer Support Demo",
        description="Demo workflow for 30s video",
        orchestration_type="sequential",
        supervisor_config={
            "enabled": True,
            "llm_provider": "openai",
            "llm_model": "gpt-4"
        },
        graph_definition=graph_definition,
        is_active=True,
        tags=["demo", "30s-video"],
        created_at=datetime.utcnow()
    )
    
    db.add(agentflow)
    db.commit()
    db.refresh(agentflow)
    
    print(f"✅ Created demo agentflow: {agentflow.id}")
    return agentflow


def create_sample_execution(db: Session, agentflow_id: str, user_id: str):
    """Create one sample execution for demo."""
    from backend.db.models.execution import Execution
    
    execution = Execution(
        user_id=user_id,
        flow_id=agentflow_id,
        flow_type="agentflow",
        status="completed",
        started_at=datetime.utcnow(),
        completed_at=datetime.utcnow(),
        duration_seconds=3.2,  # Perfect for 30s demo
        input_data={"inquiry": "Demo customer inquiry"},
        output_data={"response": "Demo response generated"},
        metrics={
            "nodes_executed": 5,
            "tokens_used": 150,
            "cache_hits": 2,
            "api_calls": 3
        }
    )
    
    db.add(execution)
    db.commit()
    print("✅ Created sample execution (3.2s duration)")


def main():
    """Quick setup for 30s demo video."""
    print("🎬 Quick Demo Setup for 30-second Video\n")
    
    db = SessionLocal()
    
    try:
        # 1. Create demo user
        demo_user = create_demo_user(db)
        
        # 2. Create essential agents
        agents = create_essential_agents(db, demo_user.id)
        
        # 3. Create demo agentflow
        agentflow = create_demo_agentflow(db, demo_user.id, agents)
        
        # 4. Create sample execution
        create_sample_execution(db, agentflow.id, demo_user.id)
        
        print("\n✅ Quick demo setup complete!")
        print("\n📋 Demo Ready:")
        print("   🎯 URL: http://localhost:3000/agent-builder/agentflows")
        print("   👤 User: demo@agentbuilder.ai")
        print("   🔄 Workflow: Customer Support Demo")
        print("   ⏱️  Expected execution: 3.2s")
        print("\n🎥 Ready for 30-second recording!")
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        db.rollback()
    finally:
        db.close()


if __name__ == "__main__":
    main()