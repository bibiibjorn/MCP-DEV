"""
Calculation Group Manager for PBIXRay MCP Server
Manage calculation groups and calculation items
"""

import logging
from typing import Dict, Any, List, Optional

logger = logging.getLogger(__name__)

AMO_AVAILABLE = True  # Determined lazily per-connection


class CalculationGroupManager:
    """Manage calculation groups and items."""

    def __init__(self, connection):
        """Initialize with ADOMD connection."""
        self.connection = connection

    def _connect_amo_server_db(self):
        """Open a TOM Server using the ADOMD connection string and return (server, db, TabularModule) or (None, None, None)."""
        try:
            import clr  # type: ignore
            import os as _os
            script_dir = _os.path.dirname(_os.path.abspath(__file__))
            parent_dir = _os.path.dirname(script_dir)
            dll_folder = _os.path.join(parent_dir, "lib", "dotnet")
            core_dll = _os.path.join(dll_folder, "Microsoft.AnalysisServices.Core.dll")
            tabular_dll = _os.path.join(dll_folder, "Microsoft.AnalysisServices.Tabular.dll")
            if _os.path.exists(core_dll):
                clr.AddReference(core_dll)  # type: ignore[attr-defined]
            if _os.path.exists(tabular_dll):
                clr.AddReference(tabular_dll)  # type: ignore[attr-defined]
            import Microsoft.AnalysisServices.Tabular as Tabular  # type: ignore
            server = Tabular.Server()
            conn_str = getattr(self.connection, 'ConnectionString', None)
            if not conn_str:
                return None, None, None
            server.Connect(conn_str)
            db = server.Databases[0] if server.Databases.Count > 0 else None
            if not db:
                try:
                    server.Disconnect()
                except Exception:
                    pass
                return None, None, None
            return server, db, Tabular
        except Exception as _e:
            logger.warning(f"AMO not available for calc groups: {_e}")
            return None, None, None

    def list_calculation_groups(self) -> Dict[str, Any]:
        """List all calculation groups and their items."""
        server, db, Tabular = self._connect_amo_server_db()
        if not server or not db or not Tabular:
            return {'success': False, 'error': 'AMO not available for calculation groups'}
        try:
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
        server, db, Tabular = self._connect_amo_server_db()
        if not server or not db or not Tabular:
            return {'success': False, 'error': 'AMO not available for calculation groups'}

        if not items:
            return {
                'success': False,
                'error': 'At least one calculation item is required'
            }

        try:
            model = db.Model

            # Check if table already exists
            existing_table = next((t for t in model.Tables if t.Name == name), None)
            if existing_table:
                return {
                    'success': False,
                    'error': f"Table '{name}' already exists. Use a different name."
                }

            # Create table for calculation group
            table = Tabular.Table()
            table.Name = name
            # Some TOM versions require explicitly marking the table as CalculationGroup
            try:
                if hasattr(Tabular, 'TableType') and hasattr(table, 'TableType'):
                    table.TableType = Tabular.TableType.CalculationGroup
            except Exception:
                pass

            # Create calculation group
            calc_group = Tabular.CalculationGroup()
            if description:
                calc_group.Description = description
            if hasattr(calc_group, 'Precedence'):
                calc_group.Precedence = precedence

            # Create the mandatory calculation group column (string).
            # Important: it belongs to the table.Columns collection, not calc_group.Columns.
            try:
                cg_col = Tabular.CalculationGroupColumn()
                cg_col.Name = name
                # Add to the table's Columns collection for TOM >= 19.x
                table.Columns.Add(cg_col)
            except Exception:
                # Older TOM fallback: use a concrete DataColumn (not abstract Column) as string
                try:
                    data_col = Tabular.DataColumn()
                    data_col.Name = name
                    try:
                        data_col.DataType = Tabular.DataType.String
                    except Exception:
                        pass
                    table.Columns.Add(data_col)
                except Exception as inner_e:
                    return {'success': False, 'error': 'Failed to create calculation group column', 'details': str(inner_e)}

            # Add calculation items
            for idx, item_data in enumerate(items):
                item = Tabular.CalculationItem()
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
        server, db, Tabular = self._connect_amo_server_db()
        if not server or not db or not Tabular:
            return {'success': False, 'error': 'AMO not available'}
        try:
            model = db.Model

            # Find table with calculation group
            table = next((t for t in model.Tables if t.Name == name and hasattr(t, 'CalculationGroup') and t.CalculationGroup is not None), None)

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
