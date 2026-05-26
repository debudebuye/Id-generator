#!/usr/bin/env python3
"""
Debug script to test expiry date extraction
"""
import sys
sys.path.insert(0, '.')

from app.services.ocr_extraction_service import OCRExtractionService

def test_expiry_extraction(front_image_path):
    """Test expiry date extraction from front card"""
    
    print("="*80)
    print("EXPIRY DATE EXTRACTION TEST")
    print("="*80)
    
    ocr_service = OCRExtractionService()
    
    # Extract regions
    print(f"\n1. Extracting regions from: {front_image_path}")
    regions = ocr_service.extract_text_regions(front_image_path)
    
    print(f"\n2. Extracted regions:")
    for key, value in regions.items():
        if 'expiry' in key:
            print(f"   {key}: '{value}'")
    
    # Parse front card data
    print(f"\n3. Parsing front card data...")
    data = ocr_service.parse_front_card_data("", image_path=front_image_path)
    
    print(f"\n4. Expiry date fields in parsed data:")
    expiry_fields = {k: v for k, v in data.items() if 'expiry' in k.lower()}
    for key, value in expiry_fields.items():
        print(f"   {key}: '{value}'")
    
    print(f"\n5. All date fields:")
    date_fields = {k: v for k, v in data.items() if 'date' in k.lower()}
    for key, value in date_fields.items():
        print(f"   {key}: '{value}'")
    
    print("\n" + "="*80)
    
    # Check if expiry dates are extracted
    if data.get('date_of_expiry'):
        print("✅ date_of_expiry extracted successfully")
    else:
        print("❌ date_of_expiry is empty")
    
    if data.get('date_of_expiry_en'):
        print("✅ date_of_expiry_en extracted successfully")
    else:
        print("❌ date_of_expiry_en is empty")
    
    if data.get('date_of_expiry_am'):
        print("✅ date_of_expiry_am extracted successfully")
    else:
        print("❌ date_of_expiry_am is empty")
    
    print("="*80)

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python tests/debug_expiry_extraction.py <front_card_image_path>")
        print("\nExample:")
        print("  python tests/debug_expiry_extraction.py app/static/front_cropped.png")
        sys.exit(1)
    
    image_path = sys.argv[1]
    test_expiry_extraction(image_path)
