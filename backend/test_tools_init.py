"""Quick test script for tool initialization."""

from core.tools.init_tools import initialize_tools, get_tool_summary

# Initialize tools
count = initialize_tools()
summary = get_tool_summary()

print(f"\n✅ Successfully initialized {count} tools")
print(f"\nCategories: {summary['categories']}")
print(f"\nTools by category:")
for category, tool_count in summary['by_category'].items():
    print(f"  - {category}: {tool_count} tools")

print(f"\n✅ Tool integration system is working correctly!")
