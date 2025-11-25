"""
Unified calculation group operations handler
Consolidates: list_calculation_groups, create_calculation_group, delete_calculation_group + new operations

Refactored to use validation utilities for reduced code duplication.
"""
from typing import Dict, Any
import logging
from .base_operations import BaseOperationsHandler

# Import validation utilities
from core.validation import (
    get_manager_or_error,
    get_group_name,
    validate_required,
)

logger = logging.getLogger(__name__)


class CalculationGroupOperationsHandler(BaseOperationsHandler):
    """Handles all calculation group-related operations"""

    def __init__(self):
        super().__init__("calculation_group_operations")

        # Register all operations
        self.register_operation('list', self._list_calculation_groups)
        self.register_operation('create', self._create_calculation_group)
        self.register_operation('delete', self._delete_calculation_group)
        self.register_operation('list_items', self._list_items)
        # Future: update, rename, create_item, update_item, delete_item, reorder_items

    def _list_calculation_groups(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """List calculation groups"""
        # Get manager with connection check
        calc_group_mgr = get_manager_or_error('calc_group_manager')
        if isinstance(calc_group_mgr, dict):  # Error response
            return calc_group_mgr

        return calc_group_mgr.list_calculation_groups()

    def _create_calculation_group(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """Create a calculation group"""
        # Get manager with connection check
        calc_group_mgr = get_manager_or_error('calc_group_manager')
        if isinstance(calc_group_mgr, dict):  # Error response
            return calc_group_mgr

        group_name = get_group_name(args)

        # Validate required parameter
        if error := validate_required(group_name, 'group_name', 'create'):
            return error

        items = args.get('items', [])
        description = args.get('description')
        precedence = args.get('precedence')

        # If no precedence specified, find next available precedence value
        if precedence is None:
            # Get existing calculation groups to find used precedence values
            existing_groups = calc_group_mgr.list_calculation_groups()
            if existing_groups.get('success'):
                used_precedences = set()
                for group in existing_groups.get('calculation_groups', []):
                    used_precedences.add(group.get('precedence', 0))

                # Find first available precedence (starting from 0)
                precedence = 0
                while precedence in used_precedences:
                    precedence += 1

                logger.info(f"Auto-assigned precedence {precedence} for calculation group '{group_name}'")
            else:
                # Fallback to 0 if we can't list existing groups
                precedence = 0
        else:
            # Validate that the specified precedence isn't already taken
            existing_groups = calc_group_mgr.list_calculation_groups()
            if existing_groups.get('success'):
                for group in existing_groups.get('calculation_groups', []):
                    if group.get('precedence') == precedence:
                        used_precedences = [g.get('precedence', 0) for g in existing_groups.get('calculation_groups', [])]
                        available = [p for p in range(max(used_precedences) + 2) if p not in used_precedences]
                        return {
                            'success': False,
                            'error': f'Precedence {precedence} is already taken by calculation group "{group.get("name")}"',
                            'suggestion': f'Use one of these available precedence values: {available[:5]}'
                        }

        return calc_group_mgr.create_calculation_group(
            name=group_name,
            items=items,
            description=description,
            precedence=precedence
        )

    def _delete_calculation_group(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """Delete a calculation group"""
        # Get manager with connection check
        calc_group_mgr = get_manager_or_error('calc_group_manager')
        if isinstance(calc_group_mgr, dict):  # Error response
            return calc_group_mgr

        group_name = get_group_name(args)

        # Validate required parameter
        if error := validate_required(group_name, 'group_name', 'delete'):
            return error

        return calc_group_mgr.delete_calculation_group(group_name)

    def _list_items(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """List calculation items for a specific group"""
        # Get manager with connection check
        calc_group_mgr = get_manager_or_error('calc_group_manager')
        if isinstance(calc_group_mgr, dict):  # Error response
            return calc_group_mgr

        group_name = get_group_name(args)

        # Validate required parameter
        if error := validate_required(group_name, 'group_name', 'list_items'):
            return error

        # Get all calculation groups and filter for the specific one
        result = calc_group_mgr.list_calculation_groups()

        if result.get('success'):
            groups = result.get('calculation_groups', [])
            matching = [g for g in groups if g.get('name') == group_name]

            if matching:
                group = matching[0]
                items = group.get('calculationItems', [])
                return {
                    'success': True,
                    'group_name': group_name,
                    'item_count': len(items),
                    'items': items
                }
            else:
                return {
                    'success': False,
                    'error': f'Calculation group not found: {group_name}'
                }

        return result

    # Future methods: _update_calculation_group, _rename_calculation_group,
    # _create_item, _update_item, _delete_item, _reorder_items
