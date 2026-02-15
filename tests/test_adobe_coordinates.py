"""
Test and visualize the exact Adobe coordinates on Ethiopian ID card
"""

import cv2
import numpy as np
import os

# Adobe coordinates (exact pixels from user)
adobe_coords = {
    'full_name_am': {'x': 205, 'y': 1209, 'w': 675, 'h': 47, 'color': (255, 0, 0)},      # Blue
    'full_name_en': {'x': 202, 'y': 1257, 'w': 675, 'h': 47, 'color': (255, 100, 0)},    # Light Blue
    'dob_am': {'x': 197, 'y': 1339, 'w': 183, 'h': 47, 'color': (0, 255, 0)},            # Green
    'dob_en': {'x': 389, 'y': 1339, 'w': 409, 'h': 49, 'color': (0, 255, 100)},          # Light Green
    'sex_am': {'x': 201, 'y': 1413, 'w': 63, 'h': 49, 'color': (0, 0, 255)},             # Red
    'sex_en': {'x': 265, 'y': 1403, 'w': 125, 'h': 49, 'color': (100, 0, 255)},          # Purple
    'expiry_am': {'x': 201, 'y': 1495, 'w': 175, 'h': 43, 'color': (255, 255, 0)},       # Cyan
    'expiry_en': {'x': 387, 'y': 1489, 'w': 339, 'h': 49, 'color': (255, 255, 100)},     # Light Cyan
    'fan': {'x': 321, 'y': 1577, 'w': 427, 'h': 27, 'color': (255, 0, 255)},             # Magenta
    'issue_am': {'x': 895, 'y': 861, 'w': 45, 'h': 231, 'color': (0, 255, 255)},         # Yellow
    'issue_en': {'x': 892, 'y': 576, 'w': 45, 'h': 278, 'color': (100, 255, 255)},       # Light Yellow
}

# Reference dimensions
ref_width = 900
ref_height = 1650

def visualize_adobe_coordinates(image_path, output_path):
    """Visualize Adobe coordinates on the ID card image"""
    
    # Read image
    img = cv2.imread(image_path)
    if img is None:
        print(f"❌ Could not read image: {image_path}")
        return
    
    height, width = img.shape[:2]
    print(f"📐 Image dimensions: {width}x{height}")
    print(f"📐 Reference dimensions: {ref_width}x{ref_height}")
    
    # Calculate scale factors
    scale_x = width / ref_width
    scale_y = height / ref_height
    print(f"📐 Scale factors: x={scale_x:.3f}, y={scale_y:.3f}")
    
    # Create overlay
    overlay = img.copy()
    
    # Draw each region
    for field_name, coords in adobe_coords.items():
        # Scale coordinates to actual image size
        x1 = int(coords['x'] * scale_x)
        y1 = int(coords['y'] * scale_y)
        x2 = int((coords['x'] + coords['w']) * scale_x)
        y2 = int((coords['y'] + coords['h']) * scale_y)
        
        color = coords['color']
        
        # Draw rectangle
        cv2.rectangle(overlay, (x1, y1), (x2, y2), color, 2)
        
        # Add label
        label = field_name.replace('_', ' ').title()
        font_scale = 0.4
        thickness = 1
        (text_width, text_height), _ = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, font_scale, thickness)
        
        # Position label above the box
        label_y = y1 - 5 if y1 > 20 else y2 + text_height + 5
        cv2.putText(overlay, label, (x1, label_y), cv2.FONT_HERSHEY_SIMPLEX, font_scale, color, thickness)
        
        print(f"✓ {field_name:20} -> ({x1:4}, {y1:4}) to ({x2:4}, {y2:4})")
    
    # Blend overlay with original
    alpha = 0.7
    result = cv2.addWeighted(overlay, alpha, img, 1 - alpha, 0)
    
    # Save result
    cv2.imwrite(output_path, result)
    print(f"\n✅ Saved visualization: {output_path}")

# Test with sample front card
front_image = "data/sample_cards/front.jpg"
if not os.path.exists(front_image):
    front_image = "data/front_card.jpg"
if not os.path.exists(front_image):
    # Try to find any front card image
    for root, dirs, files in os.walk("data"):
        for file in files:
            if "front" in file.lower() and file.endswith(('.jpg', '.png', '.jpeg')):
                front_image = os.path.join(root, file)
                break

if os.path.exists(front_image):
    print(f"🎯 Testing Adobe coordinates on: {front_image}\n")
    visualize_adobe_coordinates(front_image, "debug_adobe_coordinates.png")
else:
    print(f"❌ No front card image found. Please provide a front card image.")
    print(f"   Expected location: data/sample_cards/front.jpg or data/front_card.jpg")
