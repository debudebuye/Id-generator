#!/usr/bin/env python3
"""
Debug script to visualize and test name extraction regions
"""
import cv2
import pytesseract
import numpy as np

def test_name_extraction(image_path):
    """Test name extraction with different region sizes"""
    
    img = cv2.imread(image_path)
    if img is None:
        print(f"❌ Could not read image: {image_path}")
        return
    
    height, width = img.shape[:2]
    print(f"📐 Image dimensions: {width}x{height}")
    
    # Reference dimensions
    ref_width = 591
    ref_height = 1280
    
    # Test different region configurations
    test_regions = {
        'Original (100-478)': (100/ref_width, 664/ref_height, 478/ref_width, 686/ref_height),
        'Extended (85-490)': (85/ref_width, 664/ref_height, 490/ref_width, 686/ref_height),
        'Wide (70-500)': (70/ref_width, 664/ref_height, 500/ref_width, 686/ref_height),
        'Extra Wide (60-510)': (60/ref_width, 664/ref_height, 510/ref_width, 686/ref_height),
    }
    
    print("\n" + "="*80)
    print("Testing different region sizes for Amharic name extraction:")
    print("="*80)
    
    for region_name, (x1, y1, x2, y2) in test_regions.items():
        # Convert percentages to pixels
        x1_px = int(x1 * width)
        y1_px = int(y1 * height)
        x2_px = int(x2 * width)
        y2_px = int(y2 * height)
        
        # Add padding
        padding_x = 5
        padding_y = 2
        x1_px = max(0, x1_px - padding_x)
        y1_px = max(0, y1_px - padding_y)
        x2_px = min(width, x2_px + padding_x)
        y2_px = min(height, y2_px + padding_y)
        
        # Extract region
        region_img = img[y1_px:y2_px, x1_px:x2_px]
        
        # Convert to grayscale
        gray = cv2.cvtColor(region_img, cv2.COLOR_BGR2GRAY)
        
        # Resize for better OCR
        scale = 3.0
        gray = cv2.resize(gray, None, fx=scale, fy=scale, interpolation=cv2.INTER_CUBIC)
        
        # Preprocess
        bilateral = cv2.bilateralFilter(gray, 9, 75, 75)
        _, thresh = cv2.threshold(bilateral, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
        
        # OCR with Amharic priority
        config = '--oem 3 --psm 7'
        text = pytesseract.image_to_string(thresh, lang='amh+eng', config=config).strip()
        
        print(f"\n{region_name}:")
        print(f"  Region: ({x1_px}, {y1_px}) to ({x2_px}, {y2_px})")
        print(f"  Size: {x2_px-x1_px}x{y2_px-y1_px} pixels")
        print(f"  Extracted: '{text}'")
        print(f"  Length: {len(text)} characters")
        
        # Save debug image
        debug_filename = f"debug_name_{region_name.replace(' ', '_').replace('(', '').replace(')', '')}.png"
        cv2.imwrite(debug_filename, thresh)
        print(f"  Saved: {debug_filename}")
    
    print("\n" + "="*80)
    print("✓ Test complete. Check the debug_name_*.png files to see the extracted regions.")
    print("="*80)

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python debug_name_extraction.py <front_card_image_path>")
        print("\nExample:")
        print("  python debug_name_extraction.py app/static/front_cropped.png")
        sys.exit(1)
    
    image_path = sys.argv[1]
    test_name_extraction(image_path)
