#!/usr/bin/env python3
"""
Test OCR extraction with Adobe coordinates
"""
import sys
import os

# Add app to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'app'))

from services.ocr_extraction_service import OCRExtractionService

def test_extraction(image_path):
    """Test extraction with Adobe coordinates"""
    
    if not os.path.exists(image_path):
        print(f"❌ Image not found: {image_path}")
        return
    
    print("=" * 80)
    print("TESTING ADOBE COORDINATE EXTRACTION")
    print("=" * 80)
    print(f"\n📸 Image: {image_path}\n")
    
    # Initialize service
    ocr_service = OCRExtractionService()
    
    # Extract regions
    print("🔍 Extracting text regions...\n")
    regions = ocr_service.extract_text_regions(image_path)
    
    if not regions:
        print("❌ No regions extracted")
        return
    
    # Display results
    print("\n" + "=" * 80)
    print("EXTRACTION RESULTS")
    print("=" * 80)
    
    field_labels = {
        'full_name_am': 'Full Name (Amharic)',
        'full_name_en': 'Full Name (English)',
        'dob_gregorian': 'Date of Birth (Gregorian)',
        'dob_ethiopian': 'Date of Birth (Ethiopian)',
        'sex_am': 'Sex (Amharic)',
        'sex_en': 'Sex (English)',
        'expiry_gregorian': 'Expiry Date (Gregorian)',
        'expiry_ethiopian': 'Expiry Date (Ethiopian)',
        'fan_number': 'FAN Number',
        'issue_gregorian': 'Issue Date (Gregorian)',
        'issue_ethiopian': 'Issue Date (Ethiopian)',
    }
    
    for field_name, text in regions.items():
        label = field_labels.get(field_name, field_name)
        status = "✅" if text else "⚠️ "
        print(f"\n{status} {label}:")
        if text:
            print(f"   {text}")
        else:
            print("   (empty)")
    
    print("\n" + "=" * 80)
    
    # Summary
    extracted = sum(1 for text in regions.values() if text)
    total = len(regions)
    print(f"\n📊 Summary: {extracted}/{total} fields extracted")
    print("=" * 80)

if __name__ == "__main__":
    if len(sys.argv) > 1:
        test_extraction(sys.argv[1])
    else:
        print("Usage: python test_adobe_extraction.py <image_path>")
        print("\nExample:")
        print("  python test_adobe_extraction.py uploads/front_card.jpg")
