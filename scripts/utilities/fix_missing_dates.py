#!/usr/bin/env python3
"""
Fix for missing Issue Date and Expiry Date extraction

This script will:
1. Test the current extraction on a sample image
2. Show what's being extracted
3. Provide recommendations for fixes
"""

import sys
import os

# Add app directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'app'))

from services.ocr_extraction_service import OCRExtractionService

def test_date_extraction(front_card_path):
    """Test date extraction from front card"""
    
    if not os.path.exists(front_card_path):
        print(f"❌ File not found: {front_card_path}")
        return
    
    print("="*80)
    print("TESTING DATE EXTRACTION")
    print("="*80)
    
    ocr_service = OCRExtractionService()
    
    # Test region-based extraction
    print("\n1️⃣ Testing region-based extraction...")
    print("-"*80)
    regions = ocr_service.extract_text_regions(front_card_path)
    
    print("\n📊 Extracted Regions:")
    for key, value in regions.items():
        if 'issue' in key or 'expiry' in key:
            print(f"  {key}: '{value}'")
    
    # Test full parsing
    print("\n2️⃣ Testing full card parsing...")
    print("-"*80)
    
    # Get full text
    full_text = ocr_service.extract_text_from_image(front_card_path)
    
    # Parse front card data
    parsed_data = ocr_service.parse_front_card_data(full_text, front_card_path)
    
    print("\n📊 Parsed Date Fields:")
    date_fields = {
        'date_of_issue': parsed_data.get('date_of_issue', ''),
        'date_of_issue_am': parsed_data.get('date_of_issue_am', ''),
        'date_of_issue_en': parsed_data.get('date_of_issue_en', ''),
        'date_of_expiry': parsed_data.get('date_of_expiry', ''),
        'date_of_expiry_am': parsed_data.get('date_of_expiry_am', ''),
        'date_of_expiry_en': parsed_data.get('date_of_expiry_en', ''),
    }
    
    for key, value in date_fields.items():
        status = "✅" if value else "❌"
        print(f"  {status} {key}: '{value}'")
    
    # Check what will be sent to template
    print("\n3️⃣ Field Mapping (what template will receive):")
    print("-"*80)
    
    # Simulate the mapping in routes.py
    template_data = {
        'issue_date': parsed_data.get('date_of_issue', ''),
        'issue_date_am': parsed_data.get('date_of_issue_am', parsed_data.get('issue_date_am', '')),
        'issue_date_en': parsed_data.get('date_of_issue_en', parsed_data.get('issue_date_en', parsed_data.get('date_of_issue', ''))),
        'expiry_date': parsed_data.get('date_of_expiry', ''),
        'expiry_date_am': parsed_data.get('date_of_expiry_am', parsed_data.get('expiry_date_am', '')),
        'expiry_date_en': parsed_data.get('date_of_expiry_en', parsed_data.get('expiry_date_en', parsed_data.get('date_of_expiry', ''))),
    }
    
    for key, value in template_data.items():
        status = "✅" if value else "❌"
        print(f"  {status} {key}: '{value}'")
    
    # Summary
    print("\n" + "="*80)
    print("SUMMARY")
    print("="*80)
    
    missing_count = sum(1 for v in template_data.values() if not v)
    total_count = len(template_data)
    success_rate = ((total_count - missing_count) / total_count) * 100
    
    print(f"✓ Extracted: {total_count - missing_count}/{total_count} fields ({success_rate:.0f}%)")
    
    if missing_count > 0:
        print(f"\n⚠️ Missing {missing_count} fields:")
        for key, value in template_data.items():
            if not value:
                print(f"   - {key}")
        
        print("\n💡 Recommendations:")
        print("   1. Check if the date regions are correctly positioned")
        print("   2. Run: python diagnose_missing_dates.py <front_card_image>")
        print("   3. Check the debug_*_original.png and debug_*_processed.png files")
        print("   4. Adjust region coordinates if needed")
        print("   5. Or use manual entry in the preview page")
    else:
        print("\n✅ All date fields extracted successfully!")
    
    print("="*80)

if __name__ == "__main__":
    if len(sys.argv) > 1:
        front_card_path = sys.argv[1]
    else:
        # Try common paths
        possible_paths = [
            'uploads/front_card.jpg',
            'uploads/front_card.png',
            'sample_front_card.jpg',
            'front_card.jpg',
        ]
        
        front_card_path = None
        for path in possible_paths:
            if os.path.exists(path):
                front_card_path = path
                break
        
        if not front_card_path:
            print("Usage: python fix_missing_dates.py <front_card_image_path>")
            print("\nOr save your front card image as one of:")
            for path in possible_paths:
                print(f"  - {path}")
            sys.exit(1)
    
    test_date_extraction(front_card_path)
