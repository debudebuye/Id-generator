#!/usr/bin/env python3
"""
Debug script to test photo and QR code generation
"""

import os
import sys
from PIL import Image
from io import BytesIO

# Add the app directory to the path
sys.path.append(os.path.join(os.path.dirname(__file__), 'app'))

# Set up the environment for relative imports
os.environ['PYTHONPATH'] = os.path.join(os.path.dirname(__file__), 'app')

from app.services.id_card_service import IDCardService

def test_photo_qr_generation():
    """Test photo and QR code generation"""
    print("=== Testing Photo and QR Code Generation ===")
    
    # Initialize the service
    service = IDCardService()
    
    # Test data
    test_data = {
        'name_en': 'Test User',
        'fcn_full': '1234567890123456',
        'dob_en': '1990/01/01',
        'gender_en': 'Male',
        'phone': '+251 911 123 456',
        'region_en': 'Addis Ababa',
        'subcity_en': 'Lemi Kura',
        'woreda_en': 'Woreda 01',
        'nationality_en': 'Ethiopian'
    }
    
    print("1. Testing get_photo_data method...")
    try:
        photo_bytes = service.get_photo_data(test_data)
        print(f"   Photo bytes length: {len(photo_bytes)}")
        
        # Try to open the photo bytes as an image
        photo_img = Image.open(BytesIO(photo_bytes))
        print(f"   Photo image size: {photo_img.size}")
        print(f"   Photo image mode: {photo_img.mode}")
        
        # Save test photo
        test_photo_path = os.path.join(service.config.STATIC_FOLDER, 'test_photo.png')
        photo_img.save(test_photo_path)
        print(f"   Test photo saved to: {test_photo_path}")
        
    except Exception as e:
        print(f"   Error in get_photo_data: {str(e)}")
    
    print("\n2. Testing generate_qr_code method...")
    try:
        qr_bytes = service.generate_qr_code(test_data)
        print(f"   QR bytes length: {len(qr_bytes)}")
        
        # Try to open the QR bytes as an image
        qr_img = Image.open(BytesIO(qr_bytes))
        print(f"   QR image size: {qr_img.size}")
        print(f"   QR image mode: {qr_img.mode}")
        
        # Save test QR
        test_qr_path = os.path.join(service.config.STATIC_FOLDER, 'test_qr.png')
        qr_img.save(test_qr_path)
        print(f"   Test QR saved to: {test_qr_path}")
        
    except Exception as e:
        print(f"   Error in generate_qr_code: {str(e)}")
    
    print("\n3. Testing photo processing...")
    try:
        from app.utils.image_utils import process_photo
        
        if os.path.exists(test_photo_path):
            processed_photo = process_photo(test_photo_path, (550, 700))
            print(f"   Processed photo size: {processed_photo.size}")
            print(f"   Processed photo mode: {processed_photo.mode}")
            
            # Save processed photo
            processed_photo_path = os.path.join(service.config.STATIC_FOLDER, 'test_processed_photo.png')
            processed_photo.save(processed_photo_path)
            print(f"   Processed photo saved to: {processed_photo_path}")
        else:
            print("   Test photo file not found")
            
    except Exception as e:
        print(f"   Error in photo processing: {str(e)}")
    
    print("\n4. Checking static folder...")
    static_folder = service.config.STATIC_FOLDER
    print(f"   Static folder: {static_folder}")
    if os.path.exists(static_folder):
        files = os.listdir(static_folder)
        print(f"   Files in static folder: {files}")
    else:
        print("   Static folder does not exist")
    
    print("\n=== Debug Test Complete ===")

if __name__ == "__main__":
    test_photo_qr_generation()
