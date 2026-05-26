"""
Debug Amharic extraction from actual ID card images
"""
import cv2
import pytesseract
import numpy as np
from PIL import Image

# Set Tesseract path
pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'

def test_name_region_extraction():
    """Test extraction from the name region specifically"""
    
    # Use the cropped front image from static folder
    image_path = r"app\static\front_cropped.png"
    
    print("=" * 70)
    print("Testing Amharic Name Extraction from Front ID Card")
    print("=" * 70)
    print()
    
    try:
        # Read image
        img = cv2.imread(image_path)
        if img is None:
            print(f"❌ Could not read image: {image_path}")
            return
        
        height, width = img.shape[:2]
        print(f"✓ Image loaded: {width}x{height}")
        print()
        
        # Extract name region (56-66% of height)
        y1 = int(height * 0.56)
        y2 = int(height * 0.66)
        x1 = int(width * 0.05)
        x2 = int(width * 0.95)
        
        name_region = img[y1:y2, x1:x2]
        
        # Save the region for inspection
        cv2.imwrite("debug_name_region.png", name_region)
        print(f"✓ Name region extracted: {name_region.shape[1]}x{name_region.shape[0]}")
        print(f"  Saved to: debug_name_region.png")
        print()
        
        # Convert to grayscale
        gray = cv2.cvtColor(name_region, cv2.COLOR_BGR2GRAY)
        
        # Upscale for better OCR
        scale = 3.0
        gray = cv2.resize(gray, None, fx=scale, fy=scale, interpolation=cv2.INTER_CUBIC)
        
        # Try different preprocessing methods
        print("Testing different OCR configurations:")
        print("-" * 70)
        
        # Test 1: Amharic only with OTSU threshold
        print("\n1. Amharic only (lang='amh') with OTSU threshold:")
        _, thresh = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
        cv2.imwrite("debug_name_thresh.png", thresh)
        text_amh = pytesseract.image_to_string(thresh, lang='amh', config='--oem 3 --psm 6')
        print(f"   Result: '{text_amh.strip()}'")
        
        # Test 2: English only
        print("\n2. English only (lang='eng'):")
        text_eng = pytesseract.image_to_string(thresh, lang='eng', config='--oem 3 --psm 6')
        print(f"   Result: '{text_eng.strip()}'")
        
        # Test 3: Both languages (Amharic first)
        print("\n3. Both languages (lang='amh+eng'):")
        text_both = pytesseract.image_to_string(thresh, lang='amh+eng', config='--oem 3 --psm 6')
        print(f"   Result: '{text_both.strip()}'")
        
        # Test 4: With bilateral filter
        print("\n4. With bilateral filter (lang='amh+eng'):")
        bilateral = cv2.bilateralFilter(gray, 9, 75, 75)
        _, thresh_bilateral = cv2.threshold(bilateral, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
        cv2.imwrite("debug_name_bilateral.png", thresh_bilateral)
        text_bilateral = pytesseract.image_to_string(thresh_bilateral, lang='amh+eng', config='--oem 3 --psm 6')
        print(f"   Result: '{text_bilateral.strip()}'")
        
        # Test 5: With CLAHE (contrast enhancement)
        print("\n5. With CLAHE contrast enhancement (lang='amh+eng'):")
        clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8,8))
        enhanced = clahe.apply(gray)
        _, thresh_clahe = cv2.threshold(enhanced, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
        cv2.imwrite("debug_name_clahe.png", thresh_clahe)
        text_clahe = pytesseract.image_to_string(thresh_clahe, lang='amh+eng', config='--oem 3 --psm 6')
        print(f"   Result: '{text_clahe.strip()}'")
        
        # Test 6: With adaptive threshold
        print("\n6. With adaptive threshold (lang='amh+eng'):")
        adaptive = cv2.adaptiveThreshold(gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, 
                                        cv2.THRESH_BINARY, 11, 2)
        cv2.imwrite("debug_name_adaptive.png", adaptive)
        text_adaptive = pytesseract.image_to_string(adaptive, lang='amh+eng', config='--oem 3 --psm 6')
        print(f"   Result: '{text_adaptive.strip()}'")
        
        # Test 7: PSM 7 (single line)
        print("\n7. Single line mode PSM 7 (lang='amh+eng'):")
        text_psm7 = pytesseract.image_to_string(thresh, lang='amh+eng', config='--oem 3 --psm 7')
        print(f"   Result: '{text_psm7.strip()}'")
        
        # Test 8: PSM 3 (fully automatic)
        print("\n8. Fully automatic PSM 3 (lang='amh+eng'):")
        text_psm3 = pytesseract.image_to_string(thresh, lang='amh+eng', config='--oem 3 --psm 3')
        print(f"   Result: '{text_psm3.strip()}'")
        
        print()
        print("=" * 70)
        print("Analysis:")
        print("=" * 70)
        
        # Analyze which method gave best results
        all_results = [
            ("Amharic only", text_amh),
            ("English only", text_eng),
            ("Both (amh+eng)", text_both),
            ("Bilateral filter", text_bilateral),
            ("CLAHE", text_clahe),
            ("Adaptive threshold", text_adaptive),
            ("PSM 7", text_psm7),
            ("PSM 3", text_psm3),
        ]
        
        # Check for Amharic characters
        for method, text in all_results:
            has_amharic = any('\u1200' <= c <= '\u137F' for c in text)
            has_english = any(c.isascii() and c.isalpha() for c in text)
            print(f"\n{method}:")
            print(f"  - Has Amharic: {'✓' if has_amharic else '✗'}")
            print(f"  - Has English: {'✓' if has_english else '✗'}")
            print(f"  - Length: {len(text.strip())} chars")
            if has_amharic:
                # Extract just Amharic characters
                amharic_chars = ''.join(c for c in text if '\u1200' <= c <= '\u137F' or c.isspace())
                print(f"  - Amharic text: '{amharic_chars.strip()}'")
        
        print()
        print("Check the debug images saved in the current directory:")
        print("  - debug_name_region.png (original region)")
        print("  - debug_name_thresh.png (OTSU threshold)")
        print("  - debug_name_bilateral.png (bilateral filter)")
        print("  - debug_name_clahe.png (CLAHE)")
        print("  - debug_name_adaptive.png (adaptive threshold)")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_name_region_extraction()
