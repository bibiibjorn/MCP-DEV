"""
Connection Manager for PBIXRay MCP Server

Manages Power BI Desktop connections, instance detection, and connection state.
"""

import logging
import subprocess
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)

# Try to load ADOMD.NET
ADOMD_AVAILABLE = False
AdomdConnection = None

try:
    import clr
    import os

    script_dir = os.path.dirname(os.path.abspath(__file__))
    parent_dir = os.path.dirname(script_dir)
    dll_folder = os.path.join(parent_dir, "lib", "dotnet")

    adomd_dll = os.path.join(dll_folder, "Microsoft.AnalysisServices.AdomdClient.dll")
    if os.path.exists(adomd_dll):
        clr.AddReference(adomd_dll)
        from Microsoft.AnalysisServices.AdomdClient import AdomdConnection
        ADOMD_AVAILABLE = True
        logger.info("ADOMD.NET available for connections")
except Exception as e:
    logger.warning(f"ADOMD.NET not available: {e}")


class PowerBIDesktopDetector:
    """
    Detects running Power BI Desktop instances using optimized netstat-based approach.

    Based on fabric-toolbox ultra-fast detection methods.
    """

    @staticmethod
    def find_powerbi_instances() -> List[Dict[str, Any]]:
        """
        Find running Power BI Desktop instances.

        Uses netstat to detect listening ports and tasklist to verify msmdsrv.exe processes.

        Returns:
            List of instance dictionaries with port, PID, and connection info
        """
        instances = []

        try:
            # Run netstat to get listening ports
            result = subprocess.run(
                ['netstat', '-ano'],
                capture_output=True,
                text=True,
                timeout=10
            )

            if result.returncode != 0:
                logger.error("netstat command failed")
                return instances

            # Parse netstat output for listening ports
            port_pid_map = {}
            for line in result.stdout.splitlines():
                if 'LISTENING' in line and ('[::]' in line or '127.0.0.1' in line):
                    parts = line.split()
                    if len(parts) >= 5:
                        try:
                            address = parts[1]
                            # Extract port number
                            if ']:' in address:  # IPv6 format
                                port = int(address.split(']:')[1])
                            else:  # IPv4 format
                                port = int(address.split(':')[-1])

                            pid = int(parts[4])
                            port_pid_map[port] = pid
                        except (ValueError, IndexError):
                            continue

            # Run tasklist to find msmdsrv.exe processes
            tasklist_result = subprocess.run(
                ['tasklist', '/FI', 'IMAGENAME eq msmdsrv.exe', '/FO', 'CSV', '/NH'],
                capture_output=True,
                text=True,
                timeout=10
            )

            msmdsrv_pids = set()
            if tasklist_result.returncode == 0:
                for line in tasklist_result.stdout.splitlines():
                    if 'msmdsrv.exe' in line:
                        parts = line.split(',')
                        if len(parts) >= 2:
                            try:
                                pid = int(parts[1].strip('"'))
                                msmdsrv_pids.add(pid)
                            except ValueError:
                                pass

            # Match ports to msmdsrv PIDs
            for port, pid in port_pid_map.items():
                if pid in msmdsrv_pids:
                    instances.append({
                        'port': port,
                        'pid': pid,
                        'workspace': f'msmdsrv_pid_{pid}',
                        'path': f'localhost:{port}',
                        'connection_string': f'Data Source=localhost:{port}',
                        'display_name': f'Power BI Desktop (Port {port})'
                    })

            # Sort by port (highest first - usually most recent)
            instances.sort(key=lambda x: x['port'], reverse=True)

            logger.info(f"Detected {len(instances)} Power BI Desktop instance(s)")

        except subprocess.TimeoutExpired:
            logger.error("Detection timed out")
        except Exception as e:
            logger.error(f"Detection error: {e}")

        return instances


class ConnectionManager:
    """
    Manages active Power BI Desktop connections.

    Handles:
    - Connection establishment
    - Connection state tracking
    - Connection reuse
    - Connection health checks
    """

    def __init__(self):
        """Initialize connection manager."""
        self.active_connection = None
        self.active_instance = None
        self.connection_string = None

    def detect_instances(self) -> List[Dict[str, Any]]:
        """
        Detect available Power BI Desktop instances.

        Returns:
            List of detected instances
        """
        detector = PowerBIDesktopDetector()
        return detector.find_powerbi_instances()

    def connect(self, model_index: int = 0) -> Dict[str, Any]:
        """
        Connect to a Power BI Desktop instance.

        Args:
            model_index: Index of instance to connect to (0 = most recent)

        Returns:
            Connection result dictionary
        """
        if not ADOMD_AVAILABLE:
            return {
                'success': False,
                'error': 'ADOMD.NET not available',
                'error_type': 'adomd_unavailable'
            }

        try:
            # Detect instances
            instances = self.detect_instances()

            if not instances:
                return {
                    'success': False,
                    'error': 'No Power BI Desktop instances detected',
                    'error_type': 'no_instances',
                    'suggestions': [
                        'Ensure Power BI Desktop is running with .pbix file open',
                        'Verify msmdsrv.exe process is running'
                    ]
                }

            if model_index >= len(instances):
                return {
                    'success': False,
                    'error': f'Invalid model index {model_index}, only {len(instances)} instance(s) found',
                    'error_type': 'invalid_index',
                    'available_instances': len(instances)
                }

            # Get selected instance
            instance = instances[model_index]
            conn_str = instance['connection_string']

            # Close existing connection if any
            if self.active_connection:
                try:
                    self.active_connection.Close()
                except:
                    pass

            # Create new connection
            self.active_connection = AdomdConnection(conn_str)
            self.active_connection.Open()
            self.active_instance = instance
            self.connection_string = conn_str

            logger.info(f"Connected to Power BI Desktop on port {instance['port']}")

            return {
                'success': True,
                'instance': instance,
                'connection_string': conn_str,
                'model_index': model_index,
                'total_instances': len(instances),
                'message': f"Successfully connected to Power BI Desktop on port {instance['port']}"
            }

        except Exception as e:
            error_msg = str(e)
            logger.error(f"Connection error: {error_msg}")

            return {
                'success': False,
                'error': error_msg,
                'error_type': 'connection_error',
                'suggestions': [
                    'Verify Power BI Desktop is running with model loaded',
                    'Check firewall settings',
                    'Try detecting instances again'
                ]
            }

    def connect_to_port(self, port: int) -> Dict[str, Any]:
        """
        Connect directly to a Power BI Desktop instance on a specific port.

        Args:
            port: Port number of the Power BI Desktop instance

        Returns:
            Connection result dictionary
        """
        if not ADOMD_AVAILABLE:
            return {
                'success': False,
                'error': 'ADOMD.NET not available'
            }

        try:
            # Build connection string
            conn_str = f'Data Source=localhost:{port}'

            # Close existing connection if any
            if self.active_connection:
                try:
                    self.active_connection.Close()
                except:
                    pass

            # Create and open connection
            self.active_connection = AdomdConnection(conn_str)
            self.active_connection.Open()

            # Get database name
            cmd = self.active_connection.CreateCommand()
            cmd.CommandText = "SELECT [CATALOG_NAME] FROM $SYSTEM.DBSCHEMA_CATALOGS"
            reader = cmd.ExecuteReader()

            db_name = None
            if reader.Read():
                db_name = str(reader.GetValue(0))
            reader.Close()

            # Store instance info
            self.active_instance = {
                'port': port,
                'database': db_name,
                'connection_string': conn_str,
                'display_name': f'Power BI Desktop (Port {port})'
            }
            self.connection_string = conn_str

            logger.info(f"Connected to Power BI Desktop on port {port}")

            return {
                'success': True,
                'port': port,
                'database_name': db_name,
                'connection_string': conn_str,
                'instance': self.active_instance,
                'message': f'Successfully connected to port {port}'
            }

        except Exception as e:
            logger.error(f"Failed to connect to port {port}: {e}")
            return {
                'success': False,
                'port': port,
                'error': str(e),
                'error_type': 'connection_failed'
            }

    def test_connection(self, port: Optional[int] = None) -> Dict[str, Any]:
        """
        Test connection to a specific port or current connection.

        Args:
            port: Optional port to test, uses current connection if None

        Returns:
            Test result dictionary
        """
        if not ADOMD_AVAILABLE:
            return {
                'success': False,
                'error': 'ADOMD.NET not available'
            }

        try:
            if port:
                # Test specific port
                conn_str = f'Data Source=localhost:{port}'
                test_conn = AdomdConnection(conn_str)
                test_conn.Open()

                # Get server info
                cmd = test_conn.CreateCommand()
                cmd.CommandText = "SELECT [CATALOG_NAME] FROM $SYSTEM.DBSCHEMA_CATALOGS"
                reader = cmd.ExecuteReader()

                db_name = None
                if reader.Read():
                    db_name = str(reader.GetValue(0))
                reader.Close()
                test_conn.Close()

                return {
                    'success': True,
                    'port': port,
                    'database_name': db_name,
                    'connection_string': conn_str,
                    'message': f'Successfully connected to port {port}'
                }

            elif self.active_connection:
                # Test current connection
                if self.active_connection.State.ToString() != 'Open':
                    return {
                        'success': False,
                        'error': 'Connection is not open',
                        'connection_state': self.active_connection.State.ToString()
                    }

                # Test with simple query
                cmd = self.active_connection.CreateCommand()
                cmd.CommandText = "EVALUATE { 1 }"
                reader = cmd.ExecuteReader()

                has_data = reader.Read()
                reader.Close()

                return {
                    'success': True,
                    'connection_state': 'Open',
                    'instance': self.active_instance,
                    'message': 'Connection is healthy'
                }

            else:
                return {
                    'success': False,
                    'error': 'No active connection to test'
                }

        except Exception as e:
            logger.error(f"Connection test error: {e}")
            return {
                'success': False,
                'error': str(e),
                'error_type': 'connection_test_error'
            }

    def get_connection(self):
        """
        Get active connection.

        Returns:
            Active ADOMD connection or None
        """
        return self.active_connection

    def get_instance_info(self) -> Optional[Dict[str, Any]]:
        """
        Get current instance information.

        Returns:
            Instance info dictionary or None
        """
        return self.active_instance

    def is_connected(self) -> bool:
        """
        Check if there's an active connection.

        Returns:
            True if connected, False otherwise
        """
        if not self.active_connection:
            return False

        try:
            return self.active_connection.State.ToString() == 'Open'
        except:
            return False

    def disconnect(self):
        """Disconnect from current instance."""
        if self.active_connection:
            try:
                self.active_connection.Close()
                logger.info("Disconnected from Power BI Desktop")
            except:
                pass
            finally:
                self.active_connection = None
                self.active_instance = None
                self.connection_string = None

    def connect_by_stable_id(self, port: int, database_id: str) -> Dict[str, Any]:
        """
        Connect to a Power BI instance using stable ID (port:databaseId)

        Args:
            port: Port number
            database_id: Database ID

        Returns:
            Connection result dictionary
        """
        if not ADOMD_AVAILABLE:
            return {
                'success': False,
                'error': 'ADOMD.NET not available',
                'error_type': 'adomd_unavailable'
            }

        try:
            # Close existing connection if any
            if self.active_connection:
                try:
                    self.active_connection.Close()
                except:
                    pass

            # Create connection string with database
            conn_str = f"Data Source=localhost:{port};Initial Catalog={database_id}"

            # Create new connection
            self.active_connection = AdomdConnection(conn_str)
            self.active_connection.Open()

            self.active_instance = {
                'port': port,
                'database': database_id,
                'stable_id': f"{port}:{database_id}",
                'connection_string': conn_str,
                'process_name': 'msmdsrv.exe',
                'pid': 0
            }
            self.connection_string = conn_str

            logger.info(f"Connected to model at {port}:{database_id}")

            return {
                'success': True,
                'stable_id': f"{port}:{database_id}",
                'port': port,
                'database': database_id,
                'connection_string': conn_str,
                'message': f'Successfully connected to model at {port}:{database_id}'
            }

        except Exception as e:
            logger.error(f"Failed to connect by stable ID: {e}")
            return {
                'success': False,
                'error': str(e),
                'error_type': 'connection_error'
            }
