# PBIXRay Server V2 - Deployment Guide for Teams

**Version:** 2.0 Enhanced  
**Last Updated:** 2025-10-04  
**Target Audience:** IT Administrators, Team Leads

---

## 📋 Table of Contents

1. [Overview](#overview)
2. [Prerequisites](#prerequisites)
3. [Deployment Methods](#deployment-methods)
4. [Step-by-Step Deployment](#step-by-step-deployment)
5. [Verification](#verification)
6. [User Onboarding](#user-onboarding)
7. [Troubleshooting](#troubleshooting)
8. [Maintenance](#maintenance)

---

## Overview

This guide helps you deploy PBIXRay Server V2 to your team, enabling Claude AI integration with Power BI Desktop for all users.

### What Gets Deployed

- **Portable Python environment** with all dependencies
- **Analysis Services client libraries** (DLLs)
- **MCP server** for Claude integration
- **Documentation** and helper scripts
- **Configuration templates**

### Deployment Characteristics

- **Size:** ~110-150 MB per installation
- **Network:** No network dependencies (fully offline capable)
- **Permissions:** Standard user permissions (no admin required)
- **Installation Time:** 5-10 minutes per user
- **Configuration Time:** 2-3 minutes per user

---

## Prerequisites

### System Requirements

**Every user needs:**
- Windows 10/11 (64-bit)
- .NET Framework 4.7.2 or higher (usually pre-installed)
- Power BI Desktop (latest version recommended)
- Claude Desktop (latest version)
- ~200 MB free disk space

**Verify .NET Framework:**
```powershell
Get-ChildItem 'HKLM:\SOFTWARE\Microsoft\NET Framework Setup\NDP' -Recurse | 
Get-ItemProperty -Name Version -EA 0 | 
Where { $_.PSChildName -match '^(?!S)\p{L}'} | 
Select PSChildName, Version
```

Should show version 4.7.2 or higher.

---

## Deployment Methods

### Method 1: Individual Installation (Recommended for Small Teams)

**Best for:** 1-10 users  
**Effort:** Low  
**Control:** User-managed

Users extract and configure themselves using provided package.

### Method 2: Network Share Deployment (Recommended for Medium Teams)

**Best for:** 10-50 users  
**Effort:** Medium  
**Control:** Centralized package, user configuration

Share a network location with the package, users copy to their machines.

### Method 3: Automated Deployment (Recommended for Large Teams)

**Best for:** 50+ users  
**Effort:** High initial, low ongoing  
**Control:** Fully automated

Use PowerShell DSC, Group Policy, or deployment tools.

### Method 4: Cloned Installation (Quick for Uniform Environments)

**Best for:** Identical machine configurations  
**Effort:** Very low  
**Control:** Standardized

Clone from a working installation to similar machines.

---

## Step-by-Step Deployment

### Phase 1: Preparation (IT Admin)

#### 1.1 Create the Master Package

On your working installation:

```powershell
# Navigate to project
cd "C:\Users\bjorn.braet\powerbi-mcp-servers\pbixray-mcp-server"

# Run consolidation script to ensure everything is in place
.\Consolidate-PBIXRayServer.ps1 -CreateBackup

# Create distribution package
.\scripts\package_for_distribution.ps1
```

This creates: `PBIXRAY-V2-Portable.zip` (~110-150 MB)

#### 1.2 Verify the Package

```powershell
# Extract to test location
Expand-Archive -Path "PBIXRAY-V2-Portable.zip" -DestinationPath "C:\Temp\PBIXRay-Test"

# Run verification
cd "C:\Temp\PBIXRay-Test\pbixray-mcp-server"
.\Verify-Installation.ps1 -Verbose
```

Ensure all checks pass before deploying to users.

#### 1.3 Prepare Documentation

Create a deployment package with:
- `PBIXRAY-V2-Portable.zip`
- `QUICK_START_GUIDE.pdf` (create from README.md)
- `INSTALLATION_INSTRUCTIONS.pdf` (simplified steps)
- Support contact information

---

### Phase 2: Distribution

#### Option A: Network Share (Recommended)

```powershell
# Create share location
New-Item -ItemType Directory -Path "\\server\share\Software\PBIXRay-V2" -Force

# Copy package
Copy-Item "PBIXRAY-V2-Portable.zip" "\\server\share\Software\PBIXRay-V2\"

# Copy documentation
Copy-Item "*.pdf" "\\server\share\Software\PBIXRay-V2\"

# Set permissions (read-only for users)
```

Send users a link: `\\server\share\Software\PBIXRay-V2`

#### Option B: Email Distribution

For small teams, email the ZIP file with installation instructions.

**Email Template:**

```
Subject: New Tool: Power BI Analysis with Claude AI

Hi Team,

We're rolling out a new tool that enables Claude AI to analyze Power BI models.

📦 Package: Attached (or download from \\server\share\Software\PBIXRay-V2)
📖 Instructions: See attached PDF
⏱️ Installation Time: ~5 minutes
💡 Training: Optional session on [DATE]

Please install by [DEADLINE] and test with a sample .pbix file.

Questions? Contact [SUPPORT CONTACT]
```

#### Option C: Automated via PowerShell DSC

Create a DSC configuration:

```powershell
Configuration DeployPBIXRay {
    param([string[]]$ComputerName)
    
    Import-DscResource -ModuleName PSDesiredStateConfiguration
    
    Node $ComputerName {
        File PBIXRayFolder {
            Ensure = "Present"
            Type = "Directory"
            DestinationPath = "C:\Tools\PBIXRay-V2"
            SourcePath = "\\server\share\Software\PBIXRay-V2-Master"
            Recurse = $true
            MatchSource = $true
        }
    }
}
```

---

### Phase 3: User Installation

#### Standard Installation Path

Recommend a consistent path across all users:
- `C:\Tools\pbixray-mcp-server` (recommended)
- `C:\Users\<username>\Tools\pbixray-mcp-server` (alternative)

**User Installation Steps:**

```powershell
# 1. Extract the package
Expand-Archive -Path "PBIXRAY-V2-Portable.zip" -DestinationPath "C:\Tools"

# 2. Navigate to folder
cd "C:\Tools\pbixray-mcp-server"

# 3. Verify installation
.\Verify-Installation.ps1

# 4. Install to Claude Desktop
.\scripts\install_to_claude.ps1

# 5. Test
.\scripts\test_connection.ps1
```

#### Alternative: One-Click Installation Script

Create `Deploy-PBIXRay.ps1` for users:

```powershell
# One-Click PBIXRay Installation
param(
    [string]$InstallPath = "C:\Tools\pbixray-mcp-server",
    [string]$PackagePath = "\\server\share\Software\PBIXRay-V2\PBIXRAY-V2-Portable.zip"
)

Write-Host "Installing PBIXRay Server V2..." -ForegroundColor Cyan

# Extract
Expand-Archive -Path $PackagePath -DestinationPath (Split-Path $InstallPath) -Force

# Verify
& "$InstallPath\Verify-Installation.ps1"

# Configure Claude
& "$InstallPath\scripts\install_to_claude.ps1"

Write-Host "`nInstallation complete! Restart Claude Desktop." -ForegroundColor Green
Read-Host "Press Enter to exit"
```

---

### Phase 4: Configuration

#### Claude Desktop Configuration

The `install_to_claude.ps1` script handles this, but manual configuration:

**Location:** `%APPDATA%\Claude\claude_desktop_config.json`

```json
{
  "mcpServers": {
    "PBIXRAY-V2": {
      "command": "C:\\Tools\\pbixray-mcp-server\\venv\\Scripts\\python.exe",
      "args": [
        "C:\\Tools\\pbixray-mcp-server\\src\\pbixray_server_enhanced.py"
      ]
    }
  }
}
```

**Important:** Users must restart Claude Desktop after configuration.

---

## Verification

### Automated Verification

Every user should run:

```powershell
cd "C:\Tools\pbixray-mcp-server"
.\Verify-Installation.ps1 -Verbose
```

Expected result: 100% pass rate (all green checkmarks)

### Manual Verification

1. **Open Power BI Desktop** with a .pbix file
2. **Open Claude Desktop**
3. **Ask Claude:** "Detect my Power BI Desktop instances"
4. **Expected:** Claude lists detected instances
5. **Connect:** "Connect to instance 0"
6. **Query:** "What tables are in this model?"

If all steps work, installation is successful.

---

## User Onboarding

### Training Materials

Create or customize:

1. **Quick Start Video** (5 minutes)
   - Show detection, connection, and basic queries
   
2. **Cheat Sheet** (1 page)
   - Top 10 commands
   - Common workflows
   - Support contacts

3. **Use Case Examples** (document)
   - Model documentation
   - Performance analysis
   - Measure auditing

### Sample Training Session Outline (30 minutes)

**Introduction (5 min)**
- What is PBIXRay Server V2?
- How does it help with Power BI?

**Live Demo (15 min)**
- Detect and connect to Power BI
- Explore a model structure
- Run a performance analysis
- Search for measures

**Hands-On Practice (10 min)**
- Users try with sample .pbix file
- Support for any issues

**Q&A (5 min)**
- Common questions
- Support process
- Resources

---

## Troubleshooting

### Common Deployment Issues

#### Issue: "DLL not found" errors

**Cause:** DLLs not copied or path incorrect  
**Fix:**
```powershell
# Re-run consolidation on master package
.\Consolidate-PBIXRayServer.ps1

# Or manually copy
Copy-Item "C:\Source\fabric-toolbox\dotnet\*" "C:\Tools\pbixray-mcp-server\lib\dotnet\" -Force
```

#### Issue: "Python not found"

**Cause:** Virtual environment not included or corrupted  
**Fix:**
```powershell
# Recreate venv
cd "C:\Tools\pbixray-mcp-server"
python -m venv venv
.\venv\Scripts\pip.exe install -r requirements.txt
```

#### Issue: "Claude doesn't see the server"

**Cause:** Configuration not loaded or incorrect  
**Fix:**
```powershell
# Re-run installation script
.\scripts\install_to_claude.ps1

# Verify config
notepad "$env:APPDATA\Claude\claude_desktop_config.json"

# Restart Claude Desktop completely
```

### Getting User Logs

Ask users to provide:

```powershell
# Collect diagnostic info
$info = @{
    VerificationReport = Get-Content "C:\Tools\pbixray-mcp-server\VERIFICATION_REPORT.md"
    ClaudeConfig = Get-Content "$env:APPDATA\Claude\claude_desktop_config.json"
    ServerLog = Get-Content "C:\Tools\pbixray-mcp-server\logs\pbixray_server.log" -Tail 50
}

$info | ConvertTo-Json | Out-File "C:\Users\$env:USERNAME\Desktop\PBIXRay-Diagnostics.json"
```

---

## Maintenance

### Update Process

When a new version is released:

```powershell
# 1. Test new version
Expand-Archive -Path "PBIXRAY-V2.1-Portable.zip" -DestinationPath "C:\Temp\PBIXRay-Test"
cd "C:\Temp\PBIXRay-Test\pbixray-mcp-server"
.\Verify-Installation.ps1

# 2. Backup current production
Copy-Item "\\server\share\Software\PBIXRay-V2" "\\server\share\Software\PBIXRay-V2-Backup-$(Get-Date -Format 'yyyyMMdd')" -Recurse

# 3. Deploy new version
Copy-Item "PBIXRAY-V2.1-Portable.zip" "\\server\share\Software\PBIXRay-V2\"

# 4. Notify users
Send-MailMessage -To "team@company.com" -Subject "PBIXRay V2.1 Available" -Body "..."
```

### Health Monitoring

Create a monitoring script:

```powershell
# Check-PBIXRayHealth.ps1
$users = Get-Content "users.txt"

foreach ($user in $users) {
    $path = "\\$user\C$\Tools\pbixray-mcp-server"
    if (Test-Path $path) {
        Write-Host "$user : Installed" -ForegroundColor Green
    } else {
        Write-Host "$user : NOT INSTALLED" -ForegroundColor Red
    }
}
```

### Collecting Feedback

Create a feedback form or survey:
- Ease of installation
- Usefulness of features
- Performance issues
- Feature requests

---

## Advanced Scenarios

### Scenario 1: Airgapped Environment

For users without internet:

1. Package includes all dependencies (already done)
2. No external connections needed
3. Can work completely offline
4. Documentation included locally

### Scenario 2: Multiple Versions

Support different versions simultaneously:

```
C:\Tools\
├── pbixray-mcp-server-v2.0\
├── pbixray-mcp-server-v2.1\
└── pbixray-mcp-server-dev\
```

Users configure Claude for their preferred version.

### Scenario 3: Custom Branding

Modify for your organization:
- Update README.md with company branding
- Add company-specific examples
- Include internal support contacts
- Customize documentation

---

## Security Considerations

### Data Privacy

- All processing is local (no data sent externally)
- Claude conversations may be stored by Anthropic
- Users should follow company policies on AI tool usage

### Access Control

- No special permissions required
- Users can only analyze .pbix files they can open
- No network exposure (binds to localhost only)

### Audit Trail

- Logs stored locally in `logs/` folder
- Can be collected for compliance if needed
- Consider log rotation policy

---

## Success Metrics

Track deployment success:

- **Installation Rate:** % of target users installed
- **Activation Rate:** % of installed users actively using
- **Support Tickets:** Number of issues reported
- **User Satisfaction:** Survey feedback scores
- **Time Savings:** Estimated hours saved per user/month

---

## Support Model

### Tier 1: Self-Service
- Documentation in `docs/` folder
- `TROUBLESHOOTING.md` guide
- Internal wiki/SharePoint

### Tier 2: Peer Support
- Team Slack/Teams channel
- Share tips and tricks
- Known issues database

### Tier 3: Administrator Support
- For complex issues
- Version updates
- Custom modifications

---

## Checklist

Use this checklist for each deployment:

### Pre-Deployment
- [ ] Master package created and verified
- [ ] Documentation prepared
- [ ] Distribution method chosen
- [ ] Support process defined
- [ ] Training materials ready

### Deployment
- [ ] Package distributed
- [ ] Users notified
- [ ] Installation deadline set
- [ ] Support channel active
- [ ] Training sessions scheduled

### Post-Deployment
- [ ] Verify installations (sample users)
- [ ] Collect initial feedback
- [ ] Document common issues
- [ ] Update troubleshooting guide
- [ ] Measure adoption rate

### Ongoing
- [ ] Monitor for issues
- [ ] Regular check-ins with users
- [ ] Update documentation as needed
- [ ] Plan for version updates
- [ ] Gather feature requests

---

## Sample Communications

### Initial Announcement Email

```
Subject: 🚀 New Tool: AI-Powered Power BI Analysis with Claude

Team,

I'm excited to announce a new tool that will transform how we work with Power BI models.

**What is it?**
PBIXRay Server V2 enables Claude AI to analyze and explore Power BI Desktop models through natural language. Ask Claude questions about your models, analyze performance, and generate documentation - all conversationally.

**Key Benefits:**
• 📊 Explore models faster with natural language queries
• ⚡ Analyze DAX performance with SE/FE breakdown
• 📝 Auto-generate model documentation
• 🔍 Search across measures and code
• 🎓 Learn Power BI concepts through AI assistance

**Installation:**
1. Download from: \\server\share\Software\PBIXRay-V2
2. Extract to C:\Tools
3. Run Verify-Installation.ps1
4. Follow the prompts

**Time Required:** ~5 minutes

**Training Session:** [DATE] at [TIME] - [MEETING LINK]
Optional but recommended for new users.

**Questions?**
- Documentation: Inside the package
- Support: #pbixray-support channel or email support@company.com

Looking forward to seeing how you use this to accelerate your Power BI work!

[Your Name]
```

### Reminder Email (1 week before deadline)

```
Subject: Reminder: Install PBIXRay Server V2 by [DATE]

Hi Team,

Quick reminder to install the PBIXRay Server V2 by [DATE].

**Installation Status:**
✅ Installed: 45 users
⏳ Pending: 15 users

**Need Help?**
- Check the TROUBLESHOOTING.md guide
- Drop-in support hours: [TIMES]
- Post in #pbixray-support

**Already Installed?**
Share your experience and tips with the team!

Thanks,
[Your Name]
```

### Success Story Email

```
Subject: 💡 PBIXRay Success Story: 80% Faster Model Documentation

Team,

Great success story from [User Name]:

"I used PBIXRay to document our Sales model in 15 minutes - a task that used to take me 2+ hours! Claude helped me:
• Export the complete model schema
• Identify unused measures
• Document all relationships
• Create a summary for the business team

Total time saved: 1.75 hours per model!"

**Your Turn:**
Have you saved time with PBIXRay? Share your story in #pbixray-success

**Tip of the Week:**
Use "analyze_query_performance" to identify slow DAX queries. Claude will show SE vs FE breakdown and suggest optimizations.

[Your Name]
```

---

## FAQs for Administrators

### Can users install to different locations?

Yes, but recommend a standard path for consistency:
- Easier troubleshooting
- Simpler instructions
- Can use scripts for bulk operations

### What if a user doesn't have admin rights?

No admin rights needed! The installation is to user space (C:\Users\username\ or C:\Tools) and doesn't require system-level changes.

### How do we handle version updates?

Two approaches:
1. **In-place update:** Users replace their installation
2. **Side-by-side:** Keep old version, install new to different folder

Recommend side-by-side for major updates to allow rollback.

### Can we customize the server?

Yes! The Python source is open for modification:
- Add custom tools
- Modify existing functionality
- Integrate with company systems
- Add custom documentation

Just maintain a fork and document changes.

### How do we track usage?

Options:
1. **Survey users:** Monthly usage reports
2. **Claude Desktop logs:** If accessible
3. **Server logs:** Check `logs/` folder for activity
4. **IT inventory:** Scan for installed versions

### What's the update frequency?

Depends on your needs:
- **Bug fixes:** As needed (immediate)
- **Minor updates:** Quarterly
- **Major versions:** Annually or when significant features added

### Can we deploy via Intune/SCCM?

Yes! Create a package:
```powershell
# Intune/SCCM install script
$InstallPath = "C:\Tools\pbixray-mcp-server"
$PackagePath = "$PSScriptRoot\PBIXRAY-V2-Portable.zip"

Expand-Archive -Path $PackagePath -DestinationPath (Split-Path $InstallPath) -Force

# Verify installation
$verifyScript = Join-Path $InstallPath "Verify-Installation.ps1"
& $verifyScript

# Auto-configure Claude for user (runs at first login)
$autoConfig = @"
`$installScript = "C:\Tools\pbixray-mcp-server\scripts\install_to_claude.ps1"
if (Test-Path `$installScript) {
    & `$installScript
}
"@

Set-Content -Path "$env:APPDATA\Microsoft\Windows\Start Menu\Programs\Startup\ConfigurePBIXRay.ps1" -Value $autoConfig
```

---

## Performance Optimization Tips

### For Administrators

**Network Share Performance:**
- Use DFS for better distribution
- Enable read caching
- Consider BitLocker encryption

**Package Optimization:**
- Compress with maximum compression
- Use 7-Zip instead of Windows ZIP
- Split into smaller packages if needed

**Deployment Speed:**
- Deploy during off-hours
- Use local distribution points
- Parallel deployment to user groups

### For Users

**Installation Location:**
- Local disk (C:) faster than network drives
- SSD better than HDD
- Avoid OneDrive/cloud synced folders

---

## Compliance & Governance

### Data Classification

Document what data can be analyzed:
- ✅ Development/test models
- ✅ Sample data models
- ⚠️ Production models (with approval)
- ❌ Models with PII/sensitive data (unless approved)

### Usage Policy Template

```markdown
# PBIXRay Server V2 - Usage Policy

**Approved Uses:**
- Model exploration and documentation
- Performance analysis and optimization
- Learning and training
- Development and testing

**Restricted Uses:**
- Analysis of production data without approval
- Sharing of sensitive model structures externally
- Commercial use outside company scope

**User Responsibilities:**
- Follow company AI usage policies
- Protect sensitive information
- Report security concerns
- Use only on company-owned equipment

**Claude AI Integration:**
- Conversations may be stored by Anthropic
- Do not paste sensitive data directly to Claude
- Use generic examples when possible
- Follow company policies on AI tool usage
```

### Audit Requirements

If needed for compliance:

```powershell
# Create audit log
function Write-AuditLog {
    param($User, $Action, $Details)
    
    $logEntry = @{
        Timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
        User = $User
        Action = $Action
        Details = $Details
    }
    
    $logEntry | ConvertTo-Json -Compress | 
        Add-Content "\\server\audit\pbixray-audit.log"
}

# Log installations
Write-AuditLog -User $env:USERNAME -Action "INSTALL" -Details "Version 2.0"
```

---

## Cost-Benefit Analysis

### Implementation Costs

**One-Time Costs:**
- IT admin time: 8-16 hours
- Package preparation: 2-4 hours
- Documentation: 4-8 hours
- Training development: 4-8 hours
- **Total:** 18-36 hours

**Per-User Costs:**
- Installation time: 5-10 minutes
- Training: 30 minutes (optional)
- Learning curve: 1-2 hours
- **Total:** ~2.5 hours per user

**Ongoing Costs:**
- Support: 2-4 hours/month
- Updates: 4-8 hours/year
- **Total:** 28-56 hours/year

### Expected Benefits

**Time Savings per User:**
- Model documentation: 1-2 hours/model
- Performance analysis: 30-60 min/query
- Measure auditing: 1-2 hours/audit
- Learning/exploration: 2-4 hours/month

**Estimated ROI:**
- For a team of 20 analysts
- Average 2 hours/week saved per user
- 20 users × 2 hours × 50 weeks = 2,000 hours/year
- At $50/hour = $100,000 annual value
- Investment: ~$5,000 (100 hours × $50)
- **ROI: 2000%**

---

## Rollback Plan

If critical issues arise:

### Immediate Rollback (Emergency)

```powershell
# Disable in Claude Desktop
$configPath = "$env:APPDATA\Claude\claude_desktop_config.json"
$config = Get-Content $configPath | ConvertFrom-Json

# Remove PBIXRAY-V2
$config.mcpServers.PSObject.Properties.Remove("PBIXRAY-V2")

$config | ConvertTo-Json | Set-Content $configPath

# Notify users to restart Claude Desktop
```

### Restore Previous Version

```powershell
# If users backed up before update
Copy-Item "C:\Tools\pbixray-mcp-server_backup" `
          "C:\Tools\pbixray-mcp-server" -Recurse -Force

# Re-run verification
cd "C:\Tools\pbixray-mcp-server"
.\Verify-Installation.ps1
```

### Communication Template

```
Subject: URGENT: PBIXRay Server Temporary Rollback

Team,

We've identified a critical issue with PBIXRay Server V2.1 and are rolling back to V2.0.

**Action Required:**
1. Close Claude Desktop
2. Run: \\server\share\Scripts\Rollback-PBIXRay.ps1
3. Restart Claude Desktop

**Timeline:**
- Rollback: Immediate
- Fix expected: [DATE]
- Redeployment: [DATE]

**Impact:**
Minimal - previous version fully functional.

Sorry for the inconvenience. Questions? #pbixray-support

[Your Name]
```

---

## Future Roadmap Considerations

### Potential Enhancements

**Short-term (3-6 months):**
- Automated model comparison
- Custom report templates
- Integration with version control
- Enhanced visualization generation

**Medium-term (6-12 months):**
- Multi-model analysis
- Batch processing capabilities
- Custom plugin system
- Advanced collaboration features

**Long-term (12+ months):**
- Web-based interface option
- Enterprise management console
- Advanced analytics and insights
- Integration with Power BI Service

### Gathering Requirements

Create a feedback mechanism:
```powershell
# Feature request form
$request = @{
    User = $env:USERNAME
    Date = Get-Date
    Feature = Read-Host "Feature description"
    UseCase = Read-Host "How would you use this?"
    Priority = Read-Host "Priority (Low/Medium/High)"
}

$request | ConvertTo-Json | 
    Add-Content "\\server\share\PBIXRay\FeatureRequests.json"

Write-Host "Thank you! Your request has been logged." -ForegroundColor Green
```

---

## Appendix A: Command Reference

Quick reference for administrators:

```powershell
# Package creation
.\scripts\package_for_distribution.ps1

# Verification
.\Verify-Installation.ps1 -Verbose

# Installation to Claude
.\scripts\install_to_claude.ps1

# Test connection
.\scripts\test_connection.ps1

# Consolidation
.\Consolidate-PBIXRayServer.ps1 -CreateBackup

# Auto-fix issues
.\Verify-Installation.ps1 -FixIssues
```

---

## Appendix B: Network Share Setup

Complete network share configuration:

```powershell
# Create share
New-Item -ItemType Directory -Path "D:\Shares\PBIXRay-V2" -Force
New-SmbShare -Name "PBIXRay-V2" `
             -Path "D:\Shares\PBIXRay-V2" `
             -ReadAccess "Domain Users" `
             -FullAccess "IT-Admins"

# Set NTFS permissions
$acl = Get-Acl "D:\Shares\PBIXRay-V2"
$accessRule = New-Object System.Security.AccessControl.FileSystemAccessRule(
    "Domain Users","ReadAndExecute","ContainerInherit,ObjectInherit","None","Allow")
$acl.SetAccessRule($accessRule)
Set-Acl "D:\Shares\PBIXRay-V2" $acl

# Copy files
Copy-Item "PBIXRAY-V2-Portable.zip" "D:\Shares\PBIXRay-V2\"
Copy-Item "*.pdf" "D:\Shares\PBIXRay-V2\"
```

---

## Appendix C: Troubleshooting Decision Tree

```
Installation Issue
│
├─ Package won't extract
│  └─ Check: File corruption, permissions, disk space
│
├─ Verification fails
│  ├─ DLL missing → Run consolidation script
│  ├─ Python error → Recreate venv
│  └─ Path issues → Check relative paths in code
│
├─ Claude doesn't see server
│  ├─ Config syntax → Validate JSON
│  ├─ Wrong path → Update config
│  └─ Didn't restart → Restart Claude Desktop
│
├─ Can't detect Power BI
│  ├─ PBI not running → Start Power BI Desktop
│  ├─ No model loaded → Open .pbix file
│  └─ Wait longer → Allow 10-15 seconds
│
└─ Queries fail
   ├─ Not connected → Run detect + connect
   ├─ Syntax error → Check DAX syntax
   └─ Timeout → Limit result set with TOPN()
```

---

## Contact & Support

**Internal Support:**
- Email: support@company.com
- Teams: #pbixray-support
- Phone: x1234 (IT Helpdesk)

**Documentation:**
- Quick Start: `README.md`
- Full Guide: `docs/SETUP_GUIDE.md`
- Troubleshooting: `docs/TROUBLESHOOTING.md`
- FAQ: `docs/FAQ.md`

**External Resources:**
- Power BI Community
- Claude AI Documentation
- Microsoft Analysis Services Docs

---

**Document Version:** 1.0  
**Last Updated:** 2025-10-04  
**Owner:** IT Administration / BI Team  
**Review Schedule:** Quarterly

---

*This deployment guide should be reviewed and updated with each major version release of PBIXRay Server.*