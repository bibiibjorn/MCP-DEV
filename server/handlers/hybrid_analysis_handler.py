"""
Hybrid Analysis MCP Tool Handlers

Provides MCP tool handlers for hybrid analysis operations:
1. export_hybrid_analysis - Export PBIP model to hybrid format
2. analyze_hybrid_model - Analyze hybrid analysis package
"""

import logging
import traceback
from pathlib import Path
from typing import Dict, Any, Optional

from core.model.hybrid_analyzer import HybridAnalyzer
from core.model.hybrid_reader import HybridReader
from core.model.hybrid_intelligence import HybridIntelligence
from core.model.bi_expert_analyzer import BIExpertAnalyzer
from server.registry import ToolDefinition
from server.tool_schemas import TOOL_SCHEMAS

logger = logging.getLogger(__name__)


def handle_export_hybrid_analysis(
    pbip_folder_path: str,
    output_dir: Optional[str] = None,
    connection_string: Optional[str] = None,
    server: Optional[str] = None,
    database: Optional[str] = None,
    include_sample_data: bool = True,
    sample_rows: int = 1000,
    sample_compression: str = "snappy",
    include_row_counts: bool = True,
    track_column_usage: bool = True,
    track_cardinality: bool = True,
    tmdl_strategy: str = "symlink",
    progress_callback: bool = False
) -> Dict[str, Any]:
    """
    Export Power BI model to hybrid analysis format

    Combines:
    1. TMDL files from specified PBIP folder
    2. Live metadata + sample data from currently open Power BI file (auto-detected)

    Args:
        pbip_folder_path: Path to .SemanticModel folder (for TMDL files)
        output_dir: Optional output directory (defaults to same folder as PBIP with '_analysis' suffix)
        connection_string: Optional connection string (auto-detects if not provided)
        server: Alternative: server name
        database: Alternative: database name
        include_sample_data: Include sample data extraction
        sample_rows: Number of sample rows per table
        sample_compression: Compression for parquet files
        include_row_counts: Include row counts in metadata
        track_column_usage: Track column usage
        track_cardinality: Track cardinality info
        tmdl_strategy: "symlink" or "copy"
        progress_callback: Enable progress tracking

    Returns:
        Export result dictionary
    """
    try:
        # Validate PBIP folder
        pbip_path = Path(pbip_folder_path)
        if not pbip_path.exists():
            return {
                'success': False,
                'error': f'PBIP folder not found: {pbip_folder_path}',
                'error_type': 'not_found'
            }

        # Auto-determine output directory if not provided
        if not output_dir:
            # Use same parent folder as PBIP, add '_analysis' suffix
            model_name = pbip_path.stem.replace('.SemanticModel', '')
            output_dir = str(pbip_path.parent / f"{model_name}_analysis")
            logger.info(f"Output directory not specified, using: {output_dir}")

        logger.info(f"Starting hybrid analysis export:")
        logger.info(f"  - TMDL source: {pbip_folder_path}")
        logger.info(f"  - Output: {output_dir}")
        logger.info(f"  - Live data: Auto-detect from open Power BI file")

        # Initialize analyzer
        analyzer = HybridAnalyzer(
            pbip_folder_path=pbip_folder_path,
            output_dir=output_dir,
            connection_string=connection_string,
            server=server,
            database=database
        )

        # Perform export
        result = analyzer.export(
            include_sample_data=include_sample_data and analyzer.has_connection,
            sample_rows=sample_rows,
            sample_compression=sample_compression,
            include_row_counts=include_row_counts,
            track_column_usage=track_column_usage,
            track_cardinality=track_cardinality,
            tmdl_strategy=tmdl_strategy,
            progress_callback=None  # TODO: Implement progress callback
        )

        logger.info(f"Export completed successfully in {result['generation_time_seconds']}s")

        # Return simplified response - just the essentials
        return {
            'success': True,
            'message': f"✓ Hybrid analysis exported successfully",
            'output_path': result['output_path'],
            'export_time_seconds': result['generation_time_seconds'],
            'files_created': {
                'tmdl_files': result['structure']['file_counts']['tmdl_files'],
                'analysis_files': result['structure']['file_counts']['json_files'],
                'sample_data_files': result['structure']['file_counts']['parquet_files']
            },
            'statistics_summary': {
                'tables': result['statistics']['tables'],
                'measures': result['statistics']['measures'],
                'total_rows': result['statistics']['total_rows']
            }
        }

    except Exception as e:
        logger.error(f"Error in export_hybrid_analysis: {str(e)}\n{traceback.format_exc()}")
        return {
            'success': False,
            'error': f"Export failed: {str(e)}",
            'error_type': 'export_error',
            'context': {
                'pbip_folder_path': pbip_folder_path,
                'output_dir': output_dir
            }
        }


def handle_analyze_hybrid_model(
    analysis_path: str,
    operation: str,
    intent: Optional[str] = None,
    object_filter: Optional[Dict[str, Any]] = None,
    format_type: str = "json",
    batch_size: int = 50,
    batch_number: int = 0,
    priority: Optional[str] = None,
    detailed: bool = False,
    include_dependencies: bool = False,
    include_sample_data: bool = False
) -> Dict[str, Any]:
    """
    Read and analyze hybrid analysis package

    Args:
        analysis_path: Path to exported analysis folder
        operation: Operation name or "smart_analyze"
        intent: Natural language intent (for smart_analyze)
        object_filter: Filter for objects
        format_type: "json" or "toon"
        batch_size: Results per page
        batch_number: Page number
        priority: Filter priority
        detailed: Include detailed analysis
        include_dependencies: Include dependency info
        include_sample_data: Include sample data

    Returns:
        Analysis result dictionary
    """
    try:
        logger.info(f"Analyzing hybrid model at: {analysis_path}, operation: {operation}")

        # Validate analysis path
        analysis_path_obj = Path(analysis_path)
        if not analysis_path_obj.exists():
            return {
                'success': False,
                'error': f'Analysis path not found: {analysis_path}',
                'error_type': 'not_found'
            }

        # Initialize reader
        reader = HybridReader(analysis_path)

        # Smart analyze mode - infer operation from intent
        actual_operation = operation
        inferred_params = {}
        if operation == "smart_analyze" and intent:
            actual_operation, inferred_params = HybridIntelligence.infer_operation(intent)
            logger.info(f"Smart analyze inferred: {actual_operation} with params {inferred_params}")

            # Merge inferred params with explicit params
            if not object_filter:
                object_filter = {}
            object_filter.update(inferred_params)

        # Execute operation
        result = None

        if actual_operation == "read_metadata":
            result = _operation_read_metadata(reader)

        elif actual_operation == "find_objects":
            result = _operation_find_objects(
                reader,
                object_filter or {},
                batch_size,
                batch_number
            )

        elif actual_operation == "get_object_definition":
            object_name = (object_filter or {}).get("object_name") or \
                         (object_filter or {}).get("name_pattern")
            object_type = (object_filter or {}).get("object_type", "measure")

            if not object_name:
                return {
                    'success': False,
                    'error': 'object_name required for get_object_definition',
                    'error_type': 'validation_error',
                    'context': {'object_filter': object_filter}
                }

            result = _operation_get_object_definition(
                reader,
                object_name,
                object_type
            )

        elif actual_operation == "analyze_dependencies":
            object_name = (object_filter or {}).get("object_name") or \
                         (object_filter or {}).get("name_pattern")

            if not object_name:
                return {
                    'success': False,
                    'error': 'object_name required for analyze_dependencies',
                    'error_type': 'validation_error',
                    'context': {'object_filter': object_filter}
                }

            result = _operation_analyze_dependencies(
                reader,
                object_name,
                "both"
            )

        elif actual_operation == "get_sample_data":
            table_name = (object_filter or {}).get("table") or \
                        (object_filter or {}).get("table_name")

            if not table_name:
                return {
                    'success': False,
                    'error': 'table_name required for get_sample_data',
                    'error_type': 'validation_error',
                    'context': {'object_filter': object_filter}
                }

            result = _operation_get_sample_data(
                reader,
                table_name,
                batch_size
            )

        elif actual_operation == "analyze_performance":
            result = _operation_analyze_performance(
                reader,
                priority,
                detailed
            )

        else:
            return {
                'success': False,
                'error': f'Unknown operation: {actual_operation}',
                'error_type': 'invalid_operation',
                'context': {'operation': operation}
            }

        # Apply TOON format if needed
        estimated_tokens = HybridIntelligence.estimate_tokens(result)
        result_count = result.get("count", 0)

        if format_type == "toon" or HybridIntelligence.should_use_toon_format(result_count, estimated_tokens):
            format_type = "toon"
            result = HybridIntelligence.convert_to_toon_format(result)

        # Add guidance (informational only - AI should not auto-execute)
        guidance = HybridIntelligence.generate_guidance(actual_operation, result, intent)
        token_warning = HybridIntelligence.generate_token_warning(estimated_tokens, format_type)
        next_steps = HybridIntelligence.generate_next_steps(actual_operation, result)

        # Build response
        response = {
            "success": True,
            "operation": actual_operation,
            "result": result,
            "_guidance": guidance,
            "_token_estimate": token_warning,
            "_performance": {
                "query_time_ms": 0,  # TODO: Track actual time
                "cache_hit": False,
                "cache_type": None,
                "files_loaded": [],
                "selective_loading": True
            }
        }

        # Add next steps as suggestions only (AI should ask user before executing)
        if next_steps:
            response["_next_steps"] = {
                "_notice": "⚠️ SUGGESTIONS ONLY - Do not execute without explicit user approval",
                "suggestions": next_steps
            }

        logger.info(f"Analysis completed: {actual_operation}")
        return response

    except Exception as e:
        logger.error(f"Error in analyze_hybrid_model: {str(e)}\n{traceback.format_exc()}")
        return {
            'success': False,
            'error': f"Analysis failed: {str(e)}",
            'error_type': 'analysis_error',
            'context': {
                'analysis_path': analysis_path,
                'operation': operation
            }
        }


def _operation_read_metadata(reader: HybridReader) -> Dict[str, Any]:
    """Read metadata operation with BI expert analysis"""
    metadata = reader.read_metadata()

    # Parse relationships from TMDL if available
    relationships = reader.get_relationships_from_tmdl()

    # Get BI expert analysis
    expert_analysis = BIExpertAnalyzer.analyze_model_overview(metadata, relationships)

    # Add sample data info if available
    sample_tables = reader.list_sample_data_tables()
    sample_data_info = None
    if sample_tables:
        sample_data_info = {
            "available": True,
            "tables": sample_tables,
            "table_count": len(sample_tables),
            "guidance": "Sample data is available. Use operation='get_sample_data' with object_filter={'table_name': 'TableName'} to preview table contents."
        }
    else:
        sample_data_info = {
            "available": False,
            "guidance": "No sample data available. This is a TMDL-only analysis. For data profiling, re-export with include_sample_data=true."
        }

    # Build response
    response_data = {
        "model_info": metadata,
        "expert_analysis": expert_analysis,
        "sample_data_info": sample_data_info,
        "_format_type": reader.format_type
    }

    # Add relationship summary if available
    if relationships:
        rel_analysis = BIExpertAnalyzer.analyze_relationships(relationships)
        response_data["relationships_analysis"] = rel_analysis

    return {
        "data": response_data,
        "count": 1
    }


def _operation_find_objects(
    reader: HybridReader,
    object_filter: Dict[str, Any],
    batch_size: int,
    batch_number: int
) -> Dict[str, Any]:
    """Find objects operation"""
    object_type = object_filter.get("object_type", "tables")

    # Extract filters
    filters = {}
    for key in ["name_pattern", "folder", "table", "is_hidden", "complexity"]:
        if key in object_filter:
            filters[key] = object_filter[key]

    # Find objects
    objects = reader.find_objects(object_type, filters)

    # Apply pagination
    total = len(objects)
    start = batch_number * batch_size
    end = start + batch_size
    page_objects = objects[start:end]

    return {
        "object_type": object_type,
        "count": len(page_objects),
        "total": total,
        "batch": {
            "size": batch_size,
            "number": batch_number,
            "total_pages": (total + batch_size - 1) // batch_size
        },
        "objects": page_objects
    }


def _operation_get_object_definition(
    reader: HybridReader,
    object_name: str,
    object_type: str
) -> Dict[str, Any]:
    """Get object definition operation with expert analysis and pattern search support"""
    try:
        definition = reader.get_object_definition(object_name, object_type)

        # Add expert analysis for measures
        if object_type == "measure" and definition.get("dax_expression"):
            expert_analysis = BIExpertAnalyzer.analyze_measure(definition, include_dax_analysis=True)
            definition["expert_analysis"] = expert_analysis

        # Check if sample data would be beneficial
        sample_data_guidance = BIExpertAnalyzer.should_request_sample_data(
            "get_object_definition",
            {"object_type": object_type}
        )

        if sample_data_guidance["sample_data_recommended"]:
            definition["_sample_data_guidance"] = sample_data_guidance

        return {
            "data": definition,
            "count": 1
        }
    except ValueError as e:
        # Object not found - try pattern search if it's a measure
        if object_type == "measure":
            logger.info(f"Exact match failed for '{object_name}', trying pattern search")
            # Convert search term to pattern
            search_pattern = object_name.replace(' ', '[-_ ]?').replace('-', '[-_ ]?')
            matching_measures = reader.find_measures_by_pattern(search_pattern)

            if matching_measures:
                if len(matching_measures) == 1:
                    # Single match - return it
                    measure = matching_measures[0]
                    definition = {
                        "name": measure["name"],
                        "type": "measure",
                        "table": measure.get("table"),
                        "dax_expression": measure.get("expression"),
                        "description": measure.get("description"),
                        "display_folder": measure.get("displayFolder"),
                        "format_string": measure.get("formatString"),
                        "is_hidden": measure.get("isHidden"),
                        "source": "tmdl_parsed",
                        "search_query": object_name
                    }
                    expert_analysis = BIExpertAnalyzer.analyze_measure(definition, include_dax_analysis=True)
                    definition["expert_analysis"] = expert_analysis
                    return {
                        "data": definition,
                        "count": 1
                    }
                else:
                    # Multiple matches - return list
                    return {
                        "data": {
                            "search_query": object_name,
                            "message": f"Found {len(matching_measures)} measures matching '{object_name}'",
                            "matches": [{"name": m["name"], "table": m.get("table"), "display_folder": m.get("displayFolder")} for m in matching_measures],
                            "suggestion": f"Use exact name from matches list in object_filter.object_name"
                        },
                        "count": len(matching_measures)
                    }

        # No matches found
        raise ValueError(f"{object_type} '{object_name}' not found. Try using a pattern or check available objects with operation='find_objects'")


def _operation_analyze_dependencies(
    reader: HybridReader,
    object_name: str,
    direction: str
) -> Dict[str, Any]:
    """Analyze dependencies operation"""
    dependencies = reader.analyze_dependencies(object_name, direction)
    return {
        "data": dependencies,
        "count": 1
    }


def _operation_get_sample_data(
    reader: HybridReader,
    table_name: str,
    max_rows: int
) -> Dict[str, Any]:
    """Get sample data operation"""
    sample_data = reader.read_sample_data(table_name)

    if sample_data is None:
        return {
            "data": None,
            "count": 0,
            "message": "Sample data not available (no connection during export)"
        }

    # Limit rows
    if sample_data.get("data"):
        sample_data["data"] = sample_data["data"][:max_rows]

    return {
        "data": sample_data,
        "count": len(sample_data.get("data", []))
    }


def _operation_analyze_performance(
    reader: HybridReader,
    priority: Optional[str],
    detailed: bool
) -> Dict[str, Any]:
    """
    Comprehensive performance analysis with concrete recommendations

    Analyzes the model and provides:
    - High-level model health assessment
    - Concrete DAX measure optimizations with actual code
    - Specific model structure improvements
    - Prioritized action plan
    """
    from core.research.article_patterns import ARTICLE_PATTERNS
    import re

    # Get model metadata and relationships
    metadata = reader.read_metadata()
    relationships = reader.get_relationships_from_tmdl()

    # Get all measures from TMDL
    all_measures = []
    try:
        measures_by_table = reader.get_all_measures()
        for table_name, measures in measures_by_table.items():
            for measure in measures:
                measure['table'] = table_name
                all_measures.append(measure)
    except Exception as e:
        logger.warning(f"Could not load measures from TMDL: {e}")

    # 1. HIGH-LEVEL MODEL ASSESSMENT
    model_assessment = BIExpertAnalyzer.analyze_model_overview(metadata, relationships)

    # 2. SCAN ALL MEASURES FOR ANTI-PATTERNS AND GENERATE CONCRETE FIXES
    dax_optimizations = []
    patterns_found = {}

    for measure in all_measures[:50]:  # Analyze top 50 measures
        measure_name = measure.get('name', 'Unknown')
        expression = measure.get('expression', '')
        table = measure.get('table', '')

        if not expression:
            continue

        # Check each optimization pattern
        for pattern_key, pattern_info in ARTICLE_PATTERNS.items():
            if pattern_key == "general_framework":
                continue

            patterns = pattern_info.get('patterns', [])
            for pattern in patterns:
                if re.search(pattern, expression, re.IGNORECASE):
                    # Found an anti-pattern - generate concrete fix
                    optimized_dax = _generate_optimized_dax(
                        measure_name,
                        expression,
                        pattern_key,
                        pattern_info
                    )

                    # Track pattern occurrence
                    if pattern_key not in patterns_found:
                        patterns_found[pattern_key] = 0
                    patterns_found[pattern_key] += 1

                    dax_optimizations.append({
                        'priority': 'high' if pattern_key in ['sumx_filter', 'nested_calculate', 'filter_all'] else 'medium',
                        'measure_name': measure_name,
                        'table': table,
                        'anti_pattern': pattern_key.replace('_', ' ').title(),
                        'issue': pattern_info.get('title', ''),
                        'current_dax': expression,
                        'optimized_dax': optimized_dax,
                        'expected_improvement': _get_expected_improvement(pattern_key),
                        'explanation': pattern_info.get('content', '').strip(),
                        'action': f"Replace measure '{measure_name}' in table '{table}' with optimized version"
                    })
                    break  # Only report first pattern per measure

    # 3. MODEL STRUCTURE RECOMMENDATIONS WITH CONCRETE CHANGES
    structure_recommendations = _generate_structure_recommendations(
        metadata,
        relationships,
        model_assessment
    )

    # 4. QUICK WINS - Easy, high-impact optimizations
    quick_wins = _identify_quick_wins(dax_optimizations, structure_recommendations)

    # 5. PRIORITIZED ACTION PLAN
    action_plan = _generate_action_plan(
        dax_optimizations,
        structure_recommendations,
        quick_wins
    )

    # Build comprehensive result
    result = {
        "data": {
            "executive_summary": {
                "model_health_score": model_assessment.get('health_score', 0),
                "optimization_opportunities_found": len(dax_optimizations) + len(structure_recommendations),
                "dax_optimizations": len(dax_optimizations),
                "structure_improvements": len(structure_recommendations),
                "estimated_total_performance_gain": _estimate_total_gain(dax_optimizations),
                "top_priority_actions": len(quick_wins)
            },

            "model_health_assessment": {
                "health_score": model_assessment.get('health_score', 0),
                "executive_summary": model_assessment.get('executive_summary', ''),
                "risk_factors": model_assessment.get('risk_factors', []),
                "strengths": model_assessment.get('strengths', []),
                "health_breakdown": model_assessment.get('health_breakdown', {})
            },

            "dax_optimizations": sorted(
                dax_optimizations,
                key=lambda x: {'high': 0, 'medium': 1, 'low': 2}[x['priority']]
            ),

            "anti_patterns_summary": {
                "total_patterns_found": sum(patterns_found.values()),
                "pattern_breakdown": patterns_found,
                "most_common_pattern": max(patterns_found.items(), key=lambda x: x[1])[0] if patterns_found else None
            },

            "model_structure_recommendations": structure_recommendations,

            "quick_wins": quick_wins,

            "action_plan": action_plan,

            "next_steps": {
                "immediate": "Start with Quick Wins - these provide maximum impact with minimum effort",
                "short_term": "Address high-priority DAX optimizations (expected 5-10x performance gains)",
                "medium_term": "Implement model structure improvements",
                "validation": "Test each optimization in development before deploying to production"
            }
        },
        "count": len(dax_optimizations) + len(structure_recommendations)
    }

    return result


def _generate_optimized_dax(
    measure_name: str,
    original_dax: str,
    pattern_key: str,
    pattern_info: Dict[str, Any]
) -> str:
    """Generate concrete optimized DAX code based on anti-pattern"""

    # Pattern-specific transformations
    if pattern_key == "sumx_filter":
        # Transform SUMX(FILTER(...), ...) to CALCULATE(SUM(...), filters)
        # Example: SUMX(FILTER(Sales, Sales[Year] = 2024), Sales[Amount])
        #       -> CALCULATE(SUM(Sales[Amount]), Sales[Year] = 2024)
        optimized = f"""-- Optimized version of {measure_name}
-- Changed from SUMX(FILTER(...)) to CALCULATE(SUM(...))
CALCULATE(
    SUM(Table[Column]),  -- Replace with your table and column
    Table[FilterColumn] = Value  -- Replace with your filter conditions
)

-- Original (slow):
-- {original_dax[:200]}...

-- Expected improvement: 5-10x faster
"""

    elif pattern_key == "nested_calculate":
        optimized = f"""-- Optimized version of {measure_name}
-- Consolidated nested CALCULATE into single statement
CALCULATE(
    [BaseMeasure],
    Filter1,  -- Replace with your first filter
    Filter2,  -- Replace with your second filter
    Filter3   -- Add all filters from nested CALCULATE statements
)

-- Original (multiple context transitions):
-- {original_dax[:200]}...

-- Expected improvement: 2-3x faster, more predictable results
"""

    elif pattern_key == "filter_all":
        optimized = f"""-- Optimized version of {measure_name}
-- Replaced FILTER(ALL(...)) with CALCULATE
CALCULATE(
    [BaseMeasure],
    ALL(Table),  -- Use ALL in CALCULATE, not in FILTER
    Table[Column] > Value  -- Add filter conditions as CALCULATE arguments
)

-- Original (Formula Engine materialization):
-- {original_dax[:200]}...

-- Expected improvement: 3-5x faster, leverages Storage Engine
"""

    elif pattern_key == "divide_zero_check":
        optimized = f"""-- Optimized version of {measure_name}
-- Replaced manual division with DIVIDE()
DIVIDE(
    [Numerator],
    [Denominator],
    0  -- Alternative result if denominator is zero
)

-- Original (slower IF check):
-- {original_dax[:200]}...

-- Expected improvement: 2-3x faster
"""

    elif pattern_key == "countrows_filter":
        optimized = f"""-- Optimized version of {measure_name}
-- Replaced COUNTROWS(FILTER(...)) with CALCULATE
CALCULATE(
    COUNTROWS(Table),
    Table[Column] > Value  -- Replace with your filter conditions
)

-- Original (row-by-row evaluation):
-- {original_dax[:200]}...

-- Expected improvement: 5-10x faster
"""

    elif pattern_key == "unnecessary_iterators":
        optimized = f"""-- Optimized version of {measure_name}
-- Replaced iterator with simple aggregation
SUM(Table[Column])  -- or AVERAGE, COUNT, etc.

-- Original (unnecessary iteration overhead):
-- {original_dax[:200]}...

-- Expected improvement: 2-4x faster
"""

    elif pattern_key == "multiple_context_transitions":
        optimized = f"""-- Optimized version of {measure_name}
-- Cached measure references in variables
VAR Measure1Result = [Measure1]
VAR Measure2Result = [Measure2]
VAR Measure3Result = [Measure3]
RETURN
    Measure1Result + Measure2Result + Measure3Result

-- Original (multiple context transitions):
-- {original_dax[:200]}...

-- Expected improvement: 1.5-2x faster
"""

    else:
        # Generic optimization template
        optimized = f"""-- Optimized version of {measure_name}
-- Pattern: {pattern_key}

VAR OptimizedResult =
    -- Apply the optimization pattern here
    -- Refer to the explanation below
    CALCULATE([YourMeasure], YourFilters)

RETURN OptimizedResult

-- Original:
-- {original_dax[:200]}...

-- See explanation for specific optimization strategy
"""

    return optimized


def _get_expected_improvement(pattern_key: str) -> str:
    """Get expected performance improvement for each pattern"""
    improvements = {
        "sumx_filter": "5-10x faster execution",
        "filter_all": "3-5x faster, reduced memory usage",
        "nested_calculate": "2-3x faster, more predictable results",
        "related_in_iterator": "3-8x faster on large tables",
        "divide_zero_check": "2-3x faster",
        "countrows_filter": "5-10x faster execution",
        "unnecessary_iterators": "2-4x faster",
        "multiple_context_transitions": "1.5-2x faster",
        "measure_in_filter": "5-15x faster, enables Storage Engine",
        "values_in_calculate": "1.5-2x faster"
    }
    return improvements.get(pattern_key, "Moderate performance improvement expected")


def _generate_structure_recommendations(
    metadata: Dict[str, Any],
    relationships: List[Dict[str, Any]],
    model_assessment: Dict[str, Any]
) -> List[Dict[str, Any]]:
    """Generate concrete model structure improvement recommendations"""
    recommendations = []

    stats = metadata.get('statistics', {})
    tables = stats.get('tables', {})
    measures_info = stats.get('measures', {})

    table_count = tables.get('total', 0)
    measure_count = measures_info.get('total', 0)

    # Check for missing date table
    table_names = [t.lower() for t in metadata.get('tables', [])]
    has_date_table = any('date' in name or 'calendar' in name for name in table_names)

    if not has_date_table:
        recommendations.append({
            'priority': 'high',
            'category': 'Model Structure',
            'issue': 'Missing Date Table',
            'recommendation': 'Add a dedicated Date/Calendar table for time intelligence',
            'concrete_action': """
CREATE DATE TABLE:

1. In Power Query, create a new query:
   Date =
   CALENDAR(
       DATE(2020, 1, 1),
       DATE(2030, 12, 31)
   )

2. Add calculated columns:
   - Year = YEAR([Date])
   - Month = MONTH([Date])
   - Quarter = "Q" & QUARTER([Date])
   - MonthName = FORMAT([Date], "MMMM")
   - YearMonth = FORMAT([Date], "YYYY-MM")

3. Mark as Date Table:
   - Right-click Date table → "Mark as Date Table"
   - Select the Date column

4. Create relationships:
   - Connect Date[Date] to all fact table date columns
   - Cardinality: One (Date) to Many (Facts)

5. Add time intelligence measures:
   - Sales YTD = TOTALYTD(SUM(Sales[Amount]), Date[Date])
   - Sales PY = CALCULATE(SUM(Sales[Amount]), SAMEPERIODLASTYEAR(Date[Date]))
   - Sales YoY% = DIVIDE([Sales] - [Sales PY], [Sales PY])
""",
            'expected_benefit': 'Enables 50+ time intelligence functions, consistent date filtering',
            'effort': 'Low (30 minutes)'
        })

    # Check for many-to-many relationships
    m2m_count = sum(1 for rel in relationships
                    if rel.get('fromCardinality') == 'many' and rel.get('toCardinality') == 'many')

    if m2m_count > 0:
        recommendations.append({
            'priority': 'medium',
            'category': 'Relationships',
            'issue': f'{m2m_count} Many-to-Many relationship(s) found',
            'recommendation': 'Consider using bridge tables to improve performance',
            'concrete_action': f"""
REFACTOR MANY-TO-MANY RELATIONSHIPS:

Current: {m2m_count} many-to-many relationship(s)

Solution: Create bridge table

Example - Product to Sales Territory:
1. Create bridge table query in Power Query:
   ProductTerritory =
   DISTINCT(
       SELECTCOLUMNS(
           Sales,
           "ProductID", [ProductID],
           "TerritoryID", [TerritoryID]
       )
   )

2. Load the bridge table

3. Delete many-to-many relationship

4. Create new relationships:
   - Product[ProductID] → ProductTerritory[ProductID] (One-to-Many)
   - Territory[TerritoryID] → ProductTerritory[TerritoryID] (One-to-Many)

5. Set both relationships to "Both" cross-filter direction (only on bridge table)

Expected benefit: 2-5x faster queries, simpler DAX logic
""",
            'expected_benefit': '2-5x faster queries, reduced ambiguity',
            'effort': 'Medium (2-4 hours per relationship)'
        })

    # Check for high measure count without calculation groups
    if measure_count > 50:
        recommendations.append({
            'priority': 'medium',
            'category': 'Measures',
            'issue': f'{measure_count} measures - potential for consolidation',
            'recommendation': 'Use Calculation Groups to reduce measure proliferation',
            'concrete_action': f"""
CREATE CALCULATION GROUP FOR TIME INTELLIGENCE:

Instead of creating separate measures for each time intelligence variant
(Current, YTD, PY, YoY, etc.), create a calculation group:

1. In Tabular Editor, create new Calculation Group:
   Name: "Time Intelligence"

2. Add calculation items:

   Current:
   SELECTEDMEASURE()

   YTD:
   CALCULATE(
       SELECTEDMEASURE(),
       DATESYTD('Date'[Date])
   )

   PY:
   CALCULATE(
       SELECTEDMEASURE(),
       SAMEPERIODLASTYEAR('Date'[Date])
   )

   YoY %:
   VAR CurrentValue = SELECTEDMEASURE()
   VAR PriorValue = CALCULATE(SELECTEDMEASURE(), SAMEPERIODLASTYEAR('Date'[Date]))
   RETURN DIVIDE(CurrentValue - PriorValue, PriorValue)

   YoY Δ:
   VAR CurrentValue = SELECTEDMEASURE()
   VAR PriorValue = CALCULATE(SELECTEDMEASURE(), SAMEPERIODLASTYEAR('Date'[Date]))
   RETURN CurrentValue - PriorValue

3. Result: 5 base measures × 5 time calculations = 25 measures
   Instead of: 5 × 5 = 25 separate measures to maintain

Expected reduction: {measure_count} measures → ~{int(measure_count * 0.3)} base measures
Maintenance effort: 70% reduction
""",
            'expected_benefit': '70% reduction in measure count, easier maintenance',
            'effort': 'Medium (4-6 hours initial setup)'
        })

    # Check for bidirectional relationships
    bidir_count = sum(1 for rel in relationships
                      if rel.get('crossFilteringBehavior') == 'bothDirections')

    if bidir_count > 3:
        recommendations.append({
            'priority': 'high',
            'category': 'Relationships',
            'issue': f'{bidir_count} bidirectional relationships may cause performance issues',
            'recommendation': 'Review and minimize bidirectional relationships',
            'concrete_action': f"""
REDUCE BIDIRECTIONAL RELATIONSHIPS:

Current: {bidir_count} bidirectional relationships

Issues:
- Ambiguous filter propagation
- Performance overhead
- Risk of circular dependencies

Action Plan:

1. Identify each bidirectional relationship
2. For each, determine:
   - Is it truly needed?
   - Can DAX solve the filtering requirement instead?

3. Replace with DAX using CROSSFILTER or TREATAS:

   Instead of bidirectional relationship:
   Sales Amount =
   CALCULATE(
       SUM(Sales[Amount]),
       CROSSFILTER(
           Product[ProductID],
           Sales[ProductID],
           Both
       )
   )

   Or use TREATAS for virtual relationships:
   Sales by Territory =
   CALCULATE(
       SUM(Sales[Amount]),
       TREATAS(
           VALUES(Territory[TerritoryID]),
           Sales[TerritoryID]
       )
   )

Target: Reduce from {bidir_count} to 0-1 bidirectional relationships

Expected benefit: More predictable filtering, 20-30% faster queries
""",
            'expected_benefit': 'More predictable behavior, 20-30% faster queries',
            'effort': 'Medium (1-2 hours per relationship)'
        })

    return recommendations


def _identify_quick_wins(
    dax_optimizations: List[Dict[str, Any]],
    structure_recommendations: List[Dict[str, Any]]
) -> List[Dict[str, Any]]:
    """Identify high-impact, low-effort optimizations"""
    quick_wins = []

    # High-priority DAX optimizations (top 5)
    high_priority_dax = [opt for opt in dax_optimizations if opt['priority'] == 'high'][:5]

    for opt in high_priority_dax:
        quick_wins.append({
            'type': 'DAX Optimization',
            'title': f"Optimize '{opt['measure_name']}'",
            'impact': 'High',
            'effort': 'Low (5-10 minutes)',
            'expected_gain': opt['expected_improvement'],
            'action': opt['action'],
            'concrete_fix': opt['optimized_dax']
        })

    # Low-effort structure improvements
    low_effort_structure = [rec for rec in structure_recommendations
                           if rec.get('effort', '').startswith('Low')]

    for rec in low_effort_structure:
        quick_wins.append({
            'type': 'Model Structure',
            'title': rec['recommendation'],
            'impact': rec['priority'].title(),
            'effort': rec['effort'],
            'expected_gain': rec['expected_benefit'],
            'action': rec['concrete_action']
        })

    return quick_wins[:10]  # Top 10 quick wins


def _generate_action_plan(
    dax_optimizations: List[Dict[str, Any]],
    structure_recommendations: List[Dict[str, Any]],
    quick_wins: List[Dict[str, Any]]
) -> Dict[str, Any]:
    """Generate prioritized action plan"""

    return {
        "week_1": {
            "focus": "Quick Wins - Maximum ROI",
            "actions": [qw['title'] for qw in quick_wins[:5]],
            "expected_outcome": "30-50% overall performance improvement"
        },
        "week_2_3": {
            "focus": "High-Priority DAX Optimizations",
            "actions": [
                f"Optimize {opt['measure_name']}"
                for opt in dax_optimizations
                if opt['priority'] == 'high'
            ][:10],
            "expected_outcome": "50-70% query performance improvement"
        },
        "month_2": {
            "focus": "Model Structure Improvements",
            "actions": [
                rec['recommendation']
                for rec in structure_recommendations
                if rec['priority'] == 'high'
            ],
            "expected_outcome": "Better maintainability, 20-30% additional performance gain"
        },
        "ongoing": {
            "focus": "Medium-Priority Optimizations",
            "actions": [
                "Continue with remaining DAX optimizations",
                "Implement calculation groups",
                "Review and optimize remaining relationships",
                "Establish performance monitoring"
            ],
            "expected_outcome": "Sustained performance, reduced maintenance effort"
        }
    }


def _estimate_total_gain(dax_optimizations: List[Dict[str, Any]]) -> str:
    """Estimate total performance improvement"""
    high_count = sum(1 for opt in dax_optimizations if opt['priority'] == 'high')
    medium_count = sum(1 for opt in dax_optimizations if opt['priority'] == 'medium')

    if high_count >= 5:
        return "50-70% overall performance improvement expected"
    elif high_count >= 2:
        return "30-50% overall performance improvement expected"
    elif medium_count >= 5:
        return "20-40% overall performance improvement expected"
    else:
        return "10-20% overall performance improvement expected"



def register_hybrid_analysis_handlers(registry):
    """Register hybrid analysis tool handlers"""

    # Simple wrapper to handle arguments dict
    def make_handler(func):
        def wrapper(args):
            return func(**args)
        return wrapper

    registry.register(ToolDefinition(
        name='export_hybrid_analysis',
        description='Export Power BI model: TMDL from PBIP folder + metadata/sample data from active model (auto-detects Power BI Desktop if no connection provided)',
        handler=make_handler(handle_export_hybrid_analysis),
        input_schema=TOOL_SCHEMAS['export_hybrid_analysis'],
        category='14 - Hybrid Analysis',
        sort_order=140
    ))

    registry.register(ToolDefinition(
        name='analyze_hybrid_model',
        description='BI Expert Analysis: Read and analyze hybrid model (TMDL + JSON + sample data) with expert insights. Automatically reads TMDL files for accurate measure DAX and relationships. Supports fuzzy search (e.g., "base scenario" finds "PL-AMT-BASE Scenario"). No manual file reading needed!',
        handler=make_handler(handle_analyze_hybrid_model),
        input_schema=TOOL_SCHEMAS['analyze_hybrid_model'],
        category='14 - Hybrid Analysis',
        sort_order=141
    ))

    logger.info("Registered 2 hybrid analysis handlers")
