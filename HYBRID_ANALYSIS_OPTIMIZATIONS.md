# Hybrid Analysis Feature: Analysis and Optimization Plan

This document outlines the analysis and proposed optimizations for the Hybrid Analysis feature, based on a review of `core/model/hybrid_analyzer.py` and `core/model/hybrid_intelligence.py`.

## High-Level Analysis

The Hybrid Analysis feature is a sophisticated and well-structured component that intelligently combines offline TMDL files with live model metadata. The code demonstrates high quality with excellent logging and robust error handling, particularly in the auto-detection and connection logic.

-   **`hybrid_analyzer.py`**: This is the core engine. It successfully connects to a live Power BI instance, queries for rich metadata (row counts, dependencies), and merges it with the static TMDL file structure. The automatic file splitting for managing output size is a critical and well-implemented feature. The use of `PbipDependencyEngine` is a significant architectural improvement for dependency mapping.
-   **`hybrid_intelligence.py`**: This acts as a smart, natural-language front-end. It uses regular expressions to infer user intent and provides helpful suggestions, which is a great feature for guiding the user. The concept of a token-optimized "TOON" format is noted but not yet implemented.

## Optimization and Refinement Opportunities

Here is a list of actionable items for further development to improve performance, complete planned features, and increase maintainability.

### 1. Parallelize Data Extraction (`hybrid_analyzer.py`)

-   **Observation:** The extraction of table row counts and sample data is performed sequentially in a loop. These are network-bound operations and represent a significant performance bottleneck, especially for models with many tables.
-   **Suggestion:** Use a `concurrent.futures.ThreadPoolExecutor` to run these queries in parallel. This could dramatically reduce the total export time. Introduce a configurable `max_workers` parameter to control the degree of parallelism.

### 2. Consolidate Metadata Queries (`hybrid_analyzer.py`)

-   **Observation:** Metadata (tables, columns, measures, relationships) is queried in several different methods (`_generate_metadata`, `_generate_catalog`, etc.), potentially leading to redundant calls.
-   **Suggestion:** Create a single internal method that runs the primary DMV queries (`INFO.TABLES()`, `INFO.COLUMNS()`, `INFO.MEASURES()`, `INFO.RELATIONSHIPS()`) once at the start of the `export()` process. Store these results in memory (e.g., as `polars` DataFrames). Subsequent methods can then pull from this in-memory cache instead of re-querying the live model. This will reduce network round-trips and centralize data-gathering logic.

### 3. Implement the TOON Format (`hybrid_intelligence.py`)

-   **Observation:** The `convert_to_toon_format` method is currently a `TODO` placeholder. This is a significant missed opportunity for token optimization, which is a primary goal for LLM-based tools.
-   **Suggestion:** Implement the TOON (Tabular Object Optimized Notation) format. A good approach would be to convert lists of JSON objects into a more compact tabular format.
    -   **Example:** Instead of `[{'name': 'A', 'value': 1}, {'name': 'B', 'value': 2}]`, use `{'headers': ['name', 'value'], 'rows': [['A', 1], ['B', 2]]}`.
    -   Systematically abbreviate common, verbose JSON keys (e.g., `dependencies` to `deps`). This could achieve the target 50% token reduction.

### 4. Refactor File Splitting Logic (`hybrid_analyzer.py`)

-   **Observation:** The `_split_and_write` method uses a series of `if/elif` statements for each file type (`catalog`, `dependencies`, etc.), which is not easily extensible.
-   **Suggestion:** Refactor this logic to be data-driven. Define a configuration dictionary where keys are the file types and values are objects specifying the details for splitting (e.g., `{ "file_type": "catalog", "split_key": "tables" }`). This would make the function more generic, maintainable, and easier to extend for new file types.

### 5. Enhance Intent Recognition (`hybrid_intelligence.py`)

-   **Observation:** The current regex-based intent matching is effective but can be brittle and hard to maintain as more intents are added.
-   **Suggestion:** For a more robust and scalable solution, consider using a lightweight sentence-transformer model to generate vector embeddings for the user's intent. You could then use cosine similarity to match the user's query against a list of pre-computed embeddings for canonical questions (e.g., "list all tables," "show dependencies for a measure"). This would handle a much wider and more nuanced variety of natural language phrasing.
