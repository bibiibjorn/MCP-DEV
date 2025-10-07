"""
Calculation Group Manager for PBIXRay MCP Server
Manage calculation groups and calculation items
"""

import logging
from typing import Dict, Any, List, Optional

logger = logging.getLogger(__name__)

# Try to load AMO
AMO_AVAILABLE = False
AMOServer = None
CalculationGroup = None
CalculationItem = None

try:
    import clr
    import os

    script_dir = os.path.dirname(os.path.abspath(__file__))
    parent_dir = os.path.dirname(script_dir)
    dll_folder = os.path.join(parent_dir, "lib", "dotnet")

    core_dll = os.path.join(dll_folder, "Microsoft.AnalysisServices.Core.dll")
    tabular_dll = os.path.join(dll_folder, "Microsoft.AnalysisServices.Tabular.dll")

    if os.path.exists(core_dll):
        clr.AddReference(core_dll)
    if os.path.exists(tabular_dll):
        clr.AddReference(tabular_dll)

    from Microsoft.AnalysisServices.Tabular import (
        Server as AMOServer,
        CalculationGroup,
        CalculationItem,
        Table,
        Column,
        DataType
    )
    AMO_AVAILABLE = True
    logger.info("AMO available for calculation groups")

except Exception as e:
    logger.warning(f"AMO not available: {e}")


class CalculationGroupManager:
    """Manage calculation groups and items."""

    def __init__(self, connection):
        """Initialize with ADOMD connection."""
        self.connection = connection

    def list_calculation_groups(self) -> Dict[str, Any]:
        """List all calculation groups and their items."""
        if not AMO_AVAILABLE:
            return {
                'success': False,
                'error': 'AMO not available for calculation groups'
            }

        server = AMOServer()
        try:
            server.Connect(self.connection.ConnectionString)

            if server.Databases.Count == 0:
                return {'success': False, 'error': 'No database found'}

            db = server.Databases[0]
            model = db.Model

            calc_groups = []

            for table in model.Tables:
                if hasattr(table, 'CalculationGroup') and table.CalculationGroup is not None:
                    calc_group = table.CalculationGroup

                    items = []
                    for item in calc_group.CalculationItems:
                        items.append({
                            'name': item.Name,
                            'expression': item.Expression,
                            'ordinal': item.Ordinal if hasattr(item, 'Ordinal') else None,
                            'format_string_expression': item.FormatStringExpression if hasattr(item, 'FormatStringExpression') else None
                        })

                    calc_groups.append({
                        'name': calc_group.Name if hasattr(calc_group, 'Name') else table.Name,
                        'table': table.Name,
                        'precedence': calc_group.Precedence if hasattr(calc_group, 'Precedence') else 0,
                        'description': calc_group.Description if hasattr(calc_group, 'Description') else None,
                        'items': items,
                        'item_count': len(items)
                    })

            return {
                'success': True,
                'calculation_groups': calc_groups,
                'total_groups': len(calc_groups)
            }

        except Exception as e:
            logger.error(f"Error listing calculation groups: {e}")
            return {'success': False, 'error': str(e)}
        finally:
            try:
                server.Disconnect()
            except:
                pass

    def create_calculation_group(
        self,
        name: str,
        items: List[Dict[str, Any]],
        description: Optional[str] = None,
        precedence: int = 0
    ) -> Dict[str, Any]:
        """
        Create a calculation group with items.

        Args:
            name: Name of the calculation group
            items: List of calculation items with 'name' and 'expression'
            description: Optional description
            precedence: Precedence level (default 0)

        Returns:
            Result dictionary
        """
        if not AMO_AVAILABLE:
            return {
                'success': False,
                'error': 'AMO not available for calculation groups'
            }

        if not items:
            return {
                'success': False,
                'error': 'At least one calculation item is required'
            }

        server = AMOServer()
        try:
            server.Connect(self.connection.ConnectionString)

            if server.Databases.Count == 0:
                return {'success': False, 'error': 'No database found'}

            db = server.Databases[0]
            model = db.Model

            # Check if table already exists
            existing_table = next((t for t in model.Tables if t.Name == name), None)
            if existing_table:
                return {
                    'success': False,
                    'error': f"Table '{name}' already exists. Use a different name."
                }

            # Create table for calculation group
            table = Table()
            table.Name = name

            # Create calculation group
            calc_group = CalculationGroup()
            if description:
                calc_group.Description = description
            if hasattr(calc_group, 'Precedence'):
                calc_group.Precedence = precedence

            # Create the column for calculation group
            column = Column()
            column.Name = name
            column.DataType = DataType.String
            column.SourceColumn = name

            calc_group.Columns.Add(column)

            # Add calculation items
            for idx, item_data in enumerate(items):
                item = CalculationItem()
                item.Name = item_data.get('name')
                item.Expression = item_data.get('expression')

                if 'ordinal' in item_data and hasattr(item, 'Ordinal'):
                    item.Ordinal = item_data['ordinal']
                elif hasattr(item, 'Ordinal'):
                    item.Ordinal = idx

                if 'format_string_expression' in item_data and hasattr(item, 'FormatStringExpression'):
                    item.FormatStringExpression = item_data['format_string_expression']

                calc_group.CalculationItems.Add(item)

            table.CalculationGroup = calc_group
            model.Tables.Add(table)

            # Save changes
            model.SaveChanges()

            logger.info(f"Created calculation group '{name}' with {len(items)} items")

            return {
                'success': True,
                'action': 'created',
                'calculation_group': name,
                'items_count': len(items),
                'message': f"Successfully created calculation group '{name}' with {len(items)} items"
            }

        except Exception as e:
            logger.error(f"Error creating calculation group: {e}")
            return {
                'success': False,
                'error': str(e),
                'suggestions': [
                    'Verify calculation item expressions are valid DAX',
                    'Ensure calculation group name is unique',
                    'Check that model compatibility level supports calculation groups (1470+)'
                ]
            }
        finally:
            try:
                server.Disconnect()
            except:
                pass

    def delete_calculation_group(self, name: str) -> Dict[str, Any]:
        """Delete a calculation group."""
        if not AMO_AVAILABLE:
            return {
                'success': False,
                'error': 'AMO not available'
            }

        server = AMOServer()
        try:
            server.Connect(self.connection.ConnectionString)

            if server.Databases.Count == 0:
                return {'success': False, 'error': 'No database found'}

            db = server.Databases[0]
            model = db.Model

            # Find table with calculation group
            table = next((t for t in model.Tables
                         if t.Name == name and hasattr(t, 'CalculationGroup')
                         and t.CalculationGroup is not None), None)

            if not table:
                return {
                    'success': False,
                    'error': f"Calculation group '{name}' not found"
                }

            # Remove table (which contains calculation group)
            model.Tables.Remove(table)
            model.SaveChanges()

            logger.info(f"Deleted calculation group '{name}'")

            return {
                'success': True,
                'action': 'deleted',
                'calculation_group': name,
                'message': f"Successfully deleted calculation group '{name}'"
            }

        except Exception as e:
            logger.error(f"Error deleting calculation group: {e}")
            return {'success': False, 'error': str(e)}
        finally:
            try:
                server.Disconnect()
            except:
                pass
