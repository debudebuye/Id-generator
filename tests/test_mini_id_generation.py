#!/usr/bin/env python3
"""
Test script to verify mini ID generation produces 4 images
"""

import os
import sys
from app.services.id_card_service import IDCardService

def test_mini_id_generation():
    """Test that mini ID generation produces 4 images (2 front + 2 reverse)"""
    
    # Initialize the service
    service = IDCardService()
    
    # Sample data for testing
    test_data = {
        'name_en': 'Test User',
        'name_am': 'ፈተና ተጠቃሚ',
        'dob_en': '1990/01/01',
        'dob_am': '1982/04/23',
        'gender_en': 'Male',
        'gender_am': 'ወንድ',
        'nationality_en': 'Ethiopian',
        'nationality_am': 'ኢትዮጵያዊ',
        'phone': '0912345678',
        'region_en': 'Addis Ababa',
        'region_am': 'አዲስ አበባ',
        'subcity_en': 'Kolfe Keranio',
        'subcity_am': 'ኮልፌ ከራኒዮ',
        'woreda_en': 'Woreda 01',
        'woreda_am': 'ወረዳ 01',
        'fcn_formatted': '1234 5678 9012 3456',
        'serial_number': '12345678',
        'issue_date_en': '2023/01/01',
        'issue_date_am': '2015/04/23',
        'expiry_date_en': '2033/01/01',
        'expiry_date_am': '2025/04/23',
        'address_en': 'Addis Ababa, Kolfe Keranio, Woreda 01',
        'address_am': 'አዲስ አበባ, ኮልፌ ከራኒዮ, ወረዳ 01'
    }
    
    print("🧪 Testing Mini ID Generation...")
    print(f"Test data: {test_data['name_en']}")
    
    try:
        # Test mini ID generation
        print("\n📋 Generating mini ID cards...")
        result = service.generate_id_card(
            data=test_data,
            city_option='default',
            remove_white=False,
            remove_black=False,
            generate_mini_id=True,  # This should generate 4 images
            generate_old_id=False
        )
        
        print(f"\n✅ Generation completed!")
        print(f"📁 Generated files: {list(result.keys())}")
        
        # Check if we have the expected 4 files
        expected_files = ['mini_front_color', 'mini_front_bw', 'reverse', 'reverse_bw']
        generated_files = [key for key in expected_files if key in result and result[key]]
        
        print(f"\n📊 Results:")
        print(f"Expected files: {expected_files}")
        print(f"Generated files: {generated_files}")
        print(f"Total generated: {len(generated_files)}")
        
        if len(generated_files) == 4:
            print("🎉 SUCCESS: All 4 images generated correctly!")
            print("\n📋 File details:")
            for file_key in generated_files:
                filename = result[file_key]
                file_path = os.path.join(service.config.STATIC_FOLDER, filename)
                if os.path.exists(file_path):
                    file_size = os.path.getsize(file_path) / 1024  # KB
                    print(f"  ✅ {file_key}: {filename} ({file_size:.1f} KB)")
                else:
                    print(f"  ❌ {file_key}: {filename} (file not found)")
        else:
            print(f"❌ FAILED: Expected 4 images, got {len(generated_files)}")
            print(f"Missing files: {set(expected_files) - set(generated_files)}")
            
        return len(generated_files) == 4
        
    except Exception as e:
        print(f"❌ Error during testing: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_mini_id_generation()
    sys.exit(0 if success else 1)

