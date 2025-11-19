# .NET Assembly Versions for Power BI MCP Server

This folder contains .NET assemblies required for advanced Power BI Desktop integration.

## Required Assemblies

### Core ADOMD.NET (Required for DMV queries)
- **Microsoft.AnalysisServices.AdomdClient.dll**
  - Version: 19.69.0.0 or later
  - Source: SQL Server Feature Pack or NuGet
  - Purpose: Execute DMV queries against Power BI Desktop's embedded SSAS

### AMO (Analysis Management Objects) - Optional but Recommended
- **Microsoft.AnalysisServices.Core.dll**
  - Version: 19.69.0.0 or later
  - Purpose: TOM model access, TMSL/TMDL export

- **Microsoft.AnalysisServices.Tabular.dll**
  - Version: 19.69.0.0 or later
  - Purpose: Tabular model operations

- **Microsoft.AnalysisServices.Tabular.Json.dll**
  - Version: 19.69.0.0 or later
  - Purpose: JSON serialization for TMSL

## Installation Methods

### Method 1: NuGet Packages (Recommended)
```powershell
# Run from project root
./lib/dotnet/install.ps1
```

### Method 2: Manual Download
1. Download from [Microsoft SQL Server Feature Pack](https://www.microsoft.com/en-us/download/details.aspx?id=56833)
2. Extract DLLs to this folder
3. Verify versions match requirements

### Method 3: Copy from SQL Server
If you have SQL Server Management Studio installed:
```
C:\Program Files\Microsoft SQL Server\150\SDK\Assemblies\
```

## Verification

Run verification script:
```powershell
python scripts/verify_dotnet_assemblies.py
```

Expected output:
```
✓ Microsoft.AnalysisServices.AdomdClient.dll (19.69.0.0)
✓ Microsoft.AnalysisServices.Core.dll (19.69.0.0)
✓ Microsoft.AnalysisServices.Tabular.dll (19.69.0.0)
```

## Version Compatibility

| Desktop Version | Min ADOMD Version | Min AMO Version |
|----------------|------------------|----------------|
| 2.120+         | 19.60.0.0       | 19.60.0.0     |
| 2.115-2.119    | 19.50.0.0       | 19.50.0.0     |
| 2.110-2.114    | 19.40.0.0       | 19.40.0.0     |

**Note:** Always use the latest available version for best compatibility.

## Troubleshooting

### DLLs Not Found
- Check this folder contains the DLLs
- Run `install.ps1` to auto-download
- Verify pythonnet is installed: `pip show pythonnet`

### Version Mismatch
- Update to latest Desktop
- Download matching ADOMD/AMO version
- Check compatibility table above

### Performance Analysis Unavailable
If you see "AMO SessionTrace not available":
- Ensure all three AMO DLLs are present
- Check versions match (all should be same major version)
- Restart Claude Desktop after adding DLLs

## Features Enabled by Assemblies

### With ADOMD Only
✓ Basic DMV queries
✓ Table/column/measure listing
✓ DAX execution
✓ VertiPaq stats

### With ADOMD + AMO
✓ All above features
✓ Performance tracing and timing analysis
✓ TMSL/TMDL export
✓ Calculation group management
✓ Advanced BPA checks

## License Notes

These assemblies are part of Microsoft SQL Server and covered by Microsoft's licensing terms. Ensure compliance with your organization's policies.
