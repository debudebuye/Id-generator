"""
Test back card OCR extraction
"""
import sys
import os

sys.path.insert(0, os.path.dirname(__file__))

from app.services.ocr_extraction_service import OCRExtractionService

def test_back_card_extraction():
    """Test region-based extraction on back card"""
    print("=" * 60)
    print("Testing Back Card OCR Extraction")
    print("=" * 60)
    
    ocr_service = OCRExtractionService()
    
    # Test with back image
    back_path = os.path.join('app', 'static', 'back_cropped.png')
    
    if not os.path.exists(back_path):
        print(f"❌ Back image not found: {back_path}")
        return
    
    print(f"\n📸 Testing with: {back_path}")
    print("-" * 60)
    
    # Extract regions
    regions = ocr_service.extract_back_card_regions(back_path)
    
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
    
    back_text = ocr_service.extract_text_from_image(back_path)
    back_data = ocr_service.parse_back_card_data(back_text, image_path=back_path)
    
    print("\n✅ Final Extracted Data:")
    print("-" * 60)
    for key, value in back_data.items():
        status = "✓" if value else "✗"
        print(f"{status} {key}: {value}")
    
    extracted_count = sum(1 for v in back_data.values() if v)
    print(f"\n📊 Success Rate: {extracted_count}/9 fields ({extracted_count*100//9}%)")
    
    # Expected values based on image
    print("\n" + "=" * 60)
    print("Expected Values (from image):")
    print("=" * 60)
    print("✓ Phone: 0919264253")
    print("✓ FIN: 6915 7029 3596")
    print("✓ Nationality: Ethiopian")
    print("✓ Region: Oromia")
    print("✓ Subcity: ARSI WEST")
    print("✓ Woreda: NEGELE TOWN")

if __name__ == "__main__":
    test_back_card_extraction()
