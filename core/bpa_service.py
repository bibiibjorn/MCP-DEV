"""
Deprecated/Unwired: BPA service wrapper

This module is not used by the server; BPA is invoked directly via core.bpa_analyzer.
Keeping as a stub to avoid confusion if imported accidentally.
"""

raise ImportError(
    "bpa_service is deprecated/unused. Use core.bpa_analyzer.BPAAnalyzer directly."
)
