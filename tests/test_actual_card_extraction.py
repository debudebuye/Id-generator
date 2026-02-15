#!/usr/bin/env python3
"""
Test extraction on the actual card image provided by user
This will help diagnose why Issue Date is not being extracted
"""

import cv2
import numpy as np
import pytesseract
from PIL import Image
import os
import sys

def extract_issue_date_from_edge(image_path):
    """
    Extract the vertical issue date from the right edge of the card
    Based on the actual card image: "2018/06/02 | 2026/Feb/09"
    """
    
    print("="*80)
    print("EXTRACTING ISSUE DATE FROM RIGHT EDGE")
    print("="*80)
    
    # Read image
    img = cv2.imread(image_path)
    if img is None:
        print(f"❌ Could not read image: {image_path}")
        return None
    
    height, width = img.shape[:2]
    print(f"📐 Image dimensions: {width}x{height}")
    
    # The issue date is on the right edge, running vertically
    # From the Adobe coordinates: x=892-937, y=576-1092 (for reference 900x1650)
    # Let's extract a wider region to ensure we capture it
    
    # Calculate region (right edge, full height)
    ref_width = 900
    ref_height = 1650
    
    # Issue date region - make it wider to ensure capture
    x1_percent = 880 / ref_width  # Start a bit earlier
    x2_percent = 1.0  # Go to edge
    y1_percent = 500 / ref_height  # Start a bit higher
    y2_percent = 1150 / ref_height  # End a bit lower
    
    x1_px = int(x1_percent * width)
    x2_px = int(x2_percent * width)
    y1_px = int(y1_percent * height)
    y2_px = int(y2_percent * height)
    
    print(f"📍 Extracting region: ({x1_px}, {y1_px}) to ({x2_px}, {y2_px})")
    print(f"📏 Region size: {x2_px-x1_px}x{y2_px-y1_px}")
    
    # Extract region
    region = img[y1_px:y2_px, x1_px:x2_px]
    
    # Save original
    cv2.imwrite('debug_issue_date_edge_original.png', region)
    print("💾 Saved: debug_issue_date_edge_original.png")
    
    # Convert to grayscale
    gray = cv2.cvtColor(region, cv2.COLOR_BGR2GRAY)
    
    # Rotate 90 degrees counterclockwise (vertical text becomes horizontal)
    rotated = cv2.rotate(gray, cv2.ROTATE_90_COUNTERCLOCKWISE)
    
    # Save rotated
    cv2.imwrite('debug_issue_date_edge_rotated.png', rotated)
    print("💾 Saved: debug_issue_date_edge_rotated.png")
    
    # Resize for better OCR
    scale = 3.0
    rotated_large = cv2.resize(rotated, None, fx=scale, fy=scale, interpolation=cv2.INTER_CUBIC)
    
    # Try multiple preprocessing methods
    results = []
    
    # Method 1: CLAHE + Otsu
    print("\n🔍 Method 1: CLAHE + Otsu")
    clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8,8))
    enhanced = clahe.apply(rotated_large)
    _, thresh1 = cv2.threshold(enhanced, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    cv2.imwrite('debug_issue_date_method1.png', thresh1)
    
    config = '--oem 3 --psm 6'
    text1 = pytesseract.image_to_string(thresh1, lang='eng+amh', config=config)
    print(f"   Result: '{text1.strip()}'")
    results.append(('Method 1 (CLAHE+Otsu)', text1.strip()))
    
    # Method 2: Adaptive threshold
    print("\n🔍 Method 2: Adaptive Threshold")
    adaptive = cv2.adaptiveThreshold(rotated_large, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, 
                                     cv2.THRESH_BINARY, 11, 2)
    cv2.imwrite('debug_issue_date_method2.png', adaptive)
    
    text2 = pytesseract.image_to_string(adaptive, lang='eng+amh', config=config)
    print(f"   Result: '{text2.strip()}'")
    results.append(('Method 2 (Adaptive)', text2.strip()))
    
    # Method 3: Bilateral filter + threshold
    print("\n🔍 Method 3: Bilateral Filter")
    bilateral = cv2.bilateralFilter(rotated_large, 9, 75, 75)
    _, thresh3 = cv2.threshold(bilateral, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    cv2.imwrite('debug_issue_date_method3.png', thresh3)
    
    text3 = pytesseract.image_to_string(thresh3, lang='eng+amh', config=config)
    print(f"   Result: '{text3.strip()}'")
    results.append(('Method 3 (Bilateral)', text3.strip()))
    
    # Method 4: Invert + CLAHE (for light text on dark background)
    print("\n🔍 Method 4: Inverted + CLAHE")
    inverted = cv2.bitwise_not(rotated_large)
    clahe2 = cv2.createCLAHE(clipLimit=3.0, tileGridSize=(8,8))
    enhanced2 = clahe2.apply(inverted)
    _, thresh4 = cv2.threshold(enhanced2, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    cv2.imwrite('debug_issue_date_method4.png', thresh4)
    
    text4 = pytesseract.image_to_string(thresh4, lang='eng+amh', config=config)
    print(f"   Result: '{text4.strip()}'")
    results.append(('Method 4 (Inverted)', text4.strip()))
    
    # Method 5: Simple threshold with different values
    print("\n🔍 Method 5: Fixed Threshold (150)")
    _, thresh5 = cv2.threshold(rotated_large, 150, 255, cv2.THRESH_BINARY)
    cv2.imwrite('debug_issue_date_method5.png', thresh5)
    
    text5 = pytesseract.image_to_string(thresh5, lang='eng+amh', config=config)
    print(f"   Result: '{text5.strip()}'")
    results.append(('Method 5 (Thresh 150)', text5.strip()))
    
    # Analyze results
    print("\n" + "="*80)
    print("RESULTS SUMMARY")
    print("="*80)
    
    import re
    
    best_result = None
    best_score = 0
    
    for method, text in results:
        # Look for date patterns
        gregorian = re.findall(r'\d{4}[/\-]\d{2}[/\-]\d{2}', text)
        ethiopian = re.findall(r'\d{4}[/\-][A-Za-z]{3}[/\-]\d{2}', text)
        
        score = len(gregorian) + len(ethiopian)
        
        print(f"\n{method}:")
        print(f"  Gregorian dates found: {gregorian}")
        print(f"  Ethiopian dates found: {ethiopian}")
        print(f"  Score: {score}")
        
        if score > best_score:
            best_score = score
            best_result = {
                'method': method,
                'text': text,
                'gregorian': gregorian,
                'ethiopian': ethiopian
            }
    
    if best_result and best_score > 0:
        print("\n" + "="*80)
        print("✅ BEST RESULT")
        print("="*80)
        print(f"Method: {best_result['method']}")
        print(f"Gregorian: {best_result['gregorian']}")
        print(f"Ethiopian: {best_result['ethiopian']}")
        
        return {
            'issue_date_en': best_result['gregorian'][0] if best_result['gregorian'] else '',
            'issue_date_am': best_result['ethiopian'][0] if best_result['ethiopian'] else ''
        }
    else:
        print("\n" + "="*80)
        print("❌ NO DATES FOUND")
        print("="*80)
        print("The vertical text on the right edge is too difficult to extract.")
        print("Recommendation: Use manual entry for Issue Date")
        return None

def test_full_card_extraction(image_path):
    """Test extraction of all fields from the card"""
    
    print("\n" + "="*80)
    print("TESTING FULL CARD EXTRACTION")
    print("="*80)
    
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'app'))
    from services.ocr_extraction_service import OCRExtractionService
    
    ocr_service = OCRExtractionService()
    
    # Extract regions
    print("\n1️⃣ Extracting text regions...")
    regions = ocr_service.extract_text_regions(image_path)
    
    # Get full text
    print("\n2️⃣ Extracting full text...")
    full_text = ocr_service.extract_text_from_image(image_path)
    
    # Parse data
    print("\n3️⃣ Parsing front card data...")
    data = ocr_service.parse_front_card_data(full_text, image_path)
    
    # Show results
    print("\n" + "="*80)
    print("EXTRACTION RESULTS")
    print("="*80)
    
    fields = [
        ('Full Name (English)', data.get('full_name_en', '')),
        ('Full Name (Amharic)', data.get('full_name_am', '')),
        ('Date of Birth', data.get('date_of_birth', '')),
        ('Sex', data.get('sex', '')),
        ('Date of Expiry', data.get('date_of_expiry', '')),
        ('Date of Issue', data.get('date_of_issue', '')),
        ('FAN Number', data.get('fan', '')),
    ]
    
    for field_name, value in fields:
        status = "✅" if value else "❌"
        print(f"{status} {field_name}: {value}")
    
    return data

if __name__ == "__main__":
    if len(sys.argv) > 1:
        image_path = sys.argv[1]
    else:
        # Try to find the uploaded image
        possible_paths = [
            'uploads/front_card.jpg',
            'uploads/front_card.png',
            'uploads/front.jpg',
            'uploads/front.png',
            'sample_front_card.jpg',
            'front_card.jpg',
        ]
        
        image_path = None
        for path in possible_paths:
            if os.path.exists(path):
                image_path = path
                break
        
        if not image_path:
            print("Usage: python test_actual_card_extraction.py <front_card_image>")
            print("\nOr save your front card image as one of:")
            for path in possible_paths:
                print(f"  - {path}")
            sys.exit(1)
    
    # Test issue date extraction from edge
    issue_dates = extract_issue_date_from_edge(image_path)
    
    # Test full card extraction
    all_data = test_full_card_extraction(image_path)
    
    # Final summary
    print("\n" + "="*80)
    print("FINAL SUMMARY")
    print("="*80)
    
    if issue_dates:
        print(f"✅ Issue Date (English): {issue_dates.get('issue_date_en', '')}")
        print(f"✅ Issue Date (Amharic): {issue_dates.get('issue_date_am', '')}")
    else:
        print("❌ Issue Date: Could not extract from vertical text")
        print("   Expected: 2018/06/02 | 2026/Feb/09")
        print("   Recommendation: Use manual entry")
    
    print("\n💡 Next Steps:")
    print("   1. Check the debug_issue_date_*.png files to see preprocessing results")
    print("   2. If extraction failed, use manual entry in the preview page")
    print("   3. The preview page has editable fields for all dates")
    
    print("\n" + "="*80)
