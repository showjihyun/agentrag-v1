#!/usr/bin/env python3
"""
A2A 모듈 import 테스트 스크립트
"""

def test_imports():
    """A2A 관련 모듈들이 제대로 import되는지 테스트"""
    
    print("Testing A2A imports...")
    
    try:
        print("1. Testing models.a2a...")
        from models.a2a import AgentCard, Task, Message
        print("   ✓ models.a2a imported successfully")
    except Exception as e:
        print(f"   ✗ models.a2a import failed: {e}")
        return False
    
    try:
        print("2. Testing services.a2a...")
        from services.a2a import A2AClient, A2AServer, A2AAgentRegistry
        print("   ✓ services.a2a imported successfully")
    except Exception as e:
        print(f"   ✗ services.a2a import failed: {e}")
        return False
    
    try:
        print("3. Testing services.a2a.registry...")
        from services.a2a.registry import get_a2a_registry
        registry = get_a2a_registry()
        print("   ✓ A2A registry created successfully")
    except Exception as e:
        print(f"   ✗ A2A registry creation failed: {e}")
        return False
    
    try:
        print("4. Testing api.agent_builder.a2a...")
        from api.agent_builder import a2a
        print("   ✓ A2A API module imported successfully")
        print(f"   Router prefix: {a2a.router.prefix}")
        print(f"   Router tags: {a2a.router.tags}")
    except Exception as e:
        print(f"   ✗ A2A API module import failed: {e}")
        return False
    
    print("\n✅ All A2A imports successful!")
    return True

if __name__ == "__main__":
    test_imports()