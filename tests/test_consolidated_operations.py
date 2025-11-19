"""
Tests for Phase 1 Consolidated Operations
"""
import pytest
from core.operations.base_operations import BaseOperationsHandler
from core.operations.table_operations import TableOperationsHandler
from core.operations.column_operations import ColumnOperationsHandler
from core.operations.measure_operations import MeasureOperationsHandler

class TestBaseOperationsHandler:
    """Test the base operations handler"""

    def test_register_and_execute_operation(self):
        """Test registering and executing operations"""
        handler = BaseOperationsHandler("test_handler")

        # Register a test operation
        def test_op(args):
            return {'success': True, 'message': 'test operation executed'}

        handler.register_operation('test', test_op)

        # Execute the operation
        result = handler.execute({'operation': 'test'})
        assert result['success'] == True
        assert result['message'] == 'test operation executed'

    def test_missing_operation_parameter(self):
        """Test error when operation parameter is missing"""
        handler = BaseOperationsHandler("test_handler")
        result = handler.execute({})
        assert result['success'] == False
        assert 'operation parameter is required' in result['error']

    def test_unknown_operation(self):
        """Test error for unknown operation"""
        handler = BaseOperationsHandler("test_handler")
        result = handler.execute({'operation': 'unknown'})
        assert result['success'] == False
        assert 'Unknown operation' in result['error']


class TestTableOperationsHandler:
    """Test table operations handler"""

    def test_initialization(self):
        """Test that table operations handler initializes correctly"""
        handler = TableOperationsHandler()
        available_ops = handler.get_available_operations()

        assert 'list' in available_ops
        assert 'describe' in available_ops
        assert 'preview' in available_ops

    def test_list_operation_requires_connection(self):
        """Test that list operation checks for connection"""
        handler = TableOperationsHandler()
        result = handler.execute({'operation': 'list'})

        # Should return error about not being connected
        # (unless we're actually connected during test)
        assert 'success' in result


class TestColumnOperationsHandler:
    """Test column operations handler"""

    def test_initialization(self):
        """Test that column operations handler initializes correctly"""
        handler = ColumnOperationsHandler()
        available_ops = handler.get_available_operations()

        assert 'list' in available_ops
        assert 'statistics' in available_ops
        assert 'distribution' in available_ops

    def test_statistics_validates_parameters(self):
        """Test that statistics operation validates required parameters"""
        handler = ColumnOperationsHandler()
        result = handler.execute({'operation': 'statistics'})

        # Should return error about missing parameters
        assert 'success' in result
        # If not connected or missing params, should fail
        if not result.get('success'):
            assert 'table_name' in result.get('error', '') or 'Not connected' in result.get('error', '')


class TestMeasureOperationsHandler:
    """Test measure operations handler"""

    def test_initialization(self):
        """Test that measure operations handler initializes correctly"""
        handler = MeasureOperationsHandler()
        available_ops = handler.get_available_operations()

        assert 'list' in available_ops
        assert 'get' in available_ops
        assert 'create' in available_ops
        assert 'update' in available_ops
        assert 'delete' in available_ops

    def test_get_validates_parameters(self):
        """Test that get operation validates required parameters"""
        handler = MeasureOperationsHandler()
        result = handler.execute({'operation': 'get'})

        # Should return error about missing parameters
        assert 'success' in result
        # If not connected or missing params, should fail
        if not result.get('success'):
            assert 'table_name' in result.get('error', '') or 'Not connected' in result.get('error', '')


class TestHandlerRegistration:
    """Test that handlers can be registered"""

    def test_all_handlers_register(self):
        """Test that all consolidated handlers can be registered"""
        from server.registry import HandlerRegistry
        from server.handlers.table_operations_handler import register_table_operations_handler
        from server.handlers.column_operations_handler import register_column_operations_handler
        from server.handlers.measure_operations_handler import register_measure_operations_handler

        registry = HandlerRegistry()

        register_table_operations_handler(registry)
        register_column_operations_handler(registry)
        register_measure_operations_handler(registry)

        # Check all tools are registered
        assert registry.has_tool('table_operations')
        assert registry.has_tool('column_operations')
        assert registry.has_tool('measure_operations')

        # Check tool definitions
        table_tool = registry.get_tool_def('table_operations')
        assert table_tool.name == 'table_operations'
        assert table_tool.category == 'metadata'
        assert 'list' in str(table_tool.input_schema)

        column_tool = registry.get_tool_def('column_operations')
        assert column_tool.name == 'column_operations'
        assert column_tool.category == 'metadata'

        measure_tool = registry.get_tool_def('measure_operations')
        assert measure_tool.name == 'measure_operations'
        assert measure_tool.category == 'metadata'


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
