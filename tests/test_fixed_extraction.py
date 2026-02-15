#!/usr/bin/env python3
"""
Test the fixed region extraction with proper field mapping
"""
import sys
import os

# Add app to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'app'))

from services.ocr_extraction_service import OCRExtractionService

def test_extraction(image_path):
    """Test extraction with fixed region mapping"""
    
    if not os.path.exists(image_path):
        print(f"❌ Image not found: {image_path}")
        return
    
    print("=" * 80)
    print("TESTING FIXED REGION EXTRACTION")
    print("=" * 80)
    print(f"\n📸 Image: {image_path}\n")
    
    # Initialize service
    ocr_service = OCRExtractionService()
    
    # Test 1: Extract regions directly
    print("🔍 Step 1: Extracting text regions...\n")
    regions = ocr_service.extract_text_regions(image_path)
    
    if not regions:
        print("❌ No regions extracted")
        return
    
    print("\n" + "=" * 80)
    print("RAW REGION EXTRACTION")
    print("=" * 80)
    
    for region_name, text in regions.items():
        status = "✅" if text else "⚠️ "
        print(f"\n{status} {region_name}:")
        if text:
            print(f"   {text[:100]}")
        else:
            print("   (empty)")
    
    # Test 2: Parse front card data
    print("\n" + "=" * 80)
    print("🔍 Step 2: Parsing front card data...\n")
    data = ocr_service.parse_front_card_data("", image_path)
    
    print("\n" + "=" * 80)
    print("PARSED DATA")
    print("=" * 80)
    
    field_labels = {
        'full_name_en': 'Full Name (English)',
        'full_name_am': 'Full Name (Amharic)',
        'date_of_birth': 'Date of Birth',
        'date_of_birth_en': 'DOB (Gregorian)',
        'date_of_birth_am': 'DOB (Ethiopian)',
        'sex': 'Sex',
        'sex_en': 'Sex (English)',
        'sex_am': 'Sex (Amharic)',
        'date_of_expiry': 'Expiry Date',
        'date_of_expiry_en': 'Expiry (Gregorian)',
        'date_of_expiry_am': 'Expiry (Ethiopian)',
        'date_of_issue': 'Issue Date',
        'date_of_issue_en': 'Issue (Gregorian)',
        'date_of_issue_am': 'Issue (Ethiopian)',
        'fan': 'FAN Number',
    }
    
    for field_name, label in field_labels.items():
        if field_name in data:
            value = data[field_name]
            status = "✅" if value else "⚠️ "
            print(f"{status} {label}: {value if value else '(empty)'}")
    
    print("\n" + "=" * 80)
    
    # Summary
    extracted = sum(1 for k, v in data.items() if v and k in field_labels)
    total = len(field_labels)
    print(f"\n📊 Summary: {extracted}/{total} fields extracted")
    
    # Check critical fields
    critical_fields = ['full_name_en', 'date_of_birth', 'sex', 'fan']
    missing_critical = [f for f in critical_fields if not data.get(f)]
    
    if missing_critical:
        print(f"\n⚠️  Missing critical fields: {', '.join(missing_critical)}")
    else:
        print("\n✅ All critical fields extracted!")
    
    print("=" * 80)

if __name__ == "__main__":
    if len(sys.argv) > 1:
        test_extraction(sys.argv[1])
    else:
        print("Usage: python test_fixed_extraction.py <image_path>")
        print("\nExample:")
        print("  python test_fixed_extraction.py uploads/front_card.jpg")
