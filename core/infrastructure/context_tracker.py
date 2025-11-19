"""
Context Tracking System

This module tracks analysis context across multiple tool calls to enable
intelligent suggestions and context-aware tool orchestration.
"""

from typing import Dict, Any, List, Optional, Set
from dataclasses import dataclass, field
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


@dataclass
class AnalysisContext:
    """Tracks context across multiple tool calls"""
    session_id: str
    focus_object: Optional[str] = None  # e.g., "Sales[Total Revenue]"
    focus_type: Optional[str] = None  # "measure", "table", "relationship", "model"
    analyzed_objects: List[str] = field(default_factory=list)
    relationships_involved: List[str] = field(default_factory=list)
    tables_involved: Set[str] = field(default_factory=set)
    measures_involved: Set[str] = field(default_factory=set)
    columns_involved: Set[str] = field(default_factory=set)
    discovered_issues: List[Dict[str, Any]] = field(default_factory=list)
    performance_data: Dict[str, Any] = field(default_factory=dict)
    tools_used: List[str] = field(default_factory=list)
    timestamp: datetime = field(default_factory=datetime.now)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def add_table(self, table_name: str):
        """Add a table to the context"""
        if table_name:
            self.tables_involved.add(table_name)

    def add_measure(self, measure_name: str, table_name: Optional[str] = None):
        """Add a measure to the context"""
        if measure_name:
            if table_name:
                self.measures_involved.add(f"{table_name}[{measure_name}]")
            else:
                self.measures_involved.add(measure_name)

    def add_column(self, column_name: str, table_name: Optional[str] = None):
        """Add a column to the context"""
        if column_name:
            if table_name:
                self.columns_involved.add(f"{table_name}[{column_name}]")
            else:
                self.columns_involved.add(column_name)


class ContextTracker:
    """Tracks analysis context across tool calls"""

    def __init__(self):
        self.current_context: Optional[AnalysisContext] = None
        self.context_history: List[AnalysisContext] = []
        self._max_history = 10  # Keep last 10 contexts

    def start_analysis(self, object_name: str, object_type: str, metadata: Optional[Dict[str, Any]] = None):
        """
        Start new analysis context

        Args:
            object_name: Name of the object being analyzed (e.g., "Sales[Total Revenue]")
            object_type: Type of object ("measure", "table", "relationship", "model")
            metadata: Optional metadata about the analysis
        """
        # Save previous context to history
        if self.current_context:
            self.context_history.append(self.current_context)
            # Trim history if needed
            if len(self.context_history) > self._max_history:
                self.context_history = self.context_history[-self._max_history:]

        # Create new context
        self.current_context = AnalysisContext(
            session_id=str(datetime.now().timestamp()),
            focus_object=object_name,
            focus_type=object_type,
            metadata=metadata or {}
        )

        logger.info(f"Started analysis context: {object_type}:{object_name}")

    def add_tool_used(self, tool_name: str):
        """Track that a tool was used in current context"""
        if self.current_context:
            if tool_name not in self.current_context.tools_used:
                self.current_context.tools_used.append(tool_name)

    def add_analyzed_object(self, object_name: str, object_type: str):
        """Track that we analyzed an object"""
        if self.current_context:
            obj_key = f"{object_type}:{object_name}"
            if obj_key not in self.current_context.analyzed_objects:
                self.current_context.analyzed_objects.append(obj_key)
                logger.debug(f"Added analyzed object: {obj_key}")

    def add_relationship(self, from_table: str, to_table: str, is_active: bool = True):
        """Track relationship discovered during analysis"""
        if self.current_context:
            rel_key = f"{from_table}→{to_table}"
            if not is_active:
                rel_key += " (inactive)"

            if rel_key not in self.current_context.relationships_involved:
                self.current_context.relationships_involved.append(rel_key)
                logger.debug(f"Added relationship: {rel_key}")

            # Also track tables
            self.current_context.add_table(from_table)
            self.current_context.add_table(to_table)

    def add_issue(self, issue: Dict[str, Any]):
        """Track discovered issue"""
        if self.current_context:
            self.current_context.discovered_issues.append(issue)
            logger.info(f"Added issue: {issue.get('category', 'Unknown')} - {issue.get('severity', 'medium')}")

    def add_performance_data(self, key: str, value: Any):
        """Add performance metric to current context"""
        if self.current_context:
            self.current_context.performance_data[key] = value

    def get_enrichment_suggestions(self) -> List[Dict[str, Any]]:
        """
        Get suggestions for additional analysis based on current context

        Returns:
            List of enrichment suggestions sorted by priority
        """
        suggestions = []

        if not self.current_context:
            return suggestions

        # If analyzing a measure but haven't checked dependencies
        if self.current_context.focus_type == "measure":
            if not any("analyze_measure_dependencies" in tool for tool in self.current_context.tools_used):
                suggestions.append({
                    'action': 'analyze_dependencies',
                    'tool': 'analyze_measure_dependencies',
                    'reason': 'Dependency analysis not performed yet',
                    'priority': 9,
                    'context': {
                        'measure': self.current_context.focus_object
                    }
                })

            if not any("dax_intelligence" in tool for tool in self.current_context.tools_used):
                suggestions.append({
                    'action': 'analyze_dax_patterns',
                    'tool': 'dax_intelligence',
                    'reason': 'DAX pattern analysis not performed yet',
                    'priority': 8
                })

            if not any("get_measure_impact" in tool for tool in self.current_context.tools_used):
                suggestions.append({
                    'action': 'check_impact',
                    'tool': 'get_measure_impact',
                    'reason': 'Impact analysis not performed yet',
                    'priority': 7
                })

        # If we found relationships but haven't validated cardinality
        if len(self.current_context.relationships_involved) > 0:
            if not any("validate" in tool for tool in self.current_context.tools_used):
                suggestions.append({
                    'action': 'validate_relationship_cardinality',
                    'reason': f'{len(self.current_context.relationships_involved)} relationships involved - validate cardinality',
                    'priority': 7
                })

        # If we found multiple tables but haven't checked relationships
        if len(self.current_context.tables_involved) > 1:
            if not any("list_relationships" in tool for tool in self.current_context.tools_used):
                suggestions.append({
                    'action': 'check_relationships',
                    'tool': 'list_relationships',
                    'reason': f'{len(self.current_context.tables_involved)} tables involved - check relationships between them',
                    'priority': 8
                })

            if not any("describe_table" in tool for tool in self.current_context.tools_used):
                suggestions.append({
                    'action': 'check_table_sizes',
                    'tool': 'describe_table',
                    'reason': 'Multiple tables involved - check for large fact tables',
                    'priority': 6
                })

        # If analyzing a table but haven't checked measures
        if self.current_context.focus_type == "table":
            if not any("list_measures" in tool for tool in self.current_context.tools_used):
                suggestions.append({
                    'action': 'list_measures_in_table',
                    'tool': 'list_measures',
                    'reason': 'Check what measures exist in this table',
                    'priority': 7
                })

            if not any("list_relationships" in tool for tool in self.current_context.tools_used):
                suggestions.append({
                    'action': 'check_table_relationships',
                    'tool': 'list_relationships',
                    'reason': 'Check how this table relates to other tables',
                    'priority': 8
                })

        # Sort by priority (highest first)
        return sorted(suggestions, key=lambda x: x['priority'], reverse=True)

    def get_context_summary(self) -> Dict[str, Any]:
        """Get summary of current context"""
        if not self.current_context:
            return {'status': 'no_active_context'}

        return {
            'status': 'active',
            'focus': f"{self.current_context.focus_type}:{self.current_context.focus_object}",
            'tools_used': len(self.current_context.tools_used),
            'tables_involved': len(self.current_context.tables_involved),
            'measures_involved': len(self.current_context.measures_involved),
            'relationships_involved': len(self.current_context.relationships_involved),
            'issues_found': len(self.current_context.discovered_issues),
            'analyzed_objects': len(self.current_context.analyzed_objects)
        }

    def get_relevant_context_for_tool(self, tool_name: str) -> Dict[str, Any]:
        """
        Get relevant context information for a specific tool

        Args:
            tool_name: Name of the tool about to be executed

        Returns:
            Dictionary of relevant context information
        """
        if not self.current_context:
            return {}

        context = {
            'focus_object': self.current_context.focus_object,
            'focus_type': self.current_context.focus_type
        }

        # Add relevant context based on tool
        if 'relationship' in tool_name.lower():
            context['tables_involved'] = list(self.current_context.tables_involved)
            context['relationships_known'] = self.current_context.relationships_involved

        if 'measure' in tool_name.lower():
            context['measures_involved'] = list(self.current_context.measures_involved)
            context['tables_involved'] = list(self.current_context.tables_involved)

        if 'table' in tool_name.lower():
            context['tables_involved'] = list(self.current_context.tables_involved)

        return context

    def clear_context(self):
        """Clear current context (useful after completing an analysis)"""
        if self.current_context:
            self.context_history.append(self.current_context)
            if len(self.context_history) > self._max_history:
                self.context_history = self.context_history[-self._max_history:]

        self.current_context = None
        logger.info("Cleared current context")

    def get_previous_context(self, index: int = -1) -> Optional[AnalysisContext]:
        """Get a previous context from history"""
        try:
            return self.context_history[index]
        except (IndexError, KeyError):
            return None

    def has_analyzed_object(self, object_name: str, object_type: str) -> bool:
        """Check if an object was already analyzed in current context"""
        if not self.current_context:
            return False

        obj_key = f"{object_type}:{object_name}"
        return obj_key in self.current_context.analyzed_objects

    def get_analysis_insights(self) -> Dict[str, Any]:
        """Get insights from current analysis context"""
        if not self.current_context:
            return {'status': 'no_active_context'}

        insights = {
            'focus': {
                'object': self.current_context.focus_object,
                'type': self.current_context.focus_type
            },
            'scope': {
                'tables': list(self.current_context.tables_involved),
                'measures': list(self.current_context.measures_involved),
                'relationships': self.current_context.relationships_involved
            },
            'analysis_completeness': {
                'tools_used': self.current_context.tools_used,
                'objects_analyzed': len(self.current_context.analyzed_objects),
                'suggestions_available': len(self.get_enrichment_suggestions())
            },
            'issues': {
                'total': len(self.current_context.discovered_issues),
                'by_severity': self._group_issues_by_severity()
            }
        }

        # Add performance insights if available
        if self.current_context.performance_data:
            insights['performance'] = self.current_context.performance_data

        return insights

    def _group_issues_by_severity(self) -> Dict[str, int]:
        """Group discovered issues by severity"""
        severity_counts = {'critical': 0, 'high': 0, 'medium': 0, 'low': 0}

        for issue in self.current_context.discovered_issues:
            severity = issue.get('severity', 'medium').lower()
            if severity in severity_counts:
                severity_counts[severity] += 1

        return severity_counts

    def enrich_result_with_context(self, result: Dict[str, Any], tool_name: str) -> Dict[str, Any]:
        """
        Enrich a tool result with relevant context information

        Args:
            result: The tool result to enrich
            tool_name: Name of the tool that produced the result

        Returns:
            Enriched result with context information
        """
        if not self.current_context:
            return result

        # Add context metadata
        result['_context'] = {
            'focus_object': self.current_context.focus_object,
            'focus_type': self.current_context.focus_type,
            'session_id': self.current_context.session_id
        }

        # Add relevant context based on tool
        if tool_name == 'list_relationships' and self.current_context.tables_involved:
            # Filter relationships to show most relevant ones first
            if 'rows' in result:
                relevant_rels = []
                other_rels = []

                for rel in result['rows']:
                    from_table = rel.get('fromTable', '')
                    to_table = rel.get('toTable', '')

                    if from_table in self.current_context.tables_involved or to_table in self.current_context.tables_involved:
                        relevant_rels.append(rel)
                    else:
                        other_rels.append(rel)

                if relevant_rels:
                    result['_context_relevant'] = relevant_rels
                    result['_context']['relevant_count'] = len(relevant_rels)
                    result['_context']['message'] = f"Found {len(relevant_rels)} relationships relevant to current analysis"

        # Add enrichment suggestions
        suggestions = self.get_enrichment_suggestions()
        if suggestions:
            result['_enrichment_suggestions'] = suggestions

        return result
