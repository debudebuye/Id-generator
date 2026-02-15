"""
Debug FAN extraction from front card
"""
import cv2
import pytesseract
import numpy as np

# Set Tesseract path
pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'

# Use the cropped front image
image_path = r"app\static\front_cropped.png"

print("=" * 70)
print("Front Card FAN Extraction Debug")
print("=" * 70)
print()

img = cv2.imread(image_path)
if img is None:
    print(f"❌ Could not read image: {image_path}")
    exit(1)

height, width = img.shape[:2]
print(f"✓ Image loaded: {width}x{height}")
print()

# Try different regions for FAN (it's in the barcode area)
fan_regions = {
    'current': (0.30, 0.85, 0.70, 0.92),  # Current region
    'wider': (0.20, 0.85, 0.80, 0.92),    # Wider region
    'higher': (0.30, 0.82, 0.70, 0.89),   # Higher up
    'lower': (0.30, 0.88, 0.70, 0.95),    # Lower down
    'full_barcode': (0.15, 0.82, 0.85, 0.96),  # Full barcode area
}

for region_name, (x1, y1, x2, y2) in fan_regions.items():
    print(f"\n{region_name.upper()} REGION:")
    print("-" * 70)
    
    # Convert percentages to pixels
    x1_px = int(x1 * width)
    y1_px = int(y1 * height)
    x2_px = int(x2 * width)
    y2_px = int(y2 * height)
    
    print(f"  Region: ({x1_px}, {y1_px}) to ({x2_px}, {y2_px})")
    print(f"  Size: {x2_px-x1_px}x{y2_px-y1_px}")
    
    # Extract region
    region_img = img[y1_px:y2_px, x1_px:x2_px]
    
    # Save region
    region_filename = f"debug_fan_{region_name}.png"
    cv2.imwrite(region_filename, region_img)
    print(f"  Saved: {region_filename}")
    
    # Convert to grayscale
    gray = cv2.cvtColor(region_img, cv2.COLOR_BGR2GRAY)
    
    # Resize for better OCR
    scale = 3.0
    gray = cv2.resize(gray, None, fx=scale, fy=scale, interpolation=cv2.INTER_CUBIC)
    
    # Try different preprocessing
    print(f"\n  OCR Attempts:")
    
    # Method 1: OTSU threshold
    _, thresh1 = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    cv2.imwrite(f"debug_fan_{region_name}_otsu.png", thresh1)
    text1 = pytesseract.image_to_string(thresh1, lang='eng', config='--oem 3 --psm 7 -c tessedit_char_whitelist=0123456789')
    print(f"    1. OTSU + numbers only: '{text1.strip()}'")
    
    # Method 2: CLAHE
    clahe = cv2.createCLAHE(clipLimit=3.0, tileGridSize=(8,8))
    enhanced = clahe.apply(gray)
    _, thresh2 = cv2.threshold(enhanced, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    text2 = pytesseract.image_to_string(thresh2, lang='eng', config='--oem 3 --psm 7 -c tessedit_char_whitelist=0123456789')
    print(f"    2. CLAHE + numbers only: '{text2.strip()}'")
    
    # Method 3: No whitelist
    text3 = pytesseract.image_to_string(thresh1, lang='eng', config='--oem 3 --psm 7')
    print(f"    3. OTSU + no whitelist: '{text3.strip()}'")
    
    # Method 4: PSM 6 (block)
    text4 = pytesseract.image_to_string(thresh1, lang='eng', config='--oem 3 --psm 6 -c tessedit_char_whitelist=0123456789')
    print(f"    4. OTSU + PSM 6: '{text4.strip()}'")

print()
print("=" * 70)
print("✓ Check the debug_fan_*.png files for extracted regions")
print("=" * 70)
