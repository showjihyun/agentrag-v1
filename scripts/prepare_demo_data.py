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


def create_sample_chatflows(db: Session, user_id: str) -> list[Chatflow]:
    """Create 3 representative sample chatflows."""
    
    # Clear existing sample chatflows first
    existing_chatflows = db.query(Chatflow).filter(Chatflow.user_id == user_id).all()
    for chatflow in existing_chatflows:
        db.delete(chatflow)
    db.commit()
    print("🗑️  Cleared existing chatflows")
    
    chatflows = []
    
    # 1. Customer Support Chatbot
    customer_support = Chatflow(
        user_id=user_id,
        name="고객 지원 챗봇",
        description="고객 문의를 처리하고 FAQ를 제공하는 AI 챗봇입니다. 실시간으로 고객의 질문에 답변하고 적절한 부서로 연결해드립니다.",
        chat_config={
            "llm_provider": "ollama",
            "llm_model": "llama3.3:70b",
            "system_prompt": "당신은 친절하고 전문적인 고객 지원 담당자입니다. 고객의 문의사항을 정확히 파악하고 도움이 되는 답변을 제공하세요. 해결할 수 없는 문제는 적절한 부서로 안내해주세요.",
            "temperature": 0.3,
            "max_tokens": 1500,
            "streaming": True,
            "welcome_message": "안녕하세요! 고객 지원팀입니다. 어떤 도움이 필요하신가요?",
            "suggested_questions": [
                "주문 상태를 확인하고 싶어요",
                "환불 정책이 궁금합니다",
                "제품 사용법을 알려주세요",
                "기술 지원이 필요해요"
            ]
        },
        memory_config={
            "type": "hybrid",
            "buffer_size": 15,
            "summary_threshold": 30,
            "vector_top_k": 5,
            "hybrid_weights": {
                "buffer": 0.4,
                "summary": 0.3,
                "vector": 0.3
            }
        },
        rag_config={
            "enabled": True,
            "knowledgebase_ids": ["customer_support_kb"],
            "retrieval_strategy": "hybrid",
            "top_k": 7,
            "score_threshold": 0.75,
            "reranking_enabled": True
        },
        is_active=True,
        tags=["고객지원", "FAQ", "실시간채팅"],
        created_at=datetime.utcnow()
    )
    
    # 2. Product Recommendation Assistant
    product_assistant = Chatflow(
        user_id=user_id,
        name="상품 추천 어시스턴트",
        description="사용자의 취향과 요구사항을 분석하여 맞춤형 상품을 추천하는 AI 어시스턴트입니다. 개인화된 쇼핑 경험을 제공합니다.",
        chat_config={
            "llm_provider": "ollama",
            "llm_model": "llama3.3:70b",
            "system_prompt": "당신은 전문적인 상품 추천 어시스턴트입니다. 고객의 선호도, 예산, 용도를 파악하여 최적의 상품을 추천해주세요. 상품의 특징과 장단점을 명확히 설명하고, 비교 분석도 제공하세요.",
            "temperature": 0.5,
            "max_tokens": 2000,
            "streaming": True,
            "welcome_message": "안녕하세요! 상품 추천 어시스턴트입니다. 어떤 상품을 찾고 계신가요?",
            "suggested_questions": [
                "노트북 추천해주세요",
                "가성비 좋은 스마트폰 찾아요",
                "운동화 추천 부탁드려요",
                "선물용 상품 추천해주세요"
            ]
        },
        memory_config={
            "type": "vector",
            "vector_top_k": 8,
            "buffer_size": 10,
            "max_context_messages": 25
        },
        rag_config={
            "enabled": True,
            "knowledgebase_ids": ["product_catalog_kb", "reviews_kb"],
            "retrieval_strategy": "hybrid",
            "top_k": 10,
            "score_threshold": 0.7,
            "reranking_enabled": True
        },
        is_active=True,
        tags=["상품추천", "개인화", "쇼핑"],
        created_at=datetime.utcnow()
    )
    
    # 3. Learning & Tutorial Assistant
    learning_assistant = Chatflow(
        user_id=user_id,
        name="학습 도우미",
        description="복잡한 개념을 쉽게 설명하고 단계별 학습을 도와주는 AI 튜터입니다. 개인 맞춤형 학습 경험을 제공합니다.",
        chat_config={
            "llm_provider": "ollama",
            "llm_model": "llama3.3:70b",
            "system_prompt": "당신은 친근하고 인내심 있는 AI 튜터입니다. 복잡한 개념을 단계별로 쉽게 설명하고, 학습자의 수준에 맞춰 설명을 조정하세요. 예시와 비유를 활용하여 이해를 돕고, 학습자가 스스로 생각할 수 있도록 질문도 던져주세요.",
            "temperature": 0.7,
            "max_tokens": 2500,
            "streaming": True,
            "welcome_message": "안녕하세요! 학습 도우미입니다. 무엇을 배우고 싶으신가요?",
            "suggested_questions": [
                "프로그래밍 기초를 배우고 싶어요",
                "수학 개념을 쉽게 설명해주세요",
                "영어 문법을 도와주세요",
                "과학 원리를 알려주세요"
            ]
        },
        memory_config={
            "type": "summary",
            "summary_threshold": 40,
            "summary_interval": 15,
            "buffer_size": 20
        },
        rag_config={
            "enabled": True,
            "knowledgebase_ids": ["educational_content_kb", "tutorials_kb"],
            "retrieval_strategy": "semantic",
            "top_k": 6,
            "score_threshold": 0.8,
            "reranking_enabled": True
        },
        is_active=True,
        tags=["교육", "튜터링", "학습지원"],
        created_at=datetime.utcnow()
    )
    
    # Add all chatflows to database
    chatflows = [customer_support, product_assistant, learning_assistant]
    for chatflow in chatflows:
        db.add(chatflow)
    
    db.commit()
    
    for chatflow in chatflows:
        db.refresh(chatflow)
        print(f"✅ Created Chatflow: {chatflow.name} ({chatflow.id})")
    
    return chatflows


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
        
        # 4. Create sample chatflows (3 representative examples)
        chatflows = create_sample_chatflows(db, demo_user.id)
        
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
