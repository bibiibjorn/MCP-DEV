"""
Deprecated/Unwired: Enhanced Measure Manager

This module is not used by the server paths. It was intended to manipulate
measures via TMSL end-to-end and currently references a non-existent
`DAXInjector.execute_tmsl()` method. The active and supported path for
measure operations is `core.dax_injector.DAXInjector` (upsert/delete).

Keeping as a stub to avoid confusion if imported accidentally.
"""

raise ImportError(
    "measure_manager_enhanced is deprecated/unwired. Use core.dax_injector.DAXInjector instead."
)
