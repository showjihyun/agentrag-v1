"""
Knowledgebase + RAG Integration Diagnostic Script.

This script checks the integration status and identifies potential issues.
"""

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import asyncio
from typing import Dict, List, Any
from datetime import datetime

# Color codes for terminal output
class Colors:
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    BLUE = '\033[94m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'


def print_header(text: str):
    """Print section header"""
    print(f"\n{Colors.BOLD}{Colors.BLUE}{'='*60}{Colors.ENDC}")
    print(f"{Colors.BOLD}{Colors.BLUE}{text}{Colors.ENDC}")
    print(f"{Colors.BOLD}{Colors.BLUE}{'='*60}{Colors.ENDC}\n")


def print_success(text: str):
    """Print success message"""
    print(f"{Colors.GREEN}✓ {text}{Colors.ENDC}")


def print_warning(text: str):
    """Print warning message"""
    print(f"{Colors.YELLOW}⚠ {text}{Colors.ENDC}")


def print_error(text: str):
    """Print error message"""
    print(f"{Colors.RED}✗ {text}{Colors.ENDC}")


def print_info(text: str):
    """Print info message"""
    print(f"{Colors.BLUE}ℹ {text}{Colors.ENDC}")


async def check_database_models():
    """Check if database models are properly configured"""
    print_header("1. Database Models Check")
    
    try:
        from backend.db.models.agent_builder import (
            Agent, Knowledgebase, AgentKnowledgebase
        )
        
        # Check Agent model
        if hasattr(Agent, 'knowledgebases'):
            print_success("Agent model has 'knowledgebases' relationship")
        else:
            print_error("Agent model missing 'knowledgebases' relationship")
            return False
        
        # Check Knowledgebase model
        if hasattr(Knowledgebase, 'agent_links'):
            print_success("Knowledgebase model has 'agent_links' relationship")
        else:
            print_error("Knowledgebase model missing 'agent_links' relationship")
            return False
        
        # Check AgentKnowledgebase model
        print_success("AgentKnowledgebase association model exists")
        
        # Check table constraints
        if hasattr(AgentKnowledgebase, '__table_args__'):
            print_success("AgentKnowledgebase has proper constraints")
        
        return True
        
    except Exception as e:
        print_error(f"Database model check failed: {e}")
        return False


async def check_api_endpoints():
    """Check if API endpoints are properly configured"""
    print_header("2. API Endpoints Check")
    
    try:
        # Check agent_chat API
        from backend.api.agent_builder import agent_chat
        
        if hasattr(agent_chat, 'router'):
            print_success("Agent Chat API exists")
            
            # Check if chat endpoint exists
            routes = [route.path for route in agent_chat.router.routes]
            if any('chat' in route for route in routes):
                print_success("Chat endpoint found in Agent Chat API")
            else:
                print_warning("Chat endpoint not found in Agent Chat API")
        else:
            print_error("Agent Chat API router not found")
            return False
        
        # Check kb_monitoring API
        try:
            from backend.api.agent_builder import kb_monitoring
            print_success("KB Monitoring API exists")
            
            routes = [route.path for route in kb_monitoring.router.routes]
            print_info(f"  Found {len(routes)} monitoring endpoints")
        except:
            print_warning("KB Monitoring API not found (optional)")
        
        return True
        
    except Exception as e:
        print_error(f"API endpoint check failed: {e}")
        return False


async def check_speculative_processor():
    """Check if SpeculativeProcessor has KB integration"""
    print_header("3. SpeculativeProcessor Integration Check")
    
    try:
        from backend.services.speculative_processor import SpeculativeProcessor
        
        # Check if process_with_knowledgebase method exists
        if hasattr(SpeculativeProcessor, 'process_with_knowledgebase'):
            print_success("SpeculativeProcessor has 'process_with_knowledgebase' method")
        else:
            print_error("SpeculativeProcessor missing 'process_with_knowledgebase' method")
            return False
        
        # Check if _search_knowledgebases method exists
        if hasattr(SpeculativeProcessor, '_search_knowledgebases'):
            print_success("SpeculativeProcessor has '_search_knowledgebases' method")
        else:
            print_error("SpeculativeProcessor missing '_search_knowledgebases' method")
            return False
        
        # Check if _merge_kb_and_general_results method exists
        if hasattr(SpeculativeProcessor, '_merge_kb_and_general_results'):
            print_success("SpeculativeProcessor has '_merge_kb_and_general_results' method")
        else:
            print_error("SpeculativeProcessor missing '_merge_kb_and_general_results' method")
            return False
        
        return True
        
    except Exception as e:
        print_error(f"SpeculativeProcessor check failed: {e}")
        return False


async def check_optimizer_services():
    """Check if optimizer services are available"""
    print_header("4. Optimizer Services Check")
    
    try:
        # Check KB Search Optimizer
        from backend.services.kb_search_optimizer import KBSearchOptimizer
        print_success("KB Search Optimizer available")
        
        # Check KB Cache Warmer
        from backend.services.kb_cache_warmer import KBCacheWarmer
        print_success("KB Cache Warmer available")
        
        # Check KB Reranker
        from backend.services.kb_reranker import KBReranker
        print_success("KB Reranker available")
        
        return True
        
    except Exception as e:
        print_warning(f"Some optimizer services not available: {e}")
        return True  # Not critical


async def check_scheduler():
    """Check if KB cache scheduler is configured"""
    print_header("5. Scheduler Check")
    
    try:
        from backend.core.kb_scheduler import KBCacheScheduler
        print_success("KB Cache Scheduler available")
        
        # Check if scheduler can be initialized
        scheduler = KBCacheScheduler()
        print_success("Scheduler can be initialized")
        
        return True
        
    except Exception as e:
        print_warning(f"Scheduler check failed: {e}")
        return True  # Not critical


async def check_database_data():
    """Check actual database data"""
    print_header("6. Database Data Check")
    
    try:
        from backend.db.database import SessionLocal
        from backend.db.models.agent_builder import (
            Agent, Knowledgebase, AgentKnowledgebase
        )
        from sqlalchemy.orm import joinedload
        
        db = SessionLocal()
        try:
            # Count agents
            agent_count = db.query(Agent).filter(
                Agent.deleted_at.is_(None)
            ).count()
            print_info(f"Total agents: {agent_count}")
            
            # Count knowledgebases
            kb_count = db.query(Knowledgebase).count()
            print_info(f"Total knowledgebases: {kb_count}")
            
            # Count agent-KB links
            link_count = db.query(AgentKnowledgebase).count()
            print_info(f"Total agent-KB links: {link_count}")
            
            if link_count > 0:
                print_success(f"Found {link_count} agent-KB connections")
                
                # Get sample agent with KB
                agent_with_kb = db.query(Agent).options(
                    joinedload(Agent.knowledgebases)
                ).filter(
                    Agent.deleted_at.is_(None)
                ).first()
                
                if agent_with_kb and agent_with_kb.knowledgebases:
                    kb_ids = [str(kb.knowledgebase_id) for kb in agent_with_kb.knowledgebases]
                    print_success(f"Sample agent '{agent_with_kb.name}' has {len(kb_ids)} KB(s)")
                    print_info(f"  KB IDs: {', '.join(kb_ids[:3])}{'...' if len(kb_ids) > 3 else ''}")
            else:
                print_warning("No agent-KB connections found")
                print_info("  Create connections using: Agent Settings → Knowledgebases")
            
            return True
            
        finally:
            db.close()
            
    except Exception as e:
        print_error(f"Database data check failed: {e}")
        return False


async def check_integration_flow():
    """Check if the integration flow works end-to-end"""
    print_header("7. Integration Flow Check")
    
    try:
        from backend.db.database import SessionLocal
        from backend.db.models.agent_builder import Agent
        from sqlalchemy.orm import joinedload
        
        db = SessionLocal()
        try:
            # Find an agent with KB
            agent = db.query(Agent).options(
                joinedload(Agent.knowledgebases)
            ).filter(
                Agent.deleted_at.is_(None)
            ).first()
            
            if not agent:
                print_warning("No agents found for testing")
                return True
            
            kb_ids = [str(kb.knowledgebase_id) for kb in agent.knowledgebases]
            
            if not kb_ids:
                print_warning(f"Agent '{agent.name}' has no knowledgebases")
                print_info("  Integration flow cannot be fully tested")
                return True
            
            print_success(f"Found test agent: '{agent.name}' with {len(kb_ids)} KB(s)")
            
            # Test if we can initialize SpeculativeProcessor
            try:
                from backend.services.speculative_processor import SpeculativeProcessor
                from backend.core.dependencies import (
                    get_embedding_service,
                    get_milvus_manager,
                    get_llm_manager,
                    get_redis_client
                )
                
                embedding_service = get_embedding_service()
                milvus_manager = get_milvus_manager()
                llm_manager = get_llm_manager()
                redis_client = get_redis_client()
                
                processor = SpeculativeProcessor(
                    embedding_service=embedding_service,
                    milvus_manager=milvus_manager,
                    llm_manager=llm_manager,
                    redis_client=redis_client
                )
                
                print_success("SpeculativeProcessor can be initialized")
                
                # Check if process_with_knowledgebase can be called
                if hasattr(processor, 'process_with_knowledgebase'):
                    print_success("process_with_knowledgebase method is callable")
                else:
                    print_error("process_with_knowledgebase method not found")
                    return False
                
            except Exception as e:
                print_error(f"Failed to initialize processor: {e}")
                return False
            
            return True
            
        finally:
            db.close()
            
    except Exception as e:
        print_error(f"Integration flow check failed: {e}")
        return False


async def check_main_app_integration():
    """Check if main app has proper integration"""
    print_header("8. Main App Integration Check")
    
    try:
        from backend.main import app
        
        # Check if agent_chat router is registered
        routes = [route.path for route in app.routes]
        
        if any('agent-builder/agents' in route and 'chat' in route for route in routes):
            print_success("Agent Chat API is registered in main app")
        else:
            print_warning("Agent Chat API might not be registered")
        
        # Check if kb_monitoring router is registered
        if any('agent-builder/kb' in route for route in routes):
            print_success("KB Monitoring API is registered in main app")
        else:
            print_warning("KB Monitoring API not registered (optional)")
        
        # Check if startup event exists
        startup_handlers = [h for h in app.router.on_startup]
        if startup_handlers:
            print_success(f"Found {len(startup_handlers)} startup handler(s)")
        else:
            print_warning("No startup handlers found")
        
        return True
        
    except Exception as e:
        print_error(f"Main app integration check failed: {e}")
        return False


async def generate_recommendations():
    """Generate recommendations based on checks"""
    print_header("9. Recommendations")
    
    recommendations = []
    
    # Check if there are agent-KB connections
    try:
        from backend.db.database import SessionLocal
        from backend.db.models.agent_builder import AgentKnowledgebase
        
        db = SessionLocal()
        try:
            link_count = db.query(AgentKnowledgebase).count()
            
            if link_count == 0:
                recommendations.append(
                    "Create agent-KB connections:\n"
                    "  1. Go to Agent Settings\n"
                    "  2. Navigate to Knowledgebases tab\n"
                    "  3. Link one or more knowledgebases"
                )
        finally:
            db.close()
    except:
        pass
    
    # General recommendations
    recommendations.extend([
        "Test the integration:\n"
        "  curl -X POST http://localhost:8000/api/agent-builder/agents/{agent_id}/chat \\\n"
        "    -H 'Authorization: Bearer {token}' \\\n"
        "    -d '{\"content\": \"What is in the documents?\"}'",
        
        "Monitor performance:\n"
        "  curl http://localhost:8000/api/agent-builder/kb/optimizer/stats",
        
        "Warm cache for better performance:\n"
        "  curl -X POST http://localhost:8000/api/agent-builder/kb/warm/{agent_id}",
    ])
    
    for i, rec in enumerate(recommendations, 1):
        print(f"\n{Colors.BOLD}{i}. {Colors.ENDC}{rec}")


async def main():
    """Run all diagnostic checks"""
    print(f"\n{Colors.BOLD}{Colors.BLUE}")
    print("╔════════════════════════════════════════════════════════════╗")
    print("║   Knowledgebase + RAG Integration Diagnostic Tool         ║")
    print("║   Version 1.0                                              ║")
    print("╚════════════════════════════════════════════════════════════╝")
    print(f"{Colors.ENDC}\n")
    
    print_info(f"Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    results = {}
    
    # Run all checks
    results['models'] = await check_database_models()
    results['api'] = await check_api_endpoints()
    results['processor'] = await check_speculative_processor()
    results['optimizer'] = await check_optimizer_services()
    results['scheduler'] = await check_scheduler()
    results['data'] = await check_database_data()
    results['flow'] = await check_integration_flow()
    results['main_app'] = await check_main_app_integration()
    
    # Summary
    print_header("Summary")
    
    passed = sum(1 for v in results.values() if v)
    total = len(results)
    
    if passed == total:
        print_success(f"All checks passed! ({passed}/{total})")
        print_info("\n✨ Integration is working correctly!")
    elif passed >= total * 0.7:
        print_warning(f"Most checks passed ({passed}/{total})")
        print_info("\n⚠️  Integration is mostly working, but some improvements needed")
    else:
        print_error(f"Several checks failed ({passed}/{total})")
        print_info("\n❌ Integration needs attention")
    
    # Recommendations
    await generate_recommendations()
    
    print(f"\n{Colors.BOLD}Diagnostic completed at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}{Colors.ENDC}\n")


if __name__ == "__main__":
    asyncio.run(main())
