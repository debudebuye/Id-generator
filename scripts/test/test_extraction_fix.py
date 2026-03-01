#!/usr/bin/env python3
"""
Test the extraction fix with a sample PDF structure
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.services.id_card_service import IDCardService
from io import BytesIO
import fitz

def test_extraction():
    """Test the extraction with the corrected mapping"""
    
    service = IDCardService()
    
    # Create a mock PDF structure that matches your document
    sample_lines = [
        "3084567890123456",  # FCN number (line 0)
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
    
    print("=== Testing Extraction with Fixed Mapping ===")
    print("Sample lines:")
    for i, line in enumerate(sample_lines):
        print(f"  Line {i}: '{line}'")
    
    # Test the extraction logic manually
    mapping = service.PDF_FORMAT_MAPPING['default']
    
    print(f"\n=== Extraction Results ===")
    
    # FCN
    fcn_raw = sample_lines[mapping['fcn']].strip()
    fcn = ''.join(ch for ch in fcn_raw if ch.isdigit())
    print(f"FCN (line {mapping['fcn']}): '{fcn_raw}' -> '{fcn}'")
    
    # Name
    name_am, name_en = service._parse_line(sample_lines, mapping['name'])
    print(f"Name (line {mapping['name']}): '{name_am}' | '{name_en}'")
    
    # Region
    region_am, region_en = service._parse_line(sample_lines, mapping['region'])
    print(f"Region (line {mapping['region']}): '{region_am}' | '{region_en}'")
    
    # DOB
    dob_am, dob_en = service._parse_line(sample_lines, mapping['dob'])
    print(f"DOB (line {mapping['dob']}): '{dob_am}' | '{dob_en}'")
    
    # Subcity
    subcity_am, subcity_en = service._parse_line(sample_lines, mapping['subcity'])
    print(f"Subcity (line {mapping['subcity']}): '{subcity_am}' | '{subcity_en}'")
    
    # Gender
    gender_am, gender_en = service._parse_line(sample_lines, mapping['gender'])
    print(f"Gender (line {mapping['gender']}): '{gender_am}' | '{gender_en}'")
    
    # Woreda
    woreda_am, woreda_en = service._parse_line(sample_lines, mapping['woreda'])
    print(f"Woreda (line {mapping['woreda']}): '{woreda_am}' | '{woreda_en}'")
    
    # Nationality
    nationality_am, nationality_en = service._parse_line(sample_lines, mapping['nationality'])
    print(f"Nationality (line {mapping['nationality']}): '{nationality_am}' | '{nationality_en}'")
    
    # Phone
    phone_am, phone_en = service._parse_line(sample_lines, mapping['phone'])
    print(f"Phone (line {mapping['phone']}): '{phone_am}' | '{phone_en}'")
    
    print(f"\n=== Expected vs Actual ===")
    expected = {
        'fcn': '3084567890123456',
        'name_am': 'ዘውዱ ተፈሪ አባተ',
        'name_en': 'Zewudu Teferi Abate',
        'region_am': 'አማራ',
        'region_en': 'Amhara',
        'subcity_am': 'ምስራቅ ጎጃም ዞን',
        'subcity_en': 'East Gojjam Zone',
        'woreda_am': 'ደብረ ማርቆስ',
        'woreda_en': 'Debre Markos',
        'nationality_am': 'ኢትዮጵያዊ',
        'nationality_en': 'Ethiopian',
        'phone': '0928978013'
    }
    
    actual = {
        'fcn': fcn,
        'name_am': name_am,
        'name_en': name_en,
        'region_am': region_am,
        'region_en': region_en,
        'subcity_am': subcity_am,
        'subcity_en': subcity_en,
        'woreda_am': woreda_am,
        'woreda_en': woreda_en,
        'nationality_am': nationality_am,
        'nationality_en': nationality_en,
        'phone': phone_am
    }
    
    all_correct = True
    for key in expected:
        status = "✓" if actual[key] == expected[key] else "✗"
        print(f"  {key}: Expected '{expected[key]}', Got '{actual[key]}' {status}")
        if actual[key] != expected[key]:
            all_correct = False
    
    if all_correct:
        print(f"\n✅ All extractions are correct!")
    else:
        print(f"\n❌ Some extractions need attention!")

if __name__ == "__main__":
    test_extraction()