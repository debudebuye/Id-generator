#!/usr/bin/env python3
"""
Diagnose why Issue Date and Expiry Date fields are not being extracted
"""

import cv2
import numpy as np
from PIL import Image
import pytesseract
import os

def test_date_extraction(front_card_path):
    """Test extraction of issue and expiry dates from front card"""
    
    if not os.path.exists(front_card_path):
        print(f"❌ File not found: {front_card_path}")
        print("Please provide path to front card image")
        return
    
    img = cv2.imread(front_card_path)
    if img is None:
        print(f"❌ Could not read image: {front_card_path}")
        return
    
    height, width = img.shape[:2]
    print(f"📐 Image dimensions: {width}x{height}")
    print("="*60)
    
    # Reference dimensions from Adobe coordinates
    ref_width = 900
    ref_height = 1650
    
    # Test regions for dates
    test_regions = {
        'issue_gregorian': (892/ref_width, 576/ref_height, (892+45)/ref_width, (576+278)/ref_height),
        'issue_ethiopian': (895/ref_width, 861/ref_height, (895+45)/ref_width, (861+231)/ref_height),
        'expiry_gregorian': (201/ref_width, 1495/ref_height, (201+175)/ref_width, (1495+43)/ref_height),
        'expiry_ethiopian': (387/ref_width, 1489/ref_height, (387+339)/ref_width, (1489+49)/ref_height),
    }
    
    for region_name, (x1, y1, x2, y2) in test_regions.items():
        print(f"\n🔍 Testing: {region_name}")
        print("-"*60)
        
        # Convert percentages to pixels
        x1_px = int(x1 * width)
        y1_px = int(y1 * height)
        x2_px = int(x2 * width)
        y2_px = int(y2 * height)
        
        print(f"📍 Region: ({x1_px}, {y1_px}) to ({x2_px}, {y2_px})")
        print(f"📏 Size: {x2_px-x1_px}x{y2_px-y1_px}")
        
        # Extract region
        region_img = img[y1_px:y2_px, x1_px:x2_px]
        
        # Save original region
        cv2.imwrite(f'debug_{region_name}_original.png', region_img)
        
        # Convert to grayscale
        gray = cv2.cvtColor(region_img, cv2.COLOR_BGR2GRAY)
        
        # Resize for better OCR
        scale = 2.0
        gray = cv2.resize(gray, None, fx=scale, fy=scale, interpolation=cv2.INTER_CUBIC)
        
        # For vertical text (issue dates), rotate
        if 'issue_' in region_name:
            print("🔄 Rotating 90° counterclockwise (vertical text)")
            rotated = cv2.rotate(gray, cv2.ROTATE_90_COUNTERCLOCKWISE)
            
            # Apply CLAHE
            clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8,8))
            enhanced = clahe.apply(rotated)
            
            # Threshold
            _, thresh = cv2.threshold(enhanced, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
            
            # Save processed
            cv2.imwrite(f'debug_{region_name}_processed.png', thresh)
            
            # OCR
            config = '--oem 3 --psm 6'
            text = pytesseract.image_to_string(thresh, lang='eng+amh', config=config)
        else:
            # For horizontal text (expiry dates)
            # Apply CLAHE
            clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8,8))
            enhanced = clahe.apply(gray)
            
            # Threshold
            _, thresh = cv2.threshold(enhanced, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
            
            # Save processed
            cv2.imwrite(f'debug_{region_name}_processed.png', thresh)
            
            # OCR
            config = '--oem 3 --psm 7'  # Single line
            text = pytesseract.image_to_string(thresh, lang='eng+amh', config=config)
        
        print(f"📝 Raw OCR output:")
        print(f"   '{text.strip()}'")
        
        if text.strip():
            print(f"✅ Extracted text (length: {len(text.strip())})")
        else:
            print(f"❌ No text extracted")
        
        print(f"💾 Saved: debug_{region_name}_original.png, debug_{region_name}_processed.png")
    
    print("\n" + "="*60)
    print("📋 Summary:")
    print("   Check the debug_*_original.png and debug_*_processed.png files")
    print("   to see what the OCR is trying to read.")
    print("="*60)

if __name__ == "__main__":
    import sys
    
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
            print("Usage: python diagnose_missing_dates.py <front_card_image_path>")
            print("\nOr save your front card image as one of:")
            for path in possible_paths:
                print(f"  - {path}")
            sys.exit(1)
    
    test_date_extraction(front_card_path)
