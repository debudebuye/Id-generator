#!/usr/bin/env python3
"""
Debug script for default format PDF extraction
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.services.id_card_service import IDCardService
import fitz

def debug_pdf_extraction():
    """Debug the PDF extraction for default format"""
    
    # Initialize service
    service = IDCardService()
    
    print("=== PDF Format Mapping Debug ===")
    print("Current default format mapping:")
    for key, value in service.PDF_FORMAT_MAPPING['default'].items():
        print(f"  {key}: {value}")
    
    print("\n=== Expected PDF Structure ===")
    expected_lines = [
        "Line 0: FCN or Demographics header",
        "Line 1: Name label (ሙሉ ስም | First, Middle, Surname)",
        "Line 2: Name value (ዘውዱ ተፈሪ አባተ | Zewudu Teferi Abate)",
        "Line 3: Region label (ክልል/ከተማ አስተዳደር | Region/City Admin)",
        "Line 4: Region value (አማራ | Amhara)",
        "Line 5: DOB label (የትውልድ ዘመን | Date of Birth)",
        "Line 6: DOB value (1995/9/1 | 2003/05/09)",
        "Line 7: Subcity label (ዞን/ክፍለ ከተማ | Zone/Sub City)",
        "Line 8: Subcity value (ምስራቅ ጎጃም ዞን | East Gojjam Zone)",
        "Line 9: Gender label (ጾታ | Sex)",
        "Line 10: Gender value (ወንድ | Male)",
        "Line 11: Woreda label (ወረዳ | Woreda)",
        "Line 12: Woreda value (ደብረ ማርቆስ | Debre Markos)",
        "Line 13: Nationality label (ዜግነት | Nationality)",
        "Line 14: Nationality value (ኢትዮጵያዊ | Ethiopian)",
        "Line 15: Phone label (ስልክ ቁጥር | Phone Number)",
        "Line 16: Phone value (0928978013)"
    ]
    
    for line in expected_lines:
        print(f"  {line}")
    
    print("\n=== Mapping Validation ===")
    mapping = service.PDF_FORMAT_MAPPING['default']
    print(f"Name should be at line 2, mapped to: {mapping['name']}")
    print(f"Region should be at line 4, mapped to: {mapping['region']}")
    print(f"DOB should be at line 6, mapped to: {mapping['dob']}")
    print(f"Subcity should be at line 8, mapped to: {mapping['subcity']}")
    print(f"Gender should be at line 10, mapped to: {mapping['gender']}")
    print(f"Woreda should be at line 12, mapped to: {mapping['woreda']}")
    print(f"Nationality should be at line 14, mapped to: {mapping['nationality']}")
    print(f"Phone should be at line 16, mapped to: {mapping['phone']}")
    
    # Check if mapping is correct
    correct_mapping = {
        'name': 2,
        'region': 4,
        'dob': 6,
        'subcity': 8,
        'gender': 10,
        'woreda': 12,
        'nationality': 14,
        'phone': 16
    }
    
    print("\n=== Mapping Correctness Check ===")
    all_correct = True
    for field, expected_line in correct_mapping.items():
        actual_line = mapping.get(field)
        status = "✓" if actual_line == expected_line else "✗"
        print(f"  {field}: Expected {expected_line}, Got {actual_line} {status}")
        if actual_line != expected_line:
            all_correct = False
    
    if all_correct:
        print("\n✅ All mappings are correct!")
    else:
        print("\n❌ Some mappings need correction!")
    
    print("\n=== Test with Sample Data ===")
    sample_lines = [
        "የስነ ሕዝብና መረጃ | Demographics Data",
        "ሙሉ ስም | First, Middle, Surname", 
        "ዘውዱ ተፈሪ አባተ | Zewudu Teferi Abate",
        "ክልል/ከተማ አስተዳደር | Region/City Admin",
        "አማራ | Amhara",
        "የትውልድ ዘመን | Date of Birth",
        "1995/9/1 | 2003/05/09",
        "ዞን/ክፍለ ከተማ | Zone/Sub City",
        "ምስራቅ ጎጃም ዞን | East Gojjam Zone",
        "ጾታ | Sex",
        "ወንድ | Male",
        "ወረዳ | Woreda",
        "ደብረ ማርቆስ | Debre Markos",
        "ዜግነት | Nationality",
        "ኢትዮጵያዊ | Ethiopian",
        "ስልክ ቁጥር | Phone Number",
        "0928978013"
    ]
    
    print("Sample lines:")
    for i, line in enumerate(sample_lines):
        print(f"  Line {i}: '{line}'")
    
    print("\nTesting _parse_line method:")
    for field, line_idx in mapping.items():
        if field in ['photo_img_index', 'qr_img_index']:
            continue
        try:
            am, en = service._parse_line(sample_lines, line_idx)
            print(f"  {field} (line {line_idx}): '{am}' | '{en}'")
        except Exception as e:
            print(f"  {field} (line {line_idx}): ERROR - {str(e)}")

if __name__ == "__main__":
    debug_pdf_extraction()