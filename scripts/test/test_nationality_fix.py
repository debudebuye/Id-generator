#!/usr/bin/env python3
"""
Test script to verify nationality extraction fix
"""

# Mock test data based on the image provided
test_lines = [
    "FAN:41320659642877549",
    "ሙሉ ስም | First, Middle, Surname",
    "ልደት አያለው ተናው | Lidetu Ayalew Tenaw",
    "ክልል/ከተማ አስተዳደር | Region/City Admin",
    "አዲስ አበባ | Addis Ababa",
    "የትውልድ ዓመት | Date of Birth",
    "1997/5/15 | 2005/01/27",
    "ዞን/ክፍለ ከተማ | Zone/Sub City",
    "ለሚ ኩራ | Lemi Kura",
    "ፆታ | Sex",
    "ወንድ | Male",
    "ወረዳ | Woreda",
    "ወረዳ 06 | Woreda 06",
    "ዜግነት | Nationality (በተለያዩ መሰረት/Self declared)",
    "ኢትዮጵያዊ | Ethiopian",
    "",
    "ስልክ ቁጥር | Phone Number:",
    "0938079636"
]

def test_nationality_extraction():
    """Test the nationality extraction logic"""
    print("Testing nationality extraction with mock data...")
    print(f"Total lines: {len(test_lines)}")
    print("\nLines around nationality:")
    for i, line in enumerate(test_lines):
        if i >= 10 and i <= 16:
            print(f"  Line {i}: '{line}'")
    
    # Test the label detection
    nationality_label_line = "ዜግነት | Nationality (በተለያዩ መሰረት/Self declared)"
    nationality_value_line = "ኢትዮጵያዊ | Ethiopian"
    
    print(f"\nLabel line: '{nationality_label_line}'")
    print(f"Value line: '{nationality_value_line}'")
    
    # Check if our improved logic would detect these correctly
    def looks_like_label(text: str) -> bool:
        t = text.lower()
        return (("nationality" in t) or ("ዜግነት" in t) or 
               ("(amharic)" in t and "nationality" in t) or 
               ("(english)" in t and "nationality" in t) or
               ("self declared" in t) or ("በተለያዩ መሰረት" in t))
    
    def is_valid_nationality_value(text):
        """Simplified version of the validation function"""
        if not text or len(text.strip()) == 0:
            return False
        
        text = text.strip()
        
        # Basic length check
        if len(text) < 2 or len(text) > 50:
            return False
        
        # Should not contain numbers
        if any(char.isdigit() for char in text):
            return False
        
        # Skip lines that are clearly not nationality values
        excluded_keywords = [
            "ክልል", "region", "ወረዳ", "woreda", "ከተማ", "city", "ስልክ", "phone", 
            "የትውልድ", "birth", "ቀን", "date", "ፕሮግራም", "program", "ፆታ", "sex",
            "መታወቂያ", "identity", "addis", "ababa", "zone", "kebele", "address", 
            "number", "card", "id", "self declared", "በተለያዩ መሰረት"
        ]
        
        text_lower = text.lower()
        if text_lower.strip() in excluded_keywords:
            return False
        
        return True
    
    print(f"\nLabel detection test:")
    print(f"  '{nationality_label_line}' -> {looks_like_label(nationality_label_line)}")
    print(f"  '{nationality_value_line}' -> {looks_like_label(nationality_value_line)}")
    
    print(f"\nValue validation test:")
    print(f"  'ኢትዮጵያዊ' -> {is_valid_nationality_value('ኢትዮጵያዊ')}")
    print(f"  'Ethiopian' -> {is_valid_nationality_value('Ethiopian')}")
    print(f"  'Nationality (በተለያዩ መሰረት/Self declared)' -> {is_valid_nationality_value('Nationality (በተለያዩ መሰረት/Self declared)')}")
    
    # Simulate the extraction process
    print(f"\nSimulating extraction process:")
    for i, line in enumerate(test_lines):
        if looks_like_label(line):
            print(f"  Found nationality label at line {i}: '{line}'")
            # Check next few lines
            for j in range(i + 1, min(i + 4, len(test_lines))):
                candidate = test_lines[j].strip()
                if not candidate:
                    continue
                print(f"    Checking line {j}: '{candidate}'")
                if "|" in candidate:
                    left, right = [p.strip() for p in candidate.split("|", 1)]
                    if is_valid_nationality_value(left) and is_valid_nationality_value(right):
                        print(f"    ✅ Found valid nationality: '{left}' | '{right}'")
                        return left, right
                elif is_valid_nationality_value(candidate):
                    print(f"    ✅ Found valid nationality: '{candidate}'")
                    return candidate, candidate
    
    print("  ❌ No nationality found")
    return "", ""

if __name__ == "__main__":
    test_nationality_extraction()