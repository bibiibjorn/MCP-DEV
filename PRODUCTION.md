# Production Deployment Guide

## Overview
This guide covers deploying MCP-PowerBi-Finvision server in production environments.

## Pre-Deployment Checklist

### ✅ Code Quality
- [ ] Run `black .` to format code
- [ ] Run `flake8` to check for linting issues
- [ ] Run `mypy core/` to check types
- [ ] Run `pytest` to ensure all tests pass
- [ ] Review and address all warnings

### ✅ Security
- [ ] Review `.gitignore` for sensitive files
- [ ] Ensure no hardcoded credentials
- [ ] Validate input validation is enabled
- [ ] Confirm rate limiting is configured
- [ ] Review logging to ensure no sensitive data exposure

### ✅ Performance
- [ ] Enable caching (set `performance.cache_ttl_seconds > 0`)
- [ ] Configure appropriate timeouts in `config/default_config.json`
- [ ] Review memory limits for large queries
- [ ] Test with production-sized Power BI models

### ✅ Monitoring
- [ ] Enable admin tools: `server.show_admin_tools: true` (temporarily for setup)
- [ ] Configure log file location
- [ ] Set up log rotation if needed
- [ ] Test performance metrics endpoints

## Installation Steps

### 1. Environment Setup

```bash
# Clone repository
git clone https://github.com/bibiibjorn/MCP-PowerBi-Finvision.git
cd MCP-PowerBi-Finvision

# Create virtual environment
python -m venv venv

# Activate virtual environment
# Windows:
venv\Scripts\activate
# Linux/Mac:
source venv/bin/activate

# Install production dependencies
pip install -r requirements.txt
```

### 2. Configuration

Create `config/local_config.json`:

```json
{
  "server": {
    "show_admin_tools": false,
    "log_level": "INFO"
  },
  "performance": {
    "cache_ttl_seconds": 300,
    "max_cache_size": 1000
  },
  "security": {
    "rate_limit_enabled": true,
    "input_validation_enabled": true
  },
  "features": {
    "bpa_enabled": true,
    "documentation_generation": true
  }
}
```

### 3. Testing

```bash
# Run server in test mode
python run_server.py

# Test connection (from another terminal with Claude Desktop or MCP client)
# Connect to Power BI Desktop instance
# Run basic operations to verify functionality
```

### 4. Claude Desktop Integration

Add to Claude Desktop configuration (`%APPDATA%\Claude\claude_desktop_config.json`):

```json
{
  "mcpServers": {
    "powerbi-finvision": {
      "command": "python",
      "args": [
        "C:\\path\\to\\MCP-PowerBi-Finvision\\run_server.py"
      ],
      "env": {
        "PYTHONIOENCODING": "utf-8"
      }
    }
  }
}
```

## Performance Tuning

### Cache Configuration

```json
{
  "performance": {
    "cache_ttl_seconds": 300,      // 5 minutes
    "max_cache_size": 1000,         // Max cached items
    "query_cache_enabled": true
  }
}
```

### Timeout Configuration

Timeouts are configured in `core/tool_timeouts.py`. To override:

```json
{
  "tool_timeouts": {
    "run_dax": 120,                 // 2 minutes for DAX queries
    "full_analysis": 600,           // 10 minutes for full analysis
    "generate_model_documentation_word": 300  // 5 minutes for docs
  }
}
```

### Rate Limiting

```json
{
  "rate_limiting": {
    "query_execution": 30,          // 30 queries per minute
    "metadata_fetch": 60,           // 60 metadata requests per minute
    "export": 10,                   // 10 exports per minute
    "connection": 5                 // 5 connection attempts per minute
  }
}
```

## Monitoring

### Enable Admin Tools (Temporarily)

```json
{
  "server": {
    "show_admin_tools": true
  }
}
```

Then access via MCP client:
- `server: info` - Server status and configuration
- `server: performance metrics` - Operation execution times
- `server: performance summary` - Overall performance stats
- `server: slow operations` - Operations exceeding thresholds
- `server: rate limiter stats` - Rate limiting statistics
- `server: runtime cache stats` - Cache hit/miss rates

### Log Monitoring

Logs are written to `logs/pbixray.log`. Monitor for:
- ERROR level messages (critical issues)
- WARNING level messages (slow operations, rate limiting)
- Performance degradation patterns

```bash
# Tail logs in real-time
tail -f logs/pbixray.log

# Search for errors
grep "ERROR" logs/pbixray.log

# Count warnings
grep -c "WARNING" logs/pbixray.log
```

## Security Best Practices

### 1. Input Validation
Always enabled by default. Validates:
- DAX query syntax and dangerous patterns
- File paths (prevents directory traversal)
- Table/column names (prevents injection)

### 2. Rate Limiting
Prevents resource exhaustion:
- Per-operation limits
- Per-minute token buckets
- Automatic throttling

### 3. Logging Security
- Never logs sensitive data
- Logs to file (not stdout - prevents MCP corruption)
- Structured log format for parsing

### 4. Network Security
- Runs over stdio (no exposed ports)
- Local connections only to Power BI Desktop
- No external network access required

## Troubleshooting

### Performance Issues

1. **Check slow operations:**
   ```
   Tool: server: slow operations
   Args: {"threshold": 1.0}
   ```

2. **Review cache stats:**
   ```
   Tool: server: runtime cache stats
   ```

3. **Increase cache TTL:**
   ```json
   {"performance": {"cache_ttl_seconds": 600}}
   ```

### Connection Issues

1. **Verify Power BI Desktop is running:**
   ```
   Tool: connection: detect powerbi desktop
   ```

2. **Check port availability:**
   - Power BI Desktop uses random ports (50000-60000)
   - Firewall must allow local connections

3. **Review logs:**
   ```
   Tool: server: recent logs
   Args: {"lines": 100}
   ```

### Memory Issues

1. **Limit query result sizes:**
   ```json
   {"limits": {"max_rows": 1000}}
   ```

2. **Reduce cache size:**
   ```json
   {"performance": {"max_cache_size": 500}}
   ```

3. **Monitor memory usage:**
   ```
   Tool: health_check
   ```

## Maintenance

### Regular Tasks

**Daily:**
- Monitor logs for errors
- Check performance metrics
- Verify cache hit rates

**Weekly:**
- Review slow operations
- Update dependencies if needed
- Clean old log files

**Monthly:**
- Performance audit
- Security review
- Update to latest version

### Updates

```bash
# Pull latest changes
git pull origin main

# Update dependencies
pip install -r requirements.txt --upgrade

# Test after update
pytest
```

## Rollback Procedure

If issues occur after deployment:

1. **Stop server** (close Claude Desktop or kill process)
2. **Revert to previous version:**
   ```bash
   git checkout <previous-commit>
   pip install -r requirements.txt
   ```
3. **Restore configuration:**
   ```bash
   cp config/local_config.backup.json config/local_config.json
   ```
4. **Restart server**
5. **Verify functionality**

## Support

- **Documentation:** `docs/PBIXRAY_Quickstart.md`
- **Issues:** https://github.com/bibiibjorn/MCP-PowerBi-Finvision/issues
- **Review Report:** `.claude/CODE_REVIEW_REPORT.md`

## Production Checklist Summary

- ✅ Virtual environment created
- ✅ Production dependencies installed
- ✅ Configuration customized
- ✅ Security settings verified
- ✅ Performance tuning applied
- ✅ Monitoring enabled (temporarily)
- ✅ Logs configured
- ✅ Integration tested
- ✅ Backup created
- ✅ Rollback procedure documented

**Recommendation:** Run in test mode for 24-48 hours before full production deployment.
