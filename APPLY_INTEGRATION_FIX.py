#!/usr/bin/env python3
"""
MCP-PowerBi-Finvision Integration Fix Script
Automatically applies all necessary changes to integrate new modules.

Run from: C:\\Users\\bjorn.braet\\powerbi-mcp-servers\\MCP-PowerBi-Finvision
"""

import os
import re
from pathlib import Path

def fix_server_file():
    """Add missing imports and initializations to pbixray_server_enhanced.py"""
    server_path = Path("src/pbixray_server_enhanced.py")
    
    if not server_path.exists():
        print(f"❌ File not found: {server_path}")
        return False
    
    content = server_path.read_text(encoding='utf-8')
    
    # Check if already patched
    if 'from core.tool_timeouts import' in content:
        print("✅ Server file already patched")
        return True
    
    # 1. Add imports after existing core imports
    import_section = """from core.tool_timeouts import ToolTimeoutManager
from core.cache_manager import EnhancedCacheManager
from core.input_validator import InputValidator
from core.rate_limiter import RateLimiter

"""
    
    # Find insertion point (after other core imports)
    pattern = r"(from core\.agent_policy import AgentPolicy)"
    if re.search(pattern, content):
        content = re.sub(pattern, import_section + r"\1", content)
    else:
        # Fallback: add after all imports
        pattern = r"(from __version__ import __version__\n)"
        content = re.sub(pattern, r"\1\n" + import_section, content)
    
    # 2. Add manager initializations
    init_section = """
# Initialize enhanced managers
timeout_manager = ToolTimeoutManager(config.get('tool_timeouts', {}))
enhanced_cache = EnhancedCacheManager(config)
rate_limiter = RateLimiter(config.get('rate_limiting', {}))

"""
    
    # Add after connection_manager initialization
    pattern = r"(connection_manager = ConnectionManager\(\))"
    content = re.sub(pattern, r"\1" + init_section, content)
    
    # 3. Update agent_policy initialization
    old_policy = "agent_policy = AgentPolicy(config)"
    new_policy = """agent_policy = AgentPolicy(
    config,
    timeout_manager=timeout_manager,
    cache_manager=enhanced_cache,
    rate_limiter=rate_limiter
)"""
    content = content.replace(old_policy, new_policy)
    
    # 4. Add input validation to call_tool
    validation_code = """        # Input validation
        if 'table' in arguments:
            is_valid, error = InputValidator.validate_table_name(arguments['table'])
            if not is_valid:
                return [TextContent(type="text", text=json.dumps({
                    'success': False, 
                    'error': error,
                    'error_type': 'invalid_input'
                }, indent=2))]
        
        if 'query' in arguments:
            is_valid, error = InputValidator.validate_dax_query(arguments['query'])
            if not is_valid:
                return [TextContent(type="text", text=json.dumps({
                    'success': False,
                    'error': error,
                    'error_type': 'invalid_input'
                }, indent=2))]
        
        # Rate limiting
        if rate_limiter and not rate_limiter.allow_request(name):
            return [TextContent(type="text", text=json.dumps({
                'success': False,
                'error': 'Rate limit exceeded',
                'error_type': 'rate_limit',
                'retry_after': rate_limiter.get_retry_after(name)
            }, indent=2))]
        
"""
    
    # Add validation after try: in call_tool
    pattern = r"(@app\.call_tool\(\)\nasync def call_tool\(name: str, arguments: Any\) -> List\[TextContent\]:\n    try:\n        _t0 = time\.time\(\))"
    replacement = r"\g<0>\n        " + validation_code
    content = re.sub(pattern, replacement, content, flags=re.MULTILINE)
    
    # Write back
    server_path.write_text(content, encoding='utf-8')
    print("✅ Server file patched successfully")
    return True


def fix_agent_policy():
    """Update agent_policy.py __init__ signature"""
    policy_path = Path("core/agent_policy.py")
    
    if not policy_path.exists():
        print(f"❌ File not found: {policy_path}")
        return False
    
    content = policy_path.read_text(encoding='utf-8')
    
    # Check if already patched
    if 'timeout_manager=None' in content:
        print("✅ AgentPolicy already patched")
        return True
    
    # Update __init__ signature
    old_init = "def __init__(self, config):"
    new_init = "def __init__(self, config, timeout_manager=None, cache_manager=None, rate_limiter=None):"
    
    if old_init in content:
        content = content.replace(old_init, new_init)
        
        # Add manager assignments after self.config
        old_assignment = "        self.config = config"
        new_assignment = """        self.config = config
        self.timeout_manager = timeout_manager
        self.cache_manager = cache_manager
        self.rate_limiter = rate_limiter"""
        
        content = content.replace(old_assignment, new_assignment)
        
        policy_path.write_text(content, encoding='utf-8')
        print("✅ AgentPolicy patched successfully")
        return True
    else:
        print("⚠️ AgentPolicy __init__ not found in expected format")
        return False


def verify_files():
    """Verify all required files exist"""
    required_files = [
        "core/tool_timeouts.py",
        "core/cache_manager.py",
        "core/enhanced_error_handler.py",
        "core/rate_limiter.py",
        "core/input_validator.py"
    ]
    
    missing = []
    for file in required_files:
        if not Path(file).exists():
            missing.append(file)
    
    if missing:
        print(f"❌ Missing files: {', '.join(missing)}")
        return False
    
    print("✅ All required utility files present")
    return True


def main():
    print("=" * 60)
    print("MCP-PowerBi-Finvision Integration Fix")
    print("=" * 60)
    
    # Check we're in the right directory
    if not Path("src/pbixray_server_enhanced.py").exists():
        print("❌ Wrong directory! Run from: MCP-PowerBi-Finvision root")
        print(f"Current: {os.getcwd()}")
        return False
    
    # Verify files
    if not verify_files():
        print("\n❌ Missing required files")
        print("Need: enhanced_error_handler.py and rate_limiter.py")
        print("Copy from artifacts provided")
        return False
    
    # Apply fixes
    print("\nApplying fixes...")
    success = all([
        fix_server_file(),
        fix_agent_policy()
    ])
    
    if success:
        print("\n" + "=" * 60)
        print("✅ ALL FIXES APPLIED SUCCESSFULLY")
        print("=" * 60)
        print("\nNext steps:")
        print("1. Restart Claude Desktop")
        print("2. Test with: connection: connect to powerbi")
        print("3. Verify: admin: get rate limit stats")
        return True
    else:
        print("\n❌ Some fixes failed - check errors above")
        return False


if __name__ == "__main__":
    main()
