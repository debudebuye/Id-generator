#!/usr/bin/env python3
"""
Debug script to visualize where the region coordinates are pointing
on the actual uploaded images
"""

import cv2
import numpy as np
import os

def visualize_regions(image_path, regions, output_path, title="Regions"):
    """Draw rectangles on image to show where regions are"""
    img = cv2.imread(image_path)
    if img is None:
        print(f"❌ Could not read image: {image_path}")
        return
    
    height, width = img.shape[:2]
    print(f"\n📐 Image: {title}")
    print(f"   Dimensions: {width}x{height}")
    
    # Create a copy for drawing
    vis_img = img.copy()
    
    # Colors for different regions
    colors = [
        (0, 255, 0),    # Green
        (255, 0, 0),    # Blue
        (0, 0, 255),    # Red
        (255, 255, 0),  # Cyan
        (255, 0, 255),  # Magenta
        (0, 255, 255),  # Yellow
        (128, 255, 0),  # Light green
        (255, 128, 0),  # Orange
        (128, 0, 255),  # Purple
        (0, 128, 255),  # Light blue
    ]
    
    for idx, (region_name, (x1, y1, x2, y2)) in enumerate(regions.items()):
        # Convert percentages to pixels
        x1_px = int(x1 * width)
        y1_px = int(y1 * height)
        x2_px = int(x2 * width)
        y2_px = int(y2 * height)
        
        color = colors[idx % len(colors)]
        
        # Draw rectangle
        cv2.rectangle(vis_img, (x1_px, y1_px), (x2_px, y2_px), color, 2)
        
        # Add label
        label = region_name.replace('_', ' ').title()
        cv2.putText(vis_img, label, (x1_px, y1_px - 5), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.4, color, 1)
        
        print(f"   {region_name}: ({x1_px},{y1_px}) -> ({x2_px},{y2_px})")
    
    # Save visualization
    cv2.imwrite(output_path, vis_img)
    print(f"✓ Saved visualization: {output_path}")

# Front card regions (current coordinates)
front_regions = {
    'full_name_am': (150/900, 980/1500, 700/900, 1040/1500),
    'full_name_en': (150/900, 1040/1500, 700/900, 1100/1500),
    'dob_gregorian': (150/900, 1120/1500, 400/900, 1185/1500),
    'dob_ethiopian': (420/900, 1120/1500, 700/900, 1185/1500),
    'sex_am': (150/900, 1200/1500, 300/900, 1260/1500),
    'sex_en': (320/900, 1200/1500, 500/900, 1260/1500),
    'expiry_gregorian': (150/900, 1280/1500, 400/900, 1350/1500),
    'expiry_ethiopian': (420/900, 1280/1500, 700/900, 1350/1500),
    'fan_number': (260/900, 1380/1500, 760/900, 1480/1500),
}

# Back card regions (current coordinates)
back_regions = {
    'phone_number': (150/900, 1030/1600, 420/900, 1085/1600),
    'fin_number': (520/900, 1030/1600, 860/900, 1085/1600),
    'nationality_am': (150/900, 1110/1600, 420/900, 1160/1600),
    'nationality_en': (430/900, 1110/1600, 700/900, 1160/1600),
    'region_am': (150/900, 1190/1600, 700/900, 1250/1600),
    'region_en': (150/900, 1250/1600, 700/900, 1310/1600),
    'subcity_am': (150/900, 1330/1600, 700/900, 1390/1600),
    'subcity_en': (150/900, 1390/1600, 700/900, 1450/1600),
    'woreda_am': (150/900, 1470/1600, 700/900, 1530/1600),
    'woreda_en': (150/900, 1530/1600, 700/900, 1590/1600),
}

# Paths to your uploaded images
front_image = r"app\static\front_cropped.png"
back_image = r"app\static\back_cropped.png"

if os.path.exists(front_image):
    visualize_regions(front_image, front_regions, "debug_front_regions_actual.png", "FRONT CARD")
else:
    print(f"❌ Front image not found: {front_image}")

if os.path.exists(back_image):
    visualize_regions(back_image, back_regions, "debug_back_regions_actual.png", "BACK CARD")
else:
    print(f"❌ Back image not found: {back_image}")

print("\n" + "="*60)
print("Check the generated images to see where regions are pointing!")
print("="*60)
