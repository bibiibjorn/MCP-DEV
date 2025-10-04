# PBIXRay Server V2 - Frequently Asked Questions (FAQ)

## General Questions

### What is PBIXRay Server V2?

PBIXRay Server V2 is a Model Context Protocol (MCP) server that allows Claude AI to analyze Power BI Desktop models. It provides deep insights into data models, DAX measures, Power Query code, and query performance with Storage Engine (SE) and Formula Engine (FE) breakdown.

### Do I need to install anything else?

No! The package is completely self-contained with:
- Python 3.13 in the `venv` folder
- All required Python packages
- Analysis Services DLLs
- Complete documentation

The only external requirement is .NET Framework 4.7.2+ which is typically pre-installed on Windows.

### Does this work with Power BI Service models?

No, this version only works with **Power BI Desktop** instances running locally on your machine. It connects to the local Analysis Services instance that Power BI Desktop creates when you open a .pbix file.

### Can I use this with .pbix files directly?

Not directly. You need to:
1. Open the .pbix file in Power BI Desktop
2. Wait for the model to load
3. Then use the server to detect and connect to the running instance

### Is my data secure?

Yes! All analysis happens **locally** on your machine. The server:
- Connects only to localhost (127.0.0.1)
- Doesn't send data to any external services
- Works completely offline
- Only Claude can access it via MCP protocol

---

## Installation & Setup

### Where should I extract the server?

Any location you have write access to. Common choices:
- `C:\Tools\pbixray-mcp-server`
- `C:\Users\<username>\powerbi-tools\pbixray-mcp-server`
- `D:\Development\pbixray-mcp-server`

Avoid paths with spaces or special characters.

### How do I know if it's installed correctly?

Run the test script:
```powershell
cd "C:\Tools\pbixray-mcp-server"
.\scripts\test_connection.ps1
```

You should see a list of available tools without errors.

### Why isn't Claude seeing the MCP server?

Common causes:
1. **Config file syntax error** - Validate JSON at JSONLint.com
2. **Wrong path** - Use absolute paths with double backslashes
3. **Didn't restart Claude** - Must fully close and reopen
4. **Config in wrong location** - Should be `%APPDATA%\Claude\claude_desktop_config.json`

### Can multiple people use the same installation?

Each user should have their own copy because:
- Claude Desktop config is per-user
- Paths may differ between users
- Virtual environment is user-specific

Use the `package_for_distribution.ps1` script to create copies for colleagues.

---

## Usage Questions

### How do I connect to a Power BI model?

1. Open Power BI Desktop with your .pbix file
2. Wait 10-15 seconds for the model to fully load
3. In Claude, say: "Detect my Power BI Desktop instances"
4. Claude will list detected instances
5. Say: "Connect to instance 0" (or whichever index)

### Why does detection find 0 instances?

Make sure:
- Power BI Desktop is actually running (check Task Manager for `PBIDesktop.exe`)
- A .pbix file is **opened** (not just Power BI Desktop)
- The model has finished loading (check status bar)
- Wait 10-15 seconds after opening the file

### Can I connect to multiple Power BI instances simultaneously?

The server connects to one instance at a time. To switch:
1. Detect instances again
2. Connect to a different index

### What DAX queries can I run?

Any valid DAX query! Examples:

**Simple value:**
```dax
EVALUATE ROW("Total Sales", [Total Sales Measure])
```

**Table expression:**
```dax
EVALUATE TOPN(100, Sales)
```

**Aggregation:**
```dax
EVALUATE
SUMMARIZECOLUMNS(
    Sales[Region],
    "Total", SUM(Sales[Amount])
)
```

---

## Performance Analysis

### What is SE vs FE analysis?

- **Storage Engine (SE):** Time spent reading data from compressed columns
- **Formula Engine (FE):** Time spent calculating DAX expressions

High SE time = data retrieval bottleneck  
High FE time = complex calculation bottleneck

### Why do I get "metrics_available: false"?

This happens when AMO (Analysis Management Objects) libraries can't capture detailed trace events. The server still gives you total execution time, which is useful for comparing query performance.

### How many runs should I use for performance analysis?

- **Quick test:** 1 run
- **Standard:** 3 runs (default)
- **Detailed:** 5 runs
- **Benchmarking:** 10+ runs

More runs = more accurate average, but takes longer.

### Should I clear cache for performance testing?

- **Cold cache test:** `clear_cache=True` - Shows worst-case performance
- **Warm cache test:** `clear_cache=False` - Shows best-case performance
- **Typical usage:** Run both to understand the range

---

## Troubleshooting

### Query returns "Not connected" error

You need to connect first:
```
1. detect_powerbi_desktop
2. connect_to_powerbi(index=0)
3. Then run your query
```

### DAX query fails with syntax error

Common issues:
- Missing single quotes around table names with spaces: `'Sales Table'`
- Incorrect column references: `Sales[Amount]` not `Sales.Amount`
- Forgot to wrap measure in ROW(): `EVALUATE ROW("Result", [Measure])`

Test the query in DAX Studio or Performance Analyzer first.

### Queries are very slow

Try:
- Use `TOPN(100, ...)` to limit results
- Filter data before aggregating
- Check table sizes with `get_vertipaq_stats()`
- Reduce the number of columns selected

### Connection drops unexpectedly

This can happen if:
- Power BI Desktop is refreshing data
- Model is being edited
- Power BI Desktop crashes

Solution: Detect and reconnect.

---

## Advanced Topics

### Can I use this for automated testing?

Yes! You can script queries using Python:

```python
import subprocess
import json

# Run DAX query
result = subprocess.run([
    r"C:\Tools\pbixray-mcp-server\venv\Scripts\python.exe",
    r"C:\Tools\pbixray-mcp-server\src\pbixray_server_enhanced.py",
    "--query", "EVALUATE ROW('Test', [Measure])"
], capture_output=True, text=True)

data = json.loads(result.stdout)
```

### How do I export the entire model structure?

Use `export_model_schema()` which returns:
- All tables
- All columns with data types
- All measures (names only, not expressions)
- All relationships

This is great for documentation or analysis.

### Can I modify the model through the server?

No, this is **read-only**. You can:
- Query data
- Analyze structure
- Test DAX
- Measure performance

You cannot:
- Add/remove tables
- Create measures
- Modify relationships
- Change data

### What's the difference between this and DAX Studio?

| Feature | PBIXRay V2 | DAX Studio |
|---------|------------|------------|
| AI Integration | ✅ Via Claude | ❌ No |
| Natural Language | ✅ Yes | ❌ No |
| SE/FE Analysis | ✅ Yes | ✅ Yes |
| Query Editor | ❌ No | ✅ Advanced |
| Model Documentation | ✅ Automatic | ⚠️ Manual |
| VertiPaq Analyzer | ✅ Yes | ✅ Yes |

They complement each other! Use Claude for exploration and questions, DAX Studio for detailed query development.

---

## Data & Privacy

### What data does the server access?

The server can access:
- Model metadata (table/column names, data types)
- DAX expressions (measures, calculated columns)
- Power Query M code
- Sample data when explicitly queried

It **cannot** access:
- Your actual data unless you query it
- Credentials or connection strings (only visible in M code)

### Does it log my queries?

Logs are stored locally in `logs/pbixray_server.log` and contain:
- Connection events
- Tool invocations
- Error messages
- Performance metrics

Logs are **not** sent anywhere. They stay on your machine.

### Can I use this on sensitive data?

Yes! Everything runs locally. However:
- Be aware that Claude's conversations may be stored by Anthropic
- Don't share screenshots with sensitive data
- Review what queries you ask Claude to run
- Consider using on sample/test data first

---

## Distribution & Sharing

### How do I share this with my team?

1. Run `.\scripts\package_for_distribution.ps1`
2. Share the generated ZIP file
3. Provide installation instructions from `README.md`

### Does each person need their own copy?

Yes, because:
- Claude Desktop config is per-user
- Virtual environment is user-specific
- Better isolation and troubleshooting

### Can I commit this to Git?

Yes! The `.gitignore` is already configured. Consider:
- **Committing venv:** Simpler for users (just clone and use)
- **Not committing venv:** Smaller repo, users run `pip install -r requirements.txt`

For enterprise: Don't commit venv, use a setup script.

### How do I update to a new version?

1. Backup your current folder
2. Extract the new version
3. Copy any custom configurations
4. Update Claude Desktop config if paths changed
5. Test with `.\scripts\test_connection.ps1`

---

## Performance & Limits

### What's the maximum model size it can handle?

Limited by Power BI Desktop itself. If Power BI can open it, the server can analyze it. However:
- Very large models (10GB+) may have slow query response
- Use TOPN() to limit result sets
- Performance analysis may timeout on complex queries

### How many rows can I query?

No hard limit, but recommended:
- Preview: 10-100 rows
- Analysis: 1,000-10,000 rows
- Large exports: Use Power BI's export features instead

### Can multiple instances run simultaneously?

Yes! You can:
- Run multiple Power BI Desktop instances
- The server will detect all of them
- Connect to any one at a time

### What if Power BI Desktop hangs during a query?

The query may timeout. To recover:
- Stop the query in Power BI Desktop (if possible)
- Close the problematic .pbix file
- Reopen and reconnect
- Use simpler queries with filters

---

## Development & Customization

### Can I modify the server code?

Absolutely! The source code is in `src/pbixray_server_enhanced.py`. You can:
- Add new tools
- Modify existing functionality
- Extend analysis capabilities

Just test thoroughly before distributing.

### How do I add a new tool?

1. Define the tool in `@app.list_tools()`
2. Implement handler in `@app.call_tool()`
3. Test with Claude
4. Update documentation

### Can I contribute improvements?

If this is a shared team project, yes! Use Git to:
- Create feature branches
- Submit pull requests
- Document changes
- Update version numbers

---

## Getting Help

### Where do I start if something doesn't work?

1. Check [TROUBLESHOOTING.md](TROUBLESHOOTING.md)
2. Review this FAQ
3. Run `.\scripts\test_connection.ps1`
4. Check logs in `logs/` folder
5. Test with a simple .pbix file

### How do I report a bug?

Document:
- What you were trying to do
- What happened vs. what you expected
- Error messages (check logs)
- Steps to reproduce
- Your environment (Windows version, Power BI version)

### Can I get training on using this?

Share these resources with your team:
- `README.md` - Overview and quick start
- `docs/QUICK_REFERENCE.md` - Command examples
- `docs/SETUP_GUIDE.md` - Installation
- This FAQ

Consider creating example queries relevant to your business.

---

## Best Practices

### What are some good starter questions for Claude?

1. "What tables are in my model?"
2. "Show me all measures in the Sales table"
3. "What relationships involve the Date table?"
4. "Preview 10 rows from the Customer table"
5. "Analyze the performance of this query: EVALUATE Sales"
6. "What are the largest tables in my model by storage size?"
7. "Search for all measures containing 'CALCULATE'"

### How should I structure complex queries?

**Start simple, then refine:**

```
❌ Bad: "Show me all sales by region and product with year-over-year growth"

✅ Good sequence:
1. "List all tables"
2. "Describe the Sales table"
3. "Show me measures in Sales"
4. "Run this DAX: EVALUATE TOPN(100, Sales)"
5. "Analyze performance of that query"
```

### What should I document about my models?

Use the server to generate documentation:
- Export model schema
- List all measures with descriptions
- Document relationships
- Capture VertiPaq stats for baseline performance

Save these as reference for onboarding or troubleshooting.

### How often should I analyze performance?

- **During development:** After major changes
- **Before deployment:** Final validation
- **Production issues:** When users report slowness
- **Regular audits:** Monthly or quarterly

---

## Comparison Questions

### PBIXRay vs Power BI External Tools?

**PBIXRay Server:**
- Natural language interaction via Claude
- Automated analysis and insights
- Great for exploration and learning
- No GUI

**Traditional External Tools (DAX Studio, Tabular Editor):**
- Advanced query editing
- Model modification capabilities
- Rich graphical interfaces
- Specialized features

**Best approach:** Use both! PBIXRay for AI-assisted analysis, external tools for detailed work.

### Should I use this or Power BI REST API?

Different purposes:
- **PBIXRay:** Local Power BI Desktop analysis
- **REST API:** Power BI Service (cloud) management and operations

They don't overlap - use the right tool for your context.

---

## Version & Compatibility

### What versions of Power BI Desktop are supported?

Any modern version (2020+). The server connects via Analysis Services protocol which is stable across versions.

### Does it work on MacOS or Linux?

No, Windows only because:
- Power BI Desktop is Windows-only
- Uses Windows-specific APIs (WMI)
- Requires .NET Framework

You could potentially use it with Power BI Desktop in a Windows VM.

### What Python version is required?

Python 3.10 or higher. The included `venv` has Python 3.13, which is recommended.

### Can I upgrade Python in the venv?

Yes, but easier to recreate:

```powershell
# Backup
Rename-Item venv venv.old

# Create new with system Python
python -m venv venv

# Install packages
.\venv\Scripts\pip.exe install -r requirements.txt

# Test
.\scripts\test_connection.ps1
```

---

## Common Workflows

### Model Health Check

```
1. Connect to model
2. export_model_schema - Get complete structure
3. get_vertipaq_stats - Check storage
4. list_measures - Review all measures
5. search_string("TODO") - Find incomplete work
```

### Performance Investigation

```
1. Run suspect query normally
2. analyze_query_performance with 5 runs
3. Check SE% vs FE%
4. If SE-heavy: review relationships and filters
5. If FE-heavy: review DAX complexity
6. get_vertipaq_stats for impacted tables
```

### Documentation Generation

```
1. export_model_schema - Save as JSON
2. list_measures - Export to CSV/Excel
3. get_data_sources - Document connections
4. list_relationships - Create diagram source
5. Preview sample data from key tables
```

### Measure Quality Audit

```
1. list_measures
2. search_string("CALCULATE") - Common patterns
3. search_string("FILTER") - Check for inefficiencies
4. search_string("--") - Find commented code
5. Test critical measures with performance analysis
```

---

## Tips & Tricks

### Speed up large model analysis

1. **Filter early:** Use WHERE clauses in DAX
2. **Limit columns:** Don't SELECT * 
3. **Use TOPN:** Limit result sets
4. **Batch operations:** Group similar queries
5. **Cache wisely:** Don't clear unnecessarily

### Find unused measures

```
1. list_measures
2. search_string for each measure name in other measures
3. Measures not referenced may be unused
4. Verify with business users before removing
```

### Compare query approaches

```
1. Write two versions of the same query
2. Run analyze_query_performance on each
3. Compare SE/FE breakdown
4. Choose the more efficient approach
5. Document the pattern for team
```

### Document model changes

Before major changes:
1. `export_model_schema` - Baseline
2. Make changes in Power BI Desktop
3. Reconnect and export again
4. Compare the two exports
5. Document what changed and why

### Create a model knowledge base

Ask Claude to:
1. "Summarize this model's structure"
2. "What are the key measures and what do they calculate?"
3. "Document the data sources"
4. "Create a table relationship diagram description"
5. Save these for onboarding new team members

---

## Scenarios & Solutions

### Scenario: New team member needs to understand a model

**Solution:**
1. Open the model in Power BI Desktop
2. Connect via Claude
3. Ask Claude: "Give me an overview of this Power BI model"
4. Follow up: "What are the main fact tables?"
5. "What measures are available for sales analysis?"
6. Export documentation for their reference

### Scenario: Report is slow, need to find the bottleneck

**Solution:**
1. Identify the slow visual's query (use Performance Analyzer in Power BI)
2. Copy the DAX query
3. Run: `analyze_query_performance(query="<DAX>", runs=5, clear_cache=True)`
4. Check SE vs FE breakdown
5. If SE-heavy (>70%): Review filters and relationships
6. If FE-heavy (>70%): Simplify DAX or add calculated columns
7. Use `get_vertipaq_stats` to check column compression

### Scenario: Need to validate measures after changes

**Solution:**
1. Before changes: Run test queries, save results
2. Make changes in Power BI Desktop
3. Reconnect to the model
4. Run same test queries
5. Compare results
6. Performance test critical measures

### Scenario: Onboarding to a new Power BI model

**Solution:**
Day 1 - Structure
- "What tables exist?"
- "What are the relationships?"
- "What measures are available?"

Day 2 - Data
- Preview key tables
- Check data quality with column summaries
- Understand date ranges and granularity

Day 3 - Business Logic
- Review measure definitions
- Understand calculation patterns
- Test queries to validate understanding

### Scenario: Model size optimization needed

**Solution:**
1. `get_vertipaq_stats()` - Identify large columns
2. Check: High cardinality? Poor compression?
3. Consider: 
   - Remove unused columns
   - Change data types
   - Split date/time columns
   - Use integer encoding for strings
4. Retest with `get_vertipaq_stats()`
5. Measure performance improvement

---

## Enterprise Considerations

### Can this be deployed organization-wide?

Yes! Consider:
1. **Central repository:** Git repo for version control
2. **Standard installation path:** e.g., `C:\Tools\PBIXRay`
3. **Automated deployment:** Use package script + PowerShell DSC
4. **Documentation site:** Internal wiki with examples
5. **Support process:** Designated support person/team

### How to ensure consistent usage?

1. **Training:** Onboard all users
2. **Standards:** Create query pattern guidelines
3. **Templates:** Provide example queries for common tasks
4. **Code reviews:** Review custom modifications
5. **Version control:** Track changes to server code

### Security considerations?

- **Network isolation:** Server only connects to localhost
- **Access control:** User must have access to .pbix file
- **Audit logging:** Logs stored locally (review retention policy)
- **Data classification:** Document what can be analyzed
- **Claude conversations:** May be stored by Anthropic (review their policy)

### Integration with existing tools?

The server can complement:
- **DAX Studio:** Use PBIXRay for exploration, DAX Studio for development
- **Tabular Editor:** PBIXRay for analysis, TE for model changes
- **Power BI Desktop:** PBIXRay provides Claude interface to desktop models
- **Azure DevOps:** Document findings in work items
- **Confluence/SharePoint:** Store exported model documentation

---

## Maintenance & Updates

### How do I check what version I have?

Check `config/server_config.json` or the main script header in `src/pbixray_server_enhanced.py`.

### When should I update?

- **Bug fixes:** As soon as available
- **New features:** When you need them
- **Security updates:** Immediately
- **Python/package updates:** Quarterly or when issues arise

### Backup before updating?

Yes! Use:
```powershell
$timestamp = Get-Date -Format "yyyyMMdd_HHmmss"
Copy-Item "C:\Tools\pbixray-mcp-server" "C:\Tools\pbixray-mcp-server_backup_$timestamp" -Recurse
```

### Can I roll back an update?

Yes, if you have a backup:
1. Stop Claude Desktop
2. Delete current installation
3. Restore from backup
4. Restart Claude Desktop
5. Test with `.\scripts\test_connection.ps1`

---

## Future & Roadmap

### What features might be added?

Potential enhancements:
- Model modification capabilities
- Automated optimization suggestions
- Comparative analysis between models
- Enhanced visualization generation
- Integration with version control
- Multi-model comparison
- Report analysis capabilities

### Can I request features?

Yes! Document:
- What you want to do
- Why it's useful
- Expected behavior
- Use cases

### Will this work with future Power BI versions?

As long as Power BI Desktop continues to use Analysis Services for the data model (which is fundamental to its architecture), the server should work. The protocol is stable and well-established.

---

## Quick Reference Card

### Connection Flow
```
detect → connect → query → analyze
```

### Essential Commands
```
detect_powerbi_desktop()
connect_to_powerbi(index=0)
list_tables()
run_dax_query(query="...")
analyze_query_performance(query="...")
```

### Troubleshooting Flow
```
1. Check Power BI is running
2. Verify model is loaded
3. Run detect_powerbi_desktop
4. Check logs in logs/ folder
5. Review TROUBLESHOOTING.md
```

### Performance Analysis Interpretation
```
SE > 70%: Storage bottleneck → Review filters/relationships
FE > 70%: Calculation bottleneck → Simplify DAX
Balanced: Optimal or complex scenario → Analyze deeper
```

---

## Final Tips

✅ **DO:**
- Keep Power BI Desktop running while using the server
- Test queries in Power BI first when developing complex DAX
- Use TOPN() to limit large result sets
- Document your findings from analysis
- Share useful query patterns with your team
- Keep the server updated

❌ **DON'T:**
- Try to connect without opening a .pbix file
- Run queries without filtering on very large tables
- Expect write/modify capabilities
- Share sensitive data in Claude conversations without review
- Modify core server code without testing
- Forget to restart Claude Desktop after config changes

---

**Last Updated:** 2025-10-04  
**Version:** 2.0 Enhanced

For more help, see:
- [README.md](../README.md)
- [QUICK_REFERENCE.md](QUICK_REFERENCE.md)
- [TROUBLESHOOTING.md](TROUBLESHOOTING.md)