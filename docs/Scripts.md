# Scripts catalog and recommendations

This page summarizes the scripts shipped in `scripts/`, what they do, and whether most users need them. No behavior changes are implied here.

Last updated: 2025-10-09

## Overview

- Common, keep for end users
- Advanced diagnostics, keep for power users
- Internal/maintenance, keep but hide from beginners
- Candidate for deprecation, ask maintainer before removal

## Scripts

- install_to_claude.ps1
  - Purpose: Register the MCP server with Claude Desktop by editing `%APPDATA%\Claude\claude_desktop_config.json`.
  - Audience: Everyone using Claude.
  - Status: Keep.

- install_to_chatgpt.ps1
  - Purpose: Generate a JSON snippet to add the MCP server in ChatGPT Desktop > Settings > Tools > Developer.
  - Audience: ChatGPT Desktop users.
  - Status: Keep.

- test_connection.ps1
  - Purpose: Quick environment check (Python, CLR, DLL presence) before wiring a client.
  - Audience: Everyone.
  - Status: Keep.

- print_tool_names.py
  - Purpose: List available tool names exposed by the server.
  - Audience: Developers/power users.
  - Status: Keep.

- quick_probe.py
  - Purpose: Minimal smoke: detect/connect, list tables/columns/measures counts.
  - Audience: Developers/power users.
  - Status: Keep.

- quick_export_compact.py
  - Purpose: Export compact schema after auto-detect/connect. Prints basic stats.
  - Audience: Developers/power users.
  - Status: Keep.

- export_columns_with_samples.py
  - Purpose: Export a flat table of all columns with a few sample values.
  - Notes: Config via env: PBIXRAY_FORMAT=csv|txt|xlsx, PBIXRAY_ROWS, PBIXRAY_EXTRAS.
  - Audience: Analysts/exporters.
  - Status: Keep.

- full_analysis_runner.py
  - Purpose: Run a comprehensive analysis and write JSON to `logs/`.
  - Audience: Power users; CI/ops.
  - Status: Keep.

- tool_compatibility_check.py
  - Purpose: Invoke a wide set of SAFE tools and record PASS/FAIL + timings to `logs/`.
  - Audience: Maintainers; CI smoke.
  - Status: Keep.

- usage_selftest.py
  - Purpose: Exercise usage analysis tools on a sample table/column.
  - Audience: Developers/power users.
  - Status: Keep.

- mini_test.py
  - Purpose: Quick calls to a few validators (model integrity, relationship/column cardinality). Requires a connection.
  - Audience: Developers.
  - Status: Keep.

- remove_unused.ps1
  - Purpose: Remove deprecated files that were previously part of the repo.
  - Audience: Maintainers.
  - Status: Keep; use with caution.

## Notes

- No destructive actions are performed by any script above except `remove_unused.ps1`, which deletes old files if present.
- For beginners, start with `install_to_claude.ps1` or `install_to_chatgpt.ps1`, then `test_connection.ps1`.
