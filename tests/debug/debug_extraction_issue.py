"""
Debug script to check what data is being extracted from ID cards
"""
import os
from app.services.ocr_extraction_service import OCRExtractionService

# Initialize OCR service
ocr_service = OCRExtractionService()

# Check if there are recent uploads
uploads_dir = 'app/static'
print("=" * 60)
print("CHECKING RECENT UPLOADS")
print("=" * 60)

# List all files in static folder
files = []
for f in os.listdir(uploads_dir):
    if f.endswith(('.png', '.jpg', '.jpeg')):
        filepath = os.path.join(uploads_dir, f)
        files.append((f, os.path.getmtime(filepath)))

# Sort by modification time (newest first)
files.sort(key=lambda x: x[1], reverse=True)

print(f"\nFound {len(files)} image files in static folder")
print("\nMost recent files:")
for i, (filename, mtime) in enumerate(files[:10]):
    print(f"{i+1}. {filename}")

# Look for front and back ID images
front_image = None
back_image = None

for filename, _ in files:
    if 'front' in filename.lower() and not front_image:
        front_image = os.path.join(uploads_dir, filename)
    elif 'back' in filename.lower() and not back_image:
        back_image = os.path.join(uploads_dir, filename)

print("\n" + "=" * 60)
print("TESTING OCR EXTRACTION")
print("=" * 60)

if front_image and os.path.exists(front_image):
    print(f"\n📸 Front Image: {front_image}")
    print("-" * 60)
    
    # Extract text
    front_text = ocr_service.extract_text_from_image(front_image)
    print(f"\nExtracted Text:\n{front_text[:500]}...")
    
    # Parse data
    front_data = ocr_service.parse_front_card_data(front_text, image_path=front_image)
    print(f"\nParsed Data:")
    for key, value in front_data.items():
        if value:
            print(f"  ✓ {key}: {value}")
        else:
            print(f"  ✗ {key}: (empty)")
else:
    print("\n⚠️ No front image found")

if back_image and os.path.exists(back_image):
    print(f"\n📸 Back Image: {back_image}")
    print("-" * 60)
    
    # Extract text
    back_text = ocr_service.extract_text_from_image(back_image)
    print(f"\nExtracted Text:\n{back_text[:500]}...")
    
    # Parse data
    back_data = ocr_service.parse_back_card_data(back_text, image_path=back_image)
    print(f"\nParsed Data:")
    for key, value in back_data.items():
        if value:
            print(f"  ✓ {key}: {value}")
        else:
            print(f"  ✗ {key}: (empty)")
else:
    print("\n⚠️ No back image found")

print("\n" + "=" * 60)
print("DIAGNOSIS COMPLETE")
print("=" * 60)
