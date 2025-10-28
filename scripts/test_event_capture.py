#!/usr/bin/env python3
"""
Test to capture actual trace events and see what EventClass returns.
"""
import os
import sys
import time
import threading

# Add parent directory to path
script_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(script_dir)
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

from core.infrastructure.connection_manager import ConnectionManager

def main():
    print("=== Testing Actual Trace Event Capture ===\n")

    # Step 1: Detect Power BI instances
    print("1. Detecting Power BI Desktop instances...")
    cm = ConnectionManager()
    instances = cm.detect_instances()

    if not instances:
        print("ERROR: No Power BI Desktop instances found!")
        return

    instance = instances[0]
    print(f"   Using: {instance['connection_string']}\n")

    # Step 2: Connect AMO and set up trace
    try:
        import clr
        dll_dir = os.path.join(parent_dir, "lib", "dotnet")
        clr.AddReference(os.path.join(dll_dir, "Microsoft.AnalysisServices.dll"))
        from Microsoft.AnalysisServices import Server

        server = Server()
        server.Connect(instance['connection_string'])
        print("2. AMO connected\n")

        # Get SessionTrace
        trace = server.SessionTrace
        print("3. Got SessionTrace\n")

        # Set up event buffer and handler
        events_captured = []
        lock = threading.Lock()

        def on_event(sender, args):
            try:
                event_class = args.EventClass
                event_class_str = str(event_class)
                event_class_name = event_class.ToString() if hasattr(event_class, 'ToString') else str(event_class)

                duration = getattr(args, "Duration", 0)
                text_data = str(getattr(args, "TextData", "") or "")[:100]  # First 100 chars

                record = {
                    "EventClass": event_class_str,
                    "EventClass_Name": event_class_name,
                    "EventClass_Type": str(type(event_class)),
                    "Duration": duration,
                    "TextData": text_data
                }

                with lock:
                    events_captured.append(record)
                    print(f"   Event: {event_class_name} | Duration: {duration}ms | Text: {text_data[:50]}")

            except Exception as e:
                print(f"   Error in handler: {e}")

        # Attach handler
        trace.OnEvent += on_event
        print("4. Event handler attached\n")

        # Start trace
        if trace.IsStarted:
            trace.Stop()

        trace.Start()
        print("5. Trace started. Now execute a query in Power BI Desktop...\n")
        print("   Listening for 15 seconds...\n")

        # Wait for events
        time.sleep(15)

        # Stop trace
        trace.Stop()
        print("\n6. Trace stopped\n")

        # Show summary
        print("=== CAPTURED EVENTS ===\n")
        with lock:
            if not events_captured:
                print("No events captured!")
            else:
                print(f"Total events: {len(events_captured)}\n")
                for i, evt in enumerate(events_captured[:10], 1):
                    print(f"Event {i}:")
                    for key, value in evt.items():
                        print(f"  {key}: {value}")
                    print()

                if len(events_captured) > 10:
                    print(f"... and {len(events_captured) - 10} more events")

    except Exception as e:
        print(f"ERROR: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
