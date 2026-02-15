#!/usr/bin/env python3
"""
Test the complete extraction with the fixes
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.services.id_card_service import IDCardService
import fitz
from io import BytesIO

def test_complete_extraction():
    """Test the complete extraction process"""
    
    service = IDCardService()
    
    # Simulate the actual PDF structure from your image
    sample_lines = [
        "3084567890123456",                             # Line 0 - FCN (will be found by fallback)
        "ሙሉ ስም | First, Middle, Surname",                # Line 1  
        "አንሙት ገነት አባሉ | Anmut Genet Abalu",             # Line 2
        "ክልል/ከተማ አስተዳደር | Region/City Admin",            # Line 3
        "አዲስ አበባ | Addis Ababa",                        # Line 4
        "የትውልድ ዘመን | Date of Birth",                    # Line 5
        "1994/11/19 | 2002/07/26",                     # Line 6
        "ዞን/ክፍለ ከተማ | Zone/Sub City",                   # Line 7
        "የካ | Yeka",                                    # Line 8
        "ጾታ | Sex",                                     # Line 9
        "ወንድ | Male",                                   # Line 10
        "ወረዳ | Woreda",                                 # Line 11
        "ወረዳ 12 | Woreda 12",                          # Line 12
        "ዜግነት | Nationality (በተለያዩ መሰረት/Self declared)", # Line 13
        "ኢትዮጵያዊ | Ethiopian",                          # Line 14
        "ስልክ ቁጥር | Phone Number:",                      # Line 15
        "0930620129"                                   # Line 16
    ]
    
    print("=== Simulating Complete Extraction ===")
    
    # Create a mock document
    class MockDoc:
        def __init__(self, lines):
            self.lines = lines
        def close(self):
            pass
    
    # Create mock images list
    images = [(0, 0, 0, 0, 0, 0, 0), (1, 1, 1, 1, 1, 1, 1), (2, 2, 2, 2, 2, 2, 2)]
    
    try:
        # Call the actual extraction method
        extracted = service._extract_default_pdf_data(MockDoc(sample_lines), sample_lines, images, "3084-5678-9012-3456")
        
        print(f"\n=== Extraction Results ===")
        for key, value in extracted.items():
            print(f"  {key}: '{value}'")
        
        print(f"\n=== Address Analysis ===")
        print(f"Region AM: '{extracted.get('region_am', 'NOT_FOUND')}'")
        print(f"Region EN: '{extracted.get('region_en', 'NOT_FOUND')}'")
        print(f"Subcity AM: '{extracted.get('subcity_am', 'NOT_FOUND')}'")
        print(f"Subcity EN: '{extracted.get('subcity_en', 'NOT_FOUND')}'")
        print(f"Woreda AM: '{extracted.get('woreda_am', 'NOT_FOUND')}'")
        print(f"Woreda EN: '{extracted.get('woreda_en', 'NOT_FOUND')}'")
        
        print(f"\n=== Expected vs Actual ===")
        expected = {
            'region_am': 'አዲስ አበባ',
            'region_en': 'Addis Ababa',
            'subcity_am': 'የካ',
            'subcity_en': 'Yeka',
            'woreda_am': 'ወረዳ 12',
            'woreda_en': 'Woreda 12'
        }
        
        all_correct = True
        for key, expected_value in expected.items():
            actual_value = extracted.get(key, 'NOT_FOUND')
            status = "✓" if actual_value == expected_value else "✗"
            print(f"  {key}: Expected '{expected_value}', Got '{actual_value}' {status}")
            if actual_value != expected_value:
                all_correct = False
        
        if all_correct:
            print(f"\n✅ All address extractions are correct!")
        else:
            print(f"\n❌ Some address extractions need attention!")
            
    except Exception as e:
        print(f"Error during extraction: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_complete_extraction()