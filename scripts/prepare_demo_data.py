#!/usr/bin/env python3
"""
Demo Data Preparation Script for Agent-Builder Video

This script creates sample data for the demo video:
- Demo user account
- Sample agents
- Sample workflows (Agentflows, Chatflows)
- Sample executions with metrics
- Sample integrations
"""

import asyncio
import sys
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent.parent / "backend"))

from sqlalchemy.orm import Session
from backend.db.database import SessionLocal
from backend.db.models.user import User
from backend.db.models.flows import Agentflow, Chatflow, Workflow
from backend.db.models.agent_builder import Agent, Block, Tool
from datetime import datetime, timedelta
import json


def create_demo_user(db: Session) -> User:
    """Create demo user account."""
    demo_user = db.query(User).filter(User.email == "demo@agentbuilder.ai").first()
    
    if not demo_user:
        demo_user = User(
            email="demo@agentbuilder.ai",
            username="demo_user",
            full_name="Demo User",
            hashed_password="$2b$12$demo_hashed_password",  # Not for production
            is_active=True,
            is_verified=True
        )
        db.add(demo_user)
        db.commit()
        db.refresh(demo_user)
        print("✅ Created demo user: demo@agentbuilder.ai")
    else:
        print("ℹ️  Demo user already exists")
    
    return demo_user


def create_sample_agents(db: Session, user_id: str) -> list:
    """Create sample AI agents."""
    agents_data = [
        {
            "name": "Intent Analyzer",
            "description": "Analyzes customer inquiry intent using GPT-4",
            "agent_type": "llm",
            "configuration": {
                "llm_provider": "openai",
                "llm_model": "gpt-4",
                "system_prompt": "You are an expert at analyzing customer inquiries. Classify the intent as: FAQ, Technical, Sales, or Other.",
                "temperature": 0.3
            }
        },
        {
            "name": "FAQ Search Agent",
            "description": "Searches FAQ database for relevant answers",
            "agent_type": "rag",
            "configuration": {
                "knowledgebase_id": "faq_kb_001",
                "retrieval_strategy": "hybrid",
                "top_k": 5
            }
        },
        {
            "name": "Ticket Creator",
            "description": "Creates support tickets in the system",
            "agent_type": "tool",
            "configuration": {
                "tool_id": "create_ticket",
                "auto_assign": True
            }
        },
        {
            "name": "Response Generator",
            "description": "Generates human-like responses to customer inquiries",
            "agent_type": "llm",
            "configuration": {
                "llm_provider": "anthropic",
                "llm_model": "claude-3-sonnet",
                "system_prompt": "You are a helpful customer support agent. Provide clear, friendly responses.",
                "temperature": 0.7
            }
        }
    ]
    
    created_agents = []
    for agent_data in agents_data:
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
    
    db.commit()
    print(f"✅ Created {len(created_agents)} sample agents")
    return created_agents


def create_customer_support_agentflow(db: Session, user_id: str, agents: list) -> Agentflow:
    """Create customer support automation agentflow."""
    
    graph_definition = {
        "nodes": [
            {
                "id": "webhook_trigger",
                "type": "trigger",
                "data": {
                    "label": "Webhook Trigger",
                    "trigger_type": "webhook",
                    "config": {"method": "POST", "path": "/customer-inquiry"}
                },
                "position": {"x": 100, "y": 100}
            },
            {
                "id": "intent_analyzer",
                "type": "agent",
                "data": {
                    "label": "Intent Analysis",
                    "agent_id": agents[0].id,
                    "agent_name": "Intent Analyzer"
                },
                "position": {"x": 300, "y": 100}
            },
            {
                "id": "condition_intent",
                "type": "condition",
                "data": {
                    "label": "Intent Type?",
                    "conditions": [
                        {"path": "FAQ", "condition": "intent == 'FAQ'"},
                        {"path": "Technical", "condition": "intent == 'Technical'"},
                        {"path": "Other", "condition": "intent == 'Other'"}
                    ]
                },
                "position": {"x": 500, "y": 100}
            },
            {
                "id": "faq_search",
                "type": "agent",
                "data": {
                    "label": "FAQ Search",
                    "agent_id": agents[1].id,
                    "agent_name": "FAQ Search Agent"
                },
                "position": {"x": 700, "y": 50}
            },
            {
                "id": "create_ticket",
                "type": "agent",
                "data": {
                    "label": "Create Ticket",
                    "agent_id": agents[2].id,
                    "agent_name": "Ticket Creator"
                },
                "position": {"x": 700, "y": 150}
            },
            {
                "id": "human_approval",
                "type": "approval",
                "data": {
                    "label": "Human Approval",
                    "approval_type": "manual"
                },
                "position": {"x": 700, "y": 250}
            },
            {
                "id": "slack_notification",
                "type": "integration",
                "data": {
                    "label": "Slack Notification",
                    "integration": "slack",
                    "config": {"channel": "#support"}
                },
                "position": {"x": 900, "y": 50}
            },
            {
                "id": "email_notification",
                "type": "integration",
                "data": {
                    "label": "Email Notification",
                    "integration": "email",
                    "config": {"to": "support@company.com"}
                },
                "position": {"x": 900, "y": 150}
            },
            {
                "id": "generate_response",
                "type": "agent",
                "data": {
                    "label": "Generate Response",
                    "agent_id": agents[3].id,
                    "agent_name": "Response Generator"
                },
                "position": {"x": 900, "y": 250}
            }
        ],
        "edges": [
            {"id": "e1", "source": "webhook_trigger", "target": "intent_analyzer"},
            {"id": "e2", "source": "intent_analyzer", "target": "condition_intent"},
            {"id": "e3", "source": "condition_intent", "target": "faq_search", "sourceHandle": "FAQ"},
            {"id": "e4", "source": "condition_intent", "target": "create_ticket", "sourceHandle": "Technical"},
            {"id": "e5", "source": "condition_intent", "target": "human_approval", "sourceHandle": "Other"},
            {"id": "e6", "source": "faq_search", "target": "slack_notification"},
            {"id": "e7", "source": "create_ticket", "target": "email_notification"},
            {"id": "e8", "source": "human_approval", "target": "generate_response"}
        ]
    }
    
    agentflow = Agentflow(
        user_id=user_id,
        name="Customer Support Automation",
        description="Automated customer support workflow with intent analysis and multi-path routing",
        orchestration_type="hierarchical",
        supervisor_config={
            "enabled": True,
            "llm_provider": "openai",
            "llm_model": "gpt-4",
            "max_iterations": 10,
            "decision_strategy": "llm_based"
        },
        graph_definition=graph_definition,
        is_active=True,
        tags=["customer-support", "automation", "multi-agent"],
        created_at=datetime.utcnow()
    )
    
    db.add(agentflow)
    db.commit()
    db.refresh(agentflow)
    
    print(f"✅ Created Customer Support Agentflow: {agentflow.id}")
    return agentflow


def create_sample_chatflow(db: Session, user_id: str) -> Chatflow:
    """Create sample chatflow for conversational AI."""
    
    chatflow = Chatflow(
        user_id=user_id,
        name="Product Assistant Chatbot",
        description="AI chatbot that helps users find products and answer questions",
        chat_config={
            "llm_provider": "openai",
            "llm_model": "gpt-4",
            "system_prompt": "You are a helpful product assistant. Help users find products and answer their questions.",
            "temperature": 0.7,
            "max_tokens": 2000,
            "streaming": True,
            "welcome_message": "Hi! I'm your product assistant. How can I help you today?",
            "suggested_questions": [
                "What are your best-selling products?",
                "Can you help me find a laptop?",
                "What's your return policy?"
            ]
        },
        memory_config={
            "type": "buffer",
            "max_messages": 10
        },
        rag_config={
            "enabled": True,
            "knowledgebase_ids": ["product_kb_001"],
            "retrieval_strategy": "hybrid",
            "top_k": 5,
            "score_threshold": 0.7,
            "reranking_enabled": True
        },
        is_active=True,
        tags=["chatbot", "product-support", "rag"],
        created_at=datetime.utcnow()
    )
    
    db.add(chatflow)
    db.commit()
    db.refresh(chatflow)
    
    print(f"✅ Created Product Assistant Chatflow: {chatflow.id}")
    return chatflow


def create_sample_executions(db: Session, agentflow_id: str, user_id: str):
    """Create sample execution history with metrics."""
    from backend.db.models.execution import Execution
    
    # Create executions for the past 7 days
    executions_data = []
    base_time = datetime.utcnow() - timedelta(days=7)
    
    for day in range(7):
        # 10-20 executions per day
        num_executions = 10 + (day * 2)
        
        for i in range(num_executions):
            execution_time = base_time + timedelta(days=day, hours=i % 24)
            
            # 85% success rate
            status = "completed" if i % 20 != 0 else "failed"
            
            # Execution duration: 1-8 seconds
            duration = 1.0 + (i % 7) * 1.0
            
            execution = Execution(
                user_id=user_id,
                flow_id=agentflow_id,
                flow_type="agentflow",
                status=status,
                started_at=execution_time,
                completed_at=execution_time + timedelta(seconds=duration),
                duration_seconds=duration,
                input_data={"inquiry": f"Sample inquiry {i}"},
                output_data={"response": f"Sample response {i}"} if status == "completed" else None,
                error_message="Sample error" if status == "failed" else None,
                metrics={
                    "nodes_executed": 7 if status == "completed" else 3,
                    "tokens_used": 500 + (i * 10),
                    "cache_hits": 3,
                    "api_calls": 5
                }
            )
            executions_data.append(execution)
    
    db.bulk_save_objects(executions_data)
    db.commit()
    
    print(f"✅ Created {len(executions_data)} sample executions")


def main():
    """Main function to prepare demo data."""
    print("🎬 Preparing demo data for Agent-Builder video...\n")
    
    db = SessionLocal()
    
    try:
        # 1. Create demo user
        demo_user = create_demo_user(db)
        
        # 2. Create sample agents
        agents = create_sample_agents(db, demo_user.id)
        
        # 3. Create customer support agentflow
        agentflow = create_customer_support_agentflow(db, demo_user.id, agents)
        
        # 4. Create sample chatflow
        chatflow = create_sample_chatflow(db, demo_user.id)
        
        # 5. Create sample executions
        create_sample_executions(db, agentflow.id, demo_user.id)
        
        print("\n✅ Demo data preparation complete!")
        print("\n📋 Demo Credentials:")
        print("   Email: demo@agentbuilder.ai")
        print("   Password: demo123 (set this in your auth system)")
        print("\n🎥 Ready for video recording!")
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        db.rollback()
    finally:
        db.close()


if __name__ == "__main__":
    main()
