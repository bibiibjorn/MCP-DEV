# INSTALL.md — MCP-PowerBi-Finvision (Windows)

This guide gets you from zero to running in minutes, with both scripted and manual setup options. No admin rights required.

## Prerequisites

- Windows 10/11 (64-bit)
- Power BI Desktop (current recommended)
- .NET Framework 4.7.2+ (usually preinstalled)
- Claude Desktop or ChatGPT Desktop (with MCP support)
- ~200 MB free disk space

Tip: Install to a user-writable path. Avoid spaces/special characters in the path.

## 1) Get the files

- Extract/clone the folder to a stable location, e.g. `C:\Tools\pbixray-mcp-server`

## 2) Set up Python (venv)

From the project folder in Windows PowerShell:

```powershell
# Create and activate a local virtual environment
py -3 -m venv venv ; ./venv/Scripts/Activate.ps1

# Upgrade pip and install dependencies
python -m pip install --upgrade pip ; pip install -r requirements.txt
```

Notes:

- If `py` is not found, install Python 3.10+ from python.org and re-run.
- If execution policy blocks Activate.ps1, run as admin once:

```powershell
Set-ExecutionPolicy -Scope CurrentUser -ExecutionPolicy RemoteSigned
```

You should now have `venv\Scripts\python.exe` available.

## 3) Optional: quick environment check

In Windows PowerShell from the project folder:

```powershell
cd "C:\Tools\pbixray-mcp-server"; ./scripts/test_connection.ps1
```

This validates Python + runtime bits and prints next steps.

## 4) Configure the MCP client

Choose one path below.

### Option A — Scripted install for Claude (recommended)

From the project folder:

```powershell
./scripts/install_to_claude.ps1
```

Then fully restart Claude Desktop (quit from the tray/Task Manager and reopen).

What the script does:

- Writes `%APPDATA%\Claude\claude_desktop_config.json`
- Adds an MCP server named `MCP-PowerBi-Finvision`
- Command: `venv\\Scripts\\python.exe`
- Args: `src\\pbixray_server_enhanced.py`

### Option B — Manual install for Claude (no scripts)

1. Close Claude Desktop completely
1. Open the config file in a text editor:
   `%APPDATA%\Claude\claude_desktop_config.json`
   - If the file doesn’t exist, create it with:
     `{ "mcpServers": {} }`
1. Add the MCP server entry under `mcpServers` (adjust paths to your install dir):

```json
{
  "mcpServers": {
    "MCP-PowerBi-Finvision": {
      "command": "C:\\Tools\\pbixray-mcp-server\\venv\\Scripts\\python.exe",
      "args": [
        "C:\\Tools\\pbixray-mcp-server\\src\\pbixray_server_enhanced.py"
      ]
    }
  }
}
```

1. Save the file and restart Claude Desktop

Notes

- If you installed elsewhere, update both paths accordingly
- If `venv\\Scripts\\python.exe` doesn’t exist yet, start Claude anyway; it will prompt you to install requirements, or run: `venv\\Scripts\\pip.exe install -r requirements.txt`

### Option C — ChatGPT Desktop (with MCP)

ChatGPT Desktop supports MCP via a Developer JSON field in Settings.

1. Open ChatGPT Desktop
1. Go to Settings → Tools → Developer
1. Add a new tool with the following JSON, adjust the two paths to your install folder:

```json
{
  "name": "MCP-PowerBi-Finvision",
  "command": "C:\\Tools\\pbixray-mcp-server\\venv\\Scripts\\python.exe",
  "args": [
    "C:\\Tools\\pbixray-mcp-server\\src\\pbixray_server_enhanced.py"
  ]
}
```

1. Save, then restart ChatGPT Desktop.

## 5) Connect and test

1) Open Power BI Desktop and load a .pbix file
2) Wait ~10–15 seconds for the model to finish loading
3) In your AI client, say: “Detect my Power BI Desktop instances”
4) Then: “Connect to instance 0”
5) Ask: “What tables are in this model?”

If you see your tables, you’re set.

## Updating

- Back up your current folder, then replace with the new package
- If you changed the install path, rerun the installer or update the JSON (manual Claude)
- To refresh Python packages:

```powershell
./venv/Scripts/pip.exe install --upgrade -r requirements.txt
```

## Uninstalling / cleanup

1) Close the MCP client (Claude/ChatGPT)
2) Remove the MCP entry
   - Claude: edit `%APPDATA%\Claude\claude_desktop_config.json` and delete `MCP-PowerBi-Finvision`
   - ChatGPT: delete the tool under Settings → Tools → Developer
3) Delete the `pbixray-mcp-server` folder

Optional: remove logs under `logs/`.

## Troubleshooting

- “No instances detected” → Ensure a .pbix is open; wait ~10 seconds
- “Not connected” → Detect → Connect → Then run tools
- Claude doesn’t see the server → Re-run the installer or use manual JSON; restart Claude; verify `%APPDATA%\Claude\claude_desktop_config.json`
- Slow queries → Use `TOPN()` to limit DMV outputs; use performance tools to see SE vs FE time

If Claude/ChatGPT can’t launch the server

- Confirm these files exist and point to your install folder:
  - `venv\Scripts\python.exe`
  - `src\pbixray_server_enhanced.py`
- Try launching once from a terminal to surface errors:

```powershell
venv\Scripts\python.exe src\pbixray_server_enhanced.py --help
```

## Team distribution (optional)

Create a ready-to-share zip:

```powershell
cd "C:\Tools\pbixray-mcp-server"; ./scripts/package_for_distribution.ps1
```

Share the archive and link users to this INSTALL.md.
