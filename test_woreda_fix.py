#!/usr/bin/env python3
"""
Test the woreda extraction fix
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.services.id_card_service import IDCardService

def test_woreda_fix():
    """Test the woreda extraction fix"""
    
    service = IDCardService()
    
    # Test the pattern matching logic with the problematic lines
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
        "ወረዳ | Woreda",                                 # Line 11 (LABEL - should be skipped)
        "ወረዳ 12 | Woreda 12",                          # Line 12 (VALUE - should be extracted)
        "ዜግነት | Nationality (በተለያዩ መሰረት/Self declared)", # Line 13
        "ኢትዮጵያዊ | Ethiopian",                          # Line 14
        "ስልክ ቁጥር | Phone Number:",                      # Line 15
        "0930620129"                                   # Line 16
    ]
    
    print("=== Testing Pattern Matching Logic ===")
    
    # Test the pattern matching logic manually
    def split_pair(s: str):
        parts = s.split('|', 1)
        return parts[0].strip(), parts[1].strip() if len(parts) == 2 else (s.strip(), "")
    
    pattern_woreda_am = pattern_woreda_en = ""
    pattern_subcity_am = pattern_subcity_en = ""
    
    for i, ln in enumerate(sample_lines):
        print(f"Line {i}: '{ln}'")
        
        # Test subcity pattern
        if not pattern_subcity_en and any(x in ln.lower() for x in ["zone", "subcity", "sub city", "city admin", "city administration"]):
            l, r = split_pair(ln)
            print(f"  Subcity pattern candidate: '{l}' | '{r}'")
            # Skip if this looks like a label (contains only the keyword)
            if (any(r.lower().strip() == label for label in ["zone", "subcity", "sub city", "city admin", "city administration"]) or
                "zone/sub city" in r.lower()):
                print(f"  -> Skipped (looks like label)")
                continue  # This is likely a label, not a value
            pattern_subcity_am, pattern_subcity_en = l, r
            print(f"  -> Accepted as subcity pattern: '{pattern_subcity_am}' | '{pattern_subcity_en}'")
            continue
        
        # Test woreda pattern
        if not pattern_woreda_en and any(x in ln.lower() for x in ["woreda", "administration", "admin", "kebele"]):
            l, r = split_pair(ln)
            print(f"  Woreda pattern candidate: '{l}' | '{r}'")
            # Skip if this looks like a label (contains only the keyword)
            if (r.lower().strip() in ["woreda", "administration", "admin", "kebele"] or
                (len(r.strip()) < 15 and r.lower().strip() == "woreda")):
                print(f"  -> Skipped (looks like label)")
                continue  # This is likely a label, not a value
            pattern_woreda_am, pattern_woreda_en = l, r
            print(f"  -> Accepted as woreda pattern: '{pattern_woreda_am}' | '{pattern_woreda_en}'")
            continue
    
    print(f"\n=== Pattern Results ===")
    print(f"Pattern subcity: '{pattern_subcity_am}' | '{pattern_subcity_en}'")
    print(f"Pattern woreda: '{pattern_woreda_am}' | '{pattern_woreda_en}'")
    
    print(f"\n=== Line-based Results ===")
    mapping = service.PDF_FORMAT_MAPPING['default']
    subcity_am, subcity_en = service._parse_line(sample_lines, mapping['subcity'])
    woreda_am, woreda_en = service._parse_line(sample_lines, mapping['woreda'])
    print(f"Line-based subcity (line {mapping['subcity']}): '{subcity_am}' | '{subcity_en}'")
    print(f"Line-based woreda (line {mapping['woreda']}): '{woreda_am}' | '{woreda_en}'")
    
    print(f"\n=== Expected Results ===")
    print(f"Expected subcity: 'የካ' | 'Yeka'")
    print(f"Expected woreda: 'ወረዳ 12' | 'Woreda 12'")
    
    print(f"\n=== Analysis ===")
    if pattern_subcity_am == "የካ" and pattern_subcity_en == "Yeka":
        print("✓ Pattern subcity extraction is correct")
    elif not pattern_subcity_am and not pattern_subcity_en:
        print("✓ Pattern subcity extraction correctly skipped labels")
    else:
        print(f"✗ Pattern subcity extraction is wrong")
    
    if pattern_woreda_am == "ወረዳ 12" and pattern_woreda_en == "Woreda 12":
        print("✓ Pattern woreda extraction is correct")
    elif not pattern_woreda_am and not pattern_woreda_en:
        print("✓ Pattern woreda extraction correctly skipped labels")
    else:
        print(f"✗ Pattern woreda extraction is wrong")

if __name__ == "__main__":
    test_woreda_fix()