"""
Analyze the actual card layout to determine correct regions
"""
import cv2
import numpy as np

# Read the front card image
front_image_path = r"app\static\front_cropped.png"
img = cv2.imread(front_image_path)

if img is None:
    print(f"❌ Could not read image: {front_image_path}")
    exit(1)

height, width = img.shape[:2]
print(f"📐 Image dimensions: {width}x{height}")
print(f"   Aspect ratio: {width/height:.2f} (width/height)")
print(f"   This is a {'PORTRAIT' if height > width else 'LANDSCAPE'} image")
print()

# The card is PORTRAIT (553x1200), so:
# - Width is 553 pixels
# - Height is 1200 pixels
# 
# Based on Ethiopian Digital ID layout (portrait):
# - Top section (0-20%): Header/Logo
# - Photo section (20-45%): Profile photo on left
# - Name section (20-35%): Name fields (right of photo)
# - Info section (35-60%): DOB, Sex, Expiry
# - FAN section (75-82%): FAN number above barcode
# - Barcode section (82-95%): Barcode
# - Issue date: Vertical text on right edge

# Let's create a grid visualization to understand the layout
vis_img = img.copy()

# Draw horizontal grid lines every 10%
for i in range(0, 11):
    y = int(height * i / 10)
    cv2.line(vis_img, (0, y), (width, y), (255, 0, 0), 1)
    cv2.putText(vis_img, f"{i*10}%", (5, y-5), cv2.FONT_HERSHEY_SIMPLEX, 0.4, (255, 0, 0), 1)

# Draw vertical grid lines every 10%
for i in range(0, 11):
    x = int(width * i / 10)
    cv2.line(vis_img, (x, 0), (x, height), (0, 255, 0), 1)
    cv2.putText(vis_img, f"{i*10}%", (x+2, 15), cv2.FONT_HERSHEY_SIMPLEX, 0.4, (0, 255, 0), 1)

# Save grid visualization
cv2.imwrite("debug_card_grid.png", vis_img)
print("✓ Saved grid visualization: debug_card_grid.png")
print("   Use this to identify the correct region coordinates")
print()

# Based on typical Ethiopian Digital ID layout (PORTRAIT):
# Let me propose regions based on the portrait layout

proposed_regions = {
    # Name is typically in the upper-middle section, right of photo
    'full_name': (0.05, 0.20, 0.95, 0.35),      # 20-35% height, full width
    
    # DOB is below name
    'date_of_birth': (0.05, 0.36, 0.95, 0.44),  # 36-44% height
    
    # Sex is below DOB (usually left side)
    'sex': (0.05, 0.45, 0.50, 0.52),            # 45-52% height, left half
    
    # Expiry date is below sex
    'date_of_expiry': (0.05, 0.53, 0.95, 0.61), # 53-61% height
    
    # FAN number is near bottom, above barcode
    'fan_number': (0.10, 0.72, 0.90, 0.79),     # 72-79% height
    
    # Issue date is vertical on right edge
    'date_of_issue': (0.88, 0.10, 1.0, 0.70),   # Right edge, 10-70% height
}

# Visualize proposed regions
vis_img2 = img.copy()

for region_name, (x1, y1, x2, y2) in proposed_regions.items():
    x1_px = int(x1 * width)
    y1_px = int(y1 * height)
    x2_px = int(x2 * width)
    y2_px = int(y2 * height)
    
    # Draw rectangle
    cv2.rectangle(vis_img2, (x1_px, y1_px), (x2_px, y2_px), (0, 255, 255), 2)
    
    # Draw label
    label = region_name.replace('_', ' ').title()
    cv2.putText(vis_img2, label, (x1_px + 5, y1_px + 20), 
                cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 255), 2)

# Save proposed regions visualization
cv2.imwrite("debug_proposed_regions.png", vis_img2)
print("✓ Saved proposed regions: debug_proposed_regions.png")
print()

print("📊 PROPOSED REGIONS (for PORTRAIT layout):")
for name, coords in proposed_regions.items():
    x1, y1, x2, y2 = coords
    print(f"  '{name}': ({x1}, {y1}, {x2}, {y2}),")

print()
print("✅ Review debug_card_grid.png and debug_proposed_regions.png")
print("   Adjust coordinates as needed based on actual card layout")
