"""
Complete Tests for All 3 Phases of Tool Consolidation
"""
import pytest
from server.registry import HandlerRegistry

# Phase 1 Tests
from server.handlers.table_operations_handler import register_table_operations_handler
from server.handlers.column_operations_handler import register_column_operations_handler
from server.handlers.measure_operations_handler import register_measure_operations_handler

# Phase 2 Tests
from server.handlers.relationship_operations_handler import register_relationship_operations_handler
from server.handlers.calculation_group_operations_handler import register_calculation_group_operations_handler
from server.handlers.role_operations_handler import register_role_operations_handler

# Phase 3 Tests
from server.handlers.batch_operations_handler import register_batch_operations_handler
from server.handlers.transaction_management_handler import register_transaction_management_handler


class TestPhase1Registration:
    """Test Phase 1 tool registration"""

    def test_all_phase1_tools_register(self):
        """Test that all Phase 1 tools can be registered"""
        registry = HandlerRegistry()

        register_table_operations_handler(registry)
        register_column_operations_handler(registry)
        register_measure_operations_handler(registry)

        assert registry.has_tool('table_operations')
        assert registry.has_tool('column_operations')
        assert registry.has_tool('measure_operations')

    def test_phase1_tool_operations(self):
        """Test that Phase 1 tools have correct operations"""
        registry = HandlerRegistry()

        register_table_operations_handler(registry)
        register_column_operations_handler(registry)
        register_measure_operations_handler(registry)

        # Test table_operations
        table_tool = registry.get_tool_def('table_operations')
        table_ops = table_tool.input_schema['properties']['operation']['enum']
        assert 'list' in table_ops
        assert 'describe' in table_ops
        assert 'preview' in table_ops

        # Test column_operations
        column_tool = registry.get_tool_def('column_operations')
        column_ops = column_tool.input_schema['properties']['operation']['enum']
        assert 'list' in column_ops
        assert 'statistics' in column_ops
        assert 'distribution' in column_ops

        # Test measure_operations
        measure_tool = registry.get_tool_def('measure_operations')
        measure_ops = measure_tool.input_schema['properties']['operation']['enum']
        assert 'list' in measure_ops
        assert 'get' in measure_ops
        assert 'create' in measure_ops
        assert 'update' in measure_ops
        assert 'delete' in measure_ops


class TestPhase2Registration:
    """Test Phase 2 tool registration"""

    def test_all_phase2_tools_register(self):
        """Test that all Phase 2 tools can be registered"""
        registry = HandlerRegistry()

        register_relationship_operations_handler(registry)
        register_calculation_group_operations_handler(registry)
        register_role_operations_handler(registry)

        assert registry.has_tool('relationship_operations')
        assert registry.has_tool('calculation_group_operations')
        assert registry.has_tool('role_operations')

    def test_phase2_tool_operations(self):
        """Test that Phase 2 tools have correct operations"""
        registry = HandlerRegistry()

        register_relationship_operations_handler(registry)
        register_calculation_group_operations_handler(registry)
        register_role_operations_handler(registry)

        # Test relationship_operations
        rel_tool = registry.get_tool_def('relationship_operations')
        rel_ops = rel_tool.input_schema['properties']['operation']['enum']
        assert 'list' in rel_ops
        assert 'get' in rel_ops
        assert 'find' in rel_ops

        # Test calculation_group_operations
        calc_tool = registry.get_tool_def('calculation_group_operations')
        calc_ops = calc_tool.input_schema['properties']['operation']['enum']
        assert 'list' in calc_ops
        assert 'create' in calc_ops
        assert 'delete' in calc_ops
        assert 'list_items' in calc_ops

        # Test role_operations
        role_tool = registry.get_tool_def('role_operations')
        role_ops = role_tool.input_schema['properties']['operation']['enum']
        assert 'list' in role_ops


class TestPhase3Registration:
    """Test Phase 3 tool registration"""

    def test_all_phase3_tools_register(self):
        """Test that all Phase 3 tools can be registered"""
        registry = HandlerRegistry()

        register_batch_operations_handler(registry)
        register_transaction_management_handler(registry)

        assert registry.has_tool('batch_operations')
        assert registry.has_tool('manage_transactions')

    def test_phase3_tool_operations(self):
        """Test that Phase 3 tools have correct operations"""
        registry = HandlerRegistry()

        register_batch_operations_handler(registry)
        register_transaction_management_handler(registry)

        # Test batch_operations
        batch_tool = registry.get_tool_def('batch_operations')
        batch_obj_types = batch_tool.input_schema['properties']['operation']['enum']
        assert 'measures' in batch_obj_types

        # Test manage_transactions
        txn_tool = registry.get_tool_def('manage_transactions')
        txn_ops = txn_tool.input_schema['properties']['operation']['enum']
        assert 'begin' in txn_ops
        assert 'commit' in txn_ops
        assert 'rollback' in txn_ops
        assert 'status' in txn_ops
        assert 'list_active' in txn_ops


class TestCompleteIntegration:
    """Test complete integration of all 3 phases"""

    def test_all_8_tools_registered(self):
        """Test that all 8 new consolidated tools are registered"""
        registry = HandlerRegistry()

        # Phase 1
        register_table_operations_handler(registry)
        register_column_operations_handler(registry)
        register_measure_operations_handler(registry)

        # Phase 2
        register_relationship_operations_handler(registry)
        register_calculation_group_operations_handler(registry)
        register_role_operations_handler(registry)

        # Phase 3
        register_batch_operations_handler(registry)
        register_transaction_management_handler(registry)

        # Verify all 8 tools
        consolidated_tools = [
            'table_operations',
            'column_operations',
            'measure_operations',
            'relationship_operations',
            'calculation_group_operations',
            'role_operations',
            'batch_operations',
            'manage_transactions'
        ]

        for tool_name in consolidated_tools:
            assert registry.has_tool(tool_name), f'{tool_name} not registered'

    def test_tool_categories(self):
        """Test that tools are in correct categories"""
        registry = HandlerRegistry()

        # Register all
        register_table_operations_handler(registry)
        register_column_operations_handler(registry)
        register_measure_operations_handler(registry)
        register_relationship_operations_handler(registry)
        register_calculation_group_operations_handler(registry)
        register_role_operations_handler(registry)
        register_batch_operations_handler(registry)
        register_transaction_management_handler(registry)

        # Check categories
        metadata_tools = [t.name for t in registry.get_tools_by_category('metadata')]
        assert 'table_operations' in metadata_tools
        assert 'column_operations' in metadata_tools
        assert 'measure_operations' in metadata_tools
        assert 'relationship_operations' in metadata_tools

        model_ops_tools = [t.name for t in registry.get_tools_by_category('model_operations')]
        assert 'calculation_group_operations' in model_ops_tools
        assert 'role_operations' in model_ops_tools
        assert 'batch_operations' in model_ops_tools
        assert 'manage_transactions' in model_ops_tools


class TestTransactionManagement:
    """Test transaction management functionality"""

    def test_transaction_operations(self):
        """Test transaction begin/commit/rollback workflow"""
        from core.operations.transaction_management import TransactionManagementHandler

        handler = TransactionManagementHandler()

        # Test begin
        begin_result = handler.execute({'operation': 'begin'})
        assert begin_result.get('success') == True
        assert 'transaction_id' in begin_result

        txn_id = begin_result['transaction_id']

        # Test status
        status_result = handler.execute({
            'operation': 'status',
            'transaction_id': txn_id
        })
        assert status_result.get('success') == True
        assert status_result['transaction']['status'] == 'active'

        # Test list_active
        list_result = handler.execute({'operation': 'list_active'})
        assert list_result.get('success') == True
        assert list_result['active_transaction_count'] >= 1

        # Test commit
        commit_result = handler.execute({
            'operation': 'commit',
            'transaction_id': txn_id
        })
        assert commit_result.get('success') == True


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
