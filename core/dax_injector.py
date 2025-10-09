"""
DAX Injector for PBIXRay MCP Server

Provides live DAX measure injection and modification capabilities.
"""

import logging
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)

# Try to load AMO
AMO_AVAILABLE = False
AMOServer = None
Measure = None

try:
    import clr
    import os

    script_dir = os.path.dirname(os.path.abspath(__file__))
    parent_dir = os.path.dirname(script_dir)
    dll_folder = os.path.join(parent_dir, "lib", "dotnet")

    core_dll = os.path.join(dll_folder, "Microsoft.AnalysisServices.Core.dll")
    amo_dll = os.path.join(dll_folder, "Microsoft.AnalysisServices.dll")
    tabular_dll = os.path.join(dll_folder, "Microsoft.AnalysisServices.Tabular.dll")

    if os.path.exists(core_dll):
        clr.AddReference(core_dll)
    if os.path.exists(amo_dll):
        clr.AddReference(amo_dll)
    if os.path.exists(tabular_dll):
        clr.AddReference(tabular_dll)

    from Microsoft.AnalysisServices.Tabular import Server as AMOServer, Measure
    AMO_AVAILABLE = True
    logger.info("AMO available for DAX injection")

except Exception as e:
    logger.warning(f"AMO not available for DAX injection: {e}")


# Try to load ADOMD for database queries
AdomdConnection = None
AdomdCommand = None

try:
    import clr
    import os

    script_dir = os.path.dirname(os.path.abspath(__file__))
    parent_dir = os.path.dirname(script_dir)
    dll_folder = os.path.join(parent_dir, "lib", "dotnet")

    adomd_dll = os.path.join(dll_folder, "Microsoft.AnalysisServices.AdomdClient.dll")
    if os.path.exists(adomd_dll):
        clr.AddReference(adomd_dll)
        from Microsoft.AnalysisServices.AdomdClient import AdomdConnection, AdomdCommand
except Exception:
    pass


class DAXInjector:
    """
    DAX measure injection and modification service.

    Allows creating and updating DAX measures in live Power BI Desktop models.
    """

    def __init__(self, connection):
        """
        Initialize DAX injector.

        Args:
            connection: Active ADOMD connection
        """
        self.connection = connection

    def upsert_measure(
        self,
        table_name: str,
        measure_name: str,
        dax_expression: str,
        display_folder: Optional[str] = None,
        description: Optional[str] = None,
        format_string: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Create or update a DAX measure.

        Args:
            table_name: Name of the table to add measure to
            measure_name: Name of the measure
            dax_expression: DAX expression for the measure
            display_folder: Optional display folder for organization
            description: Optional measure description
            format_string: Optional format string (e.g., "#,##0.00")

        Returns:
            Result dictionary with success status and details
        """
        if not AMO_AVAILABLE:
            return {
                "success": False,
                "error": "AMO not available - cannot inject measures",
                "error_type": "amo_unavailable"
            }

        # Basic identifier validation similar to Tabular MCP approach
        def _valid_identifier(s: Optional[str]) -> bool:
            return bool(s) and len(str(s).strip()) > 0 and len(str(s)) <= 128 and '\0' not in str(s)

        if not _valid_identifier(table_name) or not _valid_identifier(measure_name):
            return {
                "success": False,
                "error": "Table and measure names must be non-empty and <=128 chars",
                "error_type": "invalid_parameters"
            }

        server = AMOServer()

        try:
            # Connect to server
            server.Connect(self.connection.ConnectionString)

            # Get database name via DMV, with fallback to first database on server
            db_name = None
            try:
                db_query = "SELECT [CATALOG_NAME] FROM $SYSTEM.DBSCHEMA_CATALOGS"
                cmd = AdomdCommand(db_query, self.connection)
                reader = cmd.ExecuteReader()
                if reader.Read():
                    db_name = str(reader.GetValue(0))
                reader.Close()
            except Exception:
                db_name = None

            if not db_name:
                try:
                    # Fallback to first database exposed by AMO (typical for Desktop)
                    if server.Databases.Count > 0:
                        db_name = server.Databases[0].Name
                except Exception:
                    pass
                if not db_name:
                    return {
                        "success": False,
                        "error": "Could not determine database name",
                        "error_type": "database_error"
                    }

            # Get database and model
            db = server.Databases.GetByName(db_name)
            model = db.Model

            # Find table
            table = next((t for t in model.Tables if t.Name == table_name), None)

            if not table:
                available_tables = [t.Name for t in model.Tables]
                return {
                    "success": False,
                    "error": f"Table '{table_name}' not found",
                    "error_type": "table_not_found",
                    "available_tables": available_tables[:10]  # Show first 10
                }

            # Find or create measure
            measure = next((m for m in table.Measures if m.Name == measure_name), None)

            if measure:
                # Update existing measure
                if dax_expression:
                    measure.Expression = dax_expression

                if display_folder is not None:
                    measure.DisplayFolder = display_folder

                if description is not None:
                    measure.Description = description

                if format_string is not None:
                    measure.FormatString = format_string

                action = "updated"
                logger.info(f"Updated measure '{measure_name}' in table '{table_name}'")

            else:
                # Create new measure (requires an expression)
                if not dax_expression:
                    return {
                        "success": False,
                        "error": "Expression is required when creating a new measure",
                        "error_type": "invalid_parameters"
                    }
                measure = Measure()
                measure.Name = measure_name
                measure.Expression = dax_expression

                if display_folder:
                    measure.DisplayFolder = display_folder

                if description:
                    measure.Description = description

                if format_string:
                    measure.FormatString = format_string

                table.Measures.Add(measure)
                action = "created"
                logger.info(f"Created measure '{measure_name}' in table '{table_name}'")

            # Save changes
            model.SaveChanges()

            return {
                "success": True,
                "action": action,
                "table": table_name,
                "measure": measure_name,
                "expression": dax_expression,
                "display_folder": display_folder,
                "description": description,
                "format_string": format_string,
                "message": f"Successfully {action} measure '{measure_name}' in table '{table_name}'"
            }

        except Exception as e:
            error_msg = str(e)
            logger.error(f"Error upserting measure: {error_msg}")

            # Provide helpful suggestions based on error
            suggestions = []

            if "syntax" in error_msg.lower() or "expression" in error_msg.lower():
                suggestions.extend([
                    "Check DAX syntax - ensure expression is valid",
                    "Verify all referenced columns and measures exist",
                    "Test the DAX expression separately first"
                ])

            if "table" in error_msg.lower():
                suggestions.append(f"Verify table '{table_name}' exists in the model")

            if "duplicate" in error_msg.lower() or "already exists" in error_msg.lower():
                suggestions.append("Measure name may conflict with existing object")

            if not suggestions:
                suggestions.extend([
                    "Verify all table and column references exist",
                    "Check DAX expression syntax",
                    "Ensure model is in a valid state"
                ])

            return {
                "success": False,
                "error": error_msg,
                "error_type": "injection_error",
                "suggestions": suggestions
            }

        finally:
            try:
                server.Disconnect()
            except:
                pass

    def delete_measure(self, table_name: str, measure_name: str) -> Dict[str, Any]:
        """
        Delete a DAX measure.

        Args:
            table_name: Name of the table containing the measure
            measure_name: Name of the measure to delete

        Returns:
            Result dictionary with success status
        """
        if not AMO_AVAILABLE:
            return {
                "success": False,
                "error": "AMO not available",
                "error_type": "amo_unavailable"
            }

        # Validate identifiers early
        def _valid_identifier(s: Optional[str]) -> bool:
            return bool(s) and len(str(s).strip()) > 0 and len(str(s)) <= 128 and '\0' not in str(s)
        if not _valid_identifier(table_name) or not _valid_identifier(measure_name):
            return {
                "success": False,
                "error": "Table and measure names must be non-empty and <=128 chars",
                "error_type": "invalid_parameters"
            }

        server = AMOServer()

        try:
            server.Connect(self.connection.ConnectionString)

            # Get database name with same DMV+fallback strategy
            db_name = None
            try:
                db_query = "SELECT [CATALOG_NAME] FROM $SYSTEM.DBSCHEMA_CATALOGS"
                cmd = AdomdCommand(db_query, self.connection)
                reader = cmd.ExecuteReader()
                if reader.Read():
                    db_name = str(reader.GetValue(0))
                reader.Close()
            except Exception:
                db_name = None

            if not db_name:
                try:
                    if server.Databases.Count > 0:
                        db_name = server.Databases[0].Name
                except Exception:
                    pass
                if not db_name:
                    return {
                        "success": False,
                        "error": "Could not determine database name"
                    }

            # Get database and model
            db = server.Databases.GetByName(db_name)
            model = db.Model

            # Find table
            table = next((t for t in model.Tables if t.Name == table_name), None)

            if not table:
                return {
                    "success": False,
                    "error": f"Table '{table_name}' not found"
                }

            # Find measure
            measure = next((m for m in table.Measures if m.Name == measure_name), None)

            if not measure:
                return {
                    "success": False,
                    "error": f"Measure '{measure_name}' not found in table '{table_name}'"
                }

            # Remove measure
            table.Measures.Remove(measure)
            model.SaveChanges()

            logger.info(f"Deleted measure '{measure_name}' from table '{table_name}'")

            return {
                "success": True,
                "action": "deleted",
                "table": table_name,
                "measure": measure_name,
                "message": f"Successfully deleted measure '{measure_name}'"
            }

        except Exception as e:
            logger.error(f"Error deleting measure: {e}")
            return {
                "success": False,
                "error": str(e),
                "error_type": "deletion_error"
            }

        finally:
            try:
                server.Disconnect()
            except:
                pass
