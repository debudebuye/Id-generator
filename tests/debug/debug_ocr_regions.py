"""
Debug OCR extraction by visualizing regions
"""
import cv2
import os
import sys

# Add app directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'app'))

from services.ocr_extraction_service import OCRExtractionService

def visualize_regions(image_path, card_type='front'):
    """Visualize extraction regions on the ID card"""
    print("=" * 60)
    print(f"Visualizing {card_type.upper()} Card Regions")
    print("=" * 60)
    
    # Read image
    img = cv2.imread(image_path)
    if img is None:
        print(f"❌ Could not read image: {image_path}")
        return
    
    height, width = img.shape[:2]
    print(f"📐 Image dimensions: {width}x{height}")
    
    # Define regions based on card type
    if card_type == 'front':
        regions = {
            'full_name': (0.05, 0.58, 0.95, 0.68),
            'date_of_birth': (0.05, 0.70, 0.95, 0.74),
            'sex': (0.05, 0.745, 0.40, 0.785),
            'date_of_expiry': (0.05, 0.80, 0.95, 0.855),
            'fan_number': (0.25, 0.88, 0.75, 0.94),
        }
        colors = {
            'full_name': (0, 255, 0),      # Green
            'date_of_birth': (255, 0, 0),  # Blue
            'sex': (0, 0, 255),            # Red
            'date_of_expiry': (255, 255, 0), # Cyan
            'fan_number': (255, 0, 255),   # Magenta
        }
    else:  # back
        regions = {
            'phone_number': (0.05, 0.665, 0.45, 0.710),
            'fin_number': (0.50, 0.665, 0.95, 0.710),
            'nationality': (0.05, 0.720, 0.95, 0.790),
            'address': (0.05, 0.795, 0.95, 1.0),
            'qr_code': (0.25, 0.08, 0.75, 0.45),  # New QR region
        }
        colors = {
            'phone_number': (0, 255, 0),
            'fin_number': (255, 0, 0),
            'nationality': (0, 0, 255),
            'address': (255, 255, 0),
            'qr_code': (255, 0, 255),
        }
    
    # Draw rectangles for each region
    output_img = img.copy()
    for region_name, (x1, y1, x2, y2) in regions.items():
        # Convert percentages to pixels
        x1_px = int(x1 * width)
        y1_px = int(y1 * height)
        x2_px = int(x2 * width)
        y2_px = int(y2 * height)
        
        # Draw rectangle
        color = colors.get(region_name, (128, 128, 128))
        cv2.rectangle(output_img, (x1_px, y1_px), (x2_px, y2_px), color, 3)
        
        # Add label
        label = region_name.replace('_', ' ').title()
        cv2.putText(output_img, label, (x1_px, y1_px - 10), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.7, color, 2)
        
        print(f"✓ {region_name}: ({x1_px}, {y1_px}) to ({x2_px}, {y2_px})")
    
    # Save output
    output_path = f"debug_{card_type}_regions.png"
    cv2.imwrite(output_path, output_img)
    print(f"\n✅ Visualization saved to: {output_path}")
    print("=" * 60)

def test_ocr_extraction(image_path, card_type='front'):
    """Test OCR extraction and show results"""
    print("\n" + "=" * 60)
    print(f"Testing OCR Extraction on {card_type.upper()} Card")
    print("=" * 60)
    
    ocr_service = OCRExtractionService()
    
    if card_type == 'front':
        # Extract text
        text = ocr_service.extract_text_from_image(image_path)
        print(f"\n📄 Extracted text ({len(text)} chars):")
        print(text[:500])
        
        # Parse data
        data = ocr_service.parse_front_card_data(text, image_path=image_path)
        print(f"\n📊 Parsed data:")
        for key, value in data.items():
            if value:
                print(f"  ✓ {key}: {value}")
            else:
                print(f"  ✗ {key}: (empty)")
    else:
        # Extract text
        text = ocr_service.extract_text_from_image(image_path)
        print(f"\n📄 Extracted text ({len(text)} chars):")
        print(text[:500])
        
        # Parse data
        data = ocr_service.parse_back_card_data(text, image_path=image_path)
        print(f"\n📊 Parsed data:")
        for key, value in data.items():
            if value:
                print(f"  ✓ {key}: {value}")
            else:
                print(f"  ✗ {key}: (empty)")
    
    print("=" * 60)

if __name__ == "__main__":
    print("OCR Region Debugger")
    print("=" * 60)
    
    # Get image path
    card_type = input("Card type (front/back): ").strip().lower()
    if card_type not in ['front', 'back']:
        print("Invalid card type. Use 'front' or 'back'")
        sys.exit(1)
    
    image_path = input(f"Enter path to {card_type} card image: ").strip()
    
    if not os.path.exists(image_path):
        print(f"❌ Image not found: {image_path}")
        sys.exit(1)
    
    # Visualize regions
    visualize_regions(image_path, card_type)
    
    # Test OCR extraction
    test_ocr_extraction(image_path, card_type)
