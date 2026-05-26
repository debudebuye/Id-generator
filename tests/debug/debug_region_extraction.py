"""
Debug region extraction - show what's being extracted from each region
"""
import cv2
import pytesseract
import numpy as np

pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'

# Read the front card image
front_image_path = r"app\static\front_cropped.png"
img = cv2.imread(front_image_path)

if img is None:
    print(f"❌ Could not read image: {front_image_path}")
    exit(1)

height, width = img.shape[:2]
print(f"📐 Image dimensions: {width}x{height}")
print()

# Current regions - UPDATED v2
regions = {
    'full_name': (0.05, 0.52, 0.95, 0.59),
    'date_of_birth': (0.05, 0.59, 0.95, 0.65),
    'sex': (0.05, 0.65, 0.50, 0.71),
    'date_of_expiry': (0.05, 0.71, 0.95, 0.77),
    'fan_number': (0.10, 0.78, 0.90, 0.85),
    'date_of_issue': (0.88, 0.10, 1.0, 0.70),
}

print("=" * 70)
print("EXTRACTING TEXT FROM EACH REGION:")
print("=" * 70)

for region_name, (x1, y1, x2, y2) in regions.items():
    print(f"\n{region_name.upper()}:")
    print(f"  Region: ({x1}, {y1}, {x2}, {y2})")
    
    # Convert percentages to pixels
    x1_px = int(x1 * width)
    y1_px = int(y1 * height)
    x2_px = int(x2 * width)
    y2_px = int(y2 * height)
    
    print(f"  Pixels: ({x1_px}, {y1_px}, {x2_px}, {y2_px})")
    print(f"  Size: {x2_px-x1_px}x{y2_px-y1_px}")
    
    # Extract region
    region_img = img[y1_px:y2_px, x1_px:x2_px]
    
    # Save region image for visual inspection
    region_filename = f"debug_region_{region_name}.png"
    cv2.imwrite(region_filename, region_img)
    
    # Convert to grayscale
    gray = cv2.cvtColor(region_img, cv2.COLOR_BGR2GRAY)
    
    # Resize for better OCR
    scale = 2.0
    gray = cv2.resize(gray, None, fx=scale, fy=scale, interpolation=cv2.INTER_CUBIC)
    
    # Apply preprocessing
    clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8,8))
    enhanced = clahe.apply(gray)
    _, thresh = cv2.threshold(enhanced, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    
    # Extract text
    config = '--oem 3 --psm 6'
    text = pytesseract.image_to_string(thresh, lang='eng+amh', config=config)
    
    print(f"  Extracted text:")
    for line in text.strip().split('\n'):
        if line.strip():
            print(f"    | {line}")
    
    print(f"  Saved: {region_filename}")

print("\n" + "=" * 70)
print("✅ Check debug_region_*.png files to see what each region contains")
print("   Adjust region coordinates if needed")
