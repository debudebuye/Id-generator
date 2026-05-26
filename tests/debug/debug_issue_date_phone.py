"""
Debug script to test issue date and phone number extraction from actual ID card images
"""
import os
from app.services.ocr_extraction_service import OCRExtractionService

def test_front_card_extraction():
    """Test extraction from front card image"""
    ocr_service = OCRExtractionService()
    
    # Look for front card images in common locations
    possible_paths = [
        'uploads/front_temp.png',
        'uploads/front_temp.jpg',
        'static/front_temp.png',
        'static/front_temp.jpg',
        'temp/front_temp.png',
        'temp/front_temp.jpg',
    ]
    
    front_path = None
    for path in possible_paths:
        if os.path.exists(path):
            front_path = path
            break
    
    if not front_path:
        print("⚠️ No front card image found in uploads/static/temp folders")
        print("   Please upload an ID card first, then run this script")
        return
    
    print(f"📸 Testing front card: {front_path}")
    print("=" * 60)
    
    # Extract regions
    regions = ocr_service.extract_text_regions(front_path)
    
    print("\n📋 Extracted Regions:")
    print("-" * 60)
    for region_name, text in regions.items():
        print(f"\n{region_name}:")
        print(f"  {text[:200]}")
    
    # Parse the data
    print("\n" + "=" * 60)
    print("📊 Parsed Data:")
    print("-" * 60)
    
    full_text = ocr_service.extract_text_from_image(front_path)
    data = ocr_service.parse_front_card_data(full_text, image_path=front_path)
    
    print(f"\nIssue Date: {data.get('date_of_issue', 'NOT FOUND')}")
    print(f"Birth Date: {data.get('date_of_birth', 'NOT FOUND')}")
    print(f"Expiry Date: {data.get('date_of_expiry', 'NOT FOUND')}")
    print(f"Full Name (EN): {data.get('full_name_en', 'NOT FOUND')}")
    print(f"Full Name (AM): {data.get('full_name_am', 'NOT FOUND')}")
    print(f"FAN: {data.get('fan', 'NOT FOUND')}")

def test_back_card_extraction():
    """Test extraction from back card image"""
    ocr_service = OCRExtractionService()
    
    # Look for back card images in common locations
    possible_paths = [
        'uploads/back_temp.png',
        'uploads/back_temp.jpg',
        'static/back_temp.png',
        'static/back_temp.jpg',
        'temp/back_temp.png',
        'temp/back_temp.jpg',
    ]
    
    back_path = None
    for path in possible_paths:
        if os.path.exists(path):
            back_path = path
            break
    
    if not back_path:
        print("⚠️ No back card image found in uploads/static/temp folders")
        print("   Please upload an ID card first, then run this script")
        return
    
    print(f"📸 Testing back card: {back_path}")
    print("=" * 60)
    
    # Extract regions
    regions = ocr_service.extract_back_card_regions(back_path)
    
    print("\n📋 Extracted Regions:")
    print("-" * 60)
    for region_name, text in regions.items():
        print(f"\n{region_name}:")
        print(f"  {text[:200]}")
    
    # Parse the data
    print("\n" + "=" * 60)
    print("📊 Parsed Data:")
    print("-" * 60)
    
    full_text = ocr_service.extract_text_from_image(back_path)
    data = ocr_service.parse_back_card_data(full_text, image_path=back_path)
    
    print(f"\nPhone Number: {data.get('phone_number', 'NOT FOUND')}")
    print(f"FIN: {data.get('fin', 'NOT FOUND')}")
    print(f"Nationality (EN): {data.get('nationality_en', 'NOT FOUND')}")
    print(f"Nationality (AM): {data.get('nationality_am', 'NOT FOUND')}")
    print(f"Address (EN): {data.get('address_en', 'NOT FOUND')}")
    print(f"Address (AM): {data.get('address_am', 'NOT FOUND')}")

if __name__ == '__main__':
    print("=" * 60)
    print("Issue Date & Phone Number Extraction Debug")
    print("=" * 60)
    
    print("\n1. Testing Front Card (Issue Date):")
    print("=" * 60)
    test_front_card_extraction()
    
    print("\n\n2. Testing Back Card (Phone Number):")
    print("=" * 60)
    test_back_card_extraction()
    
    print("\n" + "=" * 60)
    print("Debug completed!")
    print("=" * 60)
