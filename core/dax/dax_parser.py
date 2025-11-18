"""
Lightweight DAX expression reference parser.

Provides best-effort extraction of table, column, and measure references from
raw DAX expressions without requiring a full parser or external dependency.
The parser is heuristic-based but leverages model metadata (when supplied) to
classify identifiers accurately.

NOTE: This module now imports from dax_reference_parser.py to avoid code duplication.
      The primary implementation is in dax_reference_parser.py.
"""

# Import from the primary implementation
from .dax_reference_parser import DaxReferenceIndex, parse_dax_references

__all__ = ["DaxReferenceIndex", "parse_dax_references"]
