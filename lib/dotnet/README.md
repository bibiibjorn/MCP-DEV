# AMO/TOM Assemblies for PBIXRay

To enable BPA, TMSL export/compare, and certain fallbacks on Power BI Desktop, place the following .NET assemblies in this folder:

Required DLLs (matching versions):
- Microsoft.AnalysisServices.Core.dll
- Microsoft.AnalysisServices.dll
- Microsoft.AnalysisServices.Tabular.dll
- (Optional for queries) Microsoft.AnalysisServices.AdomdClient.dll

Recommended source:
- Install the latest Microsoft.AnalysisServices.Tabular NuGet package (or Microsoft.AnalysisServices.retail.amd64) and copy the DLLs from the package's `lib/netstandard2.0` or appropriate `netX` folder.
- Alternatively, install SQL Server Feature Pack / SSMS that ships compatible AMO client libraries.

Version notes:
- For `JsonSerializer` and `JsonSerializeOptions` support (used in TMSL export and BPA), use a recent Tabular client version (2019+). If `JsonSerializeOptions` isn't present, PBIXRay falls back to `JsonSerializer.SerializeObject(model)` automatically.
- Ensure all three assemblies come from the same build/version to avoid `TypeLoadException` or missing method errors.

Placement:
- Put the DLLs in `lib/dotnet` (this folder). PBIXRay will attempt to load them on startup.

Troubleshooting:
- If you see errors like `cannot import name 'JsonSerializeOptions'`, update the Tabular client DLLs to a newer version.
- If ADOMD.NET is missing, some features still work, but query execution requires `Microsoft.AnalysisServices.AdomdClient.dll`.
- On locked-down environments, you can unblock files via file properties or PowerShell: `Unblock-File *.dll`.
