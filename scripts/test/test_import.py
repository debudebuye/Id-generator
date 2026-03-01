#!/usr/bin/env python3
"""Test script to debug import issues"""

import sys
import os

print("Python path:")
for path in sys.path:
    print(f"  {path}")

print(f"\nCurrent working directory: {os.getcwd()}")

print(f"\nFiles in current directory:")
for item in os.listdir('.'):
    print(f"  {item}")

print(f"\nFiles in app directory:")
if os.path.exists('app'):
    for item in os.listdir('app'):
        print(f"  {item}")

print(f"\nTrying to import app module...")
try:
    from app import create_app
    print("✅ Successfully imported create_app")
    
    app = create_app()
    print("✅ Successfully created app")
    
    print(f"\nAvailable routes:")
    for rule in app.url_map.iter_rules():
        print(f"  {rule.rule} -> {rule.endpoint}")
        
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()












