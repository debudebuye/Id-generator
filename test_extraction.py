#!/usr/bin/env python3
"""
Test script for the new residential PDF extraction method.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.services.id_card_service import IDCardService

class MockDocument:
    """Mock document class for testing."""
    def extract_image(self, image_info):
        return {'image': b'mock_image_data'}

def test_residential_extraction():
    """Test the new residential PDF extraction method."""
    
    # Create the service
    service = IDCardService()
    
    # Sample PDF lines (simulating what would be extracted from a real PDF)
    sample_lines = [
        "1234567890123456",  # FCN
        "አማኑኤል ዳንኤል ሀይሉ",  # Amharic name
        "Amanuel Daniel Hailu",  # English name
        "21/05/1999",  # Gregorian date
        "2007/01/29",  # Ethiopian date
        "ወንድ",  # Gender (Amharic)
        "ኢትዮጵያዊ",  # Nationality (Amharic)
        "አዲስ አበባ | Addis Ababa",  # Region (bilingual)
        "ለሚ ኩራ | Lemi Kura",  # Subcity (bilingual)
        "ወረዳ 03 | Woreda 03",  # Woreda (bilingual)
        "0912345678",  # Phone
    ]
    
    # Mock images list
    mock_images = [(0, "photo"), (1, "qr")]
    
    print("Testing new residential PDF extraction method...")
    print("Sample lines:")
    for i, line in enumerate(sample_lines):
        print(f"  Line {i}: '{line}'")
    
    try:
        # Call the new extraction method with mock document
        result = service._extract_residential_sheger_pdf_data(
            doc=MockDocument(),  # Use mock document instead of None
            lines=sample_lines,
            images=mock_images,
            fin_number="TEST123"
        )
        
        print("\nExtraction results:")
        print(f"  FCN: {result.get('fcn_formatted', 'N/A')}")
        print(f"  Name (Amharic): {result.get('name_am', 'N/A')}")
        print(f"  Name (English): {result.get('name_en', 'N/A')}")
        print(f"  DOB (Gregorian): {result.get('dob_am', 'N/A')}")
        print(f"  DOB (Ethiopian): {result.get('dob_en', 'N/A')}")
        print(f"  Gender (Amharic): {result.get('gender_am', 'N/A')}")
        print(f"  Gender (English): {result.get('gender_en', 'N/A')}")
        print(f"  Nationality (Amharic): {result.get('nationality_am', 'N/A')}")
        print(f"  Nationality (English): {result.get('nationality_en', 'N/A')}")
        print(f"  Phone: {result.get('phone', 'N/A')}")
        print(f"  Region (Amharic): {result.get('region_am', 'N/A')}")
        print(f"  Region (English): {result.get('region_en', 'N/A')}")
        print(f"  Subcity (Amharic): {result.get('subcity_am', 'N/A')}")
        print(f"  Subcity (English): {result.get('subcity_en', 'N/A')}")
        print(f"  Woreda (Amharic): {result.get('woreda_am', 'N/A')}")
        print(f"  Woreda (English): {result.get('woreda_en', 'N/A')}")
        
        # Check if all critical fields were extracted
        critical_fields = ['name_am', 'name_en', 'gender_am', 'gender_en', 
                          'nationality_am', 'nationality_en', 'region_am', 'region_en',
                          'subcity_am', 'subcity_en', 'woreda_am', 'woreda_en']
        
        missing_fields = [field for field in critical_fields if not result.get(field)]
        
        if missing_fields:
            print(f"\n⚠️  Missing fields: {missing_fields}")
        else:
            print("\n✅ All critical fields extracted successfully!")
            
    except Exception as e:
        print(f"\n❌ Error during extraction: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_residential_extraction()
