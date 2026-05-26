"""
Visualize OCR extraction regions to see where we're looking
"""
import cv2
import numpy as np

def visualize_regions(image_path, output_path, is_front=True):
    """Visualize the regions being extracted"""
    img = cv2.imread(image_path)
    if img is None:
        print(f"Could not read image: {image_path}")
        return
    
    height, width = img.shape[:2]
    print(f"Image dimensions: {width}x{height}")
    
    # Reference dimensions from coordinates
    ref_width = 900
    ref_height = 1650 if is_front else 1600
    
    if is_front:
        # Front card regions
        regions = {
            'full_name_am': (205, 1209, 675, 47),
            'full_name_en': (202, 1257, 675, 47),
            'dob_gregorian': (197, 1339, 183, 47),
            'dob_ethiopian': (389, 1339, 409, 49),
            'sex_am': (201, 1413, 63, 49),
            'sex_en': (265, 1403, 125, 49),
            'expiry_gregorian': (201, 1495, 175, 43),
            'expiry_ethiopian': (387, 1489, 339, 49),
            'fan_number': (321, 1577, 427, 27),
        }
    else:
        # Back card regions (placeholder - need actual coordinates)
        regions = {
            'phone_number': (205, 1209, 675, 47),
            'fin_number': (202, 1257, 675, 47),
            'nationality_am': (197, 1339, 183, 47),
            'nationality_en': (389, 1339, 409, 49),
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
    
    print("\nRegion coordinates (scaled to actual image):")
    print("="*80)
    
    for idx, (region_name, (x, y, w, h)) in enumerate(regions.items()):
        # Convert from reference coordinates to actual image coordinates
        x1_px = int((x / ref_width) * width)
        y1_px = int((y / ref_height) * height)
        x2_px = int(((x + w) / ref_width) * width)
        y2_px = int(((y + h) / ref_height) * height)
        
        # Draw rectangle
        color = colors[idx % len(colors)]
        cv2.rectangle(vis_img, (x1_px, y1_px), (x2_px, y2_px), color, 2)
        
        # Add label
        cv2.putText(vis_img, region_name, (x1_px, max(10, y1_px-5)), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.4, color, 1)
        
        # Extract region for saving
        region_img = img[y1_px:y2_px, x1_px:x2_px]
        
        if region_img.size == 0:
            print(f"{region_name}: EMPTY REGION (outside image bounds)")
            continue
        
        # Save individual region
        region_filename = f"debug_region_{region_name}.png"
        cv2.imwrite(region_filename, region_img)
        
        print(f"{region_name}:")
        print(f"  Reference: x={x}, y={y}, w={w}, h={h}")
        print(f"  Actual: ({x1_px}, {y1_px}) to ({x2_px}, {y2_px})")
        print(f"  Size: {x2_px-x1_px}x{y2_px-y1_px} pixels")
        print(f"  Saved to: {region_filename}")
        print()
    
    # Save visualization
    cv2.imwrite(output_path, vis_img)
    print(f"{'='*80}")
    print(f"Visualization saved to: {output_path}")
    print()

if __name__ == "__main__":
    print("="*80)
    print("FRONT CARD REGIONS")
    print("="*80)
    visualize_regions("app/static/front_cropped.png", "debug_front_regions_visualization.png", is_front=True)
    
    print("\n" + "="*80)
    print("BACK CARD REGIONS")
    print("="*80)
    visualize_regions("app/static/back_cropped.png", "debug_back_regions_visualization.png", is_front=False)
