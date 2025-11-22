"""
Check tool implementation completeness.
"""
import sys
import os

# Add backend to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.tools.tool_executor_registry import ToolExecutorRegistry


def check_implementation():
    """Check tool implementation completeness."""
    
    print("=" * 60)
    print("Tool Implementation Check")
    print("=" * 60)
    
    # Get all executors
    executors = ToolExecutorRegistry.list_executors()
    
    print(f"\n✅ Total executors registered: {len(executors)}")
    
    # Group by category
    by_category = {}
    for tool_id, executor in executors.items():
        category = getattr(executor, 'category', 'other')
        if category not in by_category:
            by_category[category] = []
        by_category[category].append({
            'tool_id': tool_id,
            'tool_name': executor.tool_name,
            'executor': executor
        })
    
    print(f"\n📁 Categories: {len(by_category)}")
    
    # Print by category
    for category, tools in sorted(by_category.items()):
        print(f"\n{category.upper()} ({len(tools)} tools):")
        for tool in sorted(tools, key=lambda x: x['tool_id']):
            print(f"  ✓ {tool['tool_id']:25} - {tool['tool_name']}")
    
    # Check required methods
    print("\n" + "=" * 60)
    print("Method Implementation Check")
    print("=" * 60)
    
    issues = []
    for tool_id, executor in executors.items():
        # Check execute method
        if not hasattr(executor, 'execute'):
            issues.append(f"❌ {tool_id}: Missing execute() method")
        
        # Check if it's async
        import inspect
        if hasattr(executor, 'execute'):
            if not inspect.iscoroutinefunction(executor.execute):
                issues.append(f"⚠️  {tool_id}: execute() is not async")
    
    if issues:
        print("\n⚠️  Issues found:")
        for issue in issues:
            print(f"  {issue}")
    else:
        print("\n✅ All executors have required methods")
    
    # Summary
    print("\n" + "=" * 60)
    print("Summary")
    print("=" * 60)
    print(f"Total Tools: {len(executors)}")
    print(f"Categories: {', '.join(sorted(by_category.keys()))}")
    print(f"Issues: {len(issues)}")
    
    if len(issues) == 0:
        print("\n✅ All checks passed!")
        return 0
    else:
        print(f"\n⚠️  {len(issues)} issues found")
        return 1


if __name__ == "__main__":
    exit_code = check_implementation()
    sys.exit(exit_code)
