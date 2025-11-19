# Phase 1 Implementation Guide
**Quick Start**: Implementing Consolidated Metadata Tools

---

## Overview

This guide provides step-by-step instructions for implementing Phase 1 of the tool consolidation plan: the three consolidated metadata operation tools.

**Phase 1 Goals**:
- Implement `table_operations` (replaces 2 tools)
- Implement `column_operations` (replaces 4 tools)
- Implement `measure_operations` (replaces 4 tools)
- **Net Result**: 10 tools → 3 tools (-7 tools)

**Estimated Effort**: 6-7 days

---

## Step 1: Create Base Operations Handler

### File: `core/operations/base_operations.py`

```python
"""
Base class for unified operation handlers
Provides common patterns for operation routing and validation
"""
from typing import Dict, Any, List, Callable
import logging

logger = logging.getLogger(__name__)

class BaseOperationsHandler:
    """Base class for unified operation handlers"""

    def __init__(self, operation_name: str):
        self.operation_name = operation_name
        self._operations: Dict[str, Callable] = {}

    def register_operation(self, operation: str, handler: Callable):
        """Register an operation handler"""
        self._operations[operation] = handler
        logger.debug(f"{self.operation_name}: Registered operation '{operation}'")

    def execute(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """Execute an operation based on args"""
        operation = args.get('operation')

        if not operation:
            return {
                'success': False,
                'error': 'operation parameter is required',
                'available_operations': list(self._operations.keys())
            }

        if operation not in self._operations:
            return {
                'success': False,
                'error': f'Unknown operation: {operation}',
                'available_operations': list(self._operations.keys())
            }

        handler = self._operations[operation]

        try:
            logger.info(f"{self.operation_name}: Executing operation '{operation}'")
            result = handler(args)
            logger.info(f"{self.operation_name}: Operation '{operation}' completed successfully")
            return result
        except Exception as e:
            logger.error(f"{self.operation_name}: Operation '{operation}' failed: {e}", exc_info=True)
            return {
                'success': False,
                'error': f'Operation failed: {str(e)}',
                'operation': operation
            }

    def get_available_operations(self) -> List[str]:
        """Get list of available operations"""
        return list(self._operations.keys())
```

---

## Step 2: Implement Table Operations

### File: `core/operations/table_operations.py`

```python
"""
Unified table operations handler
Consolidates: list_tables, describe_table + new CRUD operations
"""
from typing import Dict, Any
import logging
from .base_operations import BaseOperationsHandler
from core.infrastructure.connection_state import connection_state
from core.validation.error_handler import ErrorHandler

logger = logging.getLogger(__name__)

class TableOperationsHandler(BaseOperationsHandler):
    """Handles all table-related operations"""

    def __init__(self):
        super().__init__("table_operations")

        # Register all operations
        self.register_operation('list', self._list_tables)
        self.register_operation('describe', self._describe_table)
        self.register_operation('preview', self._preview_table)
        # Future: create, update, delete, rename, refresh

    def _list_tables(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """List all tables in the model"""
        if not connection_state.is_connected():
            return ErrorHandler.handle_not_connected()

        qe = connection_state.query_executor
        if not qe:
            return ErrorHandler.handle_manager_unavailable('query_executor')

        result = qe.execute_info_query("TABLES")

        # Apply pagination if requested
        page_size = args.get('page_size')
        next_token = args.get('next_token')
        if page_size or next_token:
            from server.middleware import paginate
            result = paginate(result, page_size, next_token, ['rows'])

        return result

    def _describe_table(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """Get comprehensive table description"""
        if not connection_state.is_connected():
            return ErrorHandler.handle_not_connected()

        qe = connection_state.query_executor
        if not qe:
            return ErrorHandler.handle_manager_unavailable('query_executor')

        table_name = args.get('table_name')
        if not table_name:
            return {
                'success': False,
                'error': 'table_name parameter is required for operation: describe'
            }

        # Check if method exists
        if not hasattr(qe, 'describe_table'):
            return {
                'success': False,
                'error': 'describe_table method not implemented in query executor'
            }

        try:
            result = qe.describe_table(table_name, args)
            return result
        except Exception as e:
            logger.error(f"Error describing table '{table_name}': {e}", exc_info=True)
            return ErrorHandler.handle_unexpected_error('describe_table', e)

    def _preview_table(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """Preview table data"""
        if not connection_state.is_connected():
            return ErrorHandler.handle_not_connected()

        agent_policy = connection_state.agent_policy
        if not agent_policy:
            return ErrorHandler.handle_manager_unavailable('agent_policy')

        table_name = args.get('table_name')
        if not table_name:
            return {
                'success': False,
                'error': 'table_name parameter is required for operation: preview'
            }

        max_rows = args.get('max_rows', 10)

        # Create EVALUATE query for table preview
        query = f'EVALUATE TOPN({max_rows}, \'{table_name}\')'

        result = agent_policy.safe_run_dax(
            connection_state=connection_state,
            query=query,
            mode='auto',
            max_rows=max_rows
        )

        return result

    # Future methods: _create_table, _update_table, _delete_table, _rename_table, _refresh_table
```

### Handler: `server/handlers/table_operations_handler.py`

```python
"""
Table Operations Handler
Unified handler for all table operations
"""
from typing import Dict, Any
import logging
from server.registry import ToolDefinition
from core.operations.table_operations import TableOperationsHandler

logger = logging.getLogger(__name__)

# Create singleton instance
_table_ops_handler = TableOperationsHandler()

def handle_table_operations(args: Dict[str, Any]) -> Dict[str, Any]:
    """Handle unified table operations"""
    return _table_ops_handler.execute(args)

def register_table_operations_handler(registry):
    """Register table operations handler"""

    tool = ToolDefinition(
        name="table_operations",
        description="Unified table operations: list, describe, preview, and CRUD (create/update/delete/rename/refresh)",
        handler=handle_table_operations,
        input_schema={
            "type": "object",
            "properties": {
                "operation": {
                    "type": "string",
                    "enum": ["list", "describe", "preview"],  # Add more as implemented
                    "description": "Operation to perform on tables"
                },
                "table_name": {
                    "type": "string",
                    "description": "Table name (required for: describe, preview, update, delete, rename, refresh)"
                },
                "new_name": {
                    "type": "string",
                    "description": "New table name (required for: rename)"
                },
                "definition": {
                    "type": "object",
                    "description": "Table definition (required for: create, update)"
                },
                "max_rows": {
                    "type": "integer",
                    "description": "Maximum rows to preview (default: 10, for preview operation)",
                    "default": 10
                },
                "page_size": {
                    "type": "integer",
                    "description": "Page size for list operation"
                },
                "next_token": {
                    "type": "string",
                    "description": "Pagination token for list operation"
                }
            },
            "required": ["operation"]
        },
        category="metadata",
        sort_order=2
    )

    registry.register(tool)
    logger.info("Registered table_operations handler")
```

---

## Step 3: Implement Column Operations

### File: `core/operations/column_operations.py`

```python
"""
Unified column operations handler
Consolidates: list_columns, list_calculated_columns, get_column_value_distribution, get_column_summary
"""
from typing import Dict, Any
import logging
from .base_operations import BaseOperationsHandler
from core.infrastructure.connection_state import connection_state
from core.validation.error_handler import ErrorHandler
from core.infrastructure.query_executor import COLUMN_TYPE_CALCULATED

logger = logging.getLogger(__name__)

class ColumnOperationsHandler(BaseOperationsHandler):
    """Handles all column-related operations"""

    def __init__(self):
        super().__init__("column_operations")

        # Register all operations
        self.register_operation('list', self._list_columns)
        self.register_operation('statistics', self._get_column_statistics)
        self.register_operation('distribution', self._get_column_distribution)
        # Future: get, create, update, delete, rename

    def _list_columns(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """List columns, optionally filtered by table and type"""
        if not connection_state.is_connected():
            return ErrorHandler.handle_not_connected()

        qe = connection_state.query_executor
        if not qe:
            return ErrorHandler.handle_manager_unavailable('query_executor')

        table_name = args.get('table_name')
        column_type = args.get('column_type', 'all')  # 'all', 'data', 'calculated'

        # Build filter expression based on column_type
        filter_expr = None
        if column_type == 'calculated':
            filter_expr = f'[Type] = {COLUMN_TYPE_CALCULATED}'
        elif column_type == 'data':
            filter_expr = f'[Type] <> {COLUMN_TYPE_CALCULATED}'
        # else: 'all' - no filter

        result = qe.execute_info_query("COLUMNS", table_name=table_name, filter_expr=filter_expr)

        # Apply pagination
        page_size = args.get('page_size')
        next_token = args.get('next_token')
        if page_size or next_token:
            from server.middleware import paginate
            result = paginate(result, page_size, next_token, ['rows'])

        return result

    def _get_column_statistics(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """Get column summary statistics"""
        if not connection_state.is_connected():
            return ErrorHandler.handle_not_connected()

        agent_policy = connection_state.agent_policy
        if not agent_policy:
            return ErrorHandler.handle_manager_unavailable('agent_policy')

        table_name = args.get('table_name')
        column_name = args.get('column_name')

        if not table_name or not column_name:
            return {
                'success': False,
                'error': 'table_name and column_name are required for operation: statistics'
            }

        # Create DAX query to get column statistics
        query = f'''
        EVALUATE
        ROW(
            "DistinctCount", COUNTROWS(DISTINCT('{table_name}'[{column_name}])),
            "TotalCount", COUNTROWS('{table_name}'),
            "BlankCount", COUNTBLANK('{table_name}'[{column_name}])
        )
        '''

        return agent_policy.safe_run_dax(
            connection_state=connection_state,
            query=query,
            mode='auto'
        )

    def _get_column_distribution(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """Get column value distribution"""
        if not connection_state.is_connected():
            return ErrorHandler.handle_not_connected()

        agent_policy = connection_state.agent_policy
        if not agent_policy:
            return ErrorHandler.handle_manager_unavailable('agent_policy')

        table_name = args.get('table_name')
        column_name = args.get('column_name')

        if not table_name or not column_name:
            return {
                'success': False,
                'error': 'table_name and column_name are required for operation: distribution'
            }

        top_n = args.get('top_n', 10)

        # Create DAX query to get value distribution
        query = f'''
        EVALUATE
        TOPN(
            {top_n},
            SUMMARIZECOLUMNS(
                '{table_name}'[{column_name}],
                "Count", COUNTROWS('{table_name}')
            ),
            [Count],
            DESC
        )
        '''

        return agent_policy.safe_run_dax(
            connection_state=connection_state,
            query=query,
            mode='auto',
            max_rows=top_n
        )

    # Future methods: _get_column, _create_column, _update_column, _delete_column, _rename_column
```

### Handler: `server/handlers/column_operations_handler.py`

```python
"""
Column Operations Handler
Unified handler for all column operations
"""
from typing import Dict, Any
import logging
from server.registry import ToolDefinition
from core.operations.column_operations import ColumnOperationsHandler

logger = logging.getLogger(__name__)

# Create singleton instance
_column_ops_handler = ColumnOperationsHandler()

def handle_column_operations(args: Dict[str, Any]) -> Dict[str, Any]:
    """Handle unified column operations"""
    return _column_ops_handler.execute(args)

def register_column_operations_handler(registry):
    """Register column operations handler"""

    tool = ToolDefinition(
        name="column_operations",
        description="Unified column operations: list (all/data/calculated), statistics, distribution, and CRUD",
        handler=handle_column_operations,
        input_schema={
            "type": "object",
            "properties": {
                "operation": {
                    "type": "string",
                    "enum": ["list", "statistics", "distribution"],  # Add more as implemented
                    "description": "Operation to perform on columns"
                },
                "table_name": {
                    "type": "string",
                    "description": "Table name (optional for list, required for other operations)"
                },
                "column_name": {
                    "type": "string",
                    "description": "Column name (required for: statistics, distribution, get, update, delete, rename)"
                },
                "column_type": {
                    "type": "string",
                    "enum": ["all", "data", "calculated"],
                    "description": "Filter by column type (for list operation)",
                    "default": "all"
                },
                "top_n": {
                    "type": "integer",
                    "description": "Number of top values for distribution (default: 10)",
                    "default": 10
                },
                "page_size": {
                    "type": "integer",
                    "description": "Page size for list operation"
                },
                "next_token": {
                    "type": "string",
                    "description": "Pagination token for list operation"
                }
            },
            "required": ["operation"]
        },
        category="metadata",
        sort_order=3
    )

    registry.register(tool)
    logger.info("Registered column_operations handler")
```

---

## Step 4: Implement Measure Operations

### File: `core/operations/measure_operations.py`

```python
"""
Unified measure operations handler
Consolidates: list_measures, get_measure_details, upsert_measure, delete_measure
"""
from typing import Dict, Any
import logging
from .base_operations import BaseOperationsHandler
from core.infrastructure.connection_state import connection_state
from core.validation.error_handler import ErrorHandler

logger = logging.getLogger(__name__)

class MeasureOperationsHandler(BaseOperationsHandler):
    """Handles all measure-related operations"""

    def __init__(self):
        super().__init__("measure_operations")

        # Register all operations
        self.register_operation('list', self._list_measures)
        self.register_operation('get', self._get_measure)
        self.register_operation('create', self._create_measure)
        self.register_operation('update', self._update_measure)
        self.register_operation('delete', self._delete_measure)
        # Future: rename, move

    def _list_measures(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """List measures, optionally filtered by table"""
        if not connection_state.is_connected():
            return ErrorHandler.handle_not_connected()

        qe = connection_state.query_executor
        if not qe:
            return ErrorHandler.handle_manager_unavailable('query_executor')

        table_name = args.get('table_name')

        result = qe.execute_info_query("MEASURES", table_name=table_name, exclude_columns=['Expression'])

        # Apply pagination
        page_size = args.get('page_size')
        next_token = args.get('next_token')
        if page_size or next_token:
            from server.middleware import paginate
            result = paginate(result, page_size, next_token, ['rows'])

        return result

    def _get_measure(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """Get detailed measure information including DAX formula"""
        if not connection_state.is_connected():
            return ErrorHandler.handle_not_connected()

        qe = connection_state.query_executor
        if not qe:
            return ErrorHandler.handle_manager_unavailable('query_executor')

        table_name = args.get('table_name')
        measure_name = args.get('measure_name')

        if not table_name or not measure_name:
            return {
                'success': False,
                'error': 'table_name and measure_name are required for operation: get'
            }

        result = qe.get_measure_details_with_fallback(table_name, measure_name)
        return result

    def _create_measure(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new measure"""
        if not connection_state.is_connected():
            return ErrorHandler.handle_not_connected()

        dax_injector = connection_state.dax_injector
        if not dax_injector:
            return ErrorHandler.handle_manager_unavailable('dax_injector')

        table_name = args.get('table_name')
        measure_name = args.get('measure_name')
        expression = args.get('expression')

        if not table_name or not measure_name or not expression:
            return {
                'success': False,
                'error': 'table_name, measure_name, and expression are required for operation: create'
            }

        return dax_injector.upsert_measure(
            table_name=table_name,
            measure_name=measure_name,
            dax_expression=expression,
            description=args.get('description'),
            format_string=args.get('format_string'),
            display_folder=args.get('display_folder')
        )

    def _update_measure(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """Update an existing measure"""
        # Same implementation as create (upsert_measure handles both)
        return self._create_measure(args)

    def _delete_measure(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """Delete a measure"""
        if not connection_state.is_connected():
            return ErrorHandler.handle_not_connected()

        dax_injector = connection_state.dax_injector
        if not dax_injector:
            return ErrorHandler.handle_manager_unavailable('dax_injector')

        table_name = args.get('table_name')
        measure_name = args.get('measure_name')

        if not table_name or not measure_name:
            return {
                'success': False,
                'error': 'table_name and measure_name are required for operation: delete'
            }

        return dax_injector.delete_measure(
            table_name=table_name,
            measure_name=measure_name
        )

    # Future methods: _rename_measure, _move_measure
```

### Handler: `server/handlers/measure_operations_handler.py`

```python
"""
Measure Operations Handler
Unified handler for all measure operations
"""
from typing import Dict, Any
import logging
from server.registry import ToolDefinition
from core.operations.measure_operations import MeasureOperationsHandler

logger = logging.getLogger(__name__)

# Create singleton instance
_measure_ops_handler = MeasureOperationsHandler()

def handle_measure_operations(args: Dict[str, Any]) -> Dict[str, Any]:
    """Handle unified measure operations"""
    return _measure_ops_handler.execute(args)

def register_measure_operations_handler(registry):
    """Register measure operations handler"""

    tool = ToolDefinition(
        name="measure_operations",
        description="Unified measure operations: list, get, create, update, delete, rename, move, and bulk operations",
        handler=handle_measure_operations,
        input_schema={
            "type": "object",
            "properties": {
                "operation": {
                    "type": "string",
                    "enum": ["list", "get", "create", "update", "delete"],  # Add rename, move later
                    "description": "Operation to perform on measures"
                },
                "table_name": {
                    "type": "string",
                    "description": "Table name (optional for list, required for other operations)"
                },
                "measure_name": {
                    "type": "string",
                    "description": "Measure name (required for: get, update, delete, rename, move)"
                },
                "expression": {
                    "type": "string",
                    "description": "DAX expression (required for: create, update)"
                },
                "description": {
                    "type": "string",
                    "description": "Measure description (optional for: create, update)"
                },
                "format_string": {
                    "type": "string",
                    "description": "Format string (optional for: create, update)"
                },
                "display_folder": {
                    "type": "string",
                    "description": "Display folder (optional for: create, update)"
                },
                "page_size": {
                    "type": "integer",
                    "description": "Page size for list operation"
                },
                "next_token": {
                    "type": "string",
                    "description": "Pagination token for list operation"
                }
            },
            "required": ["operation"]
        },
        category="metadata",
        sort_order=4
    )

    registry.register(tool)
    logger.info("Registered measure_operations handler")
```

---

## Step 5: Update Main Server File

### File: `server/main.py` (or wherever you register handlers)

```python
# Import new handlers
from server.handlers.table_operations_handler import register_table_operations_handler
from server.handlers.column_operations_handler import register_column_operations_handler
from server.handlers.measure_operations_handler import register_measure_operations_handler

# In your initialization function:
def initialize_handlers(registry):
    # ... existing handlers ...

    # Phase 1: Consolidated metadata operations
    register_table_operations_handler(registry)
    register_column_operations_handler(registry)
    register_measure_operations_handler(registry)

    # ... rest of handlers ...
```

---

## Step 6: Mark Old Tools as Deprecated

### Update old handlers to forward to new implementations

```python
def handle_list_tables_DEPRECATED(args: Dict[str, Any]) -> Dict[str, Any]:
    """
    DEPRECATED: Use table_operations with operation='list' instead
    This tool will be removed in v2.0.0
    """
    logger.warning("list_tables is DEPRECATED. Use table_operations with operation='list'")

    # Forward to new implementation
    return handle_table_operations({
        'operation': 'list',
        **args
    })
```

---

## Step 7: Testing

### Create test file: `tests/test_phase1_operations.py`

```python
import pytest
from server.handlers.table_operations_handler import handle_table_operations
from server.handlers.column_operations_handler import handle_column_operations
from server.handlers.measure_operations_handler import handle_measure_operations

class TestTableOperations:
    def test_list_tables(self):
        result = handle_table_operations({'operation': 'list'})
        assert result['success'] == True
        assert 'rows' in result or 'tables' in result

    def test_describe_table(self):
        result = handle_table_operations({
            'operation': 'describe',
            'table_name': 'DimDate'
        })
        assert result['success'] == True

    def test_invalid_operation(self):
        result = handle_table_operations({'operation': 'invalid'})
        assert result['success'] == False
        assert 'available_operations' in result

class TestColumnOperations:
    def test_list_all_columns(self):
        result = handle_column_operations({
            'operation': 'list',
            'column_type': 'all'
        })
        assert result['success'] == True

    def test_list_calculated_columns(self):
        result = handle_column_operations({
            'operation': 'list',
            'column_type': 'calculated'
        })
        assert result['success'] == True

    def test_column_statistics(self):
        result = handle_column_operations({
            'operation': 'statistics',
            'table_name': 'DimDate',
            'column_name': 'Date'
        })
        assert result['success'] == True

class TestMeasureOperations:
    def test_list_measures(self):
        result = handle_measure_operations({'operation': 'list'})
        assert result['success'] == True

    def test_get_measure(self):
        result = handle_measure_operations({
            'operation': 'get',
            'table_name': '_Measures',
            'measure_name': 'Total Sales'
        })
        assert result['success'] == True

    def test_create_and_delete_measure(self):
        # Create
        create_result = handle_measure_operations({
            'operation': 'create',
            'table_name': '_Measures',
            'measure_name': 'Test Measure',
            'expression': 'SUM(FactSales[Amount])'
        })
        assert create_result['success'] == True

        # Delete
        delete_result = handle_measure_operations({
            'operation': 'delete',
            'table_name': '_Measures',
            'measure_name': 'Test Measure'
        })
        assert delete_result['success'] == True
```

Run tests:
```bash
pytest tests/test_phase1_operations.py -v
```

---

## Step 8: Documentation

### Update tool documentation

Create/update: `docs/TOOL_REFERENCE.md`

```markdown
# Tool Reference: Consolidated Operations

## table_operations

Unified tool for all table operations.

### Operations

#### list
List all tables in the model.

**Example**:
```json
{
  "operation": "list",
  "page_size": 50
}
```

#### describe
Get comprehensive table description with columns, measures, and relationships.

**Example**:
```json
{
  "operation": "describe",
  "table_name": "FactSales"
}
```

#### preview
Preview table data (top N rows).

**Example**:
```json
{
  "operation": "preview",
  "table_name": "DimDate",
  "max_rows": 10
}
```

---

## column_operations

Unified tool for all column operations.

### Operations

#### list
List columns, optionally filtered by table and type.

**Example**:
```json
{
  "operation": "list",
  "table_name": "FactSales",
  "column_type": "calculated"
}
```

#### statistics
Get column statistics (distinct count, total count, blank count).

**Example**:
```json
{
  "operation": "statistics",
  "table_name": "FactSales",
  "column_name": "ProductKey"
}
```

#### distribution
Get value distribution (top N values).

**Example**:
```json
{
  "operation": "distribution",
  "table_name": "DimProduct",
  "column_name": "Category",
  "top_n": 10
}
```

---

## measure_operations

Unified tool for all measure operations.

### Operations

#### list
List measures, optionally filtered by table.

**Example**:
```json
{
  "operation": "list",
  "table_name": "_Measures"
}
```

#### get
Get detailed measure information including DAX formula.

**Example**:
```json
{
  "operation": "get",
  "table_name": "_Measures",
  "measure_name": "Total Sales"
}
```

#### create
Create a new measure.

**Example**:
```json
{
  "operation": "create",
  "table_name": "_Measures",
  "measure_name": "Total Quantity",
  "expression": "SUM(FactSales[Quantity])",
  "format_string": "#,0",
  "display_folder": "Sales"
}
```

#### update
Update an existing measure.

**Example**:
```json
{
  "operation": "update",
  "table_name": "_Measures",
  "measure_name": "Total Sales",
  "expression": "SUMX(FactSales, FactSales[Quantity] * FactSales[UnitPrice])",
  "format_string": "$#,0.00"
}
```

#### delete
Delete a measure.

**Example**:
```json
{
  "operation": "delete",
  "table_name": "_Measures",
  "measure_name": "Test Measure"
}
```
```

---

## Deployment Checklist

### Pre-Deployment
- [ ] All tests passing
- [ ] Code reviewed
- [ ] Documentation updated
- [ ] Deprecation messages added to old tools
- [ ] Migration guide created

### Deployment
- [ ] Create feature branch: `feature/phase1-consolidation`
- [ ] Commit all changes
- [ ] Create pull request
- [ ] Run CI/CD pipeline
- [ ] Deploy to staging environment
- [ ] Run integration tests
- [ ] Deploy to production

### Post-Deployment
- [ ] Monitor error rates
- [ ] Gather user feedback
- [ ] Track usage of old vs new tools
- [ ] Update examples and tutorials

---

## Timeline

**Day 1-2**: Implement table_operations
- [ ] Create base_operations.py
- [ ] Create table_operations.py
- [ ] Create table_operations_handler.py
- [ ] Write tests
- [ ] Update documentation

**Day 3-4**: Implement column_operations
- [ ] Create column_operations.py
- [ ] Create column_operations_handler.py
- [ ] Write tests
- [ ] Update documentation

**Day 5-6**: Implement measure_operations
- [ ] Create measure_operations.py
- [ ] Create measure_operations_handler.py
- [ ] Write tests
- [ ] Update documentation

**Day 7**: Integration and cleanup
- [ ] Mark old tools as deprecated
- [ ] Update main server file
- [ ] Run all tests
- [ ] Create migration guide
- [ ] Deploy to staging

---

## Success Criteria

- [ ] All 3 consolidated tools working correctly
- [ ] All read operations functional
- [ ] All write operations (create, update, delete) functional
- [ ] 95%+ test coverage
- [ ] Zero regression bugs in existing functionality
- [ ] Documentation complete with examples
- [ ] Old tools properly deprecated with forwarding logic
- [ ] Migration guide published

---

**Ready to start? Begin with Step 1!**
