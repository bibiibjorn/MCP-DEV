from typing import Any, Dict, Optional


class ConnectionPolicy:
    def __init__(self, config: Any):
        self.config = config

    def ensure_connected(self, connection_manager, connection_state, preferred_index: Optional[int] = None) -> Dict[str, Any]:
        if connection_state.is_connected():
            info = connection_manager.get_instance_info() or {}
            return {"success": True, "already_connected": True, "instance": info}

        instances = connection_manager.detect_instances()
        if not instances:
            return {
                "success": False,
                "error": "No Power BI Desktop instances detected. Open a .pbix in Power BI Desktop and try again.",
                "error_type": "no_instances",
                "suggestions": [
                    "Open Power BI Desktop with a .pbix file",
                    "Wait 10–15 seconds for the model to load",
                    "Then run detection again",
                ],
            }

        index = preferred_index if preferred_index is not None else 0
        connect_result = connection_manager.connect(index)
        if not connect_result.get("success"):
            return connect_result
        connection_state.set_connection_manager(connection_manager)
        connection_state.initialize_managers()
        return {"success": True, "connected_index": index, "instances": instances, "managers_initialized": connection_state._managers_initialized}
