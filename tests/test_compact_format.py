"""
Test OCR extraction with compact format (Emebet's card)
"""
import sys
import os

sys.path.insert(0, os.path.dirname(__file__))

from app.services.ocr_extraction_service import OCRExtractionService

def test_compact_format():
    """Test parsing with compact format from actual OCR output"""
    print("=" * 60)
    print("Testing Compact Format Extraction (Emebet's Card)")
    print("=" * 60)
    
    ocr_service = OCRExtractionService()
    
    # Actual text extracted from Emebet's card
    sample_front_text = """
oD SATLRE AMAA aohEObO HCL7
Ethiopian Digital ID Card
——s
FAYDA DIGITAL COPY

; @.
mw4 3:
by :, 5.
aS
3:

@®A AF | Full Name 3
'ODN NN ULA =
'Emebet Kebe Haile 5
°

2+OAL >) | Date of Birth
-01/01/1995 |2002/Sep/11

.Pt | Sex
7t+] Female

:POLPNSNY $9 | Date of Expiry
a2026/05/18 |2034/Jan/26

2
; nce
4531096041930180
:ee TMT |
FAN
    """
    
    print("\n📝 Testing Front Card Parsing:")
    print("-" * 60)
    front_data = ocr_service.parse_front_card_data(sample_front_text)
    
    print("\n✅ Extracted Data:")
    print("-" * 60)
    for key, value in front_data.items():
        status = "✓" if value else "✗"
        print(f"{status} {key}: {value}")
    
    print("\n" + "=" * 60)
    print("Expected Values:")
    print("=" * 60)
    print("✓ full_name_en: Emebet Kebe Haile")
    print("✓ date_of_birth: 01/01/1995")
    print("✓ sex: Female")
    print("✓ date_of_expiry: 2026/05/18")
    print("✓ fan: 4531096041930180")
    
    # Check accuracy
    print("\n" + "=" * 60)
    print("Accuracy Check:")
    print("=" * 60)
    
    checks = {
        'Name (EN)': 'Emebet Kebe Haile' in front_data['full_name_en'],
        'DOB': front_data['date_of_birth'] == '01/01/1995',
        'Sex': front_data['sex'] == 'Female',
        'Expiry': front_data['date_of_expiry'] in ['2026/05/18', '2034/Jan/26'],
        'FAN': front_data['fan'] == '4531096041930180',
    }
    
    for field, is_correct in checks.items():
        status = "✅" if is_correct else "❌"
        print(f"{status} {field}: {'Correct' if is_correct else 'Incorrect'}")
    
    success_rate = sum(checks.values()) / len(checks) * 100
    print(f"\n📊 Success Rate: {success_rate:.0f}%")

if __name__ == "__main__":
    test_compact_format()
