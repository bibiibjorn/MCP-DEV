"""
Multi-Instance Connection Manager

Manages multiple simultaneous connections to Power BI Desktop instances
for model comparison and cross-instance analysis.
"""

import logging
from typing import Dict, Any, Optional, List
from core.connection_manager import ConnectionManager

logger = logging.getLogger(__name__)


class MultiInstanceManager:
    """
    Manages multiple connections to Power BI Desktop instances.

    Enables simultaneous connections to different Power BI Desktop instances
    for model comparison, cross-instance queries, and parallel analysis.
    """

    def __init__(self):
        """Initialize multi-instance manager."""
        self.instances: Dict[int, ConnectionManager] = {}
        self.active_ports: List[int] = []

    def connect_to_instance(self, port: int) -> Dict[str, Any]:
        """
        Connect to a specific Power BI Desktop instance.

        Args:
            port: Port number of the Power BI Desktop instance

        Returns:
            Connection result dictionary
        """
        if port in self.instances:
            logger.info(f"Already connected to instance on port {port}")
            return {
                "success": True,
                "port": port,
                "status": "already_connected"
            }

        try:
            logger.info(f"Connecting to Power BI Desktop instance on port {port}")

            # Create new connection manager
            conn_manager = ConnectionManager()

            # Connect to specific port
            result = conn_manager.connect_to_port(port)

            if not result.get('success'):
                return {
                    "success": False,
                    "port": port,
                    "error": result.get('error', 'Connection failed')
                }

            # Store connection
            self.instances[port] = conn_manager
            self.active_ports.append(port)

            logger.info(f"Successfully connected to instance on port {port}")

            return {
                "success": True,
                "port": port,
                "status": "connected",
                "instance_info": result.get('instance')
            }

        except Exception as e:
            logger.error(f"Failed to connect to port {port}: {e}", exc_info=True)
            return {
                "success": False,
                "port": port,
                "error": str(e)
            }

    def disconnect_instance(self, port: int) -> Dict[str, Any]:
        """
        Disconnect from a specific instance.

        Args:
            port: Port number to disconnect from

        Returns:
            Disconnection result
        """
        if port not in self.instances:
            return {
                "success": False,
                "port": port,
                "error": "Instance not connected"
            }

        try:
            logger.info(f"Disconnecting from instance on port {port}")

            conn_manager = self.instances[port]
            conn_manager.disconnect()

            del self.instances[port]
            self.active_ports.remove(port)

            return {
                "success": True,
                "port": port,
                "status": "disconnected"
            }

        except Exception as e:
            logger.error(f"Error disconnecting from port {port}: {e}")
            return {
                "success": False,
                "port": port,
                "error": str(e)
            }

    def get_instance(self, port: int) -> Optional[ConnectionManager]:
        """
        Get connection manager for a specific port.

        Args:
            port: Port number

        Returns:
            ConnectionManager instance or None if not connected
        """
        return self.instances.get(port)

    def get_connection_string(self, port: int) -> Optional[str]:
        """
        Get connection string for a specific port.

        Args:
            port: Port number

        Returns:
            Connection string or None if not connected
        """
        instance = self.get_instance(port)
        if instance:
            return instance.connection_string
        return None

    def get_all_instances(self) -> List[Dict[str, Any]]:
        """
        Get information about all connected instances.

        Returns:
            List of instance information dictionaries
        """
        instances_info = []

        for port, conn_manager in self.instances.items():
            try:
                info = conn_manager.get_instance_info()
                if info:
                    info['port'] = port
                    info['connected'] = conn_manager.is_connected()
                    instances_info.append(info)
            except Exception as e:
                logger.warning(f"Error getting info for port {port}: {e}")

        return instances_info

    def disconnect_all(self) -> Dict[str, Any]:
        """
        Disconnect from all instances.

        Returns:
            Disconnection summary
        """
        ports_to_disconnect = list(self.active_ports)
        disconnected = []
        failed = []

        for port in ports_to_disconnect:
            result = self.disconnect_instance(port)
            if result.get('success'):
                disconnected.append(port)
            else:
                failed.append({
                    "port": port,
                    "error": result.get('error')
                })

        return {
            "success": len(failed) == 0,
            "disconnected_count": len(disconnected),
            "failed_count": len(failed),
            "disconnected_ports": disconnected,
            "failed_ports": failed
        }

    def get_status(self) -> Dict[str, Any]:
        """
        Get status of all connections.

        Returns:
            Status dictionary
        """
        return {
            "total_instances": len(self.instances),
            "active_ports": list(self.active_ports),
            "instances": self.get_all_instances()
        }

    def __del__(self):
        """Cleanup on deletion."""
        try:
            self.disconnect_all()
        except Exception as e:
            logger.warning(f"Error during cleanup: {e}")


# Global multi-instance manager
multi_instance_manager = MultiInstanceManager()
