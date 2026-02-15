"""
Diagnose OCR extraction regions to see what's being extracted
"""
import cv2
import numpy as np
import pytesseract
from PIL import Image, ImageDraw, ImageFont

def visualize_regions(image_path, output_path):
    """Visualize the regions being extracted"""
    img = cv2.imread(image_path)
    if img is None:
        print(f"Could not read image: {image_path}")
        return
    
    height, width = img.shape[:2]
    print(f"Image dimensions: {width}x{height}")
    
    # Reference dimensions from coordinates
    ref_width = 900
    ref_height = 1650
    
    # Define regions (same as in OCR service)
    regions = {
        'full_name_am': (205/ref_width, 1209/ref_height, (205+675)/ref_width, (1209+47)/ref_height),
        'full_name_en': (202/ref_width, 1257/ref_height, (202+675)/ref_width, (1257+47)/ref_height),
        'dob_gregorian': (197/ref_width, 1339/ref_height, (197+183)/ref_width, (1339+47)/ref_height),
        'dob_ethiopian': (389/ref_width, 1339/ref_height, (389+409)/ref_width, (1339+49)/ref_height),
        'sex_am': (201/ref_width, 1413/ref_height, (201+63)/ref_width, (1413+49)/ref_height),
        'sex_en': (265/ref_width, 1403/ref_height, (265+125)/ref_width, (1403+49)/ref_height),
        'expiry_gregorian': (201/ref_width, 1495/ref_height, (201+175)/ref_width, (1495+43)/ref_height),
        'expiry_ethiopian': (387/ref_width, 1489/ref_height, (387+339)/ref_width, (1489+49)/ref_height),
        'fan_number': (321/ref_width, 1577/ref_height, (321+427)/ref_width, (1577+27)/ref_height),
    }
    
    # Create visualization
    vis_img = img.copy()
    
    # Colors for different regions
    colors = [
        (255, 0, 0),    # Red
        (0, 255, 0),    # Green
        (0, 0, 255),    # Blue
        (255, 255, 0),  # Cyan
        (255, 0, 255),  # Magenta
        (0, 255, 255),  # Yellow
        (128, 0, 128),  # Purple
        (255, 128, 0),  # Orange
        (0, 128, 255),  # Sky blue
    ]
    
    print("\nExtracting regions:")
    print("="*80)
    
    for idx, (region_name, (x1, y1, x2, y2)) in enumerate(regions.items()):
        # Convert percentages to pixels
        x1_px = int(x1 * width)
        y1_px = int(y1 * height)
        x2_px = int(x2 * width)
        y2_px = int(y2 * height)
        
        # Draw rectangle
        color = colors[idx % len(colors)]
        cv2.rectangle(vis_img, (x1_px, y1_px), (x2_px, y2_px), color, 2)
        
        # Add label
        cv2.putText(vis_img, region_name, (x1_px, y1_px-5), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.4, color, 1)
        
        # Extract and OCR the region
        region_img = img[y1_px:y2_px, x1_px:x2_px]
        
        if region_img.size == 0:
            print(f"\n{region_name}: EMPTY REGION")
            continue
        
        # Save individual region
        region_filename = f"debug_region_{region_name}.png"
        cv2.imwrite(region_filename, region_img)
        
        # Convert to grayscale and preprocess
        gray = cv2.cvtColor(region_img, cv2.COLOR_BGR2GRAY)
        
        # Resize for better OCR
        scale = 2.0
        gray = cv2.resize(gray, None, fx=scale, fy=scale, interpolation=cv2.INTER_CUBIC)
        
        # Apply preprocessing
        if 'fan_number' in region_name:
            clahe = cv2.createCLAHE(clipLimit=3.0, tileGridSize=(8,8))
            enhanced = clahe.apply(gray)
            _, thresh = cv2.threshold(enhanced, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
            config = '--oem 3 --psm 7 -c tessedit_char_whitelist=0123456789'
            text = pytesseract.image_to_string(thresh, lang='eng', config=config)
        else:
            bilateral = cv2.bilateralFilter(gray, 9, 75, 75)
            _, thresh = cv2.threshold(bilateral, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
            config = '--oem 3 --psm 7'
            text = pytesseract.image_to_string(thresh, lang='eng+amh', config=config)
        
        text = text.strip()
        
        print(f"\n{region_name}:")
        print(f"  Coordinates: ({x1_px}, {y1_px}) to ({x2_px}, {y2_px})")
        print(f"  Size: {x2_px-x1_px}x{y2_px-y1_px} pixels")
        print(f"  Extracted text: '{text}'")
        print(f"  Saved to: {region_filename}")
    
    # Save visualization
    cv2.imwrite(output_path, vis_img)
    print(f"\n{'='*80}")
    print(f"Visualization saved to: {output_path}")

if __name__ == "__main__":
    print("Diagnosing FRONT card extraction...")
    visualize_regions("app/static/front_cropped.png", "debug_front_regions_diagnosis.png")
    
    print("\n\n" + "="*80)
    print("Diagnosing BACK card extraction...")
    
    # Back card regions
    img = cv2.imread("app/static/back_cropped.png")
    if img is not None:
        height, width = img.shape[:2]
        print(f"Back image dimensions: {width}x{height}")
        
        ref_width = 900
        ref_height = 1600
        
        back_regions = {
            'phone_number': (205/ref_width, 1209/ref_height, (205+675)/ref_width, (1209+47)/ref_height),
            'fin_number': (202/ref_width, 1257/ref_height, (202+675)/ref_width, (1257+47)/ref_height),
            'nationality_am': (197/ref_width, 1339/ref_height, (197+183)/ref_width, (1339+47)/ref_height),
            'nationality_en': (389/ref_width, 1339/ref_height, (389+409)/ref_width, (1339+49)/ref_height),
        }
        
        vis_img = img.copy()
        
        for idx, (region_name, (x1, y1, x2, y2)) in enumerate(back_regions.items()):
            x1_px = int(x1 * width)
            y1_px = int(y1 * height)
            x2_px = int(x2 * width)
            y2_px = int(y2 * height)
            
            color = [(255, 0, 0), (0, 255, 0), (0, 0, 255), (255, 255, 0)][idx]
            cv2.rectangle(vis_img, (x1_px, y1_px), (x2_px, y2_px), color, 2)
            cv2.putText(vis_img, region_name, (x1_px, y1_px-5), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.4, color, 1)
        
        cv2.imwrite("debug_back_regions_diagnosis.png", vis_img)
        print(f"Back card visualization saved to: debug_back_regions_diagnosis.png")
