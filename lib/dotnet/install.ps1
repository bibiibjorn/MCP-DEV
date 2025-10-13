# Auto-install .NET assemblies for Power BI MCP Server
# Downloads ADOMD.NET and AMO from NuGet

$ErrorActionPreference = "Stop"
$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path

Write-Host "==================================================" -ForegroundColor Cyan
Write-Host "Power BI MCP Server - .NET Assembly Installer" -ForegroundColor Cyan
Write-Host "==================================================" -ForegroundColor Cyan
Write-Host ""

# NuGet packages
$packages = @{
    "Microsoft.AnalysisServices.AdomdClient.NetCore.retail.amd64" = "19.81.2"
    "Microsoft.AnalysisServices.retail.amd64" = "19.81.2"
}

# Check if assemblies already exist
$existingDlls = @(
    "Microsoft.AnalysisServices.AdomdClient.dll",
    "Microsoft.AnalysisServices.Core.dll",
    "Microsoft.AnalysisServices.Tabular.dll"
)

$allExist = $true
foreach ($dll in $existingDlls) {
    if (-not (Test-Path (Join-Path $scriptDir $dll))) {
        $allExist = $false
        break
    }
}

if ($allExist) {
    Write-Host "All required assemblies already present:" -ForegroundColor Green
    foreach ($dll in $existingDlls) {
        Write-Host "  ✓ $dll" -ForegroundColor Green
    }
    Write-Host ""
    Write-Host "Run verify_dotnet_assemblies.py to check versions" -ForegroundColor Yellow
    exit 0
}

# Create temp directory
$tempDir = Join-Path $env:TEMP "powerbi-mcp-dotnet"
if (Test-Path $tempDir) {
    Remove-Item $tempDir -Recurse -Force
}
New-Item -ItemType Directory -Path $tempDir | Out-Null

Write-Host "Downloading packages..." -ForegroundColor Yellow

foreach ($package in $packages.GetEnumerator()) {
    $packageName = $package.Key
    $version = $package.Value
    
    Write-Host "  Downloading $packageName $version..." -ForegroundColor Gray
    
    $nugetUrl = "https://www.nuget.org/api/v2/package/$packageName/$version"
    $nupkgPath = Join-Path $tempDir "$packageName.$version.nupkg"
    
    try {
        Invoke-WebRequest -Uri $nugetUrl -OutFile $nupkgPath -UseBasicParsing
    }
    catch {
        Write-Host "  ERROR: Failed to download $packageName" -ForegroundColor Red
        Write-Host "  $_" -ForegroundColor Red
        continue
    }
    
    # Extract (nupkg is a zip file)
    $extractPath = Join-Path $tempDir $packageName
    Expand-Archive -Path $nupkgPath -DestinationPath $extractPath -Force
    
    Write-Host "  ✓ Downloaded and extracted" -ForegroundColor Green
}

Write-Host ""
Write-Host "Copying assemblies..." -ForegroundColor Yellow

# Map of source paths to find DLLs
$searchPaths = @(
    "lib\net472",
    "lib\netstandard2.0",
    "lib\net6.0",
    "runtimes\win\lib\netstandard2.0"
)

$copiedFiles = @()

foreach ($dll in $existingDlls) {
    $found = $false
    
    foreach ($package in $packages.Keys) {
        $extractPath = Join-Path $tempDir $package
        
        foreach ($searchPath in $searchPaths) {
            $dllPath = Join-Path $extractPath "$searchPath\$dll"
            
            if (Test-Path $dllPath) {
                Copy-Item $dllPath $scriptDir -Force
                $copiedFiles += $dll
                $found = $true
                Write-Host "  ✓ Copied $dll" -ForegroundColor Green
                break
            }
        }
        
        if ($found) { break }
    }
    
    if (-not $found) {
        Write-Host "  ⚠ Could not find $dll" -ForegroundColor Yellow
    }
}

# Cleanup
Remove-Item $tempDir -Recurse -Force

Write-Host ""
Write-Host "==================================================" -ForegroundColor Cyan
Write-Host "Installation Summary" -ForegroundColor Cyan
Write-Host "==================================================" -ForegroundColor Cyan
Write-Host ""

if ($copiedFiles.Count -eq $existingDlls.Count) {
    Write-Host "SUCCESS: All assemblies installed" -ForegroundColor Green
    Write-Host ""
    Write-Host "Installed assemblies:" -ForegroundColor White
    foreach ($dll in $copiedFiles) {
        Write-Host "  ✓ $dll" -ForegroundColor Green
    }
    Write-Host ""
    Write-Host "Next steps:" -ForegroundColor Yellow
    Write-Host "1. Restart Claude Desktop (fully close and reopen)" -ForegroundColor White
    Write-Host "2. Verify installation: python scripts/verify_dotnet_assemblies.py" -ForegroundColor White
    Write-Host "3. Test connection: Ask Claude to connect to Power BI Desktop" -ForegroundColor White
}
else {
    Write-Host "PARTIAL: Some assemblies missing" -ForegroundColor Yellow
    Write-Host ""
    Write-Host "Installed:" -ForegroundColor Green
    foreach ($dll in $copiedFiles) {
        Write-Host "  ✓ $dll" -ForegroundColor Green
    }
    Write-Host ""
    Write-Host "Missing:" -ForegroundColor Red
    foreach ($dll in $existingDlls) {
        if ($dll -notin $copiedFiles) {
            Write-Host "  ✗ $dll" -ForegroundColor Red
        }
    }
    Write-Host ""
    Write-Host "Try manual installation:" -ForegroundColor Yellow
    Write-Host "1. Download from: https://aka.ms/ssmsfullsetup" -ForegroundColor White
    Write-Host "2. Copy DLLs from: C:\Program Files\Microsoft SQL Server\150\SDK\Assemblies\" -ForegroundColor White
    Write-Host "3. Paste into: $scriptDir" -ForegroundColor White
}

Write-Host ""