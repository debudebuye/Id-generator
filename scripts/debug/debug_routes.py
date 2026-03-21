#!/usr/bin/env python3
"""Debug script to test Flask routes"""

import sys
import os

# Add current directory to Python path
sys.path.insert(0, os.getcwd())

print("Testing Flask app creation...")

try:
    from app import create_app
    print("✅ Successfully imported create_app")
    
    app = create_app()
    print("✅ Successfully created app")
    
    print(f"\nAvailable routes:")
    for rule in app.url_map.iter_rules():
        print(f"  {rule.rule} -> {rule.endpoint}")
        
    # Test the specific endpoint
    print(f"\nTesting /api/approved-users endpoint...")
    with app.test_client() as client:
        response = client.get('/api/approved-users')
        print(f"Status code: {response.status_code}")
        print(f"Response: {response.get_json()}")
        
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()












