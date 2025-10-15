#!/usr/bin/env python3
"""
Wrapper script to run MCP-PowerBi-Finvision server with correct PYTHONPATH.
This ensures bundled dependencies in venv/Lib/site-packages are found.
"""
import sys
import os
import site
from pathlib import Path

# Get the directory where this script is located
script_dir = Path(__file__).parent.absolute()

# Add bundled dependencies to Python path using site.addsitedir
# This properly handles .pth files and native extensions (.pyd files)
site_packages = script_dir / "venv" / "Lib" / "site-packages"
if site_packages.exists():
    site.addsitedir(str(site_packages))

# Now import and run the actual server
server_module = script_dir / "src" / "pbixray_server_enhanced.py"

# Execute the server module
with open(server_module, 'r', encoding='utf-8') as f:
    code = compile(f.read(), str(server_module), 'exec')
    exec(code)
