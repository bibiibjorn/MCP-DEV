#!/usr/bin/env python3
"""
Test script to verify SessionTrace event subscription works.
"""
import os
import sys
import time

# Add parent directory to path
script_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(script_dir)
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

from core.infrastructure.connection_manager import ConnectionManager
from core.performance.performance_analyzer import EnhancedAMOTraceAnalyzer

def main():
    print("=== Testing SessionTrace Event Subscription ===\n")

    # Step 1: Detect Power BI instances
    print("1. Detecting Power BI Desktop instances...")
    cm = ConnectionManager()
    instances = cm.detect_instances()

    if not instances:
        print("ERROR: No Power BI Desktop instances found!")
        print("Please open Power BI Desktop with a .pbix file and try again.")
        return

    print(f"   Found {len(instances)} instance(s)")
    instance = instances[0]
    print(f"   Using: {instance['connection_string']}\n")

    # Step 2: Create analyzer and connect AMO
    print("2. Connecting to AMO...")
    analyzer = EnhancedAMOTraceAnalyzer(instance['connection_string'])

    if not analyzer.connect_amo():
        print("ERROR: Failed to connect AMO")
        print(f"   Reason: {analyzer.amo_server}")
        # Try manually
        try:
            import clr
            dll_dir = os.path.join(parent_dir, "lib", "dotnet")
            clr.AddReference(os.path.join(dll_dir, "Microsoft.AnalysisServices.dll"))
            from Microsoft.AnalysisServices import Server

            server = Server()
            print(f"   Trying to connect to: {instance['connection_string']}")
            server.Connect(instance['connection_string'])
            print("   Manual connection succeeded!")
            analyzer.amo_server = server
        except Exception as e:
            print(f"   Manual connection also failed: {e}")
            import traceback
            traceback.print_exc()
            return

    print("   AMO connected successfully\n")

    # Step 3: Check SessionTrace availability
    print("3. Checking SessionTrace availability...")
    trace = analyzer._get_session_trace()

    if trace is None:
        print("ERROR: SessionTrace not available")
        return

    print("   SessionTrace object obtained\n")

    # Step 4: Try to subscribe to events
    print("4. Attempting event subscription...")

    try:
        # Import the TraceEventClass
        import clr
        dll_dir = os.path.join(parent_dir, "lib", "dotnet")
        clr.AddReference(os.path.join(dll_dir, "Microsoft.AnalysisServices.dll"))
        from Microsoft.AnalysisServices import TraceEventClass

        # Check if trace has Events collection
        if not hasattr(trace, 'Events'):
            print("ERROR: SessionTrace doesn't have Events collection")
            return

        print(f"   Events collection exists: {trace.Events}")
        print(f"   Current event count: {trace.Events.Count}")

        # Try to clear and add events
        try:
            trace.Events.Clear()
            print("   Cleared existing events")
        except Exception as e:
            print(f"   WARNING: Cannot clear events: {e}")

        # Subscribe to events one by one
        events_to_add = [
            ('QueryEnd', TraceEventClass.QueryEnd),
            ('VertiPaqSEQueryEnd', TraceEventClass.VertiPaqSEQueryEnd),
            ('VertiPaqSEQueryCacheMatch', TraceEventClass.VertiPaqSEQueryCacheMatch),
            ('VertiPaqSEQueryCacheMiss', TraceEventClass.VertiPaqSEQueryCacheMiss),
            ('QuerySubcube', TraceEventClass.QuerySubcube),
            ('QuerySubcubeVerbose', TraceEventClass.QuerySubcubeVerbose),
        ]

        for event_name, event_class in events_to_add:
            try:
                trace.Events.Add(event_class)
                print(f"   [OK] Added {event_name}")
            except Exception as e:
                print(f"   [FAIL] Could not add {event_name}: {e}")

        print(f"\n   Final event count: {trace.Events.Count}")

        # Try to update the trace
        try:
            trace.Update()
            print("   [OK] Trace.Update() succeeded")
        except Exception as e:
            print(f"   [FAIL] Trace.Update() failed: {e}")

        # Try to start the trace
        print("\n5. Starting trace...")
        try:
            if trace.IsStarted:
                trace.Stop()
                print("   Stopped existing trace")

            trace.Start()
            print("   [OK] Trace started successfully")
            print(f"   IsStarted: {trace.IsStarted}")

            # Let it run briefly
            print("\n6. Trace is running. Waiting 2 seconds...")
            time.sleep(2)

            # Stop the trace
            trace.Stop()
            print("   Trace stopped\n")

        except Exception as e:
            print(f"   [FAIL] Could not start trace: {e}")
            import traceback
            traceback.print_exc()

    except Exception as e:
        print(f"ERROR during event subscription: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
