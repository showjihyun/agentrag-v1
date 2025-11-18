"""
Test AI Agent Tool with n8n-level functionality.
"""

import asyncio
from backend.core.tools.integrations.ai_agent_tools import execute_ai_agent_tool


async def test_simple_task():
    """Test AI agent with a simple task."""
    print("\n=== Test 1: Simple Task ===")
    
    result = await execute_ai_agent_tool({
        "task": "What is 2 + 2?",
        "llm_provider": "ollama",
        "model": "llama3.1:8b",
        "enable_web_search": False,
        "enable_vector_search": False,
        "max_iterations": 5,
        "temperature": 0.7
    })
    
    print(f"Success: {result['success']}")
    print(f"Answer: {result['answer']}")
    print(f"Iterations: {result['iterations']}")
    print(f"Status: {result['status']}")
    
    return result


async def test_web_search_task():
    """Test AI agent with web search."""
    print("\n=== Test 2: Web Search Task ===")
    
    result = await execute_ai_agent_tool({
        "task": "Find the latest news about AI and summarize the top 3 articles",
        "llm_provider": "ollama",
        "model": "llama3.1:8b",
        "enable_web_search": True,
        "enable_vector_search": False,
        "max_iterations": 10,
        "temperature": 0.7
    })
    
    print(f"Success: {result['success']}")
    print(f"Answer: {result['answer']}")
    print(f"Tool Calls: {len(result['tool_calls'])}")
    print(f"Iterations: {result['iterations']}")
    
    # Print reasoning trace
    print("\nReasoning Trace:")
    for trace in result['reasoning_trace']:
        print(f"  Iteration {trace['iteration']}:")
        print(f"    Thought: {trace.get('thought')}")
        print(f"    Action: {trace['action']}")
        print(f"    Observation: {str(trace['observation'])[:100]}...")
    
    return result


async def test_vector_search_task():
    """Test AI agent with vector search."""
    print("\n=== Test 3: Vector Search Task ===")
    
    result = await execute_ai_agent_tool({
        "task": "Search our knowledge base for information about machine learning",
        "llm_provider": "ollama",
        "model": "llama3.1:8b",
        "enable_web_search": False,
        "enable_vector_search": True,
        "knowledgebase_id": "kb-documents",
        "max_iterations": 10,
        "temperature": 0.7
    })
    
    print(f"Success: {result['success']}")
    print(f"Answer: {result['answer']}")
    print(f"Tool Calls: {len(result['tool_calls'])}")
    
    return result


async def test_multi_tool_task():
    """Test AI agent with multiple tools."""
    print("\n=== Test 4: Multi-Tool Task ===")
    
    result = await execute_ai_agent_tool({
        "task": "Search the web for AI news, then search our knowledge base for related documents, and provide a comprehensive summary",
        "llm_provider": "ollama",
        "model": "llama3.1:8b",
        "enable_web_search": True,
        "enable_vector_search": True,
        "knowledgebase_id": "kb-documents",
        "available_tools": ["calculator", "http_request"],
        "max_iterations": 15,
        "temperature": 0.7
    })
    
    print(f"Success: {result['success']}")
    print(f"Answer: {result['answer']}")
    print(f"Tool Calls: {len(result['tool_calls'])}")
    print(f"Iterations: {result['iterations']}")
    
    # Print all tool calls
    print("\nTool Calls:")
    for call in result['tool_calls']:
        print(f"  {call['tool']} (iteration {call['iteration']})")
        print(f"    Input: {call['input']}")
        print(f"    Output: {str(call['output'])[:100]}...")
    
    return result


async def test_custom_system_prompt():
    """Test AI agent with custom system prompt."""
    print("\n=== Test 5: Custom System Prompt ===")
    
    custom_prompt = """You are a helpful AI assistant specialized in data analysis.
You have access to tools for searching and analyzing data.
Always provide detailed, data-driven answers with specific numbers and facts.
"""
    
    result = await execute_ai_agent_tool({
        "task": "Analyze the current state of AI technology",
        "llm_provider": "ollama",
        "model": "llama3.1:8b",
        "enable_web_search": True,
        "system_prompt": custom_prompt,
        "max_iterations": 10,
        "temperature": 0.5
    })
    
    print(f"Success: {result['success']}")
    print(f"Answer: {result['answer']}")
    
    return result


async def test_error_handling():
    """Test AI agent error handling."""
    print("\n=== Test 6: Error Handling ===")
    
    result = await execute_ai_agent_tool({
        "task": "This is a test task",
        "llm_provider": "invalid_provider",  # Invalid provider
        "model": "test",
        "max_iterations": 5
    })
    
    print(f"Success: {result['success']}")
    if not result['success']:
        print(f"Error: {result['error']}")
    
    return result


async def main():
    """Run all tests."""
    print("=" * 60)
    print("Testing AI Agent Tool (n8n-level functionality)")
    print("=" * 60)
    
    tests = [
        ("Simple Task", test_simple_task),
        ("Web Search Task", test_web_search_task),
        ("Vector Search Task", test_vector_search_task),
        ("Multi-Tool Task", test_multi_tool_task),
        ("Custom System Prompt", test_custom_system_prompt),
        ("Error Handling", test_error_handling),
    ]
    
    results = []
    for name, test_func in tests:
        try:
            print(f"\n{'=' * 60}")
            print(f"Running: {name}")
            print(f"{'=' * 60}")
            result = await test_func()
            results.append((name, "PASS" if result.get('success') else "FAIL"))
        except Exception as e:
            print(f"Error: {e}")
            results.append((name, "ERROR"))
    
    # Summary
    print(f"\n{'=' * 60}")
    print("Test Summary")
    print(f"{'=' * 60}")
    for name, status in results:
        status_icon = "✓" if status == "PASS" else "✗"
        print(f"{status_icon} {name}: {status}")
    
    print(f"\n{'=' * 60}")
    print("All tests completed!")
    print(f"{'=' * 60}")
    
    print("\nNote: These tests require:")
    print("1. Ollama running on localhost:11434")
    print("2. llama3.1:8b model installed")
    print("3. Internet connection for web search tests")
    print("4. Knowledge base configured for vector search tests")


if __name__ == "__main__":
    asyncio.run(main())
