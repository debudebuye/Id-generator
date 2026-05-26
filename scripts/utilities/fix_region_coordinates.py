"""
Visualize and fix region coordinates for Ethiopian Digital ID Card
"""
import cv2
import numpy as np
import os

# Read the front card image
front_image_path = r"app\static\front_cropped.png"
img = cv2.imread(front_image_path)

if img is None:
    print(f"❌ Could not read image: {front_image_path}")
    exit(1)

height, width = img.shape[:2]
print(f"📐 Image dimensions: {width}x{height}")

# Current (WRONG) regions
old_regions = {
    'full_name': (0.05, 0.56, 0.95, 0.66),
    'date_of_birth': (0.05, 0.67, 0.95, 0.72),
    'sex': (0.05, 0.72, 0.50, 0.77),
    'date_of_expiry': (0.05, 0.77, 0.95, 0.82),
    'fan_number': (0.15, 0.82, 0.85, 0.89),
    'date_of_issue': (0.88, 0.10, 1.0, 0.90),
}

# NEW regions based on actual card layout
# Looking at the card, from top to bottom:
# - Photo is on the left (0-40% width)
# - Name is in the middle section (40-100% width, around 15-30% height)
# - DOB, Sex, Expiry are below name (30-50% height)
# - FAN number is at the bottom above barcode (80-90% height)
# - Issue date is vertical on the right edge (90-100% width)

new_regions = {
    'full_name': (0.40, 0.15, 0.95, 0.30),      # Name area (right of photo)
    'date_of_birth': (0.40, 0.32, 0.95, 0.42),  # DOB area
    'sex': (0.40, 0.44, 0.70, 0.52),            # Sex area (left side)
    'date_of_expiry': (0.40, 0.54, 0.95, 0.64), # Expiry date area
    'fan_number': (0.15, 0.75, 0.85, 0.82),     # FAN number (above barcode)
    'date_of_issue': (0.90, 0.10, 1.0, 0.90),   # Issue date (vertical, right edge)
}

# Create visualization
vis_img = img.copy()

# Draw OLD regions in RED
for region_name, (x1, y1, x2, y2) in old_regions.items():
    x1_px = int(x1 * width)
    y1_px = int(y1 * height)
    x2_px = int(x2 * width)
    y2_px = int(y2 * height)
    
    cv2.rectangle(vis_img, (x1_px, y1_px), (x2_px, y2_px), (0, 0, 255), 2)
    cv2.putText(vis_img, f"OLD: {region_name}", (x1_px, y1_px - 5), 
                cv2.FONT_HERSHEY_SIMPLEX, 0.4, (0, 0, 255), 1)

# Save OLD visualization
cv2.imwrite("debug_old_regions.png", vis_img)
print("✓ Saved OLD regions visualization: debug_old_regions.png")

# Create NEW visualization
vis_img2 = img.copy()

# Draw NEW regions in GREEN
for region_name, (x1, y1, x2, y2) in new_regions.items():
    x1_px = int(x1 * width)
    y1_px = int(y1 * height)
    x2_px = int(x2 * width)
    y2_px = int(y2 * height)
    
    cv2.rectangle(vis_img2, (x1_px, y1_px), (x2_px, y2_px), (0, 255, 0), 2)
    cv2.putText(vis_img2, f"NEW: {region_name}", (x1_px, y1_px - 5), 
                cv2.FONT_HERSHEY_SIMPLEX, 0.4, (0, 255, 0), 1)

# Save NEW visualization
cv2.imwrite("debug_new_regions.png", vis_img2)
print("✓ Saved NEW regions visualization: debug_new_regions.png")

print("\n📊 Region Comparison:")
print("\nOLD REGIONS (RED):")
for name, coords in old_regions.items():
    print(f"  {name}: {coords}")

print("\nNEW REGIONS (GREEN):")
for name, coords in new_regions.items():
    print(f"  {name}: {coords}")

print("\n✅ Check debug_old_regions.png and debug_new_regions.png to verify")
print("   If NEW regions look correct, update ocr_extraction_service.py")
