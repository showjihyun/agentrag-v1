"""Test custom_tools import"""
import sys
import os

# Add backend to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    from api.agent_builder import custom_tools
    print("✓ custom_tools module imported successfully")
    print(f"✓ Router object: {custom_tools.router}")
    print(f"✓ Router prefix: {custom_tools.router.prefix}")
    print(f"✓ Router tags: {custom_tools.router.tags}")
    
    # Count routes
    route_count = len(custom_tools.router.routes)
    print(f"✓ Number of routes: {route_count}")
    
    # List routes
    print("\nAvailable routes:")
    for route in custom_tools.router.routes:
        if hasattr(route, 'methods') and hasattr(route, 'path'):
            methods = ', '.join(route.methods)
            print(f"  {methods:10} {route.path}")
    
    print("\n✅ All checks passed! Router is ready.")
    
except Exception as e:
    print(f"❌ Error importing custom_tools: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
