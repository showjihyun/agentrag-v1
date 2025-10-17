#!/usr/bin/env python3
"""
Test script for the Agentic RAG system.
Runs a series of example queries and displays the results.
"""

import requests
import json
import time
from typing import Dict, List, Any

BASE_URL = "http://localhost:8000"

# Test queries organized by category
TEST_QUERIES = {
    "Simple Fact Retrieval": [
        "What accuracy did the model achieve?",
        "What was the Q3 revenue?",
        "What is the F1 score?",
    ],
    "Comparison Queries": [
        "How does the new model compare to the baseline?",
        "Compare the revenue growth to customer acquisition growth",
    ],
    "List Extraction": [
        "What are the future work directions mentioned in the research?",
        "What challenges did the company face in Q3?",
        "List the API endpoints available",
    ],
    "Procedural Queries": [
        "How do I authenticate with the API?",
        "What should I do if I get a rate limit error?",
    ],
    "Cross-Document Analysis": [
        "What was the Q3 revenue and how many customers were acquired?",
        "Compare the technical improvements with business results",
    ],
    "Synthesis Queries": [
        "Summarize the main findings from the research paper",
        "What are the key takeaways from the quarterly report?",
    ],
}


def check_health() -> bool:
    """Check if the API is healthy."""
    try:
        response = requests.get(f"{BASE_URL}/api/health", timeout=5)
        if response.status_code == 200:
            data = response.json()
            print("✓ API is healthy")
            print(f"  Services: {data.get('services', {})}")
            return True
        else:
            print(f"✗ API health check failed: {response.status_code}")
            return False
    except requests.exceptions.RequestException as e:
        print(f"✗ Cannot connect to API: {e}")
        return False


def list_documents() -> List[Dict[str, Any]]:
    """List all uploaded documents."""
    try:
        response = requests.get(f"{BASE_URL}/api/documents", timeout=10)
        if response.status_code == 200:
            data = response.json()
            docs = data.get('documents', [])
            print(f"\n✓ Found {len(docs)} documents:")
            for doc in docs:
                print(f"  - {doc['filename']} ({doc['chunk_count']} chunks)")
            return docs
        else:
            print(f"✗ Failed to list documents: {response.status_code}")
            return []
    except requests.exceptions.RequestException as e:
        print(f"✗ Error listing documents: {e}")
        return []


def run_query(query: str, stream: bool = False, session_id: str = "test_session") -> Dict[str, Any]:
    """Run a single query."""
    try:
        response = requests.post(
            f"{BASE_URL}/api/query",
            json={
                "query": query,
                "session_id": session_id,
                "stream": stream
            },
            timeout=60
        )
        
        if response.status_code == 200:
            return response.json()
        else:
            return {
                "error": f"HTTP {response.status_code}",
                "details": response.text
            }
    except requests.exceptions.RequestException as e:
        return {
            "error": "Request failed",
            "details": str(e)
        }


def run_streaming_query(query: str, session_id: str = "test_session"):
    """Run a streaming query and display results in real-time."""
    try:
        response = requests.post(
            f"{BASE_URL}/api/query",
            json={
                "query": query,
                "session_id": session_id,
                "stream": True
            },
            stream=True,
            timeout=60
        )
        
        print("\n  Streaming response:")
        for line in response.iter_lines():
            if line:
                line_str = line.decode('utf-8')
                if line_str.startswith('data: '):
                    data = json.loads(line_str[6:])
                    event_type = data.get('type', 'unknown')
                    content = data.get('content', '')
                    
                    # Display based on event type
                    if event_type == 'planning':
                        print(f"  [PLAN] {content[:100]}...")
                    elif event_type == 'thought':
                        print(f"  [THINK] {content[:100]}...")
                    elif event_type == 'action':
                        print(f"  [ACT] {content[:100]}...")
                    elif event_type == 'observation':
                        print(f"  [OBS] {content[:100]}...")
                    elif event_type == 'reflection':
                        print(f"  [REFLECT] {content[:100]}...")
                    elif event_type == 'response':
                        print(f"\n  [RESPONSE]")
                        print(f"  {content[:200]}...")
                        sources = data.get('sources', [])
                        if sources:
                            print(f"\n  Sources ({len(sources)}):")
                            for src in sources[:3]:
                                print(f"    - {src['document_name']}: {src['excerpt'][:80]}...")
                    elif event_type == 'error':
                        print(f"  [ERROR] {content}")
        
        print()
        
    except requests.exceptions.RequestException as e:
        print(f"  ✗ Streaming failed: {e}")


def display_result(query: str, result: Dict[str, Any]):
    """Display query result in a formatted way."""
    print(f"\n{'='*80}")
    print(f"Query: {query}")
    print('='*80)
    
    if 'error' in result:
        print(f"✗ Error: {result['error']}")
        print(f"  Details: {result.get('details', 'N/A')}")
        return
    
    # Display response
    response_text = result.get('response', 'No response')
    print(f"\nResponse:")
    print(f"{response_text[:500]}{'...' if len(response_text) > 500 else ''}")
    
    # Display sources
    sources = result.get('sources', [])
    if sources:
        print(f"\nSources ({len(sources)}):")
        for i, source in enumerate(sources[:3], 1):
            print(f"  {i}. {source['document_name']} (score: {source['score']:.3f})")
            print(f"     {source['excerpt'][:100]}...")
    
    # Display metadata
    metadata = result.get('metadata', {})
    if metadata:
        processing_time = metadata.get('processing_time_ms', 0)
        total_actions = metadata.get('total_actions', 0)
        print(f"\nMetadata:")
        print(f"  Processing time: {processing_time}ms")
        print(f"  Total actions: {total_actions}")


def run_test_suite(streaming: bool = False):
    """Run the complete test suite."""
    print("\n" + "="*80)
    print("AGENTIC RAG SYSTEM - TEST SUITE")
    print("="*80)
    
    # Check health
    print("\n1. Health Check")
    print("-" * 80)
    if not check_health():
        print("\n✗ API is not available. Please start the backend server.")
        return
    
    # List documents
    print("\n2. Document Check")
    print("-" * 80)
    docs = list_documents()
    if not docs:
        print("\n⚠ No documents found. Please upload sample documents first.")
        print("  Run: cd examples/sample_documents && ./upload_samples.sh")
        return
    
    # Run test queries
    print("\n3. Running Test Queries")
    print("-" * 80)
    
    for category, queries in TEST_QUERIES.items():
        print(f"\n{category}:")
        print("-" * 80)
        
        for query in queries:
            print(f"\nQuery: {query}")
            
            if streaming:
                run_streaming_query(query)
            else:
                result = run_query(query, stream=False)
                if 'error' not in result:
                    response = result.get('response', '')
                    print(f"Response: {response[:150]}...")
                    sources = result.get('sources', [])
                    print(f"Sources: {len(sources)} documents")
                else:
                    print(f"✗ Error: {result['error']}")
            
            time.sleep(1)  # Rate limiting
    
    print("\n" + "="*80)
    print("TEST SUITE COMPLETED")
    print("="*80)


def run_interactive_mode():
    """Run in interactive mode for custom queries."""
    print("\n" + "="*80)
    print("AGENTIC RAG SYSTEM - INTERACTIVE MODE")
    print("="*80)
    print("\nType your queries (or 'quit' to exit, 'stream' to toggle streaming)")
    
    streaming = True
    session_id = f"interactive_{int(time.time())}"
    
    while True:
        try:
            query = input("\n> ").strip()
            
            if not query:
                continue
            
            if query.lower() in ['quit', 'exit', 'q']:
                print("Goodbye!")
                break
            
            if query.lower() == 'stream':
                streaming = not streaming
                print(f"Streaming mode: {'ON' if streaming else 'OFF'}")
                continue
            
            if streaming:
                run_streaming_query(query, session_id)
            else:
                result = run_query(query, stream=False, session_id=session_id)
                display_result(query, result)
        
        except KeyboardInterrupt:
            print("\n\nGoodbye!")
            break
        except Exception as e:
            print(f"Error: {e}")


def main():
    """Main entry point."""
    import sys
    
    if len(sys.argv) > 1:
        mode = sys.argv[1]
        if mode == 'interactive':
            run_interactive_mode()
        elif mode == 'streaming':
            run_test_suite(streaming=True)
        elif mode == 'test':
            run_test_suite(streaming=False)
        else:
            print(f"Unknown mode: {mode}")
            print("Usage: python test_queries.py [test|streaming|interactive]")
    else:
        # Default: run test suite without streaming
        run_test_suite(streaming=False)


if __name__ == "__main__":
    main()
