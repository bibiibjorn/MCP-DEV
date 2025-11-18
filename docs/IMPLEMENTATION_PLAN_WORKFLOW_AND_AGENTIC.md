# Implementation Plan: Workflow Orchestration & Agentic Intelligence

**Version:** 1.0
**Date:** 2025-01-18
**Status:** Planning Phase

---

## Table of Contents
1. [Overview](#overview)
2. [Workflow Orchestration Implementation](#workflow-orchestration)
3. [Agentic Intelligence Enhancement](#agentic-intelligence)
4. [Integration Strategy](#integration-strategy)
5. [Implementation Phases](#implementation-phases)
6. [Testing Strategy](#testing-strategy)
7. [Rollout Plan](#rollout-plan)

---

## Overview

### Goals
1. **Workflow Orchestration**: Enable multi-step automated workflows with progress tracking and resumability
2. **Agentic Intelligence**: Add semantic understanding, learning, and proactive recommendations

### Success Criteria
- ✅ Users can execute complex multi-step workflows with single commands
- ✅ Progress tracking shows real-time status for long-running operations
- ✅ Workflows are resumable after interruption
- ✅ System learns from user interactions and improves recommendations
- ✅ Proactive suggestions guide users through optimal workflows
- ✅ Semantic intent parsing understands nuanced user requests

### Dependencies
- Existing orchestration layer (AgentPolicy, 8 orchestrators)
- Existing tool registry and dispatcher
- Connection state management
- Configuration system

---

## Part 1: Workflow Orchestration Implementation

### 1.1 Architecture Design

#### Core Components

```
core/workflows/
├── __init__.py
├── workflow_engine.py           # Main workflow execution engine
├── workflow_registry.py         # Workflow template registry
├── workflow_state.py            # State management & persistence
├── workflow_templates.py        # Pre-defined workflow templates
├── workflow_builder.py          # Dynamic workflow construction
├── step_executor.py             # Individual step execution
└── progress_tracker.py          # Progress tracking & callbacks

server/handlers/
├── workflow_handler.py          # MCP tool handlers for workflows

config/
├── workflows/
    ├── model_review.yaml        # Model review workflow template
    ├── performance_optimization.yaml
    ├── measure_development.yaml
    └── custom/                  # User-defined workflows
```

#### Data Models

```python
# core/workflows/models.py

from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional, Callable
from enum import Enum
from datetime import datetime

class WorkflowStatus(Enum):
    PENDING = "pending"
    RUNNING = "running"
    PAUSED = "paused"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"

class StepStatus(Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"

@dataclass
class WorkflowStep:
    """Represents a single step in a workflow"""
    step_id: str
    step_name: str
    tool_name: str
    parameters: Dict[str, Any]
    description: str

    # Conditional execution
    condition: Optional[str] = None  # Python expression or "always", "on_success", "on_failure"

    # Dependencies
    depends_on: List[str] = field(default_factory=list)  # List of step_ids

    # Retry configuration
    retry_on_failure: bool = False
    max_retries: int = 3
    retry_delay_seconds: int = 5

    # Parameter mapping from previous steps
    parameter_mapping: Dict[str, str] = field(default_factory=dict)
    # e.g., {"table": "$.step1.result.table_name"}

    # Timeout
    timeout_seconds: Optional[int] = None

    # Status tracking
    status: StepStatus = StepStatus.PENDING
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    retry_count: int = 0

@dataclass
class Workflow:
    """Represents a complete workflow"""
    workflow_id: str
    workflow_name: str
    description: str
    category: str  # "analysis", "optimization", "documentation", "development"

    steps: List[WorkflowStep]

    # Metadata
    author: Optional[str] = None
    version: str = "1.0"
    tags: List[str] = field(default_factory=list)

    # Execution configuration
    parallel_execution: bool = False  # Execute independent steps in parallel
    continue_on_error: bool = False   # Continue even if non-critical steps fail

    # State tracking
    status: WorkflowStatus = WorkflowStatus.PENDING
    current_step_index: int = 0
    progress_percentage: float = 0.0
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None

    # Results accumulation
    context: Dict[str, Any] = field(default_factory=dict)  # Shared context across steps
    results: Dict[str, Any] = field(default_factory=dict)  # Results keyed by step_id

@dataclass
class WorkflowTemplate:
    """Template for creating workflows"""
    template_id: str
    template_name: str
    description: str
    category: str

    # Template parameters (filled in at runtime)
    parameters: List[Dict[str, Any]] = field(default_factory=list)
    # e.g., [{"name": "table_name", "type": "string", "required": true}]

    # Step templates
    step_templates: List[Dict[str, Any]] = field(default_factory=list)

    # Metadata
    estimated_duration_seconds: int = 60
    requires_connection: bool = True

    def instantiate(self, params: Dict[str, Any]) -> Workflow:
        """Create a Workflow instance from this template"""
        pass
```

### 1.2 Workflow Engine Implementation

```python
# core/workflows/workflow_engine.py

import logging
import asyncio
from typing import Dict, Any, Optional, Callable
from datetime import datetime
from .models import Workflow, WorkflowStep, WorkflowStatus, StepStatus
from .step_executor import StepExecutor
from .progress_tracker import ProgressTracker
from core.infrastructure.connection_state import connection_state

logger = logging.getLogger(__name__)

class WorkflowEngine:
    """
    Executes workflows with progress tracking, error handling, and resumability
    """

    def __init__(self, config):
        self.config = config
        self.step_executor = StepExecutor(config)
        self.progress_tracker = ProgressTracker()
        self.active_workflows: Dict[str, Workflow] = {}

    async def execute_workflow(
        self,
        workflow: Workflow,
        progress_callback: Optional[Callable[[Dict[str, Any]], None]] = None
    ) -> Dict[str, Any]:
        """
        Execute a workflow with progress tracking

        Args:
            workflow: Workflow to execute
            progress_callback: Optional callback for progress updates

        Returns:
            Workflow execution result
        """
        workflow.status = WorkflowStatus.RUNNING
        workflow.started_at = datetime.now()
        self.active_workflows[workflow.workflow_id] = workflow

        try:
            logger.info(f"Starting workflow: {workflow.workflow_name} ({workflow.workflow_id})")

            # Register progress callback
            if progress_callback:
                self.progress_tracker.register_callback(workflow.workflow_id, progress_callback)

            # Execute steps
            for step_index, step in enumerate(workflow.steps):
                workflow.current_step_index = step_index

                # Check if step should be executed
                if not self._should_execute_step(step, workflow):
                    step.status = StepStatus.SKIPPED
                    self._update_progress(workflow, step_index)
                    continue

                # Wait for dependencies
                await self._wait_for_dependencies(step, workflow)

                # Apply parameter mapping from previous steps
                step.parameters = self._apply_parameter_mapping(step, workflow)

                # Execute step
                step_result = await self._execute_step_with_retry(step, workflow)

                # Update workflow context and results
                workflow.results[step.step_id] = step_result
                workflow.context.update(step_result.get("context", {}))

                # Update progress
                self._update_progress(workflow, step_index)

                # Check if workflow should continue
                if step.status == StepStatus.FAILED and not workflow.continue_on_error:
                    workflow.status = WorkflowStatus.FAILED
                    break

            # Finalize workflow
            if workflow.status == WorkflowStatus.RUNNING:
                workflow.status = WorkflowStatus.COMPLETED

            workflow.completed_at = datetime.now()
            workflow.progress_percentage = 100.0

            logger.info(f"Workflow completed: {workflow.workflow_name} - Status: {workflow.status.value}")

            return self._build_workflow_result(workflow)

        except Exception as e:
            logger.error(f"Workflow execution failed: {e}", exc_info=True)
            workflow.status = WorkflowStatus.FAILED
            workflow.completed_at = datetime.now()
            return self._build_workflow_result(workflow, error=str(e))

        finally:
            # Cleanup
            self.progress_tracker.unregister_callback(workflow.workflow_id)
            if workflow.workflow_id in self.active_workflows:
                del self.active_workflows[workflow.workflow_id]

    def _should_execute_step(self, step: WorkflowStep, workflow: Workflow) -> bool:
        """Determine if a step should be executed based on its condition"""
        if step.condition is None or step.condition == "always":
            return True

        if step.condition == "on_success":
            # Check if previous step succeeded
            if workflow.current_step_index > 0:
                prev_step = workflow.steps[workflow.current_step_index - 1]
                return prev_step.status == StepStatus.COMPLETED
            return True

        if step.condition == "on_failure":
            # Check if previous step failed
            if workflow.current_step_index > 0:
                prev_step = workflow.steps[workflow.current_step_index - 1]
                return prev_step.status == StepStatus.FAILED
            return False

        # Custom condition - evaluate as Python expression
        try:
            # Create evaluation context with workflow results
            eval_context = {"results": workflow.results, "context": workflow.context}
            return bool(eval(step.condition, {"__builtins__": {}}, eval_context))
        except Exception as e:
            logger.warning(f"Failed to evaluate condition '{step.condition}': {e}")
            return True

    async def _wait_for_dependencies(self, step: WorkflowStep, workflow: Workflow):
        """Wait for step dependencies to complete"""
        if not step.depends_on:
            return

        # Check if all dependencies are completed
        for dep_id in step.depends_on:
            dep_step = next((s for s in workflow.steps if s.step_id == dep_id), None)
            if dep_step and dep_step.status != StepStatus.COMPLETED:
                # In a real implementation, this would wait asynchronously
                # For now, steps are executed sequentially
                pass

    def _apply_parameter_mapping(self, step: WorkflowStep, workflow: Workflow) -> Dict[str, Any]:
        """Apply parameter mapping from previous step results"""
        params = step.parameters.copy()

        for param_name, mapping_expr in step.parameter_mapping.items():
            # Parse mapping expression like "$.step1.result.table_name"
            if mapping_expr.startswith("$."):
                parts = mapping_expr[2:].split(".")
                value = workflow.results

                for part in parts:
                    if isinstance(value, dict):
                        value = value.get(part)
                    else:
                        break

                if value is not None:
                    params[param_name] = value

        return params

    async def _execute_step_with_retry(self, step: WorkflowStep, workflow: Workflow) -> Dict[str, Any]:
        """Execute a step with retry logic"""
        step.status = StepStatus.RUNNING
        step.started_at = datetime.now()

        for attempt in range(step.max_retries + 1):
            try:
                step.retry_count = attempt

                # Execute the step
                result = await self.step_executor.execute(step, workflow.context)

                step.status = StepStatus.COMPLETED
                step.completed_at = datetime.now()
                step.result = result

                return result

            except Exception as e:
                logger.error(f"Step {step.step_name} failed (attempt {attempt + 1}): {e}")
                step.error = str(e)

                if attempt < step.max_retries and step.retry_on_failure:
                    # Wait before retry
                    await asyncio.sleep(step.retry_delay_seconds)
                    logger.info(f"Retrying step {step.step_name}...")
                else:
                    step.status = StepStatus.FAILED
                    step.completed_at = datetime.now()
                    raise

    def _update_progress(self, workflow: Workflow, current_step_index: int):
        """Update workflow progress and notify callbacks"""
        total_steps = len(workflow.steps)
        completed_steps = sum(1 for s in workflow.steps if s.status in [StepStatus.COMPLETED, StepStatus.SKIPPED])

        workflow.progress_percentage = (completed_steps / total_steps) * 100.0

        # Build progress update
        progress_update = {
            "workflow_id": workflow.workflow_id,
            "workflow_name": workflow.workflow_name,
            "status": workflow.status.value,
            "progress_percentage": workflow.progress_percentage,
            "current_step": current_step_index + 1,
            "total_steps": total_steps,
            "current_step_name": workflow.steps[current_step_index].step_name if current_step_index < total_steps else None,
            "completed_steps": completed_steps,
            "timestamp": datetime.now().isoformat()
        }

        # Notify progress tracker
        self.progress_tracker.update(workflow.workflow_id, progress_update)

    def _build_workflow_result(self, workflow: Workflow, error: Optional[str] = None) -> Dict[str, Any]:
        """Build final workflow result"""
        duration = None
        if workflow.started_at and workflow.completed_at:
            duration = (workflow.completed_at - workflow.started_at).total_seconds()

        return {
            "success": workflow.status == WorkflowStatus.COMPLETED,
            "workflow_id": workflow.workflow_id,
            "workflow_name": workflow.workflow_name,
            "status": workflow.status.value,
            "progress_percentage": workflow.progress_percentage,
            "duration_seconds": duration,
            "steps_completed": sum(1 for s in workflow.steps if s.status == StepStatus.COMPLETED),
            "steps_failed": sum(1 for s in workflow.steps if s.status == StepStatus.FAILED),
            "steps_skipped": sum(1 for s in workflow.steps if s.status == StepStatus.SKIPPED),
            "step_results": {
                step.step_id: {
                    "step_name": step.step_name,
                    "status": step.status.value,
                    "result": step.result,
                    "error": step.error,
                    "duration_seconds": (step.completed_at - step.started_at).total_seconds()
                        if step.started_at and step.completed_at else None
                }
                for step in workflow.steps
            },
            "final_context": workflow.context,
            "error": error
        }

    def pause_workflow(self, workflow_id: str) -> bool:
        """Pause a running workflow"""
        if workflow_id in self.active_workflows:
            workflow = self.active_workflows[workflow_id]
            workflow.status = WorkflowStatus.PAUSED
            return True
        return False

    def resume_workflow(self, workflow_id: str) -> bool:
        """Resume a paused workflow"""
        if workflow_id in self.active_workflows:
            workflow = self.active_workflows[workflow_id]
            if workflow.status == WorkflowStatus.PAUSED:
                workflow.status = WorkflowStatus.RUNNING
                return True
        return False

    def cancel_workflow(self, workflow_id: str) -> bool:
        """Cancel a running workflow"""
        if workflow_id in self.active_workflows:
            workflow = self.active_workflows[workflow_id]
            workflow.status = WorkflowStatus.CANCELLED
            workflow.completed_at = datetime.now()
            return True
        return False

    def get_workflow_status(self, workflow_id: str) -> Optional[Dict[str, Any]]:
        """Get current status of a workflow"""
        if workflow_id in self.active_workflows:
            workflow = self.active_workflows[workflow_id]
            return {
                "workflow_id": workflow.workflow_id,
                "workflow_name": workflow.workflow_name,
                "status": workflow.status.value,
                "progress_percentage": workflow.progress_percentage,
                "current_step_index": workflow.current_step_index,
                "total_steps": len(workflow.steps),
                "current_step_name": workflow.steps[workflow.current_step_index].step_name
                    if workflow.current_step_index < len(workflow.steps) else None
            }
        return None
```

### 1.3 Step Executor Implementation

```python
# core/workflows/step_executor.py

import logging
from typing import Dict, Any
from .models import WorkflowStep
from server.dispatch import ToolDispatcher

logger = logging.getLogger(__name__)

class StepExecutor:
    """Executes individual workflow steps by delegating to tools"""

    def __init__(self, config):
        self.config = config
        self.dispatcher = ToolDispatcher()

    async def execute(self, step: WorkflowStep, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute a single workflow step

        Args:
            step: WorkflowStep to execute
            context: Shared workflow context

        Returns:
            Step execution result
        """
        logger.info(f"Executing step: {step.step_name} (tool: {step.tool_name})")

        try:
            # Merge context into parameters if needed
            params = self._merge_context(step.parameters, context)

            # Execute the tool
            result = self.dispatcher.dispatch(step.tool_name, params)

            # Extract context updates from result
            context_updates = self._extract_context_updates(step, result)

            return {
                "success": result.get("success", False),
                "data": result,
                "context": context_updates
            }

        except Exception as e:
            logger.error(f"Step execution failed: {e}", exc_info=True)
            raise

    def _merge_context(self, parameters: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """Merge workflow context into step parameters"""
        merged = parameters.copy()

        # Replace context placeholders like "${context.table_name}"
        for key, value in merged.items():
            if isinstance(value, str) and value.startswith("${context."):
                context_key = value[10:-1]  # Extract key from "${context.xxx}"
                if context_key in context:
                    merged[key] = context[context_key]

        return merged

    def _extract_context_updates(self, step: WorkflowStep, result: Dict[str, Any]) -> Dict[str, Any]:
        """Extract context updates from step result"""
        # Example: extract table_name from result for use in next steps
        context_updates = {}

        # Convention: tools can return _context_exports to share data
        if "_context_exports" in result:
            context_updates.update(result["_context_exports"])

        return context_updates
```

### 1.4 Progress Tracker Implementation

```python
# core/workflows/progress_tracker.py

import logging
from typing import Dict, Any, Callable, Optional

logger = logging.getLogger(__name__)

class ProgressTracker:
    """Tracks workflow progress and manages callbacks"""

    def __init__(self):
        self.callbacks: Dict[str, Callable] = {}
        self.latest_progress: Dict[str, Dict[str, Any]] = {}

    def register_callback(self, workflow_id: str, callback: Callable[[Dict[str, Any]], None]):
        """Register a progress callback for a workflow"""
        self.callbacks[workflow_id] = callback
        logger.debug(f"Registered progress callback for workflow: {workflow_id}")

    def unregister_callback(self, workflow_id: str):
        """Unregister a progress callback"""
        if workflow_id in self.callbacks:
            del self.callbacks[workflow_id]
            logger.debug(f"Unregistered progress callback for workflow: {workflow_id}")

    def update(self, workflow_id: str, progress_data: Dict[str, Any]):
        """Update progress and notify callback"""
        self.latest_progress[workflow_id] = progress_data

        if workflow_id in self.callbacks:
            try:
                self.callbacks[workflow_id](progress_data)
            except Exception as e:
                logger.error(f"Progress callback failed for {workflow_id}: {e}")

    def get_latest_progress(self, workflow_id: str) -> Optional[Dict[str, Any]]:
        """Get latest progress for a workflow"""
        return self.latest_progress.get(workflow_id)
```

### 1.5 Workflow Templates

```python
# core/workflows/workflow_templates.py

from typing import Dict, Any, List
from .models import WorkflowTemplate, WorkflowStep, Workflow
import uuid

class WorkflowTemplates:
    """Pre-defined workflow templates"""

    @staticmethod
    def get_model_review_template() -> WorkflowTemplate:
        """Complete model review workflow"""
        return WorkflowTemplate(
            template_id="model_review_complete",
            template_name="Complete Model Review",
            description="Comprehensive Power BI model analysis including connection, schema review, BPA, performance, and documentation",
            category="analysis",
            parameters=[],
            step_templates=[
                {
                    "step_id": "step1_detect",
                    "step_name": "Detect Power BI Instances",
                    "tool_name": "01_detect_pbi_instances",
                    "parameters": {},
                    "description": "Find running Power BI Desktop instances"
                },
                {
                    "step_id": "step2_connect",
                    "step_name": "Connect to Power BI",
                    "tool_name": "01_connect_to_instance",
                    "parameters": {"model_index": 0},
                    "description": "Connect to the first detected instance",
                    "depends_on": ["step1_detect"]
                },
                {
                    "step_id": "step3_list_tables",
                    "step_name": "List All Tables",
                    "tool_name": "02_list_tables",
                    "parameters": {},
                    "description": "Get overview of all tables in the model",
                    "depends_on": ["step2_connect"]
                },
                {
                    "step_id": "step4_bpa",
                    "step_name": "Run Best Practice Analyzer",
                    "tool_name": "05_comprehensive_analysis",
                    "parameters": {
                        "scope": "all",
                        "depth": "balanced"
                    },
                    "description": "Analyze model against best practices",
                    "depends_on": ["step2_connect"],
                    "timeout_seconds": 180
                },
                {
                    "step_id": "step5_relationships",
                    "step_name": "Analyze Relationships",
                    "tool_name": "03_list_relationships",
                    "parameters": {"active_only": False},
                    "description": "Review all relationships in the model",
                    "depends_on": ["step2_connect"]
                },
                {
                    "step_id": "step6_measures",
                    "step_name": "List All Measures",
                    "tool_name": "02_list_measures",
                    "parameters": {"limit": 100},
                    "description": "Get overview of all measures",
                    "depends_on": ["step2_connect"]
                },
                {
                    "step_id": "step7_export_schema",
                    "step_name": "Export Model Schema",
                    "tool_name": "07_export_model_schema",
                    "parameters": {"export_mode": "compact"},
                    "description": "Export compact schema for documentation",
                    "depends_on": ["step2_connect"]
                },
                {
                    "step_id": "step8_documentation",
                    "step_name": "Generate Documentation",
                    "tool_name": "08_generate_model_documentation_word",
                    "parameters": {
                        "include_hidden": False,
                        "dependency_depth": 1
                    },
                    "description": "Generate Word documentation report",
                    "depends_on": ["step2_connect"],
                    "timeout_seconds": 60
                }
            ],
            estimated_duration_seconds=300,
            requires_connection=True
        )

    @staticmethod
    def get_performance_optimization_template() -> WorkflowTemplate:
        """Performance optimization workflow"""
        return WorkflowTemplate(
            template_id="performance_optimization",
            template_name="Performance Optimization Analysis",
            description="Identify and analyze performance bottlenecks in your Power BI model",
            category="optimization",
            parameters=[
                {
                    "name": "include_query_analysis",
                    "type": "boolean",
                    "default": True,
                    "description": "Include query performance analysis"
                }
            ],
            step_templates=[
                {
                    "step_id": "step1_connect",
                    "step_name": "Ensure Connection",
                    "tool_name": "01_connect_to_instance",
                    "parameters": {"model_index": 0},
                    "description": "Connect to Power BI instance"
                },
                {
                    "step_id": "step2_bpa_performance",
                    "step_name": "BPA Performance Rules",
                    "tool_name": "05_comprehensive_analysis",
                    "parameters": {
                        "scope": "performance",
                        "depth": "detailed"
                    },
                    "description": "Run performance-focused BPA rules",
                    "depends_on": ["step1_connect"],
                    "timeout_seconds": 180
                },
                {
                    "step_id": "step3_relationship_cardinality",
                    "step_name": "Analyze Relationship Cardinality",
                    "tool_name": "03_list_relationships",
                    "parameters": {"active_only": True},
                    "description": "Check for cardinality issues in relationships",
                    "depends_on": ["step1_connect"]
                },
                {
                    "step_id": "step4_measure_complexity",
                    "step_name": "Identify Complex Measures",
                    "tool_name": "02_list_measures",
                    "parameters": {},
                    "description": "Find measures that may need optimization",
                    "depends_on": ["step1_connect"]
                },
                {
                    "step_id": "step5_dependencies",
                    "step_name": "Analyze Measure Dependencies",
                    "tool_name": "06_analyze_measure_dependencies",
                    "parameters": {
                        "measure_name": "${context.slowest_measure}",
                        "max_depth": 3
                    },
                    "description": "Analyze dependencies of slowest measures",
                    "depends_on": ["step4_measure_complexity"],
                    "condition": "context.get('slowest_measure') is not None"
                }
            ],
            estimated_duration_seconds=240,
            requires_connection=True
        )

    @staticmethod
    def get_measure_development_template() -> WorkflowTemplate:
        """Guided measure development workflow"""
        return WorkflowTemplate(
            template_id="measure_development",
            template_name="Guided Measure Development",
            description="Step-by-step workflow for developing and validating new measures",
            category="development",
            parameters=[
                {
                    "name": "measure_name",
                    "type": "string",
                    "required": True,
                    "description": "Name of the measure to create"
                },
                {
                    "name": "table_name",
                    "type": "string",
                    "required": True,
                    "description": "Table to add the measure to"
                },
                {
                    "name": "expression",
                    "type": "string",
                    "required": True,
                    "description": "DAX expression for the measure"
                }
            ],
            step_templates=[
                {
                    "step_id": "step1_validate_dax",
                    "step_name": "Validate DAX Syntax",
                    "tool_name": "03_dax_intelligence",
                    "parameters": {
                        "expression": "${params.expression}",
                        "analysis_mode": "analyze"
                    },
                    "description": "Validate DAX syntax and analyze context transitions"
                },
                {
                    "step_id": "step2_create_measure",
                    "step_name": "Create Measure",
                    "tool_name": "04_upsert_measure",
                    "parameters": {
                        "table": "${params.table_name}",
                        "measure_name": "${params.measure_name}",
                        "expression": "${params.expression}"
                    },
                    "description": "Create the measure in the model",
                    "condition": "$.step1_validate_dax.result.validation.valid == True",
                    "depends_on": ["step1_validate_dax"]
                },
                {
                    "step_id": "step3_test_measure",
                    "step_name": "Test Measure Execution",
                    "tool_name": "03_run_dax",
                    "parameters": {
                        "query": "EVALUATE ROW(\"Result\", [${params.measure_name}])",
                        "mode": "analyze"
                    },
                    "description": "Test the measure and get performance metrics",
                    "depends_on": ["step2_create_measure"]
                },
                {
                    "step_id": "step4_analyze_dependencies",
                    "step_name": "Analyze Dependencies",
                    "tool_name": "06_analyze_measure_dependencies",
                    "parameters": {
                        "table": "${params.table_name}",
                        "measure_name": "${params.measure_name}"
                    },
                    "description": "Analyze measure dependencies",
                    "depends_on": ["step2_create_measure"]
                }
            ],
            estimated_duration_seconds=60,
            requires_connection=True
        )

    @staticmethod
    def get_all_templates() -> List[WorkflowTemplate]:
        """Get all available workflow templates"""
        return [
            WorkflowTemplates.get_model_review_template(),
            WorkflowTemplates.get_performance_optimization_template(),
            WorkflowTemplates.get_measure_development_template()
        ]

    @staticmethod
    def instantiate_template(template: WorkflowTemplate, params: Dict[str, Any]) -> Workflow:
        """Create a Workflow instance from a template"""
        workflow_id = str(uuid.uuid4())

        # Create workflow steps from template
        steps = []
        for step_template in template.step_templates:
            # Replace parameter placeholders
            parameters = {}
            for key, value in step_template.get("parameters", {}).items():
                if isinstance(value, str) and value.startswith("${params."):
                    param_key = value[9:-1]  # Extract from "${params.xxx}"
                    parameters[key] = params.get(param_key, value)
                else:
                    parameters[key] = value

            step = WorkflowStep(
                step_id=step_template["step_id"],
                step_name=step_template["step_name"],
                tool_name=step_template["tool_name"],
                parameters=parameters,
                description=step_template.get("description", ""),
                condition=step_template.get("condition"),
                depends_on=step_template.get("depends_on", []),
                retry_on_failure=step_template.get("retry_on_failure", False),
                timeout_seconds=step_template.get("timeout_seconds")
            )
            steps.append(step)

        return Workflow(
            workflow_id=workflow_id,
            workflow_name=template.template_name,
            description=template.description,
            category=template.category,
            steps=steps
        )
```

### 1.6 MCP Tool Handlers

```python
# server/handlers/workflow_handler.py

import logging
from typing import Dict, Any
from server.registry import ToolDefinition
from core.workflows.workflow_engine import WorkflowEngine
from core.workflows.workflow_templates import WorkflowTemplates
from core.config.config_manager import config

logger = logging.getLogger(__name__)

# Global workflow engine instance
workflow_engine = WorkflowEngine(config)

def handle_execute_workflow(args: Dict[str, Any]) -> Dict[str, Any]:
    """Execute a workflow from template"""
    template_id = args.get("template_id")
    parameters = args.get("parameters", {})

    if not template_id:
        return {
            "success": False,
            "error": "template_id is required"
        }

    # Get template
    all_templates = WorkflowTemplates.get_all_templates()
    template = next((t for t in all_templates if t.template_id == template_id), None)

    if not template:
        return {
            "success": False,
            "error": f"Template not found: {template_id}",
            "available_templates": [t.template_id for t in all_templates]
        }

    # Instantiate workflow
    workflow = WorkflowTemplates.instantiate_template(template, parameters)

    # Execute workflow (synchronous for now - can be made async)
    import asyncio
    result = asyncio.run(workflow_engine.execute_workflow(workflow))

    return result

def handle_list_workflow_templates(args: Dict[str, Any]) -> Dict[str, Any]:
    """List all available workflow templates"""
    templates = WorkflowTemplates.get_all_templates()

    return {
        "success": True,
        "templates": [
            {
                "template_id": t.template_id,
                "template_name": t.template_name,
                "description": t.description,
                "category": t.category,
                "estimated_duration_seconds": t.estimated_duration_seconds,
                "parameters": t.parameters,
                "requires_connection": t.requires_connection,
                "step_count": len(t.step_templates)
            }
            for t in templates
        ],
        "count": len(templates)
    }

def handle_get_workflow_status(args: Dict[str, Any]) -> Dict[str, Any]:
    """Get status of a running workflow"""
    workflow_id = args.get("workflow_id")

    if not workflow_id:
        return {
            "success": False,
            "error": "workflow_id is required"
        }

    status = workflow_engine.get_workflow_status(workflow_id)

    if status:
        return {
            "success": True,
            "status": status
        }
    else:
        return {
            "success": False,
            "error": f"Workflow not found: {workflow_id}"
        }

def handle_cancel_workflow(args: Dict[str, Any]) -> Dict[str, Any]:
    """Cancel a running workflow"""
    workflow_id = args.get("workflow_id")

    if not workflow_id:
        return {
            "success": False,
            "error": "workflow_id is required"
        }

    cancelled = workflow_engine.cancel_workflow(workflow_id)

    return {
        "success": cancelled,
        "message": f"Workflow {'cancelled' if cancelled else 'not found or already completed'}"
    }

def register_workflow_handlers(registry):
    """Register workflow tool handlers"""
    from server.tool_schemas import TOOL_SCHEMAS

    tools = [
        ToolDefinition(
            name="execute_workflow",
            description="[20-Workflows] Execute a pre-defined workflow template for common tasks (model review, performance optimization, measure development)",
            handler=handle_execute_workflow,
            input_schema=TOOL_SCHEMAS.get('execute_workflow', {}),
            category="workflows",
            sort_order=200
        ),
        ToolDefinition(
            name="list_workflow_templates",
            description="[20-Workflows] List all available workflow templates with descriptions and parameters",
            handler=handle_list_workflow_templates,
            input_schema=TOOL_SCHEMAS.get('list_workflow_templates', {}),
            category="workflows",
            sort_order=201
        ),
        ToolDefinition(
            name="get_workflow_status",
            description="[20-Workflows] Get real-time status and progress of a running workflow",
            handler=handle_get_workflow_status,
            input_schema=TOOL_SCHEMAS.get('get_workflow_status', {}),
            category="workflows",
            sort_order=202
        ),
        ToolDefinition(
            name="cancel_workflow",
            description="[20-Workflows] Cancel a running workflow",
            handler=handle_cancel_workflow,
            input_schema=TOOL_SCHEMAS.get('cancel_workflow', {}),
            category="workflows",
            sort_order=203
        )
    ]

    for tool in tools:
        registry.register(tool)

    logger.info(f"Registered {len(tools)} workflow handlers")
```

---

## Part 2: Agentic Intelligence Enhancement

### 2.1 Architecture Design

#### Core Components

```
core/intelligence/
├── __init__.py
├── intent_analyzer.py          # Semantic intent parsing
├── recommendation_engine.py     # Proactive recommendations
├── learning_system.py          # Learn from interactions
├── workflow_recommender.py     # Workflow suggestions
└── models/
    ├── intent_models.py        # Intent classification models
    └── interaction_log.py      # Interaction history

data/
├── interactions/
    ├── interaction_log.db      # SQLite database for interactions
    └── embeddings/             # Pre-computed embeddings
```

#### Data Models

```python
# core/intelligence/models/interaction_log.py

from dataclasses import dataclass
from datetime import datetime
from typing import Optional, Dict, Any

@dataclass
class UserInteraction:
    """Record of a user interaction"""
    interaction_id: str
    timestamp: datetime

    # User input
    user_intent: str  # Natural language intent
    tool_invoked: str
    parameters: Dict[str, Any]

    # Execution details
    success: bool
    error_type: Optional[str]
    execution_time_seconds: float

    # Context
    model_name: Optional[str]
    table_name: Optional[str]

    # Outcome
    user_satisfaction: Optional[int]  # 1-5 rating (if available)
    followed_by: Optional[str]  # Next tool used

@dataclass
class IntentClassification:
    """Classification of user intent"""
    intent_category: str  # "analysis", "development", "optimization", "documentation"
    intent_subcategory: str  # "bpa", "performance", "measure_creation", etc.
    confidence: float  # 0.0 - 1.0

    # Extracted entities
    entities: Dict[str, Any]  # e.g., {"table": "Sales", "measure": "Total Revenue"}

    # Suggested tools
    suggested_tools: list  # Ranked list of tools
    suggested_workflow: Optional[str]  # Workflow template ID if applicable
```

### 2.2 Semantic Intent Analyzer

```python
# core/intelligence/intent_analyzer.py

import logging
from typing import Dict, Any, List, Tuple
from .models.intent_models import IntentClassification

logger = logging.getLogger(__name__)

class IntentAnalyzer:
    """
    Semantic intent parsing using embeddings and pattern matching

    This analyzes user requests to understand their intent beyond keywords,
    enabling more intelligent tool routing and proactive recommendations.
    """

    def __init__(self, config):
        self.config = config
        self._load_intent_patterns()
        self._load_embeddings()

    def analyze_intent(self, user_request: str, context: Dict[str, Any] = None) -> IntentClassification:
        """
        Analyze user intent from natural language request

        Args:
            user_request: Natural language user request
            context: Optional context (connected model, previous tools used, etc.)

        Returns:
            IntentClassification with suggested tools and workflows
        """
        # Normalize request
        request_lower = user_request.lower().strip()

        # Extract entities (table names, measure names, etc.)
        entities = self._extract_entities(request_lower, context)

        # Classify intent category
        intent_category, category_confidence = self._classify_category(request_lower)

        # Classify intent subcategory
        intent_subcategory, subcategory_confidence = self._classify_subcategory(
            request_lower, intent_category
        )

        # Determine suggested tools
        suggested_tools = self._suggest_tools(intent_category, intent_subcategory, entities)

        # Determine if a workflow is more appropriate
        suggested_workflow = self._suggest_workflow(intent_category, intent_subcategory)

        confidence = (category_confidence + subcategory_confidence) / 2

        return IntentClassification(
            intent_category=intent_category,
            intent_subcategory=intent_subcategory,
            confidence=confidence,
            entities=entities,
            suggested_tools=suggested_tools,
            suggested_workflow=suggested_workflow
        )

    def _classify_category(self, request: str) -> Tuple[str, float]:
        """Classify high-level intent category"""

        # Analysis patterns
        if any(pattern in request for pattern in [
            "analyze", "analysis", "check", "review", "inspect", "examine",
            "what's wrong", "issues", "problems", "quality"
        ]):
            return "analysis", 0.85

        # Development patterns
        if any(pattern in request for pattern in [
            "create", "add", "build", "develop", "make", "new measure",
            "write dax", "implement"
        ]):
            return "development", 0.85

        # Optimization patterns
        if any(pattern in request for pattern in [
            "optimize", "improve", "faster", "slow", "performance",
            "speed up", "bottleneck"
        ]):
            return "optimization", 0.85

        # Documentation patterns
        if any(pattern in request for pattern in [
            "document", "export", "generate report", "create documentation",
            "explain", "describe"
        ]):
            return "documentation", 0.80

        # Exploration patterns
        if any(pattern in request for pattern in [
            "show", "list", "what", "which", "get", "view", "see",
            "tell me about"
        ]):
            return "exploration", 0.75

        return "general", 0.50

    def _classify_subcategory(self, request: str, category: str) -> Tuple[str, float]:
        """Classify specific subcategory within category"""

        if category == "analysis":
            if "best practice" in request or "bpa" in request:
                return "best_practices", 0.90
            if "performance" in request or "slow" in request:
                return "performance", 0.90
            if "relationship" in request:
                return "relationships", 0.85
            if "measure" in request and "depend" in request:
                return "dependencies", 0.85
            return "general_analysis", 0.70

        elif category == "development":
            if "measure" in request:
                return "measure_creation", 0.90
            if "calculation group" in request:
                return "calculation_group", 0.90
            if "table" in request:
                return "table_creation", 0.85
            return "general_development", 0.70

        elif category == "optimization":
            if "dax" in request:
                return "dax_optimization", 0.90
            if "relationship" in request:
                return "relationship_optimization", 0.85
            if "aggregation" in request:
                return "aggregation", 0.85
            return "general_optimization", 0.70

        elif category == "documentation":
            if "word" in request or "docx" in request:
                return "word_export", 0.90
            if "html" in request:
                return "html_export", 0.90
            if "schema" in request:
                return "schema_export", 0.85
            return "general_documentation", 0.70

        return "general", 0.60

    def _extract_entities(self, request: str, context: Dict[str, Any] = None) -> Dict[str, Any]:
        """Extract entities (table names, measure names, etc.) from request"""
        entities = {}

        # Extract table names (simple pattern matching - can be enhanced with NER)
        # Look for patterns like "Sales table", "the Sales table", "'Sales'"
        import re

        # Table patterns
        table_pattern = r"(?:table\s+)?['\"]?([A-Z][A-Za-z0-9_\s]+)['\"]?\s+table"
        table_matches = re.findall(table_pattern, request, re.IGNORECASE)
        if table_matches:
            entities["table"] = table_matches[0].strip()

        # Measure patterns
        measure_pattern = r"(?:measure\s+)?['\"]?([A-Z][A-Za-z0-9_\s]+)['\"]?\s+measure"
        measure_matches = re.findall(measure_pattern, request, re.IGNORECASE)
        if measure_matches:
            entities["measure"] = measure_matches[0].strip()

        # Use context to fill in missing entities
        if context:
            if "table" not in entities and "last_table" in context:
                entities["table"] = context["last_table"]
            if "measure" not in entities and "last_measure" in context:
                entities["measure"] = context["last_measure"]

        return entities

    def _suggest_tools(
        self,
        category: str,
        subcategory: str,
        entities: Dict[str, Any]
    ) -> List[str]:
        """Suggest tools based on intent classification"""

        suggestions = []

        # Analysis category
        if category == "analysis":
            if subcategory == "best_practices":
                suggestions = ["05_comprehensive_analysis", "02_list_measures", "03_list_relationships"]
            elif subcategory == "performance":
                suggestions = ["05_comprehensive_analysis", "03_run_dax"]
            elif subcategory == "relationships":
                suggestions = ["03_list_relationships", "02_describe_table"]
            elif subcategory == "dependencies":
                suggestions = ["06_analyze_measure_dependencies", "06_get_measure_impact"]

        # Development category
        elif category == "development":
            if subcategory == "measure_creation":
                suggestions = ["03_dax_intelligence", "04_upsert_measure", "06_analyze_measure_dependencies"]
            elif subcategory == "calculation_group":
                suggestions = ["04_create_calculation_group", "04_list_calculation_groups"]

        # Optimization category
        elif category == "optimization":
            if subcategory == "dax_optimization":
                suggestions = ["03_dax_intelligence", "03_run_dax", "06_analyze_measure_dependencies"]
            elif subcategory == "general_optimization":
                suggestions = ["05_comprehensive_analysis", "03_list_relationships"]

        # Documentation category
        elif category == "documentation":
            if subcategory == "word_export":
                suggestions = ["08_generate_model_documentation_word"]
            elif subcategory == "html_export":
                suggestions = ["08_export_model_explorer_html"]
            elif subcategory == "schema_export":
                suggestions = ["07_export_model_schema"]

        # Exploration category
        elif category == "exploration":
            if entities.get("table"):
                suggestions = ["02_describe_table", "03_preview_table_data"]
            elif entities.get("measure"):
                suggestions = ["02_get_measure_details", "06_analyze_measure_dependencies"]
            else:
                suggestions = ["02_list_tables", "02_list_measures"]

        return suggestions

    def _suggest_workflow(self, category: str, subcategory: str) -> Optional[str]:
        """Suggest a workflow template if appropriate"""

        # Full model review
        if category == "analysis" and subcategory in ["general_analysis", "best_practices"]:
            return "model_review_complete"

        # Performance optimization
        if category == "optimization" or (category == "analysis" and subcategory == "performance"):
            return "performance_optimization"

        # Measure development
        if category == "development" and subcategory == "measure_creation":
            return "measure_development"

        return None

    def _load_intent_patterns(self):
        """Load intent patterns from configuration"""
        # In a full implementation, this would load from a config file or database
        pass

    def _load_embeddings(self):
        """Load pre-computed embeddings for semantic similarity"""
        # In a full implementation, this would load embeddings
        # Could use sentence-transformers or similar
        pass
```

### 2.3 Recommendation Engine

```python
# core/intelligence/recommendation_engine.py

import logging
from typing import Dict, Any, List, Optional
from .learning_system import LearningSystem

logger = logging.getLogger(__name__)

class RecommendationEngine:
    """
    Generates proactive recommendations based on context and learning
    """

    def __init__(self, config, learning_system: Optional[LearningSystem] = None):
        self.config = config
        self.learning_system = learning_system or LearningSystem(config)

    def get_next_step_recommendations(
        self,
        current_tool: str,
        current_result: Dict[str, Any],
        context: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """
        Recommend next steps based on current tool result

        Args:
            current_tool: Tool that was just executed
            current_result: Result from the tool
            context: Current session context

        Returns:
            List of recommended next steps with reasoning
        """
        recommendations = []

        # Rule-based recommendations
        rule_based = self._get_rule_based_recommendations(current_tool, current_result, context)
        recommendations.extend(rule_based)

        # Learning-based recommendations
        if self.learning_system:
            learned = self.learning_system.suggest_next_tools(current_tool, context)
            recommendations.extend(learned)

        # Rank and deduplicate
        recommendations = self._rank_recommendations(recommendations)

        return recommendations[:3]  # Top 3 recommendations

    def _get_rule_based_recommendations(
        self,
        current_tool: str,
        result: Dict[str, Any],
        context: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Generate recommendations based on rules"""
        recs = []

        # After connection
        if current_tool == "01_connect_to_instance":
            recs.append({
                "tool": "02_list_tables",
                "reason": "Review model structure after connecting",
                "priority": "high",
                "auto_params": {}
            })
            recs.append({
                "tool": "05_comprehensive_analysis",
                "reason": "Run comprehensive analysis to identify issues",
                "priority": "medium",
                "auto_params": {"scope": "all", "depth": "balanced"}
            })

        # After listing tables
        elif current_tool == "02_list_tables":
            table_count = result.get("count", 0)
            if table_count > 0:
                # Get first table for description
                tables = result.get("tables", [])
                if tables:
                    first_table = tables[0].get("name")
                    recs.append({
                        "tool": "02_describe_table",
                        "reason": f"Explore the '{first_table}' table in detail",
                        "priority": "medium",
                        "auto_params": {"table": first_table}
                    })

            recs.append({
                "tool": "03_list_relationships",
                "reason": "Review how tables are connected",
                "priority": "medium",
                "auto_params": {}
            })

        # After BPA analysis
        elif current_tool == "05_comprehensive_analysis":
            issues = result.get("issues", [])
            if issues:
                high_severity = [i for i in issues if i.get("severity") == "error"]
                if high_severity:
                    recs.append({
                        "tool": "08_generate_model_documentation_word",
                        "reason": "Document findings from BPA analysis",
                        "priority": "medium",
                        "auto_params": {}
                    })

                # Check for performance issues
                perf_issues = [i for i in issues if "performance" in i.get("category", "").lower()]
                if perf_issues:
                    recs.append({
                        "workflow": "performance_optimization",
                        "reason": "Performance issues detected, run optimization workflow",
                        "priority": "high",
                        "auto_params": {}
                    })

        # After creating a measure
        elif current_tool == "04_upsert_measure":
            if result.get("success"):
                measure_name = result.get("measure_name")
                table = result.get("table")

                recs.append({
                    "tool": "03_dax_intelligence",
                    "reason": "Validate the DAX expression for the new measure",
                    "priority": "high",
                    "auto_params": {
                        "expression": f"[{measure_name}]",
                        "analysis_mode": "analyze"
                    }
                })

                recs.append({
                    "tool": "06_analyze_measure_dependencies",
                    "reason": "Analyze dependencies of the new measure",
                    "priority": "medium",
                    "auto_params": {
                        "table": table,
                        "measure_name": measure_name
                    }
                })

        # After DAX intelligence analysis
        elif current_tool == "03_dax_intelligence":
            analysis = result.get("analysis", {})
            if analysis:
                context_transitions = analysis.get("context_transitions", 0)
                if context_transitions > 5:
                    recs.append({
                        "tool": "03_run_dax",
                        "reason": "Many context transitions detected, benchmark performance",
                        "priority": "high",
                        "auto_params": {
                            "mode": "analyze"
                        }
                    })

        return recs

    def _rank_recommendations(self, recommendations: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Rank and deduplicate recommendations"""
        # Remove duplicates (by tool/workflow name)
        seen = set()
        unique_recs = []

        for rec in recommendations:
            key = rec.get("tool") or rec.get("workflow")
            if key and key not in seen:
                seen.add(key)
                unique_recs.append(rec)

        # Sort by priority
        priority_order = {"high": 0, "medium": 1, "low": 2}
        unique_recs.sort(key=lambda r: priority_order.get(r.get("priority", "low"), 3))

        return unique_recs

    def get_workflow_recommendations(self, context: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Recommend workflows based on current context"""
        recs = []

        # If user hasn't run BPA yet
        if not context.get("bpa_run"):
            recs.append({
                "workflow": "model_review_complete",
                "reason": "Comprehensive model review not yet performed",
                "priority": "high",
                "estimated_duration": 300
            })

        # If performance issues detected
        if context.get("performance_issues"):
            recs.append({
                "workflow": "performance_optimization",
                "reason": "Performance issues detected in previous analysis",
                "priority": "high",
                "estimated_duration": 240
            })

        return recs
```

### 2.4 Learning System

```python
# core/intelligence/learning_system.py

import logging
import sqlite3
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from pathlib import Path

logger = logging.getLogger(__name__)

class LearningSystem:
    """
    Learn from user interactions to improve recommendations
    """

    def __init__(self, config):
        self.config = config
        self.db_path = Path("data/interactions/interaction_log.db")
        self._init_database()

    def _init_database(self):
        """Initialize SQLite database for interaction logging"""
        self.db_path.parent.mkdir(parents=True, exist_ok=True)

        conn = sqlite3.connect(str(self.db_path))
        cursor = conn.cursor()

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS interactions (
                interaction_id TEXT PRIMARY KEY,
                timestamp TEXT,
                user_intent TEXT,
                tool_invoked TEXT,
                parameters TEXT,
                success INTEGER,
                error_type TEXT,
                execution_time_seconds REAL,
                model_name TEXT,
                followed_by TEXT
            )
        """)

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS tool_sequences (
                sequence_id INTEGER PRIMARY KEY AUTOINCREMENT,
                tool_from TEXT,
                tool_to TEXT,
                frequency INTEGER DEFAULT 1,
                avg_time_between_seconds REAL,
                last_seen TEXT
            )
        """)

        conn.commit()
        conn.close()

    def log_interaction(
        self,
        tool_invoked: str,
        parameters: Dict[str, Any],
        success: bool,
        execution_time_seconds: float,
        error_type: Optional[str] = None,
        user_intent: Optional[str] = None,
        model_name: Optional[str] = None
    ):
        """Log a user interaction"""
        import uuid
        import json

        interaction_id = str(uuid.uuid4())
        timestamp = datetime.now().isoformat()

        conn = sqlite3.connect(str(self.db_path))
        cursor = conn.cursor()

        cursor.execute("""
            INSERT INTO interactions (
                interaction_id, timestamp, user_intent, tool_invoked,
                parameters, success, error_type, execution_time_seconds, model_name
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            interaction_id,
            timestamp,
            user_intent,
            tool_invoked,
            json.dumps(parameters),
            1 if success else 0,
            error_type,
            execution_time_seconds,
            model_name
        ))

        conn.commit()
        conn.close()

    def update_tool_sequence(self, tool_from: str, tool_to: str, time_between_seconds: float):
        """Update tool sequence patterns"""
        conn = sqlite3.connect(str(self.db_path))
        cursor = conn.cursor()

        # Check if sequence exists
        cursor.execute("""
            SELECT sequence_id, frequency, avg_time_between_seconds
            FROM tool_sequences
            WHERE tool_from = ? AND tool_to = ?
        """, (tool_from, tool_to))

        row = cursor.fetchone()

        if row:
            # Update existing sequence
            sequence_id, frequency, avg_time = row
            new_frequency = frequency + 1
            new_avg_time = ((avg_time * frequency) + time_between_seconds) / new_frequency

            cursor.execute("""
                UPDATE tool_sequences
                SET frequency = ?, avg_time_between_seconds = ?, last_seen = ?
                WHERE sequence_id = ?
            """, (new_frequency, new_avg_time, datetime.now().isoformat(), sequence_id))
        else:
            # Insert new sequence
            cursor.execute("""
                INSERT INTO tool_sequences (tool_from, tool_to, frequency, avg_time_between_seconds, last_seen)
                VALUES (?, ?, 1, ?, ?)
            """, (tool_from, tool_to, time_between_seconds, datetime.now().isoformat()))

        conn.commit()
        conn.close()

    def suggest_next_tools(self, current_tool: str, context: Dict[str, Any], top_n: int = 3) -> List[Dict[str, Any]]:
        """Suggest next tools based on learned patterns"""
        conn = sqlite3.connect(str(self.db_path))
        cursor = conn.cursor()

        # Get most frequent next tools
        cursor.execute("""
            SELECT tool_to, frequency, avg_time_between_seconds
            FROM tool_sequences
            WHERE tool_from = ?
            ORDER BY frequency DESC
            LIMIT ?
        """, (current_tool, top_n))

        rows = cursor.fetchall()
        conn.close()

        suggestions = []
        for tool_to, frequency, avg_time in rows:
            suggestions.append({
                "tool": tool_to,
                "reason": f"Users frequently use this after {current_tool} ({frequency} times)",
                "priority": "medium",
                "confidence": min(frequency / 10.0, 1.0),  # Normalize to 0-1
                "auto_params": {}
            })

        return suggestions

    def get_analytics(self) -> Dict[str, Any]:
        """Get analytics on tool usage patterns"""
        conn = sqlite3.connect(str(self.db_path))
        cursor = conn.cursor()

        # Most used tools
        cursor.execute("""
            SELECT tool_invoked, COUNT(*) as count
            FROM interactions
            GROUP BY tool_invoked
            ORDER BY count DESC
            LIMIT 10
        """)
        most_used_tools = [{"tool": row[0], "count": row[1]} for row in cursor.fetchall()]

        # Success rate by tool
        cursor.execute("""
            SELECT tool_invoked,
                   SUM(success) as successes,
                   COUNT(*) as total,
                   CAST(SUM(success) AS REAL) / COUNT(*) as success_rate
            FROM interactions
            GROUP BY tool_invoked
            ORDER BY success_rate ASC
            LIMIT 10
        """)
        lowest_success_tools = [
            {"tool": row[0], "success_rate": row[3], "total": row[2]}
            for row in cursor.fetchall()
        ]

        # Most common sequences
        cursor.execute("""
            SELECT tool_from, tool_to, frequency
            FROM tool_sequences
            ORDER BY frequency DESC
            LIMIT 10
        """)
        common_sequences = [
            {"from": row[0], "to": row[1], "frequency": row[2]}
            for row in cursor.fetchall()
        ]

        conn.close()

        return {
            "most_used_tools": most_used_tools,
            "lowest_success_tools": lowest_success_tools,
            "common_sequences": common_sequences
        }
```

### 2.5 Integration with Existing Server

```python
# server/handlers/intelligence_handler.py

import logging
from typing import Dict, Any
from server.registry import ToolDefinition
from core.intelligence.intent_analyzer import IntentAnalyzer
from core.intelligence.recommendation_engine import RecommendationEngine
from core.intelligence.learning_system import LearningSystem
from core.config.config_manager import config

logger = logging.getLogger(__name__)

# Global instances
intent_analyzer = IntentAnalyzer(config)
learning_system = LearningSystem(config)
recommendation_engine = RecommendationEngine(config, learning_system)

def handle_analyze_intent(args: Dict[str, Any]) -> Dict[str, Any]:
    """Analyze user intent and suggest tools/workflows"""
    user_request = args.get("request")
    context = args.get("context", {})

    if not user_request:
        return {
            "success": False,
            "error": "request parameter is required"
        }

    # Analyze intent
    classification = intent_analyzer.analyze_intent(user_request, context)

    return {
        "success": True,
        "intent_category": classification.intent_category,
        "intent_subcategory": classification.intent_subcategory,
        "confidence": classification.confidence,
        "entities": classification.entities,
        "suggested_tools": classification.suggested_tools,
        "suggested_workflow": classification.suggested_workflow,
        "explanation": f"Detected {classification.intent_category} intent with {classification.confidence:.0%} confidence"
    }

def handle_get_recommendations(args: Dict[str, Any]) -> Dict[str, Any]:
    """Get proactive recommendations"""
    current_tool = args.get("current_tool")
    current_result = args.get("current_result", {})
    context = args.get("context", {})

    if not current_tool:
        # Get general workflow recommendations
        workflow_recs = recommendation_engine.get_workflow_recommendations(context)
        return {
            "success": True,
            "recommendations": workflow_recs
        }

    # Get next step recommendations
    next_steps = recommendation_engine.get_next_step_recommendations(
        current_tool, current_result, context
    )

    return {
        "success": True,
        "recommendations": next_steps
    }

def handle_get_learning_analytics(args: Dict[str, Any]) -> Dict[str, Any]:
    """Get analytics on learned patterns"""
    analytics = learning_system.get_analytics()

    return {
        "success": True,
        "analytics": analytics
    }

def register_intelligence_handlers(registry):
    """Register intelligence tool handlers"""
    from server.tool_schemas import TOOL_SCHEMAS

    tools = [
        ToolDefinition(
            name="analyze_intent",
            description="[21-Intelligence] Analyze user intent and suggest appropriate tools or workflows",
            handler=handle_analyze_intent,
            input_schema=TOOL_SCHEMAS.get('analyze_intent', {}),
            category="intelligence",
            sort_order=210
        ),
        ToolDefinition(
            name="get_recommendations",
            description="[21-Intelligence] Get proactive recommendations for next steps",
            handler=handle_get_recommendations,
            input_schema=TOOL_SCHEMAS.get('get_recommendations', {}),
            category="intelligence",
            sort_order=211
        ),
        ToolDefinition(
            name="get_learning_analytics",
            description="[21-Intelligence] View analytics on tool usage patterns and learned behaviors",
            handler=handle_get_learning_analytics,
            input_schema=TOOL_SCHEMAS.get('get_learning_analytics', {}),
            category="intelligence",
            sort_order=212
        )
    ]

    for tool in tools:
        registry.register(tool)

    logger.info(f"Registered {len(tools)} intelligence handlers")
```

---

## Part 3: Integration Strategy

### 3.1 Modify Main Server

```python
# src/pbixray_server_enhanced.py

# Add imports
from core.workflows import workflow_engine
from core.intelligence.learning_system import LearningSystem
from core.intelligence.recommendation_engine import RecommendationEngine

# Initialize systems
learning_system = LearningSystem(config)
recommendation_engine = RecommendationEngine(config, learning_system)

# Modify @app.call_tool() to integrate learning
@app.call_tool()
async def call_tool(name: str, arguments: Any) -> List[TextContent]:
    """Execute tool via dispatcher with learning integration"""
    try:
        _t0 = time.time()

        # ... existing validation and rate limiting ...

        # Dispatch to handler
        result = dispatcher.dispatch(name, arguments)

        # Record telemetry
        _dur = round((time.time() - _t0) * 1000, 2)

        # Log interaction for learning
        learning_system.log_interaction(
            tool_invoked=name,
            parameters=arguments,
            success=result.get("success", False),
            execution_time_seconds=_dur / 1000,
            error_type=result.get("error_type")
        )

        # Add proactive recommendations
        if isinstance(result, dict) and result.get("success"):
            recommendations = recommendation_engine.get_next_step_recommendations(
                name, result, connection_state.context
            )
            if recommendations:
                result["_next_steps"] = recommendations

        # ... rest of existing code ...
```

### 3.2 Tool Schema Additions

```python
# Add to server/tool_schemas.py

TOOL_SCHEMAS.update({
    'execute_workflow': {
        "type": "object",
        "properties": {
            "template_id": {
                "type": "string",
                "description": "Workflow template ID (use list_workflow_templates to see options)"
            },
            "parameters": {
                "type": "object",
                "description": "Parameters for the workflow template"
            }
        },
        "required": ["template_id"]
    },

    'list_workflow_templates': {
        "type": "object",
        "properties": {},
        "required": []
    },

    'get_workflow_status': {
        "type": "object",
        "properties": {
            "workflow_id": {
                "type": "string",
                "description": "Workflow ID to check status"
            }
        },
        "required": ["workflow_id"]
    },

    'analyze_intent': {
        "type": "object",
        "properties": {
            "request": {
                "type": "string",
                "description": "Natural language user request"
            },
            "context": {
                "type": "object",
                "description": "Optional context (connected model, previous tools, etc.)"
            }
        },
        "required": ["request"]
    },

    'get_recommendations': {
        "type": "object",
        "properties": {
            "current_tool": {
                "type": "string",
                "description": "Tool that was just executed"
            },
            "current_result": {
                "type": "object",
                "description": "Result from the current tool"
            },
            "context": {
                "type": "object",
                "description": "Current session context"
            }
        },
        "required": []
    }
})
```

### 3.3 Handler Registration

```python
# Modify server/handlers/__init__.py

from .workflow_handler import register_workflow_handlers
from .intelligence_handler import register_intelligence_handlers

def register_all_handlers(registry):
    """Register all tool handlers"""
    # ... existing registrations ...

    # New registrations
    register_workflow_handlers(registry)
    register_intelligence_handlers(registry)
```

---

## Part 4: Implementation Phases

### Phase 1: Foundation (Week 1-2)
**Goal:** Set up core infrastructure

**Tasks:**
1. Create directory structure (core/workflows/, core/intelligence/)
2. Implement data models (models.py files)
3. Set up SQLite database for learning system
4. Create basic workflow engine skeleton
5. Implement progress tracker

**Deliverables:**
- ✅ Directory structure created
- ✅ Data models defined
- ✅ Database schema initialized
- ✅ Basic workflow engine running

**Testing:**
- Unit tests for data models
- Database initialization tests

### Phase 2: Workflow Orchestration (Week 3-4)
**Goal:** Implement workflow execution

**Tasks:**
1. Implement WorkflowEngine.execute_workflow()
2. Implement StepExecutor
3. Create 3 workflow templates (model review, performance, measure dev)
4. Implement workflow MCP handlers
5. Add tool schemas for workflow tools

**Deliverables:**
- ✅ Workflow engine fully functional
- ✅ 3 working workflow templates
- ✅ MCP tools: execute_workflow, list_workflow_templates, get_workflow_status

**Testing:**
- Integration tests for workflow execution
- Test each workflow template end-to-end
- Test error handling and retry logic

### Phase 3: Agentic Intelligence (Week 5-6)
**Goal:** Implement intelligent recommendations

**Tasks:**
1. Implement IntentAnalyzer
2. Implement RecommendationEngine
3. Implement LearningSystem with database logging
4. Create intelligence MCP handlers
5. Integrate with main server

**Deliverables:**
- ✅ Intent analyzer working
- ✅ Recommendation engine providing next steps
- ✅ Learning system logging interactions
- ✅ MCP tools: analyze_intent, get_recommendations

**Testing:**
- Test intent classification accuracy
- Test recommendation quality
- Test learning system data collection

### Phase 4: Integration & Polish (Week 7-8)
**Goal:** Integrate all components and polish UX

**Tasks:**
1. Integrate learning system into main server
2. Add proactive recommendations to all tool responses
3. Create comprehensive documentation
4. Performance optimization
5. User acceptance testing

**Deliverables:**
- ✅ Fully integrated system
- ✅ Documentation updated
- ✅ Performance benchmarks met
- ✅ User guide for workflows and intelligence

**Testing:**
- End-to-end workflow testing
- Performance testing (workflow execution speed)
- User acceptance testing with sample scenarios

---

## Part 5: Testing Strategy

### 5.1 Unit Tests

```python
# tests/test_workflow_engine.py

import pytest
from core.workflows.workflow_engine import WorkflowEngine
from core.workflows.models import Workflow, WorkflowStep, StepStatus

@pytest.fixture
def workflow_engine():
    from core.config.config_manager import config
    return WorkflowEngine(config)

@pytest.fixture
def simple_workflow():
    return Workflow(
        workflow_id="test_workflow",
        workflow_name="Test Workflow",
        description="Test workflow",
        category="test",
        steps=[
            WorkflowStep(
                step_id="step1",
                step_name="List Tables",
                tool_name="02_list_tables",
                parameters={},
                description="List all tables"
            )
        ]
    )

@pytest.mark.asyncio
async def test_execute_simple_workflow(workflow_engine, simple_workflow):
    """Test executing a simple workflow"""
    result = await workflow_engine.execute_workflow(simple_workflow)

    assert result["success"] == True
    assert result["steps_completed"] == 1
    assert result["status"] == "completed"

@pytest.mark.asyncio
async def test_workflow_with_retry(workflow_engine):
    """Test workflow retry logic"""
    workflow = Workflow(
        workflow_id="test_retry",
        workflow_name="Test Retry",
        description="Test retry",
        category="test",
        steps=[
            WorkflowStep(
                step_id="step1",
                step_name="Failing Step",
                tool_name="nonexistent_tool",
                parameters={},
                description="This should fail and retry",
                retry_on_failure=True,
                max_retries=2
            )
        ]
    )

    result = await workflow_engine.execute_workflow(workflow)

    assert result["success"] == False
    assert workflow.steps[0].retry_count == 2  # Should have retried twice
```

```python
# tests/test_intent_analyzer.py

import pytest
from core.intelligence.intent_analyzer import IntentAnalyzer

@pytest.fixture
def intent_analyzer():
    from core.config.config_manager import config
    return IntentAnalyzer(config)

def test_analyze_bpa_intent(intent_analyzer):
    """Test BPA intent detection"""
    result = intent_analyzer.analyze_intent("Run a full analysis to check for issues")

    assert result.intent_category == "analysis"
    assert result.intent_subcategory == "best_practices"
    assert result.confidence > 0.8
    assert "05_comprehensive_analysis" in result.suggested_tools

def test_analyze_measure_creation_intent(intent_analyzer):
    """Test measure creation intent detection"""
    result = intent_analyzer.analyze_intent("Create a new measure called Total Sales")

    assert result.intent_category == "development"
    assert result.intent_subcategory == "measure_creation"
    assert result.suggested_workflow == "measure_development"
    assert "measure_name" in result.entities or "Total Sales" in str(result.entities)
```

### 5.2 Integration Tests

```python
# tests/integration/test_workflows_integration.py

import pytest
from core.workflows.workflow_templates import WorkflowTemplates

@pytest.mark.integration
@pytest.mark.asyncio
async def test_model_review_workflow_end_to_end():
    """Test complete model review workflow"""
    # Prerequisite: Power BI Desktop must be running with a model

    template = WorkflowTemplates.get_model_review_template()
    workflow = WorkflowTemplates.instantiate_template(template, {})

    from core.workflows.workflow_engine import WorkflowEngine
    from core.config.config_manager import config

    engine = WorkflowEngine(config)
    result = await engine.execute_workflow(workflow)

    assert result["success"] == True
    assert result["steps_completed"] >= 5  # At least 5 steps should complete
```

### 5.3 Performance Tests

```python
# tests/performance/test_workflow_performance.py

import pytest
import time
from core.workflows.workflow_templates import WorkflowTemplates

@pytest.mark.performance
@pytest.mark.asyncio
async def test_workflow_execution_time():
    """Test that workflows complete within expected time"""
    template = WorkflowTemplates.get_model_review_template()
    workflow = WorkflowTemplates.instantiate_template(template, {})

    from core.workflows.workflow_engine import WorkflowEngine
    from core.config.config_manager import config

    engine = WorkflowEngine(config)

    start = time.time()
    result = await engine.execute_workflow(workflow)
    duration = time.time() - start

    # Should complete within 2x estimated duration
    assert duration < template.estimated_duration_seconds * 2
```

---

## Part 6: Rollout Plan

### Phase 1: Internal Testing (Week 1)
- Deploy to development environment
- Test all workflows manually
- Gather feedback from internal users
- Fix critical bugs

### Phase 2: Beta Release (Week 2-3)
- Release to select beta users
- Monitor usage analytics
- Collect feedback on workflow UX
- Refine recommendations based on usage

### Phase 3: Production Release (Week 4)
- Full release to all users
- Update documentation and README
- Create video tutorials for workflows
- Monitor performance and errors

### Phase 4: Continuous Improvement (Ongoing)
- Analyze learning system data monthly
- Add new workflow templates based on user requests
- Refine intent classification
- Improve recommendation accuracy

---

## Success Metrics

### Workflow Orchestration
- ✅ 90%+ of workflows complete successfully
- ✅ Average workflow execution time within 120% of estimate
- ✅ Progress tracking updates every 2-5 seconds
- ✅ 0 data loss on workflow interruption

### Agentic Intelligence
- ✅ Intent classification accuracy > 80%
- ✅ Recommendation acceptance rate > 40%
- ✅ Learning system logs 95%+ of interactions
- ✅ Next-step suggestions ranked correctly 70%+ of time

### User Experience
- ✅ Users execute 50%+ more complex analyses with workflows
- ✅ Time to complete common tasks reduced by 60%
- ✅ User satisfaction score > 4.0/5.0
- ✅ Support tickets reduced by 30%

---

## Appendix A: File Checklist

### New Files to Create

#### Core Workflows
- [ ] `core/workflows/__init__.py`
- [ ] `core/workflows/models.py`
- [ ] `core/workflows/workflow_engine.py`
- [ ] `core/workflows/workflow_registry.py`
- [ ] `core/workflows/workflow_state.py`
- [ ] `core/workflows/workflow_templates.py`
- [ ] `core/workflows/workflow_builder.py`
- [ ] `core/workflows/step_executor.py`
- [ ] `core/workflows/progress_tracker.py`

#### Core Intelligence
- [ ] `core/intelligence/__init__.py`
- [ ] `core/intelligence/intent_analyzer.py`
- [ ] `core/intelligence/recommendation_engine.py`
- [ ] `core/intelligence/learning_system.py`
- [ ] `core/intelligence/workflow_recommender.py`
- [ ] `core/intelligence/models/__init__.py`
- [ ] `core/intelligence/models/intent_models.py`
- [ ] `core/intelligence/models/interaction_log.py`

#### Handlers
- [ ] `server/handlers/workflow_handler.py`
- [ ] `server/handlers/intelligence_handler.py`

#### Configuration
- [ ] `config/workflows/model_review.yaml`
- [ ] `config/workflows/performance_optimization.yaml`
- [ ] `config/workflows/measure_development.yaml`

#### Tests
- [ ] `tests/test_workflow_engine.py`
- [ ] `tests/test_intent_analyzer.py`
- [ ] `tests/test_recommendation_engine.py`
- [ ] `tests/test_learning_system.py`
- [ ] `tests/integration/test_workflows_integration.py`
- [ ] `tests/performance/test_workflow_performance.py`

#### Documentation
- [ ] `docs/WORKFLOW_USER_GUIDE.md`
- [ ] `docs/INTELLIGENCE_SYSTEM.md`
- [ ] `docs/WORKFLOW_API.md`

---

## Appendix B: Configuration Updates

```json
// Add to config/default_config.json

{
  "workflows": {
    "enabled": true,
    "max_concurrent_workflows": 5,
    "progress_update_interval_seconds": 2,
    "allow_custom_workflows": true,
    "workflow_timeout_multiplier": 1.5
  },

  "intelligence": {
    "enabled": true,
    "intent_analysis_enabled": true,
    "recommendations_enabled": true,
    "learning_enabled": true,
    "learning_database_path": "data/interactions/interaction_log.db",
    "recommendation_count": 3,
    "min_confidence_threshold": 0.6
  }
}
```

---

## Next Steps

1. ✅ Review and approve this implementation plan
2. ⏭️ Set up development branch: `feature/workflow-and-intelligence`
3. ⏭️ Create directory structure and initialize files
4. ⏭️ Begin Phase 1 implementation
5. ⏭️ Schedule weekly review meetings

**Estimated Total Implementation Time: 8 weeks**

---

*This implementation plan provides a complete roadmap for adding Workflow Orchestration and Agentic Intelligence to the MCP-PowerBi-Finvision server. Follow the phases sequentially for best results.*
