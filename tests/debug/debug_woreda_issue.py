#!/usr/bin/env python3
"""
Debug the woreda extraction issue with the new document structure
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.services.id_card_service import IDCardService

def debug_woreda_extraction():
    """Debug the woreda extraction issue"""
    
    service = IDCardService()
    
    # Based on the new image, the actual structure is:
    sample_lines = [
        "የስነ ሕዝብና መረጃ | Demographics Data",           # Line 0
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
    
    print("=== Current Document Structure ===")
    for i, line in enumerate(sample_lines):
        print(f"  Line {i}: '{line}'")
    
    print(f"\n=== Current Mapping ===")
    mapping = service.PDF_FORMAT_MAPPING['default']
    for key, value in mapping.items():
        if key not in ['photo_img_index', 'qr_img_index']:
            print(f"  {key}: line {value}")
    
    print(f"\n=== Testing Current Extraction ===")
    
    # Test each field
    try:
        name_am, name_en = service._parse_line(sample_lines, mapping['name'])
        print(f"Name (line {mapping['name']}): '{name_am}' | '{name_en}'")
    except Exception as e:
        print(f"Name extraction error: {e}")
    
    try:
        region_am, region_en = service._parse_line(sample_lines, mapping['region'])
        print(f"Region (line {mapping['region']}): '{region_am}' | '{region_en}'")
    except Exception as e:
        print(f"Region extraction error: {e}")
    
    try:
        subcity_am, subcity_en = service._parse_line(sample_lines, mapping['subcity'])
        print(f"Subcity (line {mapping['subcity']}): '{subcity_am}' | '{subcity_en}'")
    except Exception as e:
        print(f"Subcity extraction error: {e}")
    
    try:
        gender_am, gender_en = service._parse_line(sample_lines, mapping['gender'])
        print(f"Gender (line {mapping['gender']}): '{gender_am}' | '{gender_en}'")
    except Exception as e:
        print(f"Gender extraction error: {e}")
    
    try:
        woreda_am, woreda_en = service._parse_line(sample_lines, mapping['woreda'])
        print(f"Woreda (line {mapping['woreda']}): '{woreda_am}' | '{woreda_en}'")
    except Exception as e:
        print(f"Woreda extraction error: {e}")
    
    try:
        nationality_am, nationality_en = service._parse_line(sample_lines, mapping['nationality'])
        print(f"Nationality (line {mapping['nationality']}): '{nationality_am}' | '{nationality_en}'")
    except Exception as e:
        print(f"Nationality extraction error: {e}")
    
    print(f"\n=== Problem Analysis ===")
    print(f"Expected woreda line {mapping['woreda']}: '{sample_lines[mapping['woreda']]}'")
    print(f"But the address shows 'ጾታ | Sex' which is from line 9")
    print(f"This suggests the extraction is getting line 9 instead of line 12")
    
    print(f"\n=== Checking Line Alignment ===")
    expected_mapping = {
        'name': 2,      # "አንሙት ገነት አባሉ | Anmut Genet Abalu"
        'region': 4,    # "አዲስ አበባ | Addis Ababa"  
        'dob': 6,       # "1994/11/19 | 2002/07/26"
        'subcity': 8,   # "የካ | Yeka"
        'gender': 10,   # "ወንድ | Male"
        'woreda': 12,   # "ወረዳ 12 | Woreda 12"
        'nationality': 14, # "ኢትዮጵያዊ | Ethiopian"
        'phone': 16     # "0930620129"
    }
    
    print("Checking if current mapping matches expected:")
    for field, expected_line in expected_mapping.items():
        current_line = mapping.get(field)
        status = "✓" if current_line == expected_line else "✗"
        print(f"  {field}: Expected {expected_line}, Current {current_line} {status}")
        if current_line == expected_line:
            try:
                if field == 'phone':
                    print(f"    Line {expected_line}: '{sample_lines[expected_line]}'")
                else:
                    am, en = service._parse_line(sample_lines, expected_line)
                    print(f"    Line {expected_line}: '{am}' | '{en}'")
            except Exception as e:
                print(f"    Error parsing line {expected_line}: {e}")

if __name__ == "__main__":
    debug_woreda_extraction()