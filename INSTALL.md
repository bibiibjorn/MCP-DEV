# INSTALL.md — PBIXRay MCP Server (Windows)

This guide gets you set up quickly on Windows with PowerShell. For enterprise/team rollout, you can adapt these steps to Intune/SCCM/DSC.

## Prerequisites

- Windows 10/11 (64-bit)
- .NET Framework 4.7.2+ (typically preinstalled)
- Power BI Desktop (current recommended)
- Claude Desktop
- ~200 MB disk space

Optional: Admin rights are NOT required; install to a user-writable path.

## 1) Get the files

- Obtain the packaged folder (or clone/extract) and place it somewhere stable. Recommended path:
  - `C:\Tools\pbixray-mcp-server`

Avoid paths with spaces or special characters.

## 2) Verify basics (optional but recommended)

Open Windows PowerShell and run from the project folder:

```powershell
cd "C:\Tools\pbixray-mcp-server"
./scripts/test_connection.ps1
```

This lists available tools and validates the local environment.

## 3) Configure Claude Desktop (or ChatGPT)

From the project folder, run:

```powershell
./scripts/install_to_claude.ps1
```

Then fully restart Claude Desktop (quit the app from the tray/Task Manager and reopen). The script adds an entry to your Claude Desktop config pointing to:

- Command: `venv\Scripts\python.exe`
- Args: `src\pbixray_server_enhanced.py`

For ChatGPT desktop (with MCP support), run:

```powershell
./scripts/install_to_chatgpt.ps1
```

Then restart the ChatGPT app.

## 4) Connect and test

1. Open Power BI Desktop and load a .pbix file
2. Wait 10–15 seconds for the model to finish loading
3. In Claude, say: “Detect my Power BI Desktop instances”
4. Then: “Connect to instance 0”
5. Ask: “What tables are in this model?”

If the server responds with your model’s tables, you’re good to go.

## Updating

- Safe update: back up your current folder, then replace with the new package.
- If you change the install path, rerun `./scripts/install_to_claude.ps1` so Claude points to the new location.
- To refresh Python packages (if needed):

```powershell
./venv/Scripts/pip.exe install --upgrade -r requirements.txt
```

## Uninstalling / Cleanup

1. Close Claude Desktop completely
2. Remove the Claude Desktop MCP entry (or rerun `install_to_claude.ps1 -Remove` if supported)
3. Delete the `pbixray-mcp-server` folder

Optionally remove logs under `logs/`.

## Troubleshooting quick tips

- “No instances detected”: ensure Power BI Desktop is open with a .pbix file and wait a few seconds
- “Not connected”: detect → connect → then run queries
- Claude doesn’t see the server: rerun `install_to_claude.ps1`, verify `%APPDATA%\Claude\claude_desktop_config.json`, and restart Claude
- Slow queries: use `TOPN()` to limit rows; check SE vs FE via performance analysis

## Team distribution (optional)

Create a ready-to-share zip:

```powershell
cd "C:\Tools\pbixray-mcp-server"
./scripts/package_for_distribution.ps1
```

Share the resulting archive with users and point them to this INSTALL.md.
