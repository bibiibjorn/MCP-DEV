"""
Query Plan Analyzer for DAX queries.

This module analyzes query plans from Extended Events trace data,
identifying scan operations, aggregations, joins, and bottlenecks.
"""

import logging
import re
import xml.etree.ElementTree as ET
from typing import Any, Dict, List, Optional, Set
from collections import defaultdict

logger = logging.getLogger(__name__)


class QueryPlanAnalyzer:
    """
    Analyzer for DAX query execution plans.

    Parses query plan data from trace events and provides insights into
    query execution strategy and bottlenecks.
    """

    def __init__(self):
        """Initialize query plan analyzer."""
        self.plans_cache: Dict[str, Dict[str, Any]] = {}

    def analyze_query_plan(self, trace_events: List[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
        """
        Analyze query plan from trace events.

        Args:
            trace_events: List of trace events captured during query execution

        Returns:
            Dictionary with query plan analysis, or None if no plan data found
        """
        # Look for query subspace events (contains query plan information)
        subspace_events = [
            evt for evt in trace_events
            if evt.get("event") in ("QuerySubcube", "QuerySubcubeVerbose")
        ]

        if not subspace_events:
            logger.debug("No query subspace events found in trace")
            return None

        # Parse plan from events
        plan_tree = self._parse_plan_from_events(subspace_events)

        if not plan_tree:
            return None

        # Analyze plan structure
        analysis = {
            "success": True,
            "plan_tree": plan_tree,
            "operations": self._extract_operations(plan_tree),
            "table_scans": self._identify_table_scans(plan_tree),
            "aggregations": self._identify_aggregations(plan_tree),
            "joins": self._identify_joins(plan_tree),
            "bottlenecks": self._identify_bottlenecks(plan_tree, trace_events),
            "recommendations": self._generate_recommendations(plan_tree),
        }

        return analysis

    def _parse_plan_from_events(self, events: List[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
        """
        Parse query plan tree from subspace events.

        In Power BI Desktop, query plan information is limited compared to
        SQL Server Analysis Services. We extract what's available from TextData.
        """
        plan_nodes: List[Dict[str, Any]] = []

        for evt in events:
            text_data = evt.get("text", "")
            if not text_data:
                continue

            # Extract operation info from text data
            node = self._parse_plan_node(text_data, evt)
            if node:
                plan_nodes.append(node)

        if not plan_nodes:
            return None

        # Build tree structure
        root_node = {
            "type": "root",
            "operation": "Query Execution",
            "children": plan_nodes,
            "estimated_rows": sum(n.get("estimated_rows", 0) for n in plan_nodes),
        }

        return root_node

    def _parse_plan_node(self, text_data: str, event: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Parse a single plan node from event text data.

        Args:
            text_data: Text data from trace event
            event: Full event dictionary

        Returns:
            Plan node dictionary or None
        """
        # Try to identify operation type
        operation_type = "Unknown"
        table_name = None
        estimated_rows = 0

        # Look for common patterns
        if "Scan" in text_data or "SCAN" in text_data:
            operation_type = "Table Scan"
            # Try to extract table name
            match = re.search(r"'([^']+)'", text_data)
            if match:
                table_name = match.group(1)

        elif "Join" in text_data or "JOIN" in text_data:
            operation_type = "Join"

        elif "Aggregate" in text_data or "SUM" in text_data or "COUNT" in text_data:
            operation_type = "Aggregation"

        elif "Filter" in text_data or "WHERE" in text_data:
            operation_type = "Filter"

        # Extract estimated row count if present
        row_match = re.search(r"rows?[:\s]+(\d+)", text_data, re.IGNORECASE)
        if row_match:
            estimated_rows = int(row_match.group(1))

        node = {
            "type": operation_type,
            "operation": text_data[:100] if len(text_data) > 100 else text_data,
            "table": table_name,
            "estimated_rows": estimated_rows,
            "duration_ms": event.get("duration_ms", 0),
            "cpu_time_ms": event.get("cpu_time_ms", 0),
        }

        return node

    def _extract_operations(self, plan_tree: Dict[str, Any]) -> Dict[str, int]:
        """
        Extract and count all operations in the plan tree.

        Returns:
            Dictionary mapping operation type to count
        """
        operation_counts: Dict[str, int] = defaultdict(int)

        def traverse(node):
            if not node:
                return
            operation_counts[node.get("type", "Unknown")] += 1
            for child in node.get("children", []):
                traverse(child)

        traverse(plan_tree)
        return dict(operation_counts)

    def _identify_table_scans(self, plan_tree: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Identify all table scan operations.

        Returns:
            List of table scan operation details
        """
        scans: List[Dict[str, Any]] = []

        def traverse(node):
            if not node:
                return
            if node.get("type") == "Table Scan":
                scans.append({
                    "table": node.get("table", "Unknown"),
                    "estimated_rows": node.get("estimated_rows", 0),
                    "duration_ms": node.get("duration_ms", 0),
                    "cpu_time_ms": node.get("cpu_time_ms", 0),
                })
            for child in node.get("children", []):
                traverse(child)

        traverse(plan_tree)
        return scans

    def _identify_aggregations(self, plan_tree: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Identify all aggregation operations.

        Returns:
            List of aggregation operation details
        """
        aggregations: List[Dict[str, Any]] = []

        def traverse(node):
            if not node:
                return
            if node.get("type") == "Aggregation":
                aggregations.append({
                    "operation": node.get("operation", ""),
                    "estimated_rows": node.get("estimated_rows", 0),
                    "duration_ms": node.get("duration_ms", 0),
                })
            for child in node.get("children", []):
                traverse(child)

        traverse(plan_tree)
        return aggregations

    def _identify_joins(self, plan_tree: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Identify all join operations.

        Returns:
            List of join operation details
        """
        joins: List[Dict[str, Any]] = []

        def traverse(node):
            if not node:
                return
            if node.get("type") == "Join":
                joins.append({
                    "operation": node.get("operation", ""),
                    "estimated_rows": node.get("estimated_rows", 0),
                    "duration_ms": node.get("duration_ms", 0),
                })
            for child in node.get("children", []):
                traverse(child)

        traverse(plan_tree)
        return joins

    def _identify_bottlenecks(
        self,
        plan_tree: Dict[str, Any],
        trace_events: List[Dict[str, Any]],
    ) -> List[Dict[str, Any]]:
        """
        Identify performance bottlenecks in the query plan.

        Args:
            plan_tree: Parsed query plan tree
            trace_events: Original trace events with timing data

        Returns:
            List of identified bottlenecks with recommendations
        """
        bottlenecks: List[Dict[str, Any]] = []

        # Check for large table scans
        scans = self._identify_table_scans(plan_tree)
        for scan in scans:
            if scan.get("estimated_rows", 0) > 1_000_000:
                bottlenecks.append({
                    "type": "Large Table Scan",
                    "severity": "High",
                    "table": scan.get("table", "Unknown"),
                    "estimated_rows": scan["estimated_rows"],
                    "impact": "Scanning large tables can cause performance issues",
                    "recommendation": "Consider adding filters or creating aggregations",
                })

        # Check for expensive joins
        joins = self._identify_joins(plan_tree)
        for join in joins:
            if join.get("duration_ms", 0) > 100:
                bottlenecks.append({
                    "type": "Expensive Join",
                    "severity": "Medium",
                    "duration_ms": join["duration_ms"],
                    "impact": "Join operation taking significant time",
                    "recommendation": "Review relationship cardinality and direction",
                })

        # Check for many aggregations
        aggregations = self._identify_aggregations(plan_tree)
        if len(aggregations) > 10:
            bottlenecks.append({
                "type": "Multiple Aggregations",
                "severity": "Medium",
                "count": len(aggregations),
                "impact": "Many aggregations can slow down query execution",
                "recommendation": "Consider pre-aggregating data or simplifying calculations",
            })

        return bottlenecks

    def _generate_recommendations(self, plan_tree: Dict[str, Any]) -> List[str]:
        """
        Generate optimization recommendations based on query plan.

        Args:
            plan_tree: Parsed query plan tree

        Returns:
            List of recommendation strings
        """
        recommendations: List[str] = []

        operations = self._extract_operations(plan_tree)

        # Check for table scans
        if operations.get("Table Scan", 0) > 5:
            recommendations.append(
                "Multiple table scans detected - consider adding filters early in the query"
            )

        # Check for aggregations
        if operations.get("Aggregation", 0) > 10:
            recommendations.append(
                "Many aggregations detected - consider using calculation groups or aggregation tables"
            )

        # Check for joins
        if operations.get("Join", 0) > 5:
            recommendations.append(
                "Multiple joins detected - review relationship design and consider star schema"
            )

        # General recommendations
        scans = self._identify_table_scans(plan_tree)
        total_scan_rows = sum(s.get("estimated_rows", 0) for s in scans)
        if total_scan_rows > 10_000_000:
            recommendations.append(
                f"Query scanning {total_scan_rows:,} total rows - consider partitioning or aggregations"
            )

        if not recommendations:
            recommendations.append("Query plan looks reasonable - no major issues detected")

        return recommendations

    def generate_plan_tree_visualization(self, plan_analysis: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate visualization-ready tree data for the query plan.

        Args:
            plan_analysis: Query plan analysis from analyze_query_plan()

        Returns:
            Dictionary with tree visualization data for rendering
        """
        plan_tree = plan_analysis.get("plan_tree")
        if not plan_tree:
            return {"type": "tree", "nodes": [], "edges": []}

        nodes: List[Dict[str, Any]] = []
        edges: List[Dict[str, Any]] = []
        node_id = 0

        def traverse(node, parent_id=None):
            nonlocal node_id
            current_id = node_id
            node_id += 1

            nodes.append({
                "id": current_id,
                "label": node.get("type", "Unknown"),
                "operation": node.get("operation", ""),
                "estimated_rows": node.get("estimated_rows", 0),
                "duration_ms": node.get("duration_ms", 0),
            })

            if parent_id is not None:
                edges.append({
                    "from": parent_id,
                    "to": current_id,
                })

            for child in node.get("children", []):
                traverse(child, current_id)

        traverse(plan_tree)

        return {
            "type": "tree",
            "nodes": nodes,
            "edges": edges,
        }
