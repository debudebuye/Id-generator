#!/usr/bin/env python3
"""
Visualize Adobe coordinate regions on an ID card image
"""
import cv2
import numpy as np
import os

# Adobe coordinates
adobe_coords = {
    'full_name_am': {'x': 205, 'y': 1209, 'w': 675, 'h': 47, 'color': (255, 0, 0)},      # Blue
    'full_name_en': {'x': 202, 'y': 1257, 'w': 675, 'h': 47, 'color': (255, 100, 0)},    # Light Blue
    'dob_gregorian': {'x': 197, 'y': 1339, 'w': 183, 'h': 47, 'color': (0, 255, 0)},     # Green
    'dob_ethiopian': {'x': 389, 'y': 1339, 'w': 409, 'h': 49, 'color': (0, 255, 100)},   # Light Green
    'sex_am': {'x': 201, 'y': 1413, 'w': 63, 'h': 49, 'color': (0, 165, 255)},           # Orange
    'sex_en': {'x': 265, 'y': 1403, 'w': 125, 'h': 49, 'color': (0, 200, 255)},          # Light Orange
    'expiry_gregorian': {'x': 201, 'y': 1495, 'w': 175, 'h': 43, 'color': (255, 0, 255)},# Magenta
    'expiry_ethiopian': {'x': 387, 'y': 1489, 'w': 339, 'h': 49, 'color': (255, 100, 255)},# Light Magenta
    'fan_number': {'x': 321, 'y': 1577, 'w': 427, 'h': 27, 'color': (0, 255, 255)},      # Yellow
    'issue_gregorian': {'x': 892, 'y': 576, 'w': 45, 'h': 278, 'color': (128, 0, 128)},  # Purple
    'issue_ethiopian': {'x': 895, 'y': 861, 'w': 45, 'h': 231, 'color': (180, 0, 180)},  # Light Purple
}

def visualize_regions(image_path, output_path='adobe_regions_visualization.png'):
    """Draw rectangles on image to show Adobe coordinate regions"""
    
    if not os.path.exists(image_path):
        print(f"❌ Image not found: {image_path}")
        return
    
    img = cv2.imread(image_path)
    if img is None:
        print(f"❌ Could not read image: {image_path}")
        return
    
    height, width = img.shape[:2]
    print(f"📐 Image dimensions: {width}x{height}")
    
    # Reference dimensions
    ref_width = 900
    ref_height = 1650
    
    # Create overlay
    overlay = img.copy()
    
    print("\n📍 Drawing regions:")
    for field_name, coords in adobe_coords.items():
        # Convert reference coordinates to actual image coordinates
        x1 = int((coords['x'] / ref_width) * width)
        y1 = int((coords['y'] / ref_height) * height)
        x2 = int(((coords['x'] + coords['w']) / ref_width) * width)
        y2 = int(((coords['y'] + coords['h']) / ref_height) * height)
        
        color = coords['color']
        
        # Draw rectangle
        cv2.rectangle(overlay, (x1, y1), (x2, y2), color, 2)
        
        # Add label
        label = field_name.replace('_', ' ').title()
        font_scale = 0.4
        thickness = 1
        (text_width, text_height), _ = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, font_scale, thickness)
        
        # Background for text
        cv2.rectangle(overlay, (x1, y1 - text_height - 4), (x1 + text_width, y1), color, -1)
        cv2.putText(overlay, label, (x1, y1 - 2), cv2.FONT_HERSHEY_SIMPLEX, font_scale, (255, 255, 255), thickness)
        
        print(f"  ✓ {field_name}: ({x1},{y1}) to ({x2},{y2})")
    
    # Blend overlay with original
    result = cv2.addWeighted(overlay, 0.7, img, 0.3, 0)
    
    # Save
    cv2.imwrite(output_path, result)
    print(f"\n✅ Saved visualization: {output_path}")

# Find a sample image
print("=" * 80)
print("ADOBE REGIONS VISUALIZATION")
print("=" * 80)

# Look for sample images
sample_paths = [
    'uploads/front_card.jpg',
    'uploads/front_card.png',
    'data/sample_front.jpg',
    'data/sample_front.png',
]

# Also check uploads directory for any images
if os.path.exists('uploads'):
    for file in os.listdir('uploads'):
        if file.lower().endswith(('.jpg', '.jpeg', '.png')) and 'front' in file.lower():
            sample_paths.insert(0, os.path.join('uploads', file))

found = False
for path in sample_paths:
    if os.path.exists(path):
        print(f"\n📸 Using image: {path}")
        visualize_regions(path)
        found = True
        break

if not found:
    print("\n⚠️  No sample image found. Please provide an image path:")
    print("   Usage: python visualize_adobe_regions.py <image_path>")
    print("\n   Or place a front card image in one of these locations:")
    for path in sample_paths[:4]:
        print(f"   - {path}")

print("=" * 80)
