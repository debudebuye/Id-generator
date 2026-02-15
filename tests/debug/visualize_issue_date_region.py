"""
Visualize the issue date region extraction to debug vertical text OCR
"""
import cv2
import numpy as np
from app.services.ocr_extraction_service import OCRExtractionService
import pytesseract
import os

def visualize_issue_date_region(image_path):
    """Extract and visualize the issue date region"""
    print(f"📸 Processing: {image_path}")
    
    if not os.path.exists(image_path):
        print(f"❌ Image not found: {image_path}")
        return
    
    # Read image
    img = cv2.imread(image_path)
    if img is None:
        print(f"❌ Could not read image")
        return
    
    height, width = img.shape[:2]
    print(f"📐 Image dimensions: {width}x{height}")
    
    # Define issue date region (vertical text on right)
    x1, y1, x2, y2 = 0.85, 0.15, 0.98, 0.85
    
    # Convert to pixels
    x1_px = int(x1 * width)
    y1_px = int(y1 * height)
    x2_px = int(x2 * width)
    y2_px = int(y2 * height)
    
    print(f"📍 Region coordinates: ({x1_px}, {y1_px}) to ({x2_px}, {y2_px})")
    
    # Extract region
    region_img = img[y1_px:y2_px, x1_px:x2_px]
    
    # Save original region
    cv2.imwrite('debug_issue_date_original.png', region_img)
    print(f"💾 Saved: debug_issue_date_original.png")
    
    # Convert to grayscale
    gray = cv2.cvtColor(region_img, cv2.COLOR_BGR2GRAY)
    
    # Resize
    scale = 2.0
    gray = cv2.resize(gray, None, fx=scale, fy=scale, interpolation=cv2.INTER_CUBIC)
    
    # Save grayscale
    cv2.imwrite('debug_issue_date_gray.png', gray)
    print(f"💾 Saved: debug_issue_date_gray.png")
    
    # Rotate 90 degrees counterclockwise
    rotated = cv2.rotate(gray, cv2.ROTATE_90_COUNTERCLOCKWISE)
    
    # Save rotated
    cv2.imwrite('debug_issue_date_rotated.png', rotated)
    print(f"💾 Saved: debug_issue_date_rotated.png")
    
    # Apply CLAHE
    clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8,8))
    enhanced = clahe.apply(rotated)
    
    # Save enhanced
    cv2.imwrite('debug_issue_date_enhanced.png', enhanced)
    print(f"💾 Saved: debug_issue_date_enhanced.png")
    
    # Apply threshold
    _, thresh = cv2.threshold(enhanced, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    
    # Save threshold
    cv2.imwrite('debug_issue_date_thresh.png', thresh)
    print(f"💾 Saved: debug_issue_date_thresh.png")
    
    # Run OCR
    print("\n🔍 Running OCR...")
    config = '--oem 3 --psm 6'
    text = pytesseract.image_to_string(thresh, lang='eng+amh', config=config)
    
    print(f"\n📄 OCR Result:")
    print("-" * 60)
    print(text)
    print("-" * 60)
    
    # Extract dates
    import re
    dates = re.findall(r'\d{4}[/\-]\d{2}[/\-]\d{2}', text)
    
    if dates:
        print(f"\n✅ Found {len(dates)} date(s):")
        for i, date in enumerate(dates, 1):
            print(f"   {i}. {date}")
        print(f"\n💡 Issue date should be: {dates[0]}")
    else:
        print("\n❌ No dates found in OCR text")
        print("   Try adjusting region coordinates or preprocessing")
    
    # Try alternative rotation
    print("\n🔄 Trying alternative rotation (clockwise)...")
    rotated_alt = cv2.rotate(gray, cv2.ROTATE_90_CLOCKWISE)
    enhanced_alt = clahe.apply(rotated_alt)
    _, thresh_alt = cv2.threshold(enhanced_alt, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    
    cv2.imwrite('debug_issue_date_rotated_alt.png', rotated_alt)
    cv2.imwrite('debug_issue_date_thresh_alt.png', thresh_alt)
    
    text_alt = pytesseract.image_to_string(thresh_alt, lang='eng+amh', config=config)
    dates_alt = re.findall(r'\d{4}[/\-]\d{2}[/\-]\d{2}', text_alt)
    
    if dates_alt:
        print(f"✅ Alternative rotation found {len(dates_alt)} date(s):")
        for i, date in enumerate(dates_alt, 1):
            print(f"   {i}. {date}")
    else:
        print("❌ Alternative rotation also found no dates")
    
    print("\n" + "="*60)
    print("Debug images saved:")
    print("  - debug_issue_date_original.png (extracted region)")
    print("  - debug_issue_date_gray.png (grayscale)")
    print("  - debug_issue_date_rotated.png (rotated 90° CCW)")
    print("  - debug_issue_date_enhanced.png (CLAHE applied)")
    print("  - debug_issue_date_thresh.png (thresholded)")
    print("  - debug_issue_date_rotated_alt.png (rotated 90° CW)")
    print("  - debug_issue_date_thresh_alt.png (alt threshold)")
    print("="*60)

if __name__ == '__main__':
    import sys
    
    if len(sys.argv) > 1:
        image_path = sys.argv[1]
    else:
        # Try to find a sample image
        possible_paths = [
            'sample_card_1.jpg',
            'sample_card_2.jpg',
            'sample_card_3.jpg',
            'uploads/front_temp.png',
            'uploads/front_temp.jpg',
            'static/front_temp.png',
            'static/front_temp.jpg',
        ]
        
        image_path = None
        for path in possible_paths:
            if os.path.exists(path):
                image_path = path
                break
        
        if not image_path:
            print("Usage: python visualize_issue_date_region.py <image_path>")
            print("\nOr save a sample card as 'sample_card_1.jpg'")
            sys.exit(1)
    
    visualize_issue_date_region(image_path)
