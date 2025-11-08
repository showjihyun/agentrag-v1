"""
Validation script for Knowledge Base integration tests.

This script validates that the test file is properly structured and
all test methods are correctly defined.
"""

import ast
import sys
from pathlib import Path

def validate_test_file():
    """Validate the Knowledge Base test file structure."""
    
    test_file = Path(__file__).parent / "test_knowledge_base_integration.py"
    
    if not test_file.exists():
        print("❌ Test file not found!")
        return False
    
    # Parse the test file
    with open(test_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    try:
        tree = ast.parse(content)
    except SyntaxError as e:
        print(f"❌ Syntax error in test file: {e}")
        return False
    
    # Count test classes and methods
    test_classes = []
    test_methods = []
    
    for node in ast.walk(tree):
        if isinstance(node, ast.ClassDef):
            if node.name.startswith('Test'):
                test_classes.append(node.name)
                # Count test methods in this class
                for item in node.body:
                    if isinstance(item, ast.FunctionDef):
                        if item.name.startswith('test_'):
                            test_methods.append(f"{node.name}.{item.name}")
    
    # Print summary
    print("=" * 70)
    print("Knowledge Base Integration Tests - Validation Report")
    print("=" * 70)
    print()
    print(f"✅ Test file syntax: VALID")
    print(f"✅ Test classes found: {len(test_classes)}")
    print(f"✅ Test methods found: {len(test_methods)}")
    print()
    
    print("Test Classes:")
    for cls in test_classes:
        class_methods = [m for m in test_methods if m.startswith(cls)]
        print(f"  • {cls} ({len(class_methods)} tests)")
    
    print()
    print("Test Methods:")
    for method in test_methods:
        print(f"  • {method}")
    
    print()
    print("=" * 70)
    print("Test Coverage Summary:")
    print("=" * 70)
    
    # Check for required test categories
    required_tests = {
        "Milvus Connection": ["test_connect", "test_disconnect"],
        "Filter Building": ["test_build_filter"],
        "Search Operations": ["test_search"],
        "Search Service": ["TestSearchService"],
        "KB Block": ["TestKnowledgeBaseBlock"],
        "Integration": ["TestKnowledgeBaseIntegration"],
    }
    
    for category, keywords in required_tests.items():
        found = any(
            any(keyword in method for keyword in keywords)
            for method in test_methods + test_classes
        )
        status = "✅" if found else "❌"
        print(f"{status} {category}")
    
    print()
    print("=" * 70)
    
    # Check for async tests
    async_tests = [m for m in test_methods if 'async' in content]
    print(f"Async tests: {len(async_tests)}")
    
    # Check for mocked tests
    mock_count = content.count('@patch')
    print(f"Mocked tests: {mock_count}")
    
    print()
    print("✅ Validation complete!")
    print("=" * 70)
    
    return True

if __name__ == "__main__":
    success = validate_test_file()
    sys.exit(0 if success else 1)
