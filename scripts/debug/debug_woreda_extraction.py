#!/usr/bin/env python3
"""
Debug script to test woreda extraction from the PDF structure shown in the image.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.services.id_card_service import IDCardService

def test_woreda_extraction():
    """Test woreda extraction with the actual PDF structure."""
    
    # Create the service
    service = IDCardService()
    
    # Sample PDF lines based on the actual structure shown in the image
    sample_lines = [
        "1234567890123456",  # FCN (line 0)
        "ጌቱ አኬሌ ሚጋናው | Getu Akele Miganaw",  # Name (line 1)
        "ክልል/ከተማ አስተዳደር | Region/City Admin",  # Region label (line 2)
        "አዲስ አበባ | Addis Ababa",  # Region value (line 3)
        "የትውልድ ቀን | Date of Birth",  # DOB label (line 4)
        "1988/4/20 | 1995/12/30",  # DOB value (line 5)
        "ዞን/ክፍለ ከተማ | Zone/Sub City",  # Zone label (line 6)
        "ለሚ ኩራ | Lemi Kura",  # Zone/Sub City value (line 7)
        "ፆታ | Sex",  # Sex label (line 8)
        "ወንድ | Male",  # Sex value (line 9)
        "ወረዳ | Woreda",  # Woreda label (line 10)
        "ወረዳ 06 | Woreda 06",  # Woreda value (line 11)
        "ዜግነት | Nationality",  # Nationality label (line 12)
        "ኢትዮጵያዊ | Ethiopian",  # Nationality value (line 13)
        "ስልክ ቁጥር | Phone Number:",  # Phone label (line 14)
        "0913400767",  # Phone value (line 15)
    ]
    
    print("Testing woreda extraction with actual PDF structure...")
    print("Sample lines:")
    for i, line in enumerate(sample_lines):
        print(f"  Line {i}: '{line}'")
    
    print(f"\nCurrent PDF_FORMAT_MAPPING['default']['woreda'] = {service.PDF_FORMAT_MAPPING['default']['woreda']}")
    
    # Test the _parse_line method directly
    woreda_index = service.PDF_FORMAT_MAPPING['default']['woreda']  # Should be 8
    print(f"\nTesting _parse_line with index {woreda_index}:")
    try:
        woreda_am, woreda_en = service._parse_line(sample_lines, woreda_index)
        print(f"Result: '{woreda_am}' | '{woreda_en}'")
    except Exception as e:
        print(f"Error: {e}")
    
    # Test with the correct index (11 based on our updated structure)
    print(f"\nTesting _parse_line with index 11 (actual woreda value line):")
    try:
        woreda_am, woreda_en = service._parse_line(sample_lines, 11)
        print(f"Result: '{woreda_am}' | '{woreda_en}'")
    except Exception as e:
        print(f"Error: {e}")
    
    # Test the pattern-based search
    print(f"\nTesting pattern-based woreda search:")
    found_woreda = False
    for i, line in enumerate(sample_lines):
        if '|' in line:
            parts = line.split('|', 1)
            left = parts[0].strip()
            right = parts[1].strip()
            
            # Look for woreda patterns with numbers
            if (('ወረዳ' in left or 'woreda' in right.lower()) and 
                any(c.isdigit() for c in line)):
                print(f"Found woreda pattern at line {i}: '{left}' | '{right}'")
                found_woreda = True
                break
    
    if not found_woreda:
        print("No woreda pattern found with current logic")

if __name__ == "__main__":
    test_woreda_extraction()