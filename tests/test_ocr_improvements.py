"""
Test script to verify OCR improvements
"""
import sys
import os

# Add app directory to path
sys.path.insert(0, os.path.dirname(__file__))

from app.services.ocr_extraction_service import OCRExtractionService

def test_ocr_service():
    """Test OCR extraction service"""
    print("=" * 60)
    print("Testing OCR Extraction Service")
    print("=" * 60)
    
    ocr_service = OCRExtractionService()
    
    # Test with sample text
    sample_front_text = """
    FEDERAL DEMOCRATIC REPUBLIC OF ETHIOPIA
    ETHIOPIAN DIGITAL ID
    
    Full Name
    ABEBE KEBEDE TESFAYE
    አበበ ከበደ ተስፋዬ
    
    Date of Birth: 15/03/1990
    Sex: Male
    
    FAN: 356247605302732
    
    Date of Issue: 01/01/2024
    Date of Expiry: 01/01/2034
    """
    
    sample_back_text = """
    Nationality
    Ethiopian
    ኢትዮጵያዊ
    
    Address
    Addis Ababa
    አዲስ አበባ
    Bole Sub-City
    Woreda 03
    
    Phone: 0919264259
    """
    
    print("\n📝 Testing Front Card Parsing:")
    print("-" * 60)
    front_data = ocr_service.parse_front_card_data(sample_front_text)
    print("\n✅ Front Card Results:")
    for key, value in front_data.items():
        print(f"  {key}: {value}")
    
    print("\n📝 Testing Back Card Parsing:")
    print("-" * 60)
    back_data = ocr_service.parse_back_card_data(sample_back_text)
    print("\n✅ Back Card Results:")
    for key, value in back_data.items():
        print(f"  {key}: {value}")
    
    print("\n" + "=" * 60)
    print("✅ OCR Service Test Complete!")
    print("=" * 60)

if __name__ == "__main__":
    test_ocr_service()
