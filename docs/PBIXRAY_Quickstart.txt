# MCP-PowerBi-Finvision Quickstart Guide (2025-10-09)

MCP-PowerBi-Finvision is a Model Context Protocol (MCP) server for Power BI Desktop. It lets tools/agents inspect and analyze your open model safely.

What you can do:
- Connect to an open Power BI Desktop model
- List tables/columns/measures and preview data
- Search objects and inspect data sources and M expressions
- Run Best Practice Analyzer (BPA) on the model
- Analyze relationships, column cardinality, VertiPaq stats
- Generate documentation and export TMSL/TMDL
- Validate RLS coverage and DAX syntax

Popular tools (friendly names):
- connection: detect powerbi desktop | connection: connect to powerbi
- list: tables | list: columns | list: measures | describe: table | preview: table
- search: objects | search: text in measures | get: data sources | get: m expressions
- analysis: best practices (BPA) | analysis: relationship/cardinality | analysis: storage compression
- usage: find unused objects | usage: column heatmap
- export: compact schema | export: tmsl | export: tmdl | docs: generate

Tips:
- Large results are paged; use page_size + next_token
- Some Desktop builds hide DMVs; the server falls back to TOM or client-side filtering
- Use list_tools to see all tool names and schemas

Troubleshooting:
- Use get_recent_logs and get_server_info
- Ensure ADOMD/AMO DLLs exist in lib/dotnet for advanced features