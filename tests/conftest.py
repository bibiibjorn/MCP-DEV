"""
Pytest configuration for MCP-PowerBi-Finvision tests.

Provides common fixtures and configuration for all tests.
"""

import pytest
import sys
from pathlib import Path

# Add the project root to the Python path
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))


@pytest.fixture(scope="session")
def project_root():
    """Return the project root path."""
    return PROJECT_ROOT


@pytest.fixture(scope="session")
def contoso_pbip_path():
    """Return the path to the Contoso PBIP model if available."""
    path = Path(r"C:\Users\bjorn.braet\OneDrive - Finvision\FINTICX - Documenten\M01 - Wealth Reporting\04-Analytics\Aggregation Analysis MCP")
    if path.exists():
        return path
    return None
