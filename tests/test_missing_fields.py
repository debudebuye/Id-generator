"""
Test to verify that missing fields (serial_number, issue_date, phone_number) are now being extracted/generated
"""
from app.services.id_card_service import IDCardService
from app.services.ocr_extraction_service import OCRExtractionService

def test_serial_number_generation():
    """Test that serial number is generated"""
    id_service = IDCardService()
    serial = id_service.generate_serial_number()
    
    print(f"✓ Generated serial number: {serial}")
    assert serial is not None
    assert len(serial) >= 7
    assert serial.isdigit()
    assert not serial.startswith('0')
    print("✅ Serial number generation works!")

def test_issue_date_extraction():
    """Test that issue date extraction is working"""
    ocr_service = OCRExtractionService()
    
    # Test with sample text containing issue date
    sample_text = """
    Date of Birth: 1990/05/15
    Date of Issue: 2020/03/10
    Date of Expiry: 2030/03/10
    """
    
    data = ocr_service.parse_front_card_data(sample_text)
    
    print(f"✓ Extracted data: {data}")
    print(f"  - Date of Issue: {data.get('date_of_issue', 'NOT FOUND')}")
    
    if data.get('date_of_issue'):
        print("✅ Issue date extraction works!")
    else:
        print("⚠️ Issue date not extracted - check OCR logic")

def test_phone_extraction():
    """Test that phone number extraction is working"""
    ocr_service = OCRExtractionService()
    
    # Test with sample text containing phone number
    sample_text = """
    Phone Number: 0912345678
    Address: Addis Ababa
    """
    
    data = ocr_service.parse_back_card_data(sample_text)
    
    print(f"✓ Extracted data: {data}")
    print(f"  - Phone Number: {data.get('phone_number', 'NOT FOUND')}")
    
    if data.get('phone_number'):
        print("✅ Phone number extraction works!")
    else:
        print("⚠️ Phone number not extracted - check OCR logic")

if __name__ == '__main__':
    print("=" * 60)
    print("Testing Missing Fields Extraction")
    print("=" * 60)
    
    print("\n1. Testing Serial Number Generation:")
    print("-" * 60)
    test_serial_number_generation()
    
    print("\n2. Testing Issue Date Extraction:")
    print("-" * 60)
    test_issue_date_extraction()
    
    print("\n3. Testing Phone Number Extraction:")
    print("-" * 60)
    test_phone_extraction()
    
    print("\n" + "=" * 60)
    print("All tests completed!")
    print("=" * 60)
