import asyncio
from typing import List

try:
    from src.pbixray_server_enhanced import list_tools  # type: ignore
except Exception as e:
    raise SystemExit(f"Failed to import list_tools: {e}")

async def main():
    tools = await list_tools()
    names = [t.name for t in tools]
    print("TOOL_COUNT:", len(names))
    for n in names:
        print(n)

if __name__ == "__main__":
    asyncio.run(main())
