#!/usr/bin/env python3
"""
Test script to demonstrate the automatic cleanup functionality
"""

import os
import sys

# Set the PYTHONPATH to include the current directory
os.environ['PYTHONPATH'] = os.path.dirname(__file__)

# Import the service
from app.services.id_card_service import IDCardService

def test_cleanup():
    """Test the cleanup functionality"""
    print("🧪 Testing ID Card Service Cleanup Functionality")
    print("=" * 50)
    
    # Initialize the service
    service = IDCardService()
    
    # Test manual cleanup
    print("\n1. Testing manual cleanup...")
    service.manual_cleanup()
    
    # Test cleanup with specific files to keep
    print("\n2. Testing cleanup with files to keep...")
    files_to_keep = ['test_file.png', 'important_image.png']
    service.cleanup_old_images(keep_current_files=files_to_keep)
    
    print("\n✅ Cleanup tests completed!")

if __name__ == "__main__":
    test_cleanup()
