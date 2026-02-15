#!/usr/bin/env python3
"""
Diagnose why specific fields are missing from extraction
"""
import sys
import os
import cv2
import pytesseract

# Add app to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'app'))

from services.ocr_extraction_service import OCRExtractionService

def diagnose_field(image_path, field_name, coords, ref_width=900, ref_height=1650):
    """Diagnose a specific field extraction"""
    
    img = cv2.imread(image_path)
    if img is None:
        print(f"❌ Could not read image")
        return
    
    height, width = img.shape[:2]
    
    # Convert coordinates
    x1, y1, x2, y2 = coords
    x1_px = int(x1 * width)
    y1_px = int(y1 * height)
    x2_px = int(x2 * width)
    y2_px = int(y2 * height)
    
    print(f"\n{'='*80}")
    print(f"DIAGNOSING: {field_name}")
    print(f"{'='*80}")
    print(f"Image size: {width}x{height}")
    print(f"Region: ({x1_px},{y1_px}) to ({x2_px},{y2_px})")
    print(f"Region size: {x2_px-x1_px}x{y2_px-y1_px}")
    
    # Extract region
    region_img = img[y1_px:y2_px, x1_px:x2_px]
    
    # Save region for inspection
    region_filename = f"debug_{field_name}_region.png"
    cv2.imwrite(region_filename, region_img)
    print(f"✓ Saved region image: {region_filename}")
    
    # Convert to grayscale
    gray = cv2.cvtColor(region_img, cv2.COLOR_BGR2GRAY)
    
    # Resize for better OCR
    scale = 2.0
    gray = cv2.resize(gray, None, fx=scale, fy=scale, interpolation=cv2.INTER_CUBIC)
    
    # Try different preprocessing methods
    methods = []
    
    # Method 1: Bilateral + OTSU
    bilateral = cv2.bilateralFilter(gray, 9, 75, 75)
    _, thresh1 = cv2.threshold(bilateral, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    methods.append(("Bilateral+OTSU", thresh1))
    
    # Method 2: CLAHE + OTSU
    clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8,8))
    enhanced = clahe.apply(gray)
    _, thresh2 = cv2.threshold(enhanced, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    methods.append(("CLAHE+OTSU", thresh2))
    
    # Method 3: Simple threshold
    _, thresh3 = cv2.threshold(gray, 127, 255, cv2.THRESH_BINARY)
    methods.append(("Simple_127", thresh3))
    
    # Method 4: Adaptive threshold
    thresh4 = cv2.adaptiveThreshold(gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 11, 2)
    methods.append(("Adaptive", thresh4))
    
    # Try OCR on each method
    print(f"\nTrying different preprocessing methods:")
    print(f"{'-'*80}")
    
    best_text = ""
    best_method = ""
    
    for method_name, processed in methods:
        # Save processed image
        processed_filename = f"debug_{field_name}_{method_name}.png"
        cv2.imwrite(processed_filename, processed)
        
        # Try different PSM modes
        psm_modes = [
            (7, "Single line"),
            (6, "Uniform block"),
            (3, "Fully automatic"),
        ]
        
        for psm, psm_desc in psm_modes:
            config = f'--oem 3 --psm {psm}'
            
            # Determine language
            lang = 'eng+amh'
            if 'fan' in field_name.lower():
                lang = 'eng'
                config += ' -c tessedit_char_whitelist=0123456789'
            
            # Handle vertical text (issue dates)
            if 'issue' in field_name.lower():
                rotated = cv2.rotate(processed, cv2.ROTATE_90_COUNTERCLOCKWISE)
                text = pytesseract.image_to_string(rotated, lang=lang, config=config).strip()
            else:
                text = pytesseract.image_to_string(processed, lang=lang, config=config).strip()
            
            if text and len(text) > len(best_text):
                best_text = text
                best_method = f"{method_name} + PSM{psm}"
            
            if text:
                print(f"  {method_name:15} PSM{psm} ({psm_desc:15}): {text[:60]}")
    
    print(f"{'-'*80}")
    if best_text:
        print(f"✅ BEST RESULT ({best_method}):")
        print(f"   {best_text}")
    else:
        print(f"❌ NO TEXT EXTRACTED")
        print(f"   Possible issues:")
        print(f"   - Region coordinates are incorrect")
        print(f"   - Image quality is too low")
        print(f"   - Text is too small or blurry")
        print(f"   - Wrong language pack (need Amharic for ሴት/ወንድ)")

def main(image_path):
    """Diagnose all fields"""
    
    if not os.path.exists(image_path):
        print(f"❌ Image not found: {image_path}")
        return
    
    print("=" * 80)
    print("FIELD EXTRACTION DIAGNOSTICS")
    print("=" * 80)
    print(f"Image: {image_path}\n")
    
    # Adobe coordinates (as percentages)
    ref_width = 900
    ref_height = 1650
    
    fields = {
        'full_name_am': (205/ref_width, 1209/ref_height, 880/ref_width, 1256/ref_height),
        'full_name_en': (202/ref_width, 1257/ref_height, 877/ref_width, 1304/ref_height),
        'dob_gregorian': (197/ref_width, 1339/ref_height, 380/ref_width, 1386/ref_height),
        'dob_ethiopian': (389/ref_width, 1339/ref_height, 798/ref_width, 1388/ref_height),
        'sex_am': (201/ref_width, 1413/ref_height, 264/ref_width, 1462/ref_height),
        'sex_en': (265/ref_width, 1403/ref_height, 390/ref_width, 1452/ref_height),
        'expiry_gregorian': (201/ref_width, 1495/ref_height, 376/ref_width, 1538/ref_height),
        'expiry_ethiopian': (387/ref_width, 1489/ref_height, 726/ref_width, 1538/ref_height),
        'fan_number': (321/ref_width, 1577/ref_height, 748/ref_width, 1604/ref_height),
        'issue_gregorian': (892/ref_width, 576/ref_height, 937/ref_width, 854/ref_height),
        'issue_ethiopian': (895/ref_width, 861/ref_height, 940/ref_width, 1092/ref_height),
    }
    
    # Ask which fields to diagnose
    print("Which fields are missing? (comma-separated, or 'all'):")
    for i, field_name in enumerate(fields.keys(), 1):
        print(f"  {i}. {field_name}")
    
    choice = input("\nEnter field names or numbers (or 'all'): ").strip().lower()
    
    if choice == 'all':
        selected_fields = list(fields.keys())
    else:
        # Parse input
        selected_fields = []
        for part in choice.split(','):
            part = part.strip()
            if part.isdigit():
                idx = int(part) - 1
                if 0 <= idx < len(fields):
                    selected_fields.append(list(fields.keys())[idx])
            elif part in fields:
                selected_fields.append(part)
    
    if not selected_fields:
        print("No fields selected. Diagnosing all fields...")
        selected_fields = list(fields.keys())
    
    # Diagnose each selected field
    for field_name in selected_fields:
        coords = fields[field_name]
        diagnose_field(image_path, field_name, coords, ref_width, ref_height)
    
    print(f"\n{'='*80}")
    print("DIAGNOSIS COMPLETE")
    print(f"{'='*80}")
    print(f"Check debug_*_region.png files to see what each region contains")
    print(f"Check debug_*_*.png files to see different preprocessing results")

if __name__ == "__main__":
    if len(sys.argv) > 1:
        main(sys.argv[1])
    else:
        print("Usage: python diagnose_missing_fields.py <image_path>")
        print("\nExample:")
        print("  python diagnose_missing_fields.py uploads/front_card.jpg")
