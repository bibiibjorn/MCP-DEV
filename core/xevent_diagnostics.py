"""
Extended Events Diagnostics for Power BI Desktop

This module discovers what XEvents are actually available on the connected
Analysis Services instance and helps diagnose trace capture issues.
"""

import logging
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


class XEventDiagnostics:
    """Diagnostic tools for Extended Events troubleshooting"""

    def __init__(self, connection_string: str):
        """Initialize diagnostics with connection string"""
        self.connection_string = connection_string
        self.connection: Optional[Any] = None

    def connect(self) -> bool:
        """Establish ADOMD connection"""
        try:
            import clr  # type: ignore
            import sys
            import os

            # Add .NET DLLs path
            dll_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "lib", "dotnet")
            dll_path = os.path.join(dll_dir, "Microsoft.AnalysisServices.AdomdClient.dll")

            if not os.path.exists(dll_path):
                logger.error(f"ADOMD.NET DLL not found: {dll_path}")
                return False

            clr.AddReference(dll_path)  # type: ignore
            from Microsoft.AnalysisServices.AdomdClient import AdomdConnection  # type: ignore

            conn = AdomdConnection(self.connection_string)
            conn.Open()
            self.connection = conn

            logger.info("✓ Connected for xEvent diagnostics")
            return True

        except Exception as e:
            logger.error(f"✗ Failed to connect: {e}", exc_info=True)
            return False

    def list_available_packages(self) -> Dict[str, Any]:
        """
        List all available XEvent packages

        Returns:
            Dictionary with packages or error
        """
        if not self.connection:
            if not self.connect():
                return {'success': False, 'error': 'Connection failed'}

        try:
            from Microsoft.AnalysisServices.AdomdClient import AdomdCommand  # type: ignore

            # Query available packages
            query = """
            SELECT
                package_id,
                name,
                description,
                capabilities,
                capabilities_desc
            FROM sys.dm_xe_packages
            ORDER BY name
            """

            cmd = AdomdCommand(query, self.connection)
            reader = cmd.ExecuteReader()

            packages = []
            while reader.Read():
                packages.append({
                    'name': str(reader.GetValue(1)) if reader.GetValue(1) else '',
                    'description': str(reader.GetValue(2)) if reader.GetValue(2) else '',
                })

            reader.Close()

            logger.info(f"Found {len(packages)} XEvent packages")
            return {'success': True, 'packages': packages, 'count': len(packages)}

        except Exception as e:
            logger.error(f"Failed to list packages: {e}")
            return {'success': False, 'error': str(e)}

    def list_available_events(self, package_filter: Optional[str] = None) -> Dict[str, Any]:
        """
        List all available XEvent events

        Args:
            package_filter: Optional package name filter (e.g., 'AS', 'sqlserver')

        Returns:
            Dictionary with events or error
        """
        if not self.connection:
            if not self.connect():
                return {'success': False, 'error': 'Connection failed'}

        try:
            from Microsoft.AnalysisServices.AdomdClient import AdomdCommand  # type: ignore

            # Query available events
            if package_filter:
                where_clause = f"WHERE p.name = '{package_filter}'"
            else:
                where_clause = ""

            query = f"""
            SELECT
                p.name AS package_name,
                o.name AS event_name,
                o.description,
                o.object_type
            FROM sys.dm_xe_objects o
            JOIN sys.dm_xe_packages p ON o.package_guid = p.guid
            WHERE o.object_type = 'event'
            {where_clause}
            ORDER BY p.name, o.name
            """

            logger.debug(f"Querying available events (package_filter={package_filter})...")
            cmd = AdomdCommand(query, self.connection)
            reader = cmd.ExecuteReader()

            events = []
            while reader.Read():
                events.append({
                    'package': str(reader.GetValue(0)) if reader.GetValue(0) else '',
                    'name': str(reader.GetValue(1)) if reader.GetValue(1) else '',
                    'description': str(reader.GetValue(2)) if reader.GetValue(2) else '',
                })

            reader.Close()

            logger.info(f"✓ Found {len(events)} XEvent events")
            return {'success': True, 'events': events, 'count': len(events)}

        except Exception as e:
            logger.warning(f"✗ Failed to list events via DMV: {e}")
            logger.debug(f"  This may indicate sys.dm_xe_objects is not supported")
            return {'success': False, 'error': str(e), 'note': 'DMV not supported on this AS version'}

    def list_active_sessions(self) -> Dict[str, Any]:
        """
        List currently active XEvent sessions

        Returns:
            Dictionary with active sessions or error
        """
        if not self.connection:
            if not self.connect():
                return {'success': False, 'error': 'Connection failed'}

        try:
            from Microsoft.AnalysisServices.AdomdClient import AdomdCommand  # type: ignore

            query = """
            SELECT
                name,
                event_session_id,
                create_time,
                event_retention_mode_desc
            FROM sys.dm_xe_sessions
            ORDER BY name
            """

            logger.debug("Querying active XEvent sessions...")
            cmd = AdomdCommand(query, self.connection)
            reader = cmd.ExecuteReader()

            sessions = []
            while reader.Read():
                sessions.append({
                    'name': str(reader.GetValue(0)) if reader.GetValue(0) else '',
                    'session_id': str(reader.GetValue(1)) if reader.GetValue(1) else '',
                    'create_time': str(reader.GetValue(2)) if reader.GetValue(2) else '',
                    'retention_mode': str(reader.GetValue(3)) if reader.GetValue(3) else '',
                })

            reader.Close()

            logger.info(f"✓ Found {len(sessions)} active XEvent sessions")
            return {'success': True, 'sessions': sessions, 'count': len(sessions)}

        except Exception as e:
            logger.warning(f"✗ Failed to list sessions: {e}")
            return {'success': False, 'error': str(e)}

    def check_session_events(self, session_name: str) -> Dict[str, Any]:
        """
        Check which events are configured for a specific session

        Args:
            session_name: Name of the XEvent session

        Returns:
            Dictionary with event configuration or error
        """
        if not self.connection:
            if not self.connect():
                return {'success': False, 'error': 'Connection failed'}

        try:
            from Microsoft.AnalysisServices.AdomdClient import AdomdCommand  # type: ignore

            query = f"""
            SELECT
                se.name AS event_name,
                se.package AS package_name,
                se.predicate
            FROM sys.dm_xe_session_events se
            JOIN sys.dm_xe_sessions s ON se.event_session_address = s.address
            WHERE s.name = '{session_name}'
            ORDER BY se.name
            """

            logger.debug(f"Querying events for session '{session_name}'...")
            cmd = AdomdCommand(query, self.connection)
            reader = cmd.ExecuteReader()

            events = []
            while reader.Read():
                events.append({
                    'name': str(reader.GetValue(0)) if reader.GetValue(0) else '',
                    'package': str(reader.GetValue(1)) if reader.GetValue(1) else '',
                    'predicate': str(reader.GetValue(2)) if reader.GetValue(2) else '',
                })

            reader.Close()

            logger.info(f"✓ Found {len(events)} events in session '{session_name}'")
            return {'success': True, 'session': session_name, 'events': events, 'count': len(events)}

        except Exception as e:
            logger.warning(f"✗ Failed to check session events: {e}")
            return {'success': False, 'error': str(e)}

    def test_dmv_support(self) -> Dict[str, Any]:
        """
        Test which XEvent-related DMVs are supported

        Returns:
            Dictionary with DMV support status
        """
        if not self.connection:
            if not self.connect():
                return {'success': False, 'error': 'Connection failed'}

        dmvs_to_test = [
            ('sys.dm_xe_packages', 'XEvent packages'),
            ('sys.dm_xe_objects', 'XEvent objects (events, actions, targets)'),
            ('sys.dm_xe_sessions', 'Active XEvent sessions'),
            ('sys.dm_xe_session_events', 'Events in sessions'),
            ('sys.dm_xe_session_targets', 'Targets in sessions'),
            ('sys.dm_xe_session_object_columns', 'Object column definitions'),
        ]

        results = {}

        for dmv, description in dmvs_to_test:
            try:
                from Microsoft.AnalysisServices.AdomdClient import AdomdCommand  # type: ignore

                query = f"SELECT TOP 1 * FROM {dmv}"
                cmd = AdomdCommand(query, self.connection)
                reader = cmd.ExecuteReader()

                # Try to read one row
                has_data = reader.Read()
                reader.Close()

                results[dmv] = {
                    'supported': True,
                    'has_data': has_data,
                    'description': description
                }
                logger.debug(f"✓ {dmv}: supported (has_data={has_data})")

            except Exception as e:
                results[dmv] = {
                    'supported': False,
                    'error': str(e),
                    'description': description
                }
                logger.debug(f"✗ {dmv}: not supported - {e}")

        supported_count = sum(1 for r in results.values() if r.get('supported'))
        total_count = len(dmvs_to_test)

        logger.info(f"DMV Support: {supported_count}/{total_count} DMVs supported")

        return {
            'success': True,
            'dmvs': results,
            'supported_count': supported_count,
            'total_count': total_count
        }

    def search_events_by_keyword(self, keyword: str) -> Dict[str, Any]:
        """
        Search for events containing a keyword (case-insensitive)

        Args:
            keyword: Keyword to search for (e.g., 'query', 'vertipaq', 'execution')

        Returns:
            Dictionary with matching events
        """
        result = self.list_available_events()

        if not result.get('success'):
            return result

        events = result.get('events', [])
        keyword_lower = keyword.lower()

        matching = [
            evt for evt in events
            if keyword_lower in evt['name'].lower() or keyword_lower in evt.get('description', '').lower()
        ]

        logger.info(f"Found {len(matching)} events matching '{keyword}'")
        return {'success': True, 'keyword': keyword, 'events': matching, 'count': len(matching)}

    def run_full_diagnostics(self) -> Dict[str, Any]:
        """
        Run comprehensive XEvent diagnostics

        Returns:
            Dictionary with all diagnostic results
        """
        logger.info("=" * 60)
        logger.info("Running Full XEvent Diagnostics")
        logger.info("=" * 60)

        results = {}

        # Test 1: DMV Support
        logger.info("\n[1/5] Testing DMV Support...")
        results['dmv_support'] = self.test_dmv_support()

        # Test 2: Available Packages
        logger.info("\n[2/5] Listing Available Packages...")
        results['packages'] = self.list_available_packages()

        # Test 3: Available Events
        logger.info("\n[3/5] Listing Available Events...")
        results['all_events'] = self.list_available_events()

        # Test 4: Query-related Events
        logger.info("\n[4/5] Searching Query-related Events...")
        results['query_events'] = self.search_events_by_keyword('query')

        # Test 5: Active Sessions
        logger.info("\n[5/5] Listing Active Sessions...")
        results['active_sessions'] = self.list_active_sessions()

        logger.info("\n" + "=" * 60)
        logger.info("Diagnostics Complete")
        logger.info("=" * 60)

        return {'success': True, 'diagnostics': results}
