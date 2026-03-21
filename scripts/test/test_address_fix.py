#!/usr/bin/env python3
"""
Test the improved address extraction logic
"""

def test_label_based_extraction():
    # Sample lines from the latest PDF structure shown in the image
    sample_lines = [
        "የስነ ሕዝብ መረጃ | Demographics Data",
        "መጀመሪያ ስም | First, Middle, Surname", 
        "ደርበው መለሰ ከበደ | Derbew Melese Kebede",
        "ክልል/ከተማ አስተዳደር | Region/City Admin",
        "አማራ | Amhara",
        "የትውልድ ቀን | Date of Birth",
        "1988/5/17 | 1996/01/26",
        "ዞን/ክፍለ ከተማ | Zone/Sub City",
        "ደቡብ ወሎ ዞን | South Wollo Zone",
        "ፆታ | Sex",
        "ወንድ | Male",
        "ወረዳ | Woreda",
        "ደላንታ | Delanta",
        "ዜግነት | Nationality (በተለያዩ መሰረት/Self declared)",
        "ኢትዮጵያዊ | Ethiopian",
        "ስልክ ቁጥር | Phone Number:",
        "0925199790"
    ]
    
    print("Testing improved label-based address extraction:")
    print("=" * 60)
    
    # Initialize address variables
    region_am, region_en = "", ""
    subcity_am, subcity_en = "", ""
    woreda_am, woreda_en = "", ""
    
    # Use label-based extraction - look for specific labels and extract the next line
    i = 0
    while i < len(sample_lines):
        line = sample_lines[i].strip().lower()
        original_line = sample_lines[i].strip()
        
        # Check for region label
        if ('region' in line and ('city' in line or 'admin' in line)) or ('ክልል' in original_line and ('ከተማ' in original_line or 'አስተዳደር' in original_line)):
            print(f"Found region label at line {i}: '{original_line}'")
            if i + 1 < len(sample_lines):
                next_line = sample_lines[i + 1].strip()
                if '|' in next_line:
                    parts = next_line.split('|', 1)
                    region_am = parts[0].strip()
                    region_en = parts[1].strip()
                else:
                    region_am = next_line
                    region_en = next_line
                print(f"Region extracted: '{region_am}' | '{region_en}'")
                i += 2  # Skip the value line
                continue
        
        # Check for subcity/zone label
        elif ('zone' in line and ('sub' in line or 'city' in line)) or ('ዞን' in original_line and 'ክፍለ' in original_line):
            print(f"Found subcity/zone label at line {i}: '{original_line}'")
            if i + 1 < len(sample_lines):
                next_line = sample_lines[i + 1].strip()
                if '|' in next_line:
                    parts = next_line.split('|', 1)
                    subcity_am = parts[0].strip()
                    subcity_en = parts[1].strip()
                else:
                    subcity_am = next_line
                    subcity_en = next_line
                print(f"Subcity extracted: '{subcity_am}' | '{subcity_en}'")
                i += 2  # Skip the value line
                continue
        
        # Check for woreda label (be more specific to avoid false matches)
        elif (line == 'woreda' or 'ወረዳ' in original_line) and len(original_line) < 30:
            print(f"Found woreda label at line {i}: '{original_line}'")
            if i + 1 < len(sample_lines):
                next_line = sample_lines[i + 1].strip()
                if '|' in next_line:
                    parts = next_line.split('|', 1)
                    woreda_am = parts[0].strip()
                    woreda_en = parts[1].strip()
                else:
                    woreda_am = next_line
                    woreda_en = next_line
                print(f"Woreda extracted: '{woreda_am}' | '{woreda_en}'")
                i += 2  # Skip the value line
                continue
        
        i += 1
    
    print("\n" + "=" * 60)
    print("RESULTS:")
    print(f"Region: '{region_am}' | '{region_en}'")
    print(f"Subcity: '{subcity_am}' | '{subcity_en}'")
    print(f"Woreda: '{woreda_am}' | '{woreda_en}'")
    
    print("\n" + "=" * 60)
    print("EXPECTED:")
    print("Region: 'አማራ' | 'Amhara'")
    print("Subcity: 'ደቡብ ወሎ ዞን' | 'South Wollo Zone'")
    print("Woreda: 'ደላንታ' | 'Delanta'")
    
    # Validate results
    success = (
        region_en == "Amhara" and
        subcity_en == "South Wollo Zone" and
        woreda_en == "Delanta"
    )
    
    print(f"\nTest {'PASSED' if success else 'FAILED'}!")
    return success

if __name__ == "__main__":
    test_label_based_extraction()