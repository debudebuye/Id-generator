"""
Test the improved OCR extraction
"""
from app.services.ocr_extraction_service import OCRExtractionService

# Initialize service
ocr_service = OCRExtractionService()

# Test with the actual cropped images
print("="*80)
print("Testing FRONT card extraction")
print("="*80)

# Extract text
front_text = ocr_service.extract_text_from_image("app/static/front_cropped.png")
print(f"\nExtracted {len(front_text)} characters")

# Parse data
front_data = ocr_service.parse_front_card_data(front_text, "app/static/front_cropped.png")

print("\n" + "="*80)
print("FRONT CARD RESULTS:")
print("="*80)
for key, value in front_data.items():
    if value:
        print(f"{key}: {value}")

print("\n" + "="*80)
print("Testing BACK card extraction")
print("="*80)

# Extract text
back_text = ocr_service.extract_text_from_image("app/static/back_cropped.png")
print(f"\nExtracted {len(back_text)} characters")

# Parse data
back_data = ocr_service.parse_back_card_data(back_text, "app/static/back_cropped.png")

print("\n" + "="*80)
print("BACK CARD RESULTS:")
print("="*80)
for key, value in back_data.items():
    if value:
        print(f"{key}: {value}")

print("\n" + "="*80)
print("SUMMARY")
print("="*80)
front_count = sum(1 for v in front_data.values() if v)
back_count = sum(1 for v in back_data.values() if v)
print(f"Front card: {front_count}/{len(front_data)} fields extracted")
print(f"Back card: {back_count}/{len(back_data)} fields extracted")
print(f"Total: {front_count + back_count}/{len(front_data) + len(back_data)} fields extracted")
