"""Documentation generation orchestration."""
import logging
from typing import Any, Dict, List, Optional
from .base_orchestrator import BaseOrchestrator
from core.utilities.type_conversions import safe_bool

logger = logging.getLogger(__name__)

class DocumentationOrchestrator(BaseOrchestrator):
    """Handles documentation generation workflows."""

    def generate_docs_safe(self, connection_state) -> Dict[str, Any]:
        """Generate documentation, preferring safe/lightweight operations for large models."""
        from core.validation.error_handler import ErrorHandler

        if not connection_state.is_connected():
            return ErrorHandler.handle_not_connected()
        exporter = connection_state.model_exporter
        executor = connection_state.query_executor
        if not exporter:
            return ErrorHandler.handle_manager_unavailable('model_exporter')
        if not executor:
            return ErrorHandler.handle_manager_unavailable('query_executor')

        # Use get_model_summary first to get scale hints
        summary = exporter.get_model_summary(executor)
        notes: List[str] = []
        if not summary.get("success"):
            notes.append("Model summary unavailable; proceeding to basic documentation")
            return exporter.generate_documentation(executor)

        # If model scale is high, prefer lightweight docs
        counts = summary.get("counts") or {}
        # Prefer named counts if provided by exporter; otherwise fallback heuristics
        measures_count = counts.get("measures", counts.get("measure_count", 0))
        tables_count = counts.get("tables", counts.get("table_count", 0))
        columns_count = counts.get("columns", counts.get("column_count", 0))
        relationships_count = counts.get("relationships", counts.get("relationship_count", 0))

        is_large = (
            measures_count > 2000 or
            tables_count > 200 or
            columns_count > 10000 or
            relationships_count > 5000
        )
        if is_large:
            notes.append("Large model detected; generating lightweight documentation")
        doc = exporter.generate_documentation(executor)
        if notes:
            doc.setdefault("notes", []).extend(notes)
        return doc

    def generate_documentation_profiled(self, connection_state, format: str = 'markdown', include_examples: bool = False) -> Dict[str, Any]:
        """Generate profiled documentation with specified format."""
        from core.validation.error_handler import ErrorHandler

        if not connection_state.is_connected():
            return ErrorHandler.handle_not_connected()
        exporter = connection_state.model_exporter
        executor = connection_state.query_executor
        if not exporter:
            return ErrorHandler.handle_manager_unavailable('model_exporter')
        if not executor:
            return ErrorHandler.handle_manager_unavailable('query_executor')
        doc = exporter.generate_documentation(executor)
        doc.setdefault('format', format)
        doc.setdefault('include_examples', include_examples)
        return doc

    def generate_model_documentation_word(
        self,
        connection_state,
        output_dir: Optional[str] = None,
        include_hidden: bool = True,
        dependency_depth: int = 1,
        export_pdf: bool = False,
    ) -> Dict[str, Any]:
        """Generate comprehensive Word documentation for the model."""
        from core.validation.error_handler import ErrorHandler
        from core.documentation.data_collector import collect_model_documentation
        from core.documentation.documentation_builder import (
            render_word_report,
            save_snapshot,
        )

        if not connection_state.is_connected():
            return ErrorHandler.handle_not_connected()

        try:
            lightweight_bpa = self.validate_best_practices(connection_state)
        except Exception:
            lightweight_bpa = None

        context = collect_model_documentation(
            connection_state,
            include_hidden=include_hidden,
            dependency_depth=dependency_depth,
            lightweight_best_practices=lightweight_bpa if isinstance(lightweight_bpa, dict) else None,
        )
        if not context.get('success'):
            return context

        # graph_path, graph_notes = generate_relationship_graph(context.get('relationships', [])  # Visualization removed, output_dir)
        graph_path = None  # Visualization removed
        graph_notes = []  # Visualization removed

        doc_result = render_word_report(
            context,
            output_dir=output_dir,
            graph_path=graph_path,
            graph_notes=graph_notes,
            change_summary=None,
            mode='full',
            export_pdf=export_pdf,
        )
        if not doc_result.get('success'):
            return doc_result

        snapshot_result = save_snapshot(context, output_dir)
        response: Dict[str, Any] = {
            'success': True,
            'doc_path': doc_result.get('doc_path'),
            'snapshot_path': snapshot_result.get('snapshot_path'),
            'graph_path': graph_path,
            'counts': (context.get('summary') or {}).get('counts'),
            'best_practices': context.get('best_practices'),
        }
        if doc_result.get('pdf_path'):
            response['pdf_path'] = doc_result.get('pdf_path')
        if doc_result.get('pdf_warning'):
            response['pdf_warning'] = doc_result.get('pdf_warning')
        if graph_notes:
            response['graph_notes'] = graph_notes
        if context.get('notes'):
            response['notes'] = context.get('notes')
        return response

    def update_model_documentation_word(
        self,
        connection_state,
        output_dir: Optional[str] = None,
        snapshot_path: Optional[str] = None,
        include_hidden: bool = True,
        dependency_depth: int = 1,
        export_pdf: bool = False,
    ) -> Dict[str, Any]:
        """Update existing Word documentation with changes detected."""
        from core.validation.error_handler import ErrorHandler
        from core.documentation.data_collector import collect_model_documentation
        from core.documentation.documentation_builder import (
            render_word_report,
            save_snapshot,
            load_snapshot,
            snapshot_from_context,
            compute_diff,
        )

        if not connection_state.is_connected():
            return ErrorHandler.handle_not_connected()

        qe = getattr(connection_state, 'query_executor', None)
        if not qe:
            return ErrorHandler.handle_manager_unavailable('query_executor')

        try:
            lightweight_bpa = self.validate_best_practices(connection_state)
        except Exception:
            lightweight_bpa = None

        try:
            database_name = qe._get_database_name()
        except Exception:
            database_name = None

        previous_snapshot = load_snapshot(snapshot_path, output_dir, database_name)

        context = collect_model_documentation(
            connection_state,
            include_hidden=include_hidden,
            dependency_depth=dependency_depth,
            lightweight_best_practices=lightweight_bpa if isinstance(lightweight_bpa, dict) else None,
        )
        if not context.get('success'):
            return context

        new_snapshot = snapshot_from_context(context)
        diff = compute_diff(previous_snapshot, new_snapshot)

        # graph_path, graph_notes = generate_relationship_graph(context.get('relationships', [])  # Visualization removed, output_dir)
        graph_path = None  # Visualization removed
        graph_notes = []  # Visualization removed

        doc_result = render_word_report(
            context,
            output_dir=output_dir,
            graph_path=graph_path,
            graph_notes=graph_notes,
            change_summary=diff,
            mode='update',
            export_pdf=export_pdf,
        )
        if not doc_result.get('success'):
            return doc_result

        snapshot_result = save_snapshot(context, output_dir)

        response: Dict[str, Any] = {
            'success': True,
            'doc_path': doc_result.get('doc_path'),
            'snapshot_path': snapshot_result.get('snapshot_path'),
            'graph_path': graph_path,
            'change_summary': diff,
            'best_practices': context.get('best_practices'),
        }
        if doc_result.get('pdf_path'):
            response['pdf_path'] = doc_result.get('pdf_path')
        if doc_result.get('pdf_warning'):
            response['pdf_warning'] = doc_result.get('pdf_warning')
        if graph_notes:
            response['graph_notes'] = graph_notes
        if context.get('notes'):
            response['notes'] = context.get('notes')
        if not diff.get('changes_detected'):
            response['message'] = 'No structural changes detected; documentation refreshed with latest metadata.'
        return response

    def export_interactive_relationship_graph(
        self,
        connection_state,
        output_dir: Optional[str] = None,
        include_hidden: bool = True,
        dependency_depth: int = 5,
    ) -> Dict[str, Any]:
        """Export an interactive HTML dependency explorer (replaces old relationship graph).

        This generates a comprehensive interactive HTML app that shows:
        - Tables with their dependencies, measures, columns, and relationships
        - Measures with dependency trees (forward and reverse)
        - Interactive relationship graph visualization with D3.js
        - Full search and navigation capabilities

        Args:
            connection_state: Active connection state
            output_dir: Optional output directory for HTML file
            include_hidden: Include hidden objects in analysis (default: True)
            dependency_depth: Maximum depth for dependency tree analysis

        Returns:
            Dictionary with success status and file path
        """
        from core.validation.error_handler import ErrorHandler

        if not connection_state.is_connected():
            return ErrorHandler.handle_not_connected()

        try:
            # Use new comprehensive dependency explorer
            from core.documentation import generate_interactive_dependency_explorer

            html_path, error_notes = generate_interactive_dependency_explorer(
                connection_state,
                output_dir=output_dir,
                include_hidden=include_hidden,
                dependency_depth=dependency_depth
            )

            if html_path:
                return {
                    'success': True,
                    'html_path': html_path,
                    'notes': error_notes if error_notes else []
                }
            else:
                # Provide more detailed error information
                error_msg = 'Failed to generate interactive dependency explorer'
                if error_notes and len(error_notes) > 0:
                    error_msg = error_notes[0] if isinstance(error_notes, list) else str(error_notes)
                return {
                    'success': False,
                    'error': error_msg,
                    'notes': error_notes if isinstance(error_notes, list) else [str(error_notes)]
                }

        except Exception as e:
            logger.error(f"Error generating dependency explorer: {e}", exc_info=True)
            return {
                'success': False,
                'error': f'Failed to generate dependency explorer: {str(e)}'
            }

    def export_interactive_relationship_graph_legacy(
        self,
        connection_state,
        output_dir: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Legacy method for backward compatibility - exports simple Plotly relationship graph."""
        from core.validation.error_handler import ErrorHandler

        if not connection_state.is_connected():
            return ErrorHandler.handle_not_connected()

        qe = getattr(connection_state, 'query_executor', None)
        if not qe:
            return ErrorHandler.handle_manager_unavailable('query_executor')

        # Get relationships
        relationships_res = qe.execute_info_query("RELATIONSHIPS")
        if not relationships_res.get('success'):
            return {
                'success': False,
                'error': 'Failed to fetch relationships from model',
                'details': relationships_res
            }

        relationships_rows = relationships_res.get('rows', [])
        if not relationships_rows:
            return {
                'success': False,
                'error': 'No relationships found in the model'
            }

        # Convert to standard format
        from core.documentation.documentation_builder import generate_interactive_relationship_graph

        def _pick(row: Dict[str, Any], *keys: str, default: Any = None) -> Any:
            for key in keys:
                if key in row and row[key] not in (None, ""):
                    return row[key]
                alt = f"[{key}]"
                if alt in row and row[alt] not in (None, ""):
                    return row[alt]
            return default

        relationships: List[Dict[str, Any]] = []
        for rel in relationships_rows:
            relationships.append({
                "from_table": str(_pick(rel, "FromTable", default="")),
                "from_column": str(_pick(rel, "FromColumn", default="")),
                "to_table": str(_pick(rel, "ToTable", default="")),
                "to_column": str(_pick(rel, "ToColumn", default="")),
                "is_active": safe_bool(_pick(rel, "IsActive", default=False)),
                "cardinality": str(_pick(rel, "Cardinality", default=_pick(rel, "RelationshipType", default=""))),
                "direction": str(_pick(rel, "CrossFilterDirection", default="")),
            })

        graph_path, graph_notes = generate_interactive_relationship_graph(relationships, output_dir)

        if graph_path:
            return {
                'success': True,
                'graph_path': graph_path,
                'relationships_count': len(relationships),
                'notes': graph_notes
            }
        else:
            return {
                'success': False,
                'error': 'Failed to generate interactive relationship graph',
                'notes': graph_notes
            }

    def auto_document(self, connection_manager, connection_state, profile: str = 'light', include_lineage: bool = False) -> Dict[str, Any]:
        """Automated documentation generation workflow."""
        from core.orchestration.connection_orchestrator import ConnectionOrchestrator

        actions: List[Dict[str, Any]] = []
        conn_orch = ConnectionOrchestrator(self.config)
        ensured = conn_orch.ensure_connected(connection_manager, connection_state)
        actions.append({'action': 'ensure_connected', 'result': ensured})
        if not ensured.get('success'):
            return {'success': False, 'phase': 'ensure_connected', 'actions': actions, 'final': ensured}
        summary = conn_orch.summarize_model_safely(connection_state)
        actions.append({'action': 'summarize_model_safely', 'result': summary})
        docs = self.generate_docs_safe(connection_state)
        actions.append({'action': 'generate_docs_safe', 'result': docs})
        return {'success': docs.get('success', False), 'actions': actions, 'final': docs}

    def validate_best_practices(self, connection_state) -> Dict[str, Any]:
        """Validate model best practices - helper method for documentation."""
        from core.validation.error_handler import ErrorHandler

        if not connection_state.is_connected():
            return ErrorHandler.handle_not_connected()
        executor = connection_state.query_executor
        validator = connection_state.model_validator
        if not executor:
            return ErrorHandler.handle_manager_unavailable('query_executor')
        issues: List[Dict[str, Any]] = []
        # Include integrity issues if validator available
        if validator:
            integrity = validator.validate_model_integrity()
            if integrity.get('success'):
                for i in integrity.get('issues', []):
                    issues.append(i)
        # Simple naming checks
        tables = executor.execute_info_query('TABLES')
        if tables.get('success'):
            for t in tables.get('rows', []):
                name = t.get('Name') or ''
                if name != name.strip():
                    issues.append({'type': 'naming', 'severity': 'low', 'object': f"Table:{name}", 'description': 'Leading/trailing spaces in table name'})
        measures = executor.execute_info_query('MEASURES')
        if measures.get('success'):
            for m in measures.get('rows', []):
                name = m.get('Name') or ''
                if ' ' in name and name.strip().endswith(')'):
                    pass
                # Example heuristic: discourage very short names
                if len(name.strip()) < 2:
                    issues.append({'type': 'naming', 'severity': 'low', 'object': f"Measure:{name}", 'description': 'Very short measure name'})
        return {'success': True, 'issues': issues, 'total_issues': len(issues)}

    def generate_word_documentation(
        self,
        connection_state,
        output_dir: Optional[str] = None,
        include_hidden: bool = True,
        dependency_depth: int = 1,
        export_pdf: bool = False,
    ) -> Dict[str, Any]:
        """
        Alias for generate_model_documentation_word for backward compatibility.
        """
        return self.generate_model_documentation_word(
            connection_state,
            output_dir=output_dir,
            include_hidden=include_hidden,
            dependency_depth=dependency_depth,
            export_pdf=export_pdf
        )

    def update_word_documentation(
        self,
        connection_state,
        snapshot_path: Optional[str] = None,
        output_dir: Optional[str] = None,
        include_hidden: bool = True,
        dependency_depth: int = 1,
        export_pdf: bool = False,
    ) -> Dict[str, Any]:
        """
        Alias for update_model_documentation_word for backward compatibility.
        """
        return self.update_model_documentation_word(
            connection_state,
            output_dir=output_dir,
            snapshot_path=snapshot_path,
            include_hidden=include_hidden,
            dependency_depth=dependency_depth,
            export_pdf=export_pdf
        )

    def export_html_explorer(
        self,
        connection_state,
        output_dir: Optional[str] = None,
        include_hidden: bool = True,
        dependency_depth: int = 5,
    ) -> Dict[str, Any]:
        """
        Alias for export_interactive_relationship_graph for backward compatibility.
        """
        return self.export_interactive_relationship_graph(
            connection_state,
            output_dir=output_dir,
            include_hidden=include_hidden,
            dependency_depth=dependency_depth
        )
