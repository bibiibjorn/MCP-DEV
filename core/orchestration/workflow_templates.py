"""
Workflow Templates System

This module defines pre-configured multi-step analysis workflows that combine
multiple tools into intelligent analysis patterns.
"""

from typing import Dict, Any, List, Callable, Optional
from dataclasses import dataclass, field
import logging
from datetime import datetime

logger = logging.getLogger(__name__)


@dataclass
class WorkflowStep:
    """Single step in a workflow"""
    step_id: str
    tool_name: str
    description: str
    required: bool
    depends_on: List[str]  # IDs of previous steps that must complete first
    context_mapping: Dict[str, str]  # How to get args from previous steps or inputs
    error_handling: str  # "stop", "continue", "retry"
    timeout_seconds: int = 60


@dataclass
class WorkflowTemplate:
    """Pre-defined multi-step workflow"""
    name: str
    workflow_id: str
    description: str
    trigger_phrases: List[str]  # Phrases that should trigger this workflow
    input_schema: Dict[str, Any]
    steps: List[WorkflowStep]
    output_format: str
    expected_duration_seconds: int = 30
    complexity_level: str = "medium"  # "simple", "medium", "complex"


# ==================== Workflow Template Definitions ====================

WORKFLOW_TEMPLATES = {
    "complete_measure_analysis": WorkflowTemplate(
        name="Complete Measure Analysis",
        workflow_id="complete_measure_analysis",
        description="Comprehensive analysis of a single measure including dependencies, patterns, performance, and impact",
        trigger_phrases=[
            "analyze measure",
            "tell me about this measure",
            "explain the measure",
            "how does this measure work",
            "complete measure analysis"
        ],
        input_schema={
            "table": {"type": "string", "required": True},
            "measure": {"type": "string", "required": True}
        },
        steps=[
            WorkflowStep(
                step_id="get_definition",
                tool_name="get_measure_details",
                description="Get measure definition and DAX expression",
                required=True,
                depends_on=[],
                context_mapping={"table": "input.table", "measure": "input.measure"},
                error_handling="stop"
            ),
            WorkflowStep(
                step_id="analyze_dependencies",
                tool_name="analyze_measure_dependencies",
                description="Analyze what this measure depends on",
                required=True,
                depends_on=["get_definition"],
                context_mapping={"table": "input.table", "measure": "input.measure"},
                error_handling="continue"
            ),
            WorkflowStep(
                step_id="check_impact",
                tool_name="get_measure_impact",
                description="Find what depends on this measure",
                required=True,
                depends_on=["get_definition"],
                context_mapping={"table": "input.table", "measure": "input.measure", "depth": "10"},
                error_handling="continue"
            ),
            WorkflowStep(
                step_id="analyze_dax",
                tool_name="dax_intelligence",
                description="Analyze DAX patterns and context transitions",
                required=True,
                depends_on=["get_definition"],
                context_mapping={"expression": "get_definition.expression", "analysis_mode": "'report'"},
                error_handling="continue"
            ),
            WorkflowStep(
                step_id="list_relationships",
                tool_name="list_relationships",
                description="Get all model relationships",
                required=False,
                depends_on=["analyze_dependencies"],
                context_mapping={},
                error_handling="continue"
            ),
            WorkflowStep(
                step_id="test_execution",
                tool_name="run_dax",
                description="Test measure execution with profiling",
                required=False,
                depends_on=["get_definition"],
                context_mapping={
                    "query": "f'EVALUATE ROW(\"Result\", [{input.measure}])'",
                    "mode": "'profile'"
                },
                error_handling="continue",
                timeout_seconds=30
            )
        ],
        output_format="comprehensive_measure_report",
        expected_duration_seconds=15,
        complexity_level="medium"
    ),

    "model_health_check": WorkflowTemplate(
        name="Model Health Check",
        workflow_id="model_health_check",
        description="Complete model validation including structure, relationships, and best practices",
        trigger_phrases=[
            "check model health",
            "validate model",
            "analyze the model",
            "model issues",
            "model health check"
        ],
        input_schema={},
        steps=[
            WorkflowStep(
                step_id="list_tables",
                tool_name="list_tables",
                description="Get all tables in model",
                required=True,
                depends_on=[],
                context_mapping={},
                error_handling="stop"
            ),
            WorkflowStep(
                step_id="list_measures",
                tool_name="list_measures",
                description="Get all measures",
                required=True,
                depends_on=[],
                context_mapping={},
                error_handling="stop"
            ),
            WorkflowStep(
                step_id="list_relationships",
                tool_name="list_relationships",
                description="Get all relationships",
                required=True,
                depends_on=[],
                context_mapping={},
                error_handling="stop"
            ),
            WorkflowStep(
                step_id="comprehensive_analysis",
                tool_name="comprehensive_analysis",
                description="Run BPA and integrity checks",
                required=True,
                depends_on=[],
                context_mapping={"scope": "'all'", "depth": "'balanced'"},
                error_handling="continue",
                timeout_seconds=120
            )
        ],
        output_format="model_health_report",
        expected_duration_seconds=45,
        complexity_level="complex"
    ),

    "measure_impact_analysis": WorkflowTemplate(
        name="Measure Change Impact Analysis",
        workflow_id="measure_impact_analysis",
        description="Analyze impact of modifying or deleting a measure",
        trigger_phrases=[
            "impact of changing",
            "what uses this measure",
            "safe to delete",
            "measure dependencies",
            "impact analysis"
        ],
        input_schema={
            "table": {"type": "string", "required": True},
            "measure": {"type": "string", "required": True}
        },
        steps=[
            WorkflowStep(
                step_id="get_definition",
                tool_name="get_measure_details",
                description="Get current measure definition",
                required=True,
                depends_on=[],
                context_mapping={"table": "input.table", "measure": "input.measure"},
                error_handling="stop"
            ),
            WorkflowStep(
                step_id="analyze_impact",
                tool_name="get_measure_impact",
                description="Find upstream and downstream dependencies",
                required=True,
                depends_on=["get_definition"],
                context_mapping={"table": "input.table", "measure": "input.measure", "depth": "10"},
                error_handling="stop"
            ),
            WorkflowStep(
                step_id="analyze_dependencies",
                tool_name="analyze_measure_dependencies",
                description="Analyze what this measure depends on",
                required=True,
                depends_on=["get_definition"],
                context_mapping={"table": "input.table", "measure": "input.measure"},
                error_handling="continue"
            ),
            WorkflowStep(
                step_id="check_calc_groups",
                tool_name="list_calculation_groups",
                description="Check if used in calculation groups",
                required=False,
                depends_on=[],
                context_mapping={},
                error_handling="continue"
            )
        ],
        output_format="impact_analysis_report",
        expected_duration_seconds=10,
        complexity_level="simple"
    ),

    "table_profiling": WorkflowTemplate(
        name="Complete Table Profiling",
        workflow_id="table_profiling",
        description="Profile a table's structure, relationships, and data characteristics",
        trigger_phrases=[
            "profile table",
            "analyze table",
            "tell me about table",
            "table profiling"
        ],
        input_schema={
            "table": {"type": "string", "required": True}
        },
        steps=[
            WorkflowStep(
                step_id="describe_table",
                tool_name="describe_table",
                description="Get table structure and metadata",
                required=True,
                depends_on=[],
                context_mapping={"table_name": "input.table"},
                error_handling="stop"
            ),
            WorkflowStep(
                step_id="list_relationships",
                tool_name="list_relationships",
                description="Find relationships for this table",
                required=True,
                depends_on=["describe_table"],
                context_mapping={},
                error_handling="continue"
            ),
            WorkflowStep(
                step_id="preview_data",
                tool_name="preview_table_data",
                description="Get sample data",
                required=False,
                depends_on=["describe_table"],
                context_mapping={"table": "input.table", "max_rows": "50"},
                error_handling="continue"
            ),
            WorkflowStep(
                step_id="list_measures",
                tool_name="list_measures",
                description="Find measures in this table",
                required=True,
                depends_on=["describe_table"],
                context_mapping={},
                error_handling="continue"
            )
        ],
        output_format="table_profile_report",
        expected_duration_seconds=15,
        complexity_level="medium"
    ),

    "performance_investigation": WorkflowTemplate(
        name="Performance Investigation",
        workflow_id="performance_investigation",
        description="Investigate performance issues in a measure or query",
        trigger_phrases=[
            "slow measure",
            "performance issue",
            "optimize measure",
            "why is it slow"
        ],
        input_schema={
            "table": {"type": "string", "required": False},
            "measure": {"type": "string", "required": False},
            "dax_query": {"type": "string", "required": False}
        },
        steps=[
            WorkflowStep(
                step_id="get_definition",
                tool_name="get_measure_details",
                description="Get measure definition (if measure provided)",
                required=False,
                depends_on=[],
                context_mapping={"table": "input.table", "measure": "input.measure"},
                error_handling="continue"
            ),
            WorkflowStep(
                step_id="analyze_dax",
                tool_name="dax_intelligence",
                description="Analyze DAX for anti-patterns",
                required=True,
                depends_on=[],
                context_mapping={"expression": "input.dax_query or get_definition.expression", "analysis_mode": "'optimize'"},
                error_handling="continue"
            ),
            WorkflowStep(
                step_id="profile_execution",
                tool_name="run_dax",
                description="Profile query execution",
                required=True,
                depends_on=[],
                context_mapping={"query": "input.dax_query", "mode": "'profile'"},
                error_handling="continue",
                timeout_seconds=60
            ),
            WorkflowStep(
                step_id="analyze_dependencies",
                tool_name="analyze_measure_dependencies",
                description="Check dependencies for complexity",
                required=False,
                depends_on=["get_definition"],
                context_mapping={"table": "input.table", "measure": "input.measure"},
                error_handling="continue"
            )
        ],
        output_format="performance_investigation_report",
        expected_duration_seconds=30,
        complexity_level="medium"
    ),

    "relationship_validation": WorkflowTemplate(
        name="Relationship Validation",
        workflow_id="relationship_validation",
        description="Validate model relationships and identify potential issues",
        trigger_phrases=[
            "validate relationships",
            "check relationships",
            "relationship problems"
        ],
        input_schema={},
        steps=[
            WorkflowStep(
                step_id="list_relationships",
                tool_name="list_relationships",
                description="Get all relationships",
                required=True,
                depends_on=[],
                context_mapping={},
                error_handling="stop"
            ),
            WorkflowStep(
                step_id="list_tables",
                tool_name="list_tables",
                description="Get all tables to check for orphans",
                required=True,
                depends_on=[],
                context_mapping={},
                error_handling="stop"
            ),
            WorkflowStep(
                step_id="comprehensive_analysis",
                tool_name="comprehensive_analysis",
                description="Run relationship integrity checks",
                required=True,
                depends_on=["list_relationships"],
                context_mapping={"scope": "'integrity'", "depth": "'balanced'"},
                error_handling="continue",
                timeout_seconds=60
            )
        ],
        output_format="relationship_validation_report",
        expected_duration_seconds=20,
        complexity_level="medium"
    )
}


class WorkflowExecutor:
    """Executes workflow templates"""

    def __init__(self, connection_state=None):
        """
        Initialize workflow executor

        Args:
            connection_state: Connection state object (will be used to execute tools)
        """
        self.connection_state = connection_state
        self.step_results: Dict[str, Any] = {}
        self.execution_log: List[Dict[str, Any]] = []

    def execute_workflow(
        self,
        template_name: str,
        inputs: Dict[str, Any],
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Execute a workflow template

        Args:
            template_name: Name of the workflow template to execute
            inputs: Input parameters for the workflow
            context: Optional additional context

        Returns:
            Workflow execution results including all step results and synthesis
        """
        template = WORKFLOW_TEMPLATES.get(template_name)
        if not template:
            return {
                'success': False,
                'error': f'Workflow template "{template_name}" not found',
                'available_workflows': list(WORKFLOW_TEMPLATES.keys())
            }

        logger.info(f"Starting workflow: {template.name}")
        start_time = datetime.now()

        # Validate inputs
        validation_error = self._validate_inputs(template, inputs)
        if validation_error:
            return {
                'success': False,
                'error': validation_error,
                'workflow': template_name
            }

        results = {
            'workflow': template_name,
            'workflow_name': template.name,
            'description': template.description,
            'steps': [],
            'success': True,
            'start_time': start_time.isoformat(),
            'inputs': inputs
        }

        # Clear previous execution state
        self.step_results = {}
        self.execution_log = []

        # Execute each step
        for i, step in enumerate(template.steps):
            step_start = datetime.now()

            # Check dependencies
            if not self._check_dependencies(step, results):
                if step.required:
                    results['success'] = False
                    results['error'] = f'Required step "{step.step_id}" failed due to dependency failure'
                    break
                else:
                    logger.info(f"Skipping optional step {step.step_id} due to dependency failure")
                    continue

            # Get arguments for this step
            try:
                args = self._get_step_arguments(step, inputs, self.step_results, context or {})
            except Exception as e:
                logger.error(f"Error getting arguments for step {step.step_id}: {e}")
                if step.required:
                    results['success'] = False
                    results['error'] = f'Failed to prepare arguments for step "{step.step_id}": {str(e)}'
                    break
                continue

            # Execute step
            try:
                logger.info(f"Executing step {i+1}/{len(template.steps)}: {step.description}")
                step_result = self._execute_tool(step.tool_name, args, timeout=step.timeout_seconds)

                self.step_results[step.step_id] = step_result
                step_duration = (datetime.now() - step_start).total_seconds()

                step_info = {
                    'step': i + 1,
                    'step_id': step.step_id,
                    'tool': step.tool_name,
                    'description': step.description,
                    'success': step_result.get('success', False),
                    'duration_seconds': round(step_duration, 2),
                    'result': step_result
                }

                results['steps'].append(step_info)

                # Log execution
                self.execution_log.append({
                    'step_id': step.step_id,
                    'tool': step.tool_name,
                    'success': step_result.get('success', False),
                    'duration': step_duration
                })

            except Exception as e:
                logger.error(f"Error executing step {step.step_id}: {e}", exc_info=True)
                step_info = {
                    'step': i + 1,
                    'step_id': step.step_id,
                    'tool': step.tool_name,
                    'description': step.description,
                    'success': False,
                    'error': str(e)
                }
                results['steps'].append(step_info)

                if step.error_handling == "stop" or step.required:
                    results['success'] = False
                    results['error'] = f'Step "{step.step_id}" failed: {str(e)}'
                    break

        # Calculate total duration
        total_duration = (datetime.now() - start_time).total_seconds()
        results['duration_seconds'] = round(total_duration, 2)
        results['end_time'] = datetime.now().isoformat()

        # Generate final analysis/synthesis
        if results['success']:
            try:
                results['synthesized_analysis'] = self._synthesize_results(template, self.step_results, inputs)
            except Exception as e:
                logger.error(f"Error synthesizing results: {e}", exc_info=True)
                results['synthesized_analysis'] = {'error': f'Synthesis failed: {str(e)}'}

        results['execution_log'] = self.execution_log

        logger.info(f"Workflow completed: {template.name} (duration: {total_duration:.2f}s, success: {results['success']})")

        return results

    def _validate_inputs(self, template: WorkflowTemplate, inputs: Dict[str, Any]) -> Optional[str]:
        """Validate workflow inputs against schema"""
        for param_name, param_schema in template.input_schema.items():
            if param_schema.get('required', False) and param_name not in inputs:
                return f'Required parameter "{param_name}" missing'

            if param_name in inputs:
                expected_type = param_schema.get('type')
                actual_value = inputs[param_name]

                if expected_type == 'string' and not isinstance(actual_value, str):
                    return f'Parameter "{param_name}" must be a string'
                if expected_type == 'number' and not isinstance(actual_value, (int, float)):
                    return f'Parameter "{param_name}" must be a number'

        return None

    def _check_dependencies(self, step: WorkflowStep, results: Dict[str, Any]) -> bool:
        """Check if step dependencies are satisfied"""
        if not step.depends_on:
            return True

        # Check if all dependencies completed successfully
        completed_steps = {s['step_id'] for s in results['steps'] if s.get('success', False)}

        for dep_id in step.depends_on:
            if dep_id not in completed_steps:
                logger.warning(f"Dependency {dep_id} not satisfied for step {step.step_id}")
                return False

        return True

    def _get_step_arguments(
        self,
        step: WorkflowStep,
        inputs: Dict[str, Any],
        step_results: Dict[str, Any],
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Get arguments for a step by mapping context

        Args:
            step: The workflow step
            inputs: Workflow inputs
            step_results: Results from previous steps
            context: Additional context

        Returns:
            Arguments dictionary for the tool
        """
        args = {}

        for arg_name, mapping in step.context_mapping.items():
            value = None

            # Handle literal values (e.g., "'report'")
            if mapping.startswith("'") and mapping.endswith("'"):
                value = mapping.strip("'")

            # Handle f-string expressions (e.g., "f'EVALUATE ROW(...)'")
            elif mapping.startswith("f'"):
                # Simple f-string evaluation
                template_str = mapping[2:-1]  # Remove f' and '
                # Replace {input.X} with actual values
                for key, val in inputs.items():
                    template_str = template_str.replace(f"{{input.{key}}}", str(val))
                value = template_str

            # Handle input references (e.g., "input.table")
            elif mapping.startswith("input."):
                key = mapping.split('.', 1)[1]
                value = inputs.get(key)

            # Handle step result references (e.g., "get_definition.expression")
            elif '.' in mapping:
                parts = mapping.split('.', 1)
                step_id = parts[0]
                result_key = parts[1]

                if step_id in step_results:
                    value = step_results[step_id].get(result_key)

            # Handle direct context reference
            else:
                value = context.get(mapping) or inputs.get(mapping)

            if value is not None:
                args[arg_name] = value

        return args

    def _execute_tool(self, tool_name: str, args: Dict[str, Any], timeout: int = 60) -> Dict[str, Any]:
        """
        Execute a specific tool

        Args:
            tool_name: Name of the tool to execute
            args: Arguments for the tool
            timeout: Timeout in seconds

        Returns:
            Tool execution result
        """
        try:
            # Import handler registry
            from server.registry import handler_registry

            handler = handler_registry.get_handler(tool_name)
            if handler:
                result = handler(args)
                return result if isinstance(result, dict) else {'success': False, 'error': 'Invalid handler response'}
            else:
                return {'success': False, 'error': f'Handler not found: {tool_name}'}

        except Exception as e:
            logger.error(f"Error executing tool {tool_name}: {e}", exc_info=True)
            return {'success': False, 'error': str(e)}

    def _synthesize_results(
        self,
        template: WorkflowTemplate,
        step_results: Dict[str, Any],
        inputs: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Synthesize results from all steps into cohesive analysis

        Args:
            template: The workflow template
            step_results: Results from all steps
            inputs: Original workflow inputs

        Returns:
            Synthesized analysis
        """
        synthesis = {
            'summary': '',
            'key_findings': [],
            'issues': [],
            'recommendations': [],
            'insights': []
        }

        # Synthesize based on workflow type
        if template.workflow_id == "complete_measure_analysis":
            synthesis = self._synthesize_measure_analysis(step_results, inputs)

        elif template.workflow_id == "model_health_check":
            synthesis = self._synthesize_health_check(step_results)

        elif template.workflow_id == "measure_impact_analysis":
            synthesis = self._synthesize_impact_analysis(step_results, inputs)

        elif template.workflow_id == "table_profiling":
            synthesis = self._synthesize_table_profiling(step_results, inputs)

        elif template.workflow_id == "performance_investigation":
            synthesis = self._synthesize_performance_investigation(step_results, inputs)

        elif template.workflow_id == "relationship_validation":
            synthesis = self._synthesize_relationship_validation(step_results)

        return synthesis

    def _synthesize_measure_analysis(self, step_results: Dict[str, Any], inputs: Dict[str, Any]) -> Dict[str, Any]:
        """Synthesize complete measure analysis results"""
        measure_def = step_results.get('get_definition', {})
        dependencies = step_results.get('analyze_dependencies', {})
        impact = step_results.get('check_impact', {})
        dax_analysis = step_results.get('analyze_dax', {})
        relationships = step_results.get('list_relationships', {})
        performance = step_results.get('test_execution', {})

        # Extract key metrics
        complexity = dax_analysis.get('complexity_assessment', {}).get('level', 'Unknown')
        dep_measure_count = len(dependencies.get('referenced_measures', []))
        dep_table_count = len(dependencies.get('referenced_tables', []))
        downstream_count = impact.get('downstream_count', 0)
        expression_length = len(measure_def.get('expression', ''))

        # Build summary
        measure_name = f"{inputs.get('table', '')}[{inputs.get('measure', '')}]"
        summary = f"Measure {measure_name} has {complexity.lower()} complexity"

        if dep_measure_count > 0:
            summary += f", depends on {dep_measure_count} other measure(s)"
        if downstream_count > 0:
            summary += f", and is used by {downstream_count} measure(s)"

        synthesis = {
            'summary': summary,
            'key_findings': [],
            'issues': [],
            'recommendations': [],
            'metrics': {
                'complexity': complexity,
                'dependencies': {
                    'measures': dep_measure_count,
                    'tables': dep_table_count,
                    'columns': len(dependencies.get('referenced_columns', []))
                },
                'impact': {
                    'downstream_measures': downstream_count
                },
                'expression_length': expression_length
            }
        }

        # Analyze complexity and impact combination
        if complexity in ["High", "Very High"] and downstream_count > 5:
            synthesis['issues'].append({
                'severity': 'high',
                'category': 'Maintainability',
                'issue': 'High-complexity measure with broad impact',
                'detail': f'This {complexity.lower()}-complexity measure affects {downstream_count} other measures, making changes risky'
            })
            synthesis['recommendations'].append({
                'priority': 'high',
                'category': 'Refactoring',
                'recommendation': 'Consider breaking into smaller, reusable helper measures',
                'benefit': 'Easier to test, debug, and maintain'
            })

        # Check for performance issues
        exec_time = performance.get('execution_time_ms', 0)
        if exec_time > 1000:
            synthesis['issues'].append({
                'severity': 'medium',
                'category': 'Performance',
                'issue': f'Slow execution time: {exec_time}ms',
                'detail': 'Measure takes over 1 second to execute'
            })

        # Check for DAX anti-patterns
        anti_patterns = dax_analysis.get('anti_patterns', [])
        if anti_patterns:
            for pattern in anti_patterns:
                synthesis['issues'].append({
                    'severity': pattern.get('severity', 'medium'),
                    'category': 'DAX Patterns',
                    'issue': pattern.get('pattern', 'Unknown anti-pattern'),
                    'detail': pattern.get('description', '')
                })

        # Check relationships
        if relationships.get('success') and dep_table_count > 1:
            rel_rows = relationships.get('rows', [])
            inactive_rels = [r for r in rel_rows if not r.get('isActive', True)]

            if inactive_rels:
                synthesis['key_findings'].append({
                    'category': 'Relationships',
                    'finding': f'{len(inactive_rels)} inactive relationships found in model',
                    'recommendation': 'Verify if measure correctly uses inactive relationships with USERELATIONSHIP'
                })

        return synthesis

    def _synthesize_health_check(self, step_results: Dict[str, Any]) -> Dict[str, Any]:
        """Synthesize model health check results"""
        tables = step_results.get('list_tables', {})
        measures = step_results.get('list_measures', {})
        relationships = step_results.get('list_relationships', {})
        analysis = step_results.get('comprehensive_analysis', {})

        table_count = len(tables.get('rows', []))
        measure_count = len(measures.get('rows', []))
        rel_count = len(relationships.get('rows', []))

        issues = analysis.get('issues', [])
        critical_issues = [i for i in issues if i.get('severity') == 'critical']
        high_issues = [i for i in issues if i.get('severity') == 'high']

        health_score = analysis.get('health_score', 0)

        summary = f"Model contains {table_count} tables, {measure_count} measures, and {rel_count} relationships. "
        if health_score:
            summary += f"Overall health score: {health_score}/100."

        return {
            'summary': summary,
            'metrics': {
                'tables': table_count,
                'measures': measure_count,
                'relationships': rel_count,
                'health_score': health_score
            },
            'issues': {
                'critical': len(critical_issues),
                'high': len(high_issues),
                'total': len(issues)
            },
            'critical_issues': critical_issues[:5],  # Top 5
            'recommendations': self._prioritize_recommendations(issues)
        }

    def _synthesize_impact_analysis(self, step_results: Dict[str, Any], inputs: Dict[str, Any]) -> Dict[str, Any]:
        """Synthesize measure impact analysis results"""
        impact = step_results.get('analyze_impact', {})
        dependencies = step_results.get('analyze_dependencies', {})

        downstream_count = impact.get('downstream_count', 0)
        upstream_count = len(dependencies.get('referenced_measures', []))

        measure_name = f"{inputs.get('table', '')}[{inputs.get('measure', '')}]"

        summary = f"Measure {measure_name} depends on {upstream_count} measure(s) and is used by {downstream_count} measure(s)."

        safety_level = "high" if downstream_count == 0 else "medium" if downstream_count < 5 else "low"

        return {
            'summary': summary,
            'change_safety': {
                'level': safety_level,
                'downstream_impact': downstream_count,
                'upstream_dependencies': upstream_count
            },
            'recommendations': [
                f"{'Safe' if safety_level == 'high' else 'Caution required'} when modifying this measure",
                f"Test all {downstream_count} dependent measures after changes" if downstream_count > 0 else "No dependent measures - safe to modify"
            ]
        }

    def _synthesize_table_profiling(self, step_results: Dict[str, Any], inputs: Dict[str, Any]) -> Dict[str, Any]:
        """Synthesize table profiling results"""
        table_info = step_results.get('describe_table', {})
        relationships = step_results.get('list_relationships', {})
        measures = step_results.get('list_measures', {})

        table_name = inputs.get('table', 'Unknown')
        row_count = table_info.get('row_count', 0)
        column_count = table_info.get('column_count', 0)

        # Count relationships
        rel_rows = relationships.get('rows', [])
        table_rels = [r for r in rel_rows if r.get('fromTable') == table_name or r.get('toTable') == table_name]

        # Count measures
        measure_rows = measures.get('rows', [])
        table_measures = [m for m in measure_rows if m.get('Table') == table_name]

        return {
            'summary': f"Table '{table_name}' has {row_count:,} rows, {column_count} columns, {len(table_rels)} relationships, and {len(table_measures)} measures",
            'metrics': {
                'rows': row_count,
                'columns': column_count,
                'relationships': len(table_rels),
                'measures': len(table_measures)
            },
            'relationships': table_rels,
            'key_findings': []
        }

    def _synthesize_performance_investigation(self, step_results: Dict[str, Any], inputs: Dict[str, Any]) -> Dict[str, Any]:
        """Synthesize performance investigation results"""
        dax_analysis = step_results.get('analyze_dax', {})
        performance = step_results.get('profile_execution', {})

        exec_time = performance.get('execution_time_ms', 0)
        anti_patterns = dax_analysis.get('anti_patterns', [])
        complexity = dax_analysis.get('complexity_assessment', {})

        return {
            'summary': f"Query execution time: {exec_time}ms, Complexity: {complexity.get('level', 'Unknown')}",
            'performance': {
                'execution_time_ms': exec_time,
                'complexity_level': complexity.get('level'),
                'complexity_score': complexity.get('score', 0)
            },
            'issues': [
                {'category': 'Anti-Pattern', 'detail': ap.get('description', '')}
                for ap in anti_patterns
            ],
            'recommendations': dax_analysis.get('optimization_suggestions', [])
        }

    def _synthesize_relationship_validation(self, step_results: Dict[str, Any]) -> Dict[str, Any]:
        """Synthesize relationship validation results"""
        relationships = step_results.get('list_relationships', {})
        tables = step_results.get('list_tables', {})
        analysis = step_results.get('comprehensive_analysis', {})

        rel_rows = relationships.get('rows', [])
        table_rows = tables.get('rows', [])

        inactive_rels = [r for r in rel_rows if not r.get('isActive', True)]
        many_to_many = [r for r in rel_rows if r.get('fromCardinality') == 'many' and r.get('toCardinality') == 'many']

        # Find orphaned tables
        connected_tables = set()
        for rel in rel_rows:
            connected_tables.add(rel.get('fromTable'))
            connected_tables.add(rel.get('toTable'))

        all_tables = {t.get('Name') for t in table_rows}
        orphaned_tables = all_tables - connected_tables

        return {
            'summary': f"Model has {len(rel_rows)} relationships, {len(inactive_rels)} inactive, {len(many_to_many)} many-to-many",
            'metrics': {
                'total_relationships': len(rel_rows),
                'inactive_relationships': len(inactive_rels),
                'many_to_many_relationships': len(many_to_many),
                'orphaned_tables': len(orphaned_tables)
            },
            'issues': [
                {'severity': 'medium', 'detail': f"Inactive relationship: {r.get('fromTable')}→{r.get('toTable')}"}
                for r in inactive_rels
            ] + [
                {'severity': 'high', 'detail': f"Many-to-many relationship: {r.get('fromTable')}↔{r.get('toTable')}"}
                for r in many_to_many
            ] + [
                {'severity': 'low', 'detail': f"Orphaned table: {t}"}
                for t in orphaned_tables
            ],
            'recommendations': [
                "Review inactive relationships and ensure they're used with USERELATIONSHIP where needed",
                "Consider using bridge tables instead of many-to-many relationships",
                "Investigate orphaned tables - they may not be needed in the model"
            ]
        }

    def _prioritize_recommendations(self, issues: List[Dict[str, Any]]) -> List[str]:
        """Prioritize recommendations from issues"""
        recommendations = []

        # Group by severity
        critical = [i for i in issues if i.get('severity') == 'critical']
        high = [i for i in issues if i.get('severity') == 'high']

        if critical:
            recommendations.append(f"[CRITICAL] Address {len(critical)} critical issues immediately")

        if high:
            recommendations.append(f"[HIGH] Resolve {len(high)} high-priority issues")

        return recommendations


def get_workflow_by_trigger(user_request: str) -> Optional[WorkflowTemplate]:
    """
    Find a workflow template based on trigger phrases in user request

    Args:
        user_request: User's natural language request

    Returns:
        Matching workflow template or None
    """
    request_lower = user_request.lower()

    for template in WORKFLOW_TEMPLATES.values():
        for trigger in template.trigger_phrases:
            if trigger.lower() in request_lower:
                return template

    return None


def list_available_workflows() -> List[Dict[str, Any]]:
    """Get list of available workflows with metadata"""
    return [
        {
            'workflow_id': template.workflow_id,
            'name': template.name,
            'description': template.description,
            'complexity': template.complexity_level,
            'expected_duration_seconds': template.expected_duration_seconds,
            'trigger_phrases': template.trigger_phrases,
            'required_inputs': [
                param for param, schema in template.input_schema.items()
                if schema.get('required', False)
            ]
        }
        for template in WORKFLOW_TEMPLATES.values()
    ]
