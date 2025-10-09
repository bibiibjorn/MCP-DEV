# MCP-PowerBi-Finvision Quickstart (2025-10-09)

This MCP server lets your AI client safely explore an open Power BI Desktop model.

What you can do

- Connect to an open model and list tables/columns/measures
- Preview data (paginated), search objects, inspect data sources and M
- Run Best Practice Analyzer (when enabled)
- Analyze relationships, column cardinality, VertiPaq stats
- Generate docs and export TMSL/TMDL
- Validate RLS coverage and DAX syntax

Popular tools (friendly names)

- connection: detect powerbi desktop | connection: connect to powerbi
- list: tables | list: columns | list: measures | describe: table | preview: table
- search: objects | search: text in measures | get: data sources | get: m expressions
- analysis: best practices (BPA) | analysis: relationship/cardinality | analysis: storage compression
- usage: find unused objects
- export: compact schema | export: tmsl | export: tmdl | docs: generate

Tips

- Large results are paged; use page_size + next_token
- Some Desktop builds hide DMVs; server falls back to TOM or client-side filtering
- Use list_tools to see all tool names and schemas

Troubleshooting

- Use get_recent_logs and get_server_info
- For advanced features, ensure ADOMD/AMO DLLs exist in lib/dotnet
