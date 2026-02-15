"""
Test OCR extraction with bilingual Ethiopian ID format
"""
import sys
import os

sys.path.insert(0, os.path.dirname(__file__))

from app.services.ocr_extraction_service import OCRExtractionService

def test_bilingual_format():
    """Test parsing with bilingual format (Amharic first, then English)"""
    print("=" * 60)
    print("Testing Bilingual Format Extraction")
    print("=" * 60)
    
    ocr_service = OCRExtractionService()
    
    # Sample text from the new card format
    sample_front_text = """
    FEDERAL DEMOCRATIC REPUBLIC OF ETHIOPIA
    Ethiopian Digital ID Card
    FAYDA DIGITAL COPY
    
    ሙሉ ስም | Full Name
    ማሊዮን አየለ ዋዳ
    Milliyon Ayele Wada
    
    የትውልድ ቀን | Date of Birth
    05/07/1986 | 1994/Mar/14
    
    ጾታ | Sex
    ወንድ | Male
    
    የማብቂያ ቀን | Date of Expiry
    2026/05/28 | 2034/Feb/05
    
    ካርድ ቁጥር
    FAN
    5164983502379087
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
    print("✓ full_name_am: ማሊዮን አየለ ዋዳ")
    print("✓ full_name_en: Milliyon Ayele Wada")
    print("✓ date_of_birth: 05/07/1986")
    print("✓ sex: Male")
    print("✓ date_of_expiry: 2026/05/28")
    print("✓ fan: 5164983502379087")
    
    # Check accuracy
    print("\n" + "=" * 60)
    print("Accuracy Check:")
    print("=" * 60)
    
    checks = {
        'Name (AM)': front_data['full_name_am'] == 'ማሊዮን አየለ ዋዳ',
        'Name (EN)': front_data['full_name_en'] == 'Milliyon Ayele Wada',
        'DOB': front_data['date_of_birth'] == '05/07/1986',
        'Sex': front_data['sex'] == 'Male',
        'Expiry': front_data['date_of_expiry'] in ['2026/05/28', '2034/Feb/05'],
        'FAN': front_data['fan'] == '5164983502379087',
    }
    
    for field, is_correct in checks.items():
        status = "✅" if is_correct else "❌"
        print(f"{status} {field}: {'Correct' if is_correct else 'Incorrect'}")
    
    success_rate = sum(checks.values()) / len(checks) * 100
    print(f"\n📊 Success Rate: {success_rate:.0f}%")

if __name__ == "__main__":
    test_bilingual_format()
