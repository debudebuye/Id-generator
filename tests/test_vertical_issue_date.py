#!/usr/bin/env python3
"""
Test extraction of vertical issue date from the right edge of the card
Based on the sample image showing: "2018/06/02 | 2026/Feb/09"
"""

import cv2
import numpy as np
import pytesseract
import re
import os
import sys

def extract_vertical_issue_date(image_path):
    """Extract the vertical issue date from right edge of card"""
    
    if not os.path.exists(image_path):
        print(f"❌ File not found: {image_path}")
        return None, None
    
    print("="*80)
    print("EXTRACTING VERTICAL ISSUE DATE FROM RIGHT EDGE")
    print("="*80)
    
    img = cv2.imread(image_path)
    if img is None:
        print(f"❌ Could not read image")
        return None, None
    
    height, width = img.shape[:2]
    print(f"📐 Image dimensions: {width}x{height}")
    
    # Adobe coordinates for issue date (vertical text on right edge)
    # Issue Date (Gregorian): x=892, y=576, w=45, h=278
    # Issue Date (Ethiopian): x=895, y=861, w=45, h=231
    
    ref_width = 900
    ref_height = 1650
    
    # Try extracting a larger region that includes both dates
    # From y=576 to y=1092 (576+278+231+7 for gap)
    x1_pct = 892 / ref_width
    y1_pct = 576 / ref_height
    x2_pct = (892 + 45) / ref_width
    y2_pct = (861 + 231) / ref_height  # End of Ethiopian date
    
    x1_px = int(x1_pct * width)
    y1_px = int(y1_pct * height)
    x2_px = int(x2_pct * width)
    y2_px = int(y2_pct * height)
    
    print(f"📍 Extracting region: ({x1_px}, {y1_px}) to ({x2_px}, {y2_px})")
    print(f"📏 Region size: {x2_px-x1_px}x{y2_px-y1_px}")
    
    # Extract the vertical text region
    region = img[y1_px:y2_px, x1_px:x2_px]
    
    # Save original
    cv2.imwrite('debug_vertical_issue_original.png', region)
    print(f"💾 Saved: debug_vertical_issue_original.png")
    
    # Convert to grayscale
    gray = cv2.cvtColor(region, cv2.COLOR_BGR2GRAY)
    
    # Rotate 90 degrees counterclockwise (vertical text becomes horizontal)
    rotated = cv2.rotate(gray, cv2.ROTATE_90_COUNTERCLOCKWISE)
    
    # Save rotated
    cv2.imwrite('debug_vertical_issue_rotated.png', rotated)
    print(f"💾 Saved: debug_vertical_issue_rotated.png")
    
    # Resize for better OCR (scale up)
    scale = 3.0
    rotated_large = cv2.resize(rotated, None, fx=scale, fy=scale, interpolation=cv2.INTER_CUBIC)
    
    # Apply CLAHE for contrast enhancement
    clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8,8))
    enhanced = clahe.apply(rotated_large)
    
    # Try multiple thresholding methods
    print("\n🔍 Trying different preprocessing methods...")
    
    results = []
    
    # Method 1: Otsu thresholding
    _, thresh1 = cv2.threshold(enhanced, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    cv2.imwrite('debug_vertical_issue_otsu.png', thresh1)
    text1 = pytesseract.image_to_string(thresh1, lang='eng+amh', config='--oem 3 --psm 6')
    results.append(('Otsu', text1))
    print(f"  Method 1 (Otsu): '{text1.strip()}'")
    
    # Method 2: Adaptive thresholding
    thresh2 = cv2.adaptiveThreshold(enhanced, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 11, 2)
    cv2.imwrite('debug_vertical_issue_adaptive.png', thresh2)
    text2 = pytesseract.image_to_string(thresh2, lang='eng+amh', config='--oem 3 --psm 6')
    results.append(('Adaptive', text2))
    print(f"  Method 2 (Adaptive): '{text2.strip()}'")
    
    # Method 3: Simple threshold
    _, thresh3 = cv2.threshold(enhanced, 127, 255, cv2.THRESH_BINARY)
    cv2.imwrite('debug_vertical_issue_simple.png', thresh3)
    text3 = pytesseract.image_to_string(thresh3, lang='eng+amh', config='--oem 3 --psm 6')
    results.append(('Simple', text3))
    print(f"  Method 3 (Simple): '{text3.strip()}'")
    
    # Method 4: Inverted threshold (white text on black)
    _, thresh4 = cv2.threshold(enhanced, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)
    cv2.imwrite('debug_vertical_issue_inverted.png', thresh4)
    text4 = pytesseract.image_to_string(thresh4, lang='eng+amh', config='--oem 3 --psm 6')
    results.append(('Inverted', text4))
    print(f"  Method 4 (Inverted): '{text4.strip()}'")
    
    # Find the best result (longest text with date patterns)
    best_text = ""
    best_method = ""
    for method, text in results:
        if len(text.strip()) > len(best_text):
            best_text = text.strip()
            best_method = method
    
    print(f"\n✓ Best result from: {best_method}")
    print(f"📝 Raw text: '{best_text}'")
    
    # Parse dates from the text
    print("\n🔍 Parsing dates...")
    
    # Clean up common OCR errors
    cleaned = best_text.replace('O', '0').replace('o', '0')
    cleaned = cleaned.replace('l', '1').replace('I', '1')
    cleaned = cleaned.replace('S', '5').replace('s', '5')
    cleaned = cleaned.replace('B', '8')
    
    # Look for Gregorian date (YYYY/MM/DD)
    gregorian_pattern = r'(\d{4}[/\-]\d{2}[/\-]\d{2})'
    gregorian_matches = re.findall(gregorian_pattern, cleaned)
    
    # Look for Ethiopian date (YYYY/Mon/DD)
    ethiopian_pattern = r'(\d{4}[/\-][A-Za-z]{3}[/\-]\d{2})'
    ethiopian_matches = re.findall(ethiopian_pattern, cleaned)
    
    issue_date_en = gregorian_matches[0] if gregorian_matches else ""
    issue_date_am = ethiopian_matches[0] if ethiopian_matches else ""
    
    print(f"✓ Issue Date (English): {issue_date_en}")
    print(f"✓ Issue Date (Amharic): {issue_date_am}")
    
    print("\n" + "="*80)
    print("SUMMARY")
    print("="*80)
    
    if issue_date_en or issue_date_am:
        print("✅ Successfully extracted issue dates!")
        print(f"   English: {issue_date_en}")
        print(f"   Amharic: {issue_date_am}")
    else:
        print("❌ Could not extract issue dates")
        print("   Check the debug images:")
        print("   - debug_vertical_issue_original.png")
        print("   - debug_vertical_issue_rotated.png")
        print("   - debug_vertical_issue_otsu.png")
        print("   - debug_vertical_issue_adaptive.png")
        print("   - debug_vertical_issue_simple.png")
        print("   - debug_vertical_issue_inverted.png")
    
    print("="*80)
    
    return issue_date_en, issue_date_am

if __name__ == "__main__":
    if len(sys.argv) > 1:
        image_path = sys.argv[1]
    else:
        # Try common paths
        possible_paths = [
            'uploads/front_card.jpg',
            'uploads/front_card.png',
            'sample_front_card.jpg',
            'front_card.jpg',
        ]
        
        image_path = None
        for path in possible_paths:
            if os.path.exists(path):
                image_path = path
                break
        
        if not image_path:
            print("Usage: python test_vertical_issue_date.py <front_card_image>")
            print("\nOr save your front card image as one of:")
            for path in possible_paths:
                print(f"  - {path}")
            sys.exit(1)
    
    extract_vertical_issue_date(image_path)
