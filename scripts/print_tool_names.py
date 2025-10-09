import asyncio
from typing import List
import os
import sys

# Ensure project root on sys.path
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(SCRIPT_DIR)
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

try:
    from src import pbixray_server_enhanced as srv  # type: ignore
except Exception as e:
    raise SystemExit(f"Failed to import server: {e}")

async def main():
    tools = await srv.list_tools()
    names = [t.name for t in tools]
    print("TOOL_COUNT:", len(names))
    for n in names:
        print(n)

if __name__ == "__main__":
    asyncio.run(main())
