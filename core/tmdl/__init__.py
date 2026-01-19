"""
TMDL Automation Module

This module provides comprehensive TMDL (Tabular Model Definition Language) automation capabilities:
- Validation and linting of TMDL files
- Bulk editing operations (find/replace, rename)
- Template library for common patterns
- Script generation for programmatic model creation

Version: 3.0.0
"""

from .validator import TmdlValidator, ValidationResult, LintIssue
from .bulk_editor import TmdlBulkEditor, ReplaceResult, RenameResult
from .templates import TmdlTemplateLibrary, TemplateInfo, TmdlTemplate
from .script_generator import TmdlScriptGenerator
from .measure_migrator import TmdlMeasureMigrator, MigrationResult, MeasureInfo

__all__ = [
    "TmdlValidator",
    "ValidationResult",
    "LintIssue",
    "TmdlBulkEditor",
    "ReplaceResult",
    "RenameResult",
    "TmdlTemplateLibrary",
    "TemplateInfo",
    "TmdlTemplate",
    "TmdlScriptGenerator",
    "TmdlMeasureMigrator",
    "MigrationResult",
    "MeasureInfo",
]
