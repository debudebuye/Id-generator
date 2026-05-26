"""
Debug back card region extraction
"""
import cv2
import pytesseract
import numpy as np

# Set Tesseract path
pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'

# Use the cropped back image
image_path = r"app\static\back_cropped.png"

print("=" * 70)
print("Back Card Region Extraction Debug")
print("=" * 70)
print()

img = cv2.imread(image_path)
if img is None:
    print(f"❌ Could not read image: {image_path}")
    exit(1)

height, width = img.shape[:2]
print(f"✓ Image loaded: {width}x{height}")
print()

# Define regions for back card
regions = {
    'phone_number': (0.05, 0.63, 0.48, 0.68),
    'fin_number': (0.52, 0.63, 0.95, 0.68),
    'nationality': (0.05, 0.69, 0.95, 0.76),
    'address': (0.05, 0.77, 0.95, 1.0),
}

# Create a copy for visualization
vis_img = img.copy()

for region_name, (x1, y1, x2, y2) in regions.items():
    print(f"\n{region_name.upper()}:")
    print("-" * 70)
    
    # Convert percentages to pixels
    x1_px = int(x1 * width)
    y1_px = int(y1 * height)
    x2_px = int(x2 * width)
    y2_px = int(y2 * height)
    
    print(f"  Region: ({x1_px}, {y1_px}) to ({x2_px}, {y2_px})")
    print(f"  Size: {x2_px-x1_px}x{y2_px-y1_px}")
    
    # Draw rectangle on visualization
    color = (0, 255, 0) if region_name in ['phone_number', 'fin_number'] else (255, 0, 0)
    cv2.rectangle(vis_img, (x1_px, y1_px), (x2_px, y2_px), color, 2)
    cv2.putText(vis_img, region_name, (x1_px, y1_px-5), 
                cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 2)
    
    # Extract region
    region_img = img[y1_px:y2_px, x1_px:x2_px]
    
    # Save region
    region_filename = f"debug_back_{region_name}.png"
    cv2.imwrite(region_filename, region_img)
    print(f"  Saved: {region_filename}")
    
    # Convert to grayscale
    gray = cv2.cvtColor(region_img, cv2.COLOR_BGR2GRAY)
    
    # Resize for better OCR
    scale = 3.0
    gray = cv2.resize(gray, None, fx=scale, fy=scale, interpolation=cv2.INTER_CUBIC)
    
    # Apply preprocessing
    if region_name in ['phone_number', 'fin_number']:
        # For numbers
        clahe = cv2.createCLAHE(clipLimit=3.0, tileGridSize=(8,8))
        enhanced = clahe.apply(gray)
        _, thresh = cv2.threshold(enhanced, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
        
        # Save preprocessed
        cv2.imwrite(f"debug_back_{region_name}_processed.png", thresh)
        
        # Try different OCR configs
        print(f"\n  OCR Attempts:")
        
        # Config 1: Numbers only
        config1 = '--oem 3 --psm 7 -c tessedit_char_whitelist=0123456789'
        text1 = pytesseract.image_to_string(thresh, lang='eng', config=config1)
        print(f"    1. Numbers only (PSM 7): '{text1.strip()}'")
        
        # Config 2: PSM 6
        config2 = '--oem 3 --psm 6 -c tessedit_char_whitelist=0123456789'
        text2 = pytesseract.image_to_string(thresh, lang='eng', config=config2)
        print(f"    2. Numbers only (PSM 6): '{text2.strip()}'")
        
        # Config 3: PSM 8 (single word)
        config3 = '--oem 3 --psm 8 -c tessedit_char_whitelist=0123456789'
        text3 = pytesseract.image_to_string(thresh, lang='eng', config=config3)
        print(f"    3. Numbers only (PSM 8): '{text3.strip()}'")
        
        # Config 4: No whitelist
        config4 = '--oem 3 --psm 7'
        text4 = pytesseract.image_to_string(thresh, lang='eng', config=config4)
        print(f"    4. No whitelist (PSM 7): '{text4.strip()}'")
        
    else:
        # For text fields
        bilateral = cv2.bilateralFilter(gray, 9, 75, 75)
        _, thresh = cv2.threshold(bilateral, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
        
        # Save preprocessed
        cv2.imwrite(f"debug_back_{region_name}_processed.png", thresh)
        
        if region_name == 'address':
            config = '--oem 3 --psm 6'
        else:
            config = '--oem 3 --psm 7'
        
        text = pytesseract.image_to_string(thresh, lang='eng+amh', config=config)
        print(f"\n  OCR Result:")
        print(f"    '{text.strip()}'")

# Save visualization
cv2.imwrite("debug_back_regions_visualization.png", vis_img)
print()
print("=" * 70)
print("✓ Visualization saved: debug_back_regions_visualization.png")
print("✓ Check the debug_back_*.png files for extracted regions")
print("=" * 70)
