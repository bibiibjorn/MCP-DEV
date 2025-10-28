"""Test script to verify tool registration with numbered names"""
import sys
import os

# Add parent directory to path
script_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(script_dir)
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

# Import registry and handlers
from server.registry import get_registry
from server.handlers import register_all_handlers
from server.dispatch import ToolDispatcher

def test_tool_registration():
    """Test that all tools are properly registered with numbered names"""

    # Initialize registry
    registry = get_registry()
    register_all_handlers(registry)

    # Get all tools as MCP tools (with numbered names)
    mcp_tools = registry.get_all_tools_as_mcp()

    print(f"\n=== Registered Tools ({len(mcp_tools)} total) ===\n")

    for tool in mcp_tools:
        try:
            print(f"  {tool.name}")
            print(f"    Description: {tool.description[:80]}...")
            print()
        except UnicodeEncodeError:
            print(f"  {tool.name} (description contains unicode)")
            print()

    # Test dispatcher mapping
    print("\n=== Testing Dispatcher Mapping ===\n")
    dispatcher = ToolDispatcher()

    test_mappings = [
        '01_detect_pbi_instances',
        '01_connect_to_instance',
        '02_list_tables',
        '03_run_dax',
        '05_export_schema',
        '06_full_analysis'
    ]

    for numbered_name in test_mappings:
        internal_name = dispatcher._resolve_tool_name(numbered_name)
        has_handler = registry.has_tool(internal_name)
        status = "OK" if has_handler else "FAIL"
        print(f"  [{status}] {numbered_name} -> {internal_name} (handler exists: {has_handler})")

    print("\n=== Test Complete ===\n")

if __name__ == "__main__":
    test_tool_registration()
