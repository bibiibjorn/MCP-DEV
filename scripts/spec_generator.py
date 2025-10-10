#!/usr/bin/env python3
"""
Rapid mockup generator that leans on the MCP visualization tools to produce
both an embeddable HTML dashboard and Vega-Lite specs you can remix elsewhere.

Example:
    python scripts/spec_generator.py --html exports/mockups/gallery.html \
        --specs exports/mockups/specs.json --page-title "Finance Mockups"
"""

import argparse
import json
import sys
from pathlib import Path
from typing import Any, Dict, Optional

import anyio
from mcp.client.session import ClientSession
from mcp.client.stdio import StdioServerParameters, stdio_client
from mcp.types import TextContent

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SERVER_SCRIPT = PROJECT_ROOT / "src" / "pbixray_server_enhanced.py"


async def call_json(session: ClientSession, tool: str, arguments: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """
    Invoke an MCP tool and parse the JSON payload returned in the text block.
    """
    result = await session.call_tool(tool, arguments or {})
    if result.isError:
        raise RuntimeError(f"{tool} failed with MCP error")
    for block in result.content:
        if isinstance(block, TextContent):
            return json.loads(block.text)
    raise RuntimeError(f"{tool} returned no text result")


async def generate_gallery(args: argparse.Namespace) -> None:
    """Spin up the MCP server, render a mockup, and persist html/spec assets."""
    server = StdioServerParameters(
        command=str(sys.executable),
        args=[str(SERVER_SCRIPT)],
        cwd=str(PROJECT_ROOT),
    )

    async with stdio_client(server) as streams:
        async with ClientSession(*streams) as session:
            await session.initialize()
            detect = await call_json(session, "detect_powerbi_desktop")
            if detect.get("total_instances", 0) == 0:
                raise RuntimeError("No Power BI Desktop instances detected. Open your PBIX model first.")

            connected = await call_json(session, "connect_to_powerbi", {"model_index": args.model_index})
            if not connected.get("success"):
                raise RuntimeError(connected.get("error") or "Unable to connect to Power BI Desktop.")

            payload: Dict[str, Any] = {
                "request_type": args.request_type,
                "library": args.library,
                "page_title": args.page_title,
                "max_rows": args.max_rows,
                "sample_rows": args.sample_rows,
            }
            if args.table:
                payload["tables"] = args.table

            result = await call_json(session, "viz_render_html_mockup", payload)
            if not result.get("success"):
                raise RuntimeError(result.get("error") or "Mockup generation failed.")

            html_text = result.get("html") or ""
            html_path = Path(args.html).resolve()
            html_path.parent.mkdir(parents=True, exist_ok=True)
            html_path.write_text(html_text, encoding="utf-8")

            specs = result.get("vega_specs")
            specs_path = Path(args.specs).resolve()
            specs_path.parent.mkdir(parents=True, exist_ok=True)
            specs_path.write_text(json.dumps(specs or [], indent=2), encoding="utf-8")

            if args.layout:
                layout_path = Path(args.layout).resolve()
                layout_path.parent.mkdir(parents=True, exist_ok=True)
                layout_path.write_text(json.dumps(result.get("layout") or {}, indent=2), encoding="utf-8")

            print(f"Wrote HTML gallery to {html_path}")
            print(f"Wrote {len(specs or [])} Vega-Lite specs to {specs_path}")
            if args.layout:
                print(f"Wrote layout blueprint to {layout_path}")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Generate HTML + Vega-Lite mockups via the MCP visualization tools.")
    parser.add_argument("--html", default=str(PROJECT_ROOT / "exports" / "mockups" / "gallery.html"), help="Output HTML file path.")
    parser.add_argument("--specs", default=str(PROJECT_ROOT / "exports" / "mockups" / "specs.json"), help="Output Vega-Lite specs file path.")
    parser.add_argument("--layout", help="Optional path to write the layout blueprint JSON.", default=None)
    parser.add_argument("--page-title", default="Power BI Mockups", help="Title to render at the top of the gallery.")
    parser.add_argument("--request-type", choices=["overview", "executive_summary", "operational", "financial", "custom"], default="overview")
    parser.add_argument("--library", choices=["vega-lite", "chartjs"], default="vega-lite", help="Visualization library to render in the HTML output.")
    parser.add_argument("--model-index", type=int, default=0, help="Power BI model index to connect to (after detection).")
    parser.add_argument("--max-rows", type=int, default=100, help="Maximum rows per underlying query.")
    parser.add_argument("--sample-rows", type=int, default=40, help="Sample size used by the viz tooling.")
    parser.add_argument("--table", action="append", help="Optional table name(s) to focus the dashboard on. Repeat for multiple tables.")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    anyio.run(generate_gallery, args, backend="trio")


if __name__ == "__main__":
    main()
