#!/usr/bin/env python3
"""
Verify .NET assemblies for Power BI MCP Server.
Checks presence, versions, and compatibility.
"""

import os
import sys
from pathlib import Path

# Color codes
GREEN = '\033[92m'
YELLOW = '\033[93m'
RED = '\033[91m'
CYAN = '\033[96m'
RESET = '\033[0m'

def print_header():
    print(f"{CYAN}{'='*60}{RESET}")
    print(f"{CYAN}.NET Assembly Verification{RESET}")
    print(f"{CYAN}{'='*60}{RESET}\n")

def check_assembly(path: Path, name: str) -> tuple:
    """Check if assembly exists and get version."""
    dll_path = path / name
    
    if not dll_path.exists():
        return False, None, "Not found"
    
    # Try to load with pythonnet
    try:
        import clr
        clr.AddReference(str(dll_path))
        
        # Get assembly info
        from System.Reflection import Assembly
        asm = Assembly.LoadFrom(str(dll_path))
        version = asm.GetName().Version.ToString()
        
        return True, version, None
    except ImportError:
        # pythonnet not available, just check file exists
        return True, "Unknown (pythonnet not installed)", None
    except Exception as e:
        return True, None, f"Load error: {str(e)[:50]}"

def main():
    print_header()
    
    # Find lib/dotnet directory
    script_dir = Path(__file__).parent
    project_root = script_dir.parent
    dotnet_dir = project_root / "lib" / "dotnet"
    
    if not dotnet_dir.exists():
        print(f"{RED}X lib/dotnet directory not found!{RESET}")
        print(f"  Expected: {dotnet_dir}")
        print(f"\n{YELLOW}Create the directory and run lib/dotnet/install.ps1{RESET}")
        return 1
    
    print(f"Checking: {dotnet_dir}\n")
    
    # Required assemblies
    assemblies = {
        "Microsoft.AnalysisServices.AdomdClient.dll": {
            "required": True,
            "description": "ADOMD.NET Client (DMV queries)"
        },
        "Microsoft.AnalysisServices.Core.dll": {
            "required": False,
            "description": "AMO Core (TMSL/TMDL)"
        },
        "Microsoft.AnalysisServices.Tabular.dll": {
            "required": False,
            "description": "AMO Tabular (Model operations)"
        },
        "Microsoft.AnalysisServices.Tabular.Json.dll": {
            "required": False,
            "description": "AMO JSON (TMSL serialization)"
        }
    }
    
    results = []
    all_required_present = True
    any_optional_present = False
    
    for dll_name, info in assemblies.items():
        exists, version, error = check_assembly(dotnet_dir, dll_name)
        
        results.append({
            'name': dll_name,
            'exists': exists,
            'version': version,
            'error': error,
            'required': info['required'],
            'description': info['description']
        })
        
        if info['required'] and not exists:
            all_required_present = False
        if not info['required'] and exists:
            any_optional_present = True
    
    # Print results
    for result in results:
        symbol = "OK" if result['exists'] else "X"
        color = GREEN if result['exists'] else (RED if result['required'] else YELLOW)
        req_label = "(Required)" if result['required'] else "(Optional)"
        
        print(f"{color}{symbol} {result['name']} {req_label}{RESET}")
        print(f"  {result['description']}")
        
        if result['exists']:
            if result['version']:
                print(f"  Version: {result['version']}")
            if result['error']:
                print(f"  {YELLOW}Warning: {result['error']}{RESET}")
        else:
            print(f"  {RED}Not found in {dotnet_dir}{RESET}")
        
        print()
    
    # Summary
    print(f"{CYAN}{'='*60}{RESET}")
    print(f"{CYAN}Summary{RESET}")
    print(f"{CYAN}{'='*60}{RESET}\n")
    
    if all_required_present:
        print(f"{GREEN}OK All required assemblies present{RESET}")
        
        if any_optional_present:
            print(f"{GREEN}OK Optional AMO assemblies available - full features enabled{RESET}")
            print(f"\n{CYAN}Enabled features:{RESET}")
            print(f"  - DMV queries and metadata")
            print(f"  - Performance analysis with SE/FE split")
            print(f"  - TMSL/TMDL export")
            print(f"  - Advanced BPA checks")
        else:
            print(f"{YELLOW}WARN Optional AMO assemblies missing - limited features{RESET}")
            print(f"\n{CYAN}Available features:{RESET}")
            print(f"  - DMV queries and metadata")
            print(f"  - Basic performance analysis")
            print(f"\n{YELLOW}Missing features:{RESET}")
            print(f"  - Advanced performance tracing")
            print(f"  - TMSL/TMDL export")
            print(f"\n{YELLOW}To enable all features:{RESET}")
            print(f"  Run: lib/dotnet/install.ps1")
        
        return 0
    else:
        print(f"{RED}X Required assemblies missing!{RESET}")
        print(f"\n{YELLOW}Installation options:{RESET}")
        print(f"  1. Automatic: Run lib/dotnet/install.ps1")
        print(f"  2. Manual: Download from https://aka.ms/ssmsfullsetup")
        print(f"     Copy DLLs to: {dotnet_dir}")
        
        return 1

if __name__ == "__main__":
    sys.exit(main())
