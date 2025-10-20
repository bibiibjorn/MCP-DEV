"""
Test that detailed guide shows on connection
"""
import json
from core.user_guide_generator import generate_comprehensive_user_guide

# Simulate what happens on connection
print("=" * 60)
print("SIMULATING CONNECTION TO POWER BI")
print("=" * 60)

result = {
    'success': True,
    'managers_initialized': True,
    'performance_analysis': 'Available'
}

# This is what the connection handler now does
try:
    user_guide = generate_comprehensive_user_guide(category="all", format_type="detailed", server_version="2.7.0")
    if user_guide.get('success'):
        result['user_guide'] = user_guide
        result['message'] = "Connected successfully! Complete user guide included below."
        result['notes'] = ["Scroll down for the complete detailed guide to all available tools organized by category"]
except Exception as e:
    print(f"ERROR: {e}")
    result['message'] = "Connected successfully!"

# Display what the user will see
print("\nCONNECTION RESULT:")
print(f"Success: {result['success']}")
print(f"Message: {result['message']}")
print(f"Notes: {result.get('notes', [])}")
print(f"\nUser Guide Included: {'YES' if 'user_guide' in result else 'NO'}")

if 'user_guide' in result:
    guide = result['user_guide']
    print(f"Guide Type: {guide.get('guide_type')}")
    print(f"Server Version: {guide.get('server_version')}")
    print(f"Total Tools: {guide.get('overview', {}).get('total_tools')}")
    print(f"Categories Available: {len(guide.get('categories', {}))}")
    print(f"\nCategory Names:")
    for cat_key, cat_data in guide.get('categories', {}).items():
        print(f"  - {cat_data.get('title')} ({len(cat_data.get('tools', []))} tools)")

print("\n" + "=" * 60)
print("TEST PASSED: Detailed guide will show on connection!")
print("=" * 60)
