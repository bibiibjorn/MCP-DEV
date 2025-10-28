#!/usr/bin/env python3
"""
Full test of SE/FE timing capture with actual DAX query execution.
"""
import os
import sys
import time
import logging

# Set up logging
logging.basicConfig(level=logging.DEBUG, format='%(levelname)s - %(name)s - %(message)s')

# Add parent directory to path
script_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(script_dir)
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

from core.infrastructure.connection_manager import ConnectionManager
from core.infrastructure.query_executor import OptimizedQueryExecutor
from core.performance.performance_analyzer import EnhancedAMOTraceAnalyzer

def main():
    print("=== Full SE/FE Timing Test ===\n")

    # Step 1: Connect to Power BI
    print("1. Connecting to Power BI Desktop...")
    cm = ConnectionManager()
    instances = cm.detect_instances()

    if not instances:
        print("ERROR: No Power BI Desktop instances found!")
        return

    instance = instances[0]
    print(f"   Connected to: {instance['connection_string']}\n")

    # Step 2: Connect and create query executor
    print("2. Creating query executor...")
    result = cm.connect(0)
    if not result.get('success'):
        print(f"ERROR: Could not connect: {result.get('error')}")
        return

    connection = cm.get_connection()
    executor = OptimizedQueryExecutor(connection)
    print("   Query executor ready\n")

    # Step 3: Create performance analyzer
    print("3. Setting up performance analyzer...")
    analyzer = EnhancedAMOTraceAnalyzer(instance['connection_string'])

    if not analyzer.connect_amo():
        print("   WARNING: AMO connection failed, trying manual connection...")
        try:
            import clr
            dll_dir = os.path.join(parent_dir, "lib", "dotnet")
            clr.AddReference(os.path.join(dll_dir, "Microsoft.AnalysisServices.dll"))
            from Microsoft.AnalysisServices import Server
            server = Server()
            server.Connect(instance['connection_string'])
            analyzer.amo_server = server
            print("   Manual AMO connection succeeded")
        except Exception as e:
            print(f"   ERROR: Could not connect AMO: {e}")
            return

    # Start trace
    if not analyzer.start_session_trace(executor):
        print("   ERROR: Could not start SessionTrace")
        return

    print("   SessionTrace started\n")

    # Step 4: Execute a simple DAX query
    print("4. Executing DAX query...")
    # First get a table name from the model
    tables_result = executor.validate_and_execute_dax("EVALUATE INFO.TABLES()", top_n=1, bypass_cache=True)
    if tables_result.get('rows'):
        # Get first table name
        first_table = None
        for row in tables_result['rows']:
            table_name = row.get('Name') or row.get('[Name]')
            if table_name:
                first_table = table_name
                break

        if first_table:
            # Use a simple table scan that will trigger SE events
            query = f"EVALUATE {first_table}"
            print(f"   Using table: {first_table}")
        else:
            query = "EVALUATE {{1}}"  # Fallback to simple expression
    else:
        query = "EVALUATE {{1}}"  # Fallback

    print(f"   Query: {query[:100]}...")
    print("   Executing...\n")

    # Take a snapshot before query
    start_idx = analyzer._snapshot_event_index()

    # Execute query
    t0 = time.perf_counter()
    try:
        result = executor.validate_and_execute_dax(query, top_n=0, bypass_cache=True)
        t1 = time.perf_counter()
        elapsed_ms = (t1 - t0) * 1000.0

        print(f"   Query completed in {elapsed_ms:.2f}ms")
        print(f"   Rows returned: {result.get('row_count', 0)}\n")

    except Exception as e:
        print(f"   ERROR executing query: {e}")
        return

    # Step 5: Wait for trace events to arrive
    print("5. Waiting for trace events...")
    time.sleep(3)  # Longer wait to ensure events arrive

    # Get events since query started
    events, _ = analyzer._events_since(start_idx)
    print(f"   Captured {len(events)} events since index {start_idx}")

    # Also check total buffer
    with analyzer._event_lock:
        total_events = len(analyzer._event_buffer)
        print(f"   Total events in buffer: {total_events}\n")

    # Step 6: Analyze events
    print("6. Analyzing events...")
    summary = analyzer._summarize_events(events, elapsed_ms)

    if summary:
        print(f"   Total Duration: {summary['total_ms']}ms")
        print(f"   Storage Engine: {summary['se_ms']}ms ({summary['se_ms'] / max(summary['total_ms'], 1) * 100:.1f}%)")
        print(f"   Formula Engine: {summary['fe_ms']}ms ({summary['fe_ms'] / max(summary['total_ms'], 1) * 100:.1f}%)")
        print(f"\n   Event counts: {summary['counts']}\n")
    else:
        print("   No timing summary available\n")

    # Show individual events
    print("7. Event details:")
    for i, evt in enumerate(events, 1):
        print(f"   Event {i}: {evt['event']} | Duration: {evt['duration_ms']}ms")

    # Stop trace
    analyzer.stop_session_trace()
    print("\n8. Trace stopped")

    # Final verdict
    print("\n=== VERDICT ===")
    if summary and summary['se_ms'] > 0:
        print("SUCCESS: SE/FE timing breakdown is working!")
    elif summary and summary['total_ms'] > 0:
        print("PARTIAL: Total timing captured but no SE events")
    else:
        print("FAILED: No timing data captured")

if __name__ == "__main__":
    main()
