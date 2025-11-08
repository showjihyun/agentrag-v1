"""Verify all implemented tools are properly registered and configured.

This script checks:
1. Tool registration in catalog
2. Tool integration implementation
3. Required parameters and outputs
4. API configuration
"""

import sys
import os
import logging
from typing import Dict, List, Set

# Add backend to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)


def check_catalog_tools():
    """Check all tools defined in catalog."""
    logger.info("=" * 60)
    logger.info("STEP 1: Checking Tool Catalog")
    logger.info("=" * 60)
    
    try:
        from core.tools.catalog import ALL_TOOLS, TOOL_CATALOG
        
        logger.info(f"✓ Total tools in catalog: {len(ALL_TOOLS)}")
        
        # Count by category
        for category, tools in TOOL_CATALOG.items():
            logger.info(f"  - {category}: {len(tools)} tools")
        
        # List all tool IDs
        tool_ids = [tool['id'] for tool in ALL_TOOLS]
        logger.info(f"\n✓ Tool IDs in catalog:")
        for tool_id in sorted(tool_ids):
            logger.info(f"  - {tool_id}")
        
        return tool_ids, ALL_TOOLS
    except Exception as e:
        logger.error(f"✗ Failed to load catalog: {e}")
        return [], []


def check_tool_registry():
    """Check tools registered in ToolRegistry."""
    logger.info("\n" + "=" * 60)
    logger.info("STEP 2: Checking Tool Registry")
    logger.info("=" * 60)
    
    try:
        from core.tools.registry import ToolRegistry
        
        registered_tools = ToolRegistry.get_all_tools()
        logger.info(f"✓ Total registered tools: {len(registered_tools)}")
        
        # List registered tool IDs
        registered_ids = list(registered_tools.keys())
        logger.info(f"\n✓ Registered tool IDs:")
        for tool_id in sorted(registered_ids):
            logger.info(f"  - {tool_id}")
        
        return registered_ids, registered_tools
    except Exception as e:
        logger.error(f"✗ Failed to load registry: {e}")
        return [], {}


def check_integration_imports():
    """Check if all integration modules can be imported."""
    logger.info("\n" + "=" * 60)
    logger.info("STEP 3: Checking Integration Imports")
    logger.info("=" * 60)
    
    integration_modules = [
        'ai_tools',
        'search_tools',
        'communication_tools',
        'productivity_tools',
    ]
    
    imported = []
    failed = []
    
    for module_name in integration_modules:
        try:
            module = __import__(
                f'core.tools.integrations.{module_name}',
                fromlist=[module_name]
            )
            imported.append(module_name)
            logger.info(f"✓ {module_name} imported successfully")
        except Exception as e:
            failed.append((module_name, str(e)))
            logger.error(f"✗ {module_name} failed: {e}")
    
    return imported, failed


def compare_catalog_vs_registry(catalog_ids: List[str], registered_ids: List[str]):
    """Compare catalog tools vs registered tools."""
    logger.info("\n" + "=" * 60)
    logger.info("STEP 4: Comparing Catalog vs Registry")
    logger.info("=" * 60)
    
    catalog_set = set(catalog_ids)
    registry_set = set(registered_ids)
    
    # Tools in catalog but not registered
    missing_in_registry = catalog_set - registry_set
    if missing_in_registry:
        logger.warning(f"\n⚠ Tools in catalog but NOT registered ({len(missing_in_registry)}):")
        for tool_id in sorted(missing_in_registry):
            logger.warning(f"  - {tool_id}")
    else:
        logger.info("✓ All catalog tools are registered")
    
    # Tools registered but not in catalog
    extra_in_registry = registry_set - catalog_set
    if extra_in_registry:
        logger.info(f"\n✓ Extra registered tools not in catalog ({len(extra_in_registry)}):")
        for tool_id in sorted(extra_in_registry):
            logger.info(f"  - {tool_id}")
    
    # Tools in both
    in_both = catalog_set & registry_set
    logger.info(f"\n✓ Tools properly registered: {len(in_both)}")
    
    return missing_in_registry, extra_in_registry, in_both


def validate_tool_configs(registered_tools: Dict):
    """Validate tool configurations."""
    logger.info("\n" + "=" * 60)
    logger.info("STEP 5: Validating Tool Configurations")
    logger.info("=" * 60)
    
    issues = []
    
    for tool_id, tool_config in registered_tools.items():
        tool_issues = []
        
        # Check required fields
        if not tool_config.get('name'):
            tool_issues.append("Missing 'name'")
        if not tool_config.get('description'):
            tool_issues.append("Missing 'description'")
        if not tool_config.get('category'):
            tool_issues.append("Missing 'category'")
        
        # Check params
        params = tool_config.get('params', {})
        if not params:
            tool_issues.append("No parameters defined")
        
        # Check outputs
        outputs = tool_config.get('outputs', {})
        if not outputs:
            tool_issues.append("No outputs defined")
        
        # Check request config
        request = tool_config.get('request')
        if request:
            if not request.get('url'):
                tool_issues.append("Missing request URL")
            if not request.get('method'):
                tool_issues.append("Missing request method")
        
        if tool_issues:
            issues.append((tool_id, tool_issues))
            logger.warning(f"⚠ {tool_id}:")
            for issue in tool_issues:
                logger.warning(f"    - {issue}")
    
    if not issues:
        logger.info("✓ All tool configurations are valid")
    else:
        logger.warning(f"\n⚠ Found issues in {len(issues)} tools")
    
    return issues


def check_api_endpoints():
    """Check if tools API endpoint works."""
    logger.info("\n" + "=" * 60)
    logger.info("STEP 6: Checking API Endpoints")
    logger.info("=" * 60)
    
    try:
        from core.tools.catalog import get_tool_by_id, search_tools
        
        # Test get_tool_by_id
        test_tool = get_tool_by_id('youtube_search')
        if test_tool:
            logger.info("✓ get_tool_by_id() works")
        else:
            logger.warning("⚠ get_tool_by_id() returned None")
        
        # Test search_tools
        results = search_tools('search')
        logger.info(f"✓ search_tools() works - found {len(results)} results")
        
        return True
    except Exception as e:
        logger.error(f"✗ API endpoint check failed: {e}")
        return False


def generate_summary(
    catalog_ids: List[str],
    registered_ids: List[str],
    missing: Set[str],
    extra: Set[str],
    in_both: Set[str],
    config_issues: List,
    imported_modules: List,
    failed_modules: List
):
    """Generate final summary."""
    logger.info("\n" + "=" * 60)
    logger.info("FINAL SUMMARY")
    logger.info("=" * 60)
    
    logger.info(f"\n📊 Statistics:")
    logger.info(f"  - Tools in catalog: {len(catalog_ids)}")
    logger.info(f"  - Tools registered: {len(registered_ids)}")
    logger.info(f"  - Properly implemented: {len(in_both)}")
    logger.info(f"  - Missing implementation: {len(missing)}")
    logger.info(f"  - Extra implementations: {len(extra)}")
    
    logger.info(f"\n📦 Integration Modules:")
    logger.info(f"  - Successfully imported: {len(imported_modules)}")
    logger.info(f"  - Failed to import: {len(failed_modules)}")
    
    logger.info(f"\n⚙️  Configuration:")
    logger.info(f"  - Tools with issues: {len(config_issues)}")
    logger.info(f"  - Tools properly configured: {len(registered_ids) - len(config_issues)}")
    
    # Calculate success rate
    if catalog_ids:
        success_rate = (len(in_both) / len(catalog_ids)) * 100
        logger.info(f"\n✨ Implementation Rate: {success_rate:.1f}%")
    
    # Overall status
    if missing or config_issues or failed_modules:
        logger.warning("\n⚠️  Status: NEEDS ATTENTION")
        logger.warning("Some tools need implementation or have configuration issues")
    else:
        logger.info("\n✅ Status: ALL GOOD")
        logger.info("All tools are properly implemented and configured")
    
    return success_rate if catalog_ids else 0


def main():
    """Main verification function."""
    logger.info("\n🔍 Starting Tool Implementation Verification\n")
    
    try:
        # Step 1: Check catalog
        catalog_ids, catalog_tools = check_catalog_tools()
        
        # Step 2: Check registry
        registered_ids, registered_tools = check_tool_registry()
        
        # Step 3: Check imports
        imported_modules, failed_modules = check_integration_imports()
        
        # Step 4: Compare
        missing, extra, in_both = compare_catalog_vs_registry(catalog_ids, registered_ids)
        
        # Step 5: Validate configs
        config_issues = validate_tool_configs(registered_tools)
        
        # Step 6: Check API
        api_works = check_api_endpoints()
        
        # Generate summary
        success_rate = generate_summary(
            catalog_ids,
            registered_ids,
            missing,
            extra,
            in_both,
            config_issues,
            imported_modules,
            failed_modules
        )
        
        # Exit code
        if success_rate >= 80 and not failed_modules:
            logger.info("\n✅ Verification PASSED")
            return 0
        else:
            logger.warning("\n⚠️  Verification completed with warnings")
            return 1
            
    except Exception as e:
        logger.error(f"\n❌ Verification FAILED: {e}")
        import traceback
        traceback.print_exc()
        return 2


if __name__ == "__main__":
    sys.exit(main())
