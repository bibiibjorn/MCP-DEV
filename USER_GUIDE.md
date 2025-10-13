# User Installation Guide

**Simple, step-by-step guide to get MCP-PowerBi-Finvision running in 5 minutes**

Version: 2.4.0 | Platform: Windows 10/11

---

## What You Need

- Windows 10 or 11 (64-bit)
- Python 3.10 or higher ([Download here](https://www.python.org/downloads/) if needed)
- Power BI Desktop ([Download here](https://powerbi.microsoft.com/desktop/))
- Claude Desktop or ChatGPT Desktop
- 5 minutes of your time

---

## Installation (The Easy Way)

### Step 1: Extract Files

1. Download and extract the MCP-PowerBi-Finvision folder
2. Move it to a simple location without spaces:

   ```text
   ✅ Good: C:\Tools\MCP-PowerBi-Finvision
   ✅ Good: C:\MCP-Servers\PowerBI
   ❌ Bad:  C:\My Documents\Power BI Tools
   ❌ Bad:  C:\Users\YourName\Downloads\...
   ```

### Step 2: Run Setup Script

1. Open the folder in File Explorer
2. Hold **Shift** and **right-click** in the empty space
3. Select **"Open PowerShell window here"**
4. Type this and press Enter:

   ```powershell
   .\setup.ps1
   ```

5. Follow the prompts:
   - It will check Python (install if needed)
   - Create a virtual environment (fresh on your machine)
   - Install dependencies (takes 2-5 minutes)
   - Ask if you want .NET assemblies (say Yes for full features)
   - Ask which AI client you use (pick Claude or ChatGPT)

**That's it!** Everything is configured automatically.

### Step 3: Restart Your AI Client

- **Claude Desktop**: Right-click tray icon → Quit → Reopen
- **ChatGPT Desktop**: Fully close and reopen

---

## First Time Use

1. **Open Power BI Desktop** with any .pbix file
2. **Wait 10-15 seconds** for the model to load completely
3. **In your AI client**, try these commands:

   ```text
   Detect my Power BI Desktop instances
   ```

   You should see: `Found 1 instance: [Port: xxxxx]`

   ```text
   Connect to instance 0
   ```

   You should see: `Successfully connected`

   ```text
   List all tables
   ```

   You should see your table names!

**🎉 Success!** You're ready to analyze your models.

---

## Common Issues

### "Python not found"

**Solution:** Install Python from [python.org](https://www.python.org/downloads/)
- ✅ Check "Add Python to PATH" during installation
- Restart PowerShell after installing

### "Execution policy error"

**Solution:** Run this once in PowerShell (as admin):

```powershell
Set-ExecutionPolicy -Scope CurrentUser -ExecutionPolicy RemoteSigned
```

### "No Power BI instances detected"

**Solution:**
- Make sure Power BI Desktop is actually open with a file loaded
- Wait 10-15 seconds after opening the file
- Check the status bar shows "Ready" not "Loading..."

### AI client doesn't see the server

**Solution:**
- Verify the setup script said "SUCCESS"
- Make sure you fully restarted the AI client (not just minimize)
- Check Task Manager and kill any lingering processes

---

## Manual Installation (If Script Fails)

If the automated script doesn't work, see [INSTALL.md](INSTALL.md) for detailed manual steps.

**Key requirement:** The configuration MUST use **full absolute paths** with **double backslashes** (`\\`):

```json
{
  "command": "C:\\Tools\\MCP-PowerBi-Finvision\\venv\\Scripts\\python.exe",
  "args": ["C:\\Tools\\MCP-PowerBi-Finvision\\src\\pbixray_server_enhanced.py"]
}
```

Never use relative paths like `./venv/...` - they won't work!

---

## What to Ask Your AI

Once connected, try these:

```text
"Search for measures containing CALCULATE"
"Analyze this DAX: SUM(Sales[Amount])"
"Export a compact schema"
"Find unused objects in the model"
"Show me rate limit statistics"
"Generate documentation"
```

See [README.md](README.md) for full feature list.

---

## Updating

To update to a new version:

1. Backup your current folder
2. Extract the new version to the same location (overwrite)
3. Run the setup script again:

   ```powershell
   .\setup.ps1
   ```

---

## Uninstalling

1. **Remove from AI client:**
   - Claude: Edit `%APPDATA%\Claude\claude_desktop_config.json` and delete the MCP-PowerBi-Finvision entry
   - ChatGPT: Settings → Tools → Developer → Remove the tool

2. **Delete the folder:**
   - Just delete `C:\Tools\MCP-PowerBi-Finvision` (or wherever you installed it)

---

## Why Virtual Environment?

**Q:** Why doesn't the venv come with the download?

**A:** Virtual environments are machine-specific:
- They contain paths specific to YOUR computer
- They're tied to YOUR Python version
- Including them would make the download 200 MB instead of 50 KB
- Creating fresh ensures compatibility

The `setup.ps1` script handles this automatically!

---

## Need Help?

- **Full documentation:** [README.md](README.md)
- **Technical details:** [INSTALL.md](INSTALL.md)
- **Report issues:** [GitHub Issues](https://github.com/bibiibjorn/MCP-PowerBi-Finvision/issues)

---

**Happy analyzing!** 🎉
