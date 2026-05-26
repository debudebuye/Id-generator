"""
Test region-based OCR extraction
"""
import sys
import os

sys.path.insert(0, os.path.dirname(__file__))

from app.services.ocr_extraction_service import OCRExtractionService

def test_region_extraction():
    """Test region-based extraction on uploaded images"""
    print("=" * 60)
    print("Testing Region-Based OCR Extraction")
    print("=" * 60)
    
    ocr_service = OCRExtractionService()
    
    # Test with front image
    front_path = os.path.join('app', 'static', 'front_cropped.png')
    
    if not os.path.exists(front_path):
        print(f"❌ Front image not found: {front_path}")
        return
    
    print(f"\n📸 Testing with: {front_path}")
    print("-" * 60)
    
    # Extract regions
    regions = ocr_service.extract_text_regions(front_path)
    
    print("\n" + "=" * 60)
    print("✅ Region Extraction Results:")
    print("=" * 60)
    for region_name, text in regions.items():
        print(f"\n{region_name}:")
        print(f"  {text[:100] if text else '(empty)'}")
    
    # Now test full parsing
    print("\n" + "=" * 60)
    print("Testing Full Parsing with Region Data:")
    print("=" * 60)
    
    front_text = ocr_service.extract_text_from_image(front_path)
    front_data = ocr_service.parse_front_card_data(front_text, image_path=front_path)
    
    print("\n✅ Final Extracted Data:")
    print("-" * 60)
    for key, value in front_data.items():
        status = "✓" if value else "✗"
        print(f"{status} {key}: {value}")
    
    extracted_count = sum(1 for v in front_data.values() if v)
    print(f"\n📊 Success Rate: {extracted_count}/8 fields ({extracted_count*100//8}%)")

if __name__ == "__main__":
    test_region_extraction()
