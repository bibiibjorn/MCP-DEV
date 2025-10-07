"""
Partition Manager for PBIXRay MCP Server
Manages table partitions for incremental refresh scenarios
"""

import logging
from typing import Dict, Any, List, Optional
from datetime import datetime

logger = logging.getLogger(__name__)

# Try to load AMO
AMO_AVAILABLE = False
AMOServer = None
RefreshType = None

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

    from Microsoft.AnalysisServices.Tabular import Server as AMOServer, RefreshType
    AMO_AVAILABLE = True
    logger.info("AMO available for partition management")

except Exception as e:
    logger.warning(f"AMO not available: {e}")


class PartitionManager:
    """Manage table partitions."""

    def __init__(self, connection):
        """Initialize with ADOMD connection."""
        self.connection = connection

    def list_table_partitions(self, table: Optional[str] = None) -> Dict[str, Any]:
        """
        List partitions for tables.

        Args:
            table: Optional table name to filter

        Returns:
            Partition information
        """
        if not AMO_AVAILABLE:
            return {
                'success': False,
                'error': 'AMO not available for partition management'
            }

        server = AMOServer()
        try:
            server.Connect(self.connection.ConnectionString)

            if server.Databases.Count == 0:
                return {'success': False, 'error': 'No database found'}

            db = server.Databases[0]
            model = db.Model

            partitions_info = []

            tables_to_check = [t for t in model.Tables if not table or t.Name == table]

            for tbl in tables_to_check:
                table_partitions = []

                for partition in tbl.Partitions:
                    # Get partition info
                    partition_data = {
                        'name': partition.Name,
                        'mode': str(partition.Mode) if hasattr(partition, 'Mode') else 'Import',
                        'state': str(partition.State) if hasattr(partition, 'State') else 'Unknown'
                    }

                    # Get source info
                    if hasattr(partition, 'Source'):
                        source = partition.Source
                        source_type = str(source.GetType().Name) if source else 'Unknown'
                        partition_data['source_type'] = source_type

                        # Try to get expression/query
                        if hasattr(source, 'Expression'):
                            partition_data['expression'] = str(source.Expression)[:500]  # Truncate
                        elif hasattr(source, 'Query'):
                            partition_data['query'] = str(source.Query)[:500]

                    # Get refresh info
                    if hasattr(partition, 'RefreshedTime'):
                        partition_data['last_refresh'] = str(partition.RefreshedTime)

                    # Get row count (may not be available)
                    if hasattr(partition, 'RowCount'):
                        partition_data['row_count'] = partition.RowCount

                    table_partitions.append(partition_data)

                partitions_info.append({
                    'table': tbl.Name,
                    'partition_count': len(table_partitions),
                    'partitions': table_partitions
                })

            return {
                'success': True,
                'tables': partitions_info,
                'total_tables': len(partitions_info),
                'total_partitions': sum(p['partition_count'] for p in partitions_info)
            }

        except Exception as e:
            logger.error(f"Error listing partitions: {e}")
            return {'success': False, 'error': str(e)}
        finally:
            try:
                server.Disconnect()
            except:
                pass

    def refresh_partition(
        self,
        table: str,
        partition: str,
        refresh_type: str = 'full'
    ) -> Dict[str, Any]:
        """
        Refresh a specific partition.

        Args:
            table: Table name
            partition: Partition name
            refresh_type: 'full', 'data', or 'calculate'

        Returns:
            Result dictionary
        """
        if not AMO_AVAILABLE:
            return {
                'success': False,
                'error': 'AMO not available for partition refresh'
            }

        server = AMOServer()
        try:
            server.Connect(self.connection.ConnectionString)

            if server.Databases.Count == 0:
                return {'success': False, 'error': 'No database found'}

            db = server.Databases[0]
            model = db.Model

            # Find table
            tbl = next((t for t in model.Tables if t.Name == table), None)
            if not tbl:
                return {
                    'success': False,
                    'error': f"Table '{table}' not found"
                }

            # Find partition
            part = next((p for p in tbl.Partitions if p.Name == partition), None)
            if not part:
                available = [p.Name for p in tbl.Partitions]
                return {
                    'success': False,
                    'error': f"Partition '{partition}' not found in table '{table}'",
                    'available_partitions': available
                }

            # Determine refresh type
            if refresh_type.lower() == 'full':
                rt = RefreshType.Full
            elif refresh_type.lower() == 'data':
                rt = RefreshType.DataOnly
            elif refresh_type.lower() == 'calculate':
                rt = RefreshType.Calculate
            else:
                return {
                    'success': False,
                    'error': f"Invalid refresh type: {refresh_type}. Use 'full', 'data', or 'calculate'"
                }

            # Execute refresh
            logger.info(f"Refreshing partition '{partition}' in table '{table}' with type '{refresh_type}'")
            start_time = datetime.now()

            part.RequestRefresh(rt)
            model.SaveChanges()

            duration = (datetime.now() - start_time).total_seconds()

            return {
                'success': True,
                'action': 'refresh',
                'table': table,
                'partition': partition,
                'refresh_type': refresh_type,
                'duration_seconds': round(duration, 2),
                'message': f"Successfully refreshed partition '{partition}' in {duration:.1f}s"
            }

        except Exception as e:
            logger.error(f"Error refreshing partition: {e}")
            return {
                'success': False,
                'error': str(e),
                'suggestions': [
                    'Verify partition name is correct',
                    'Ensure data source is accessible',
                    'Check partition source query is valid'
                ]
            }
        finally:
            try:
                server.Disconnect()
            except:
                pass

    def refresh_table(self, table: str, refresh_type: str = 'full') -> Dict[str, Any]:
        """
        Refresh entire table (all partitions).

        Args:
            table: Table name
            refresh_type: 'full', 'data', or 'calculate'

        Returns:
            Result dictionary
        """
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

            # Find table
            tbl = next((t for t in model.Tables if t.Name == table), None)
            if not tbl:
                return {'success': False, 'error': f"Table '{table}' not found"}

            # Determine refresh type
            if refresh_type.lower() == 'full':
                rt = RefreshType.Full
            elif refresh_type.lower() == 'data':
                rt = RefreshType.DataOnly
            elif refresh_type.lower() == 'calculate':
                rt = RefreshType.Calculate
            else:
                return {
                    'success': False,
                    'error': f"Invalid refresh type: {refresh_type}"
                }

            # Execute refresh
            logger.info(f"Refreshing table '{table}' with type '{refresh_type}'")
            start_time = datetime.now()

            tbl.RequestRefresh(rt)
            model.SaveChanges()

            duration = (datetime.now() - start_time).total_seconds()

            return {
                'success': True,
                'action': 'refresh',
                'table': table,
                'refresh_type': refresh_type,
                'duration_seconds': round(duration, 2),
                'message': f"Successfully refreshed table '{table}' in {duration:.1f}s"
            }

        except Exception as e:
            logger.error(f"Error refreshing table: {e}")
            return {'success': False, 'error': str(e)}
        finally:
            try:
                server.Disconnect()
            except:
                pass
