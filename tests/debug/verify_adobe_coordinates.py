#!/usr/bin/env python3
"""
Verify and update Adobe coordinates in OCR extraction service
"""

# Your provided Adobe coordinates
adobe_coords = {
    'full_name_am': {'x': 205, 'y': 1209, 'w': 675, 'h': 47},
    'full_name_en': {'x': 202, 'y': 1257, 'w': 675, 'h': 47},
    'dob_gregorian': {'x': 197, 'y': 1339, 'w': 183, 'h': 47},
    'dob_ethiopian': {'x': 389, 'y': 1339, 'w': 409, 'h': 49},
    'sex_am': {'x': 201, 'y': 1413, 'w': 63, 'h': 49},
    'sex_en': {'x': 265, 'y': 1403, 'w': 125, 'h': 49},
    'expiry_gregorian': {'x': 201, 'y': 1495, 'w': 175, 'h': 43},
    'expiry_ethiopian': {'x': 387, 'y': 1489, 'w': 339, 'h': 49},
    'fan_number': {'x': 321, 'y': 1577, 'w': 427, 'h': 27},
    'issue_gregorian': {'x': 892, 'y': 576, 'w': 45, 'h': 278},
    'issue_ethiopian': {'x': 895, 'y': 861, 'w': 45, 'h': 231},
}

# Current coordinates in code
current_coords = {
    'full_name_am': {'x': 205, 'y': 1209, 'w': 675, 'h': 47},
    'full_name_en': {'x': 202, 'y': 1257, 'w': 675, 'h': 47},
    'dob_gregorian': {'x': 197, 'y': 1339, 'w': 183, 'h': 47},
    'dob_ethiopian': {'x': 389, 'y': 1339, 'w': 409, 'h': 49},
    'sex_am': {'x': 201, 'y': 1413, 'w': 63, 'h': 49},
    'sex_en': {'x': 265, 'y': 1403, 'w': 125, 'h': 49},
    'expiry_gregorian': {'x': 201, 'y': 1495, 'w': 175, 'h': 43},
    'expiry_ethiopian': {'x': 387, 'y': 1489, 'w': 339, 'h': 49},
    'fan_number': {'x': 321, 'y': 1577, 'w': 427, 'h': 27},
    'issue_gregorian': {'x': 892, 'y': 576, 'w': 45, 'h': 278},
    'issue_ethiopian': {'x': 895, 'y': 861, 'w': 45, 'h': 231},
}

print("=" * 80)
print("ADOBE COORDINATES VERIFICATION")
print("=" * 80)

all_match = True
for field_name in adobe_coords:
    adobe = adobe_coords[field_name]
    current = current_coords[field_name]
    
    match = (adobe['x'] == current['x'] and 
             adobe['y'] == current['y'] and 
             adobe['w'] == current['w'] and 
             adobe['h'] == current['h'])
    
    status = "✅ MATCH" if match else "❌ MISMATCH"
    print(f"\n{field_name}: {status}")
    print(f"  Adobe:   x={adobe['x']:4d} y={adobe['y']:4d} w={adobe['w']:3d} h={adobe['h']:3d}")
    print(f"  Current: x={current['x']:4d} y={current['y']:4d} w={current['w']:3d} h={current['h']:3d}")
    
    if not match:
        all_match = False

print("\n" + "=" * 80)
if all_match:
    print("✅ ALL COORDINATES MATCH! Your Adobe coordinates are already in the code.")
else:
    print("❌ SOME COORDINATES DON'T MATCH. Update needed.")

print("=" * 80)

# Generate the regions dictionary code
print("\n\nGENERATED CODE FOR ocr_extraction_service.py:")
print("=" * 80)

ref_width = 900
ref_height = 1650

print(f"""
            # Reference dimensions (from Adobe coordinate specifications)
            ref_width = {ref_width}
            ref_height = {ref_height}
            
            # Calculate percentage-based regions (will scale to actual image size)
            # EXACT coordinates from Adobe measurements - DO NOT MODIFY
            regions = {{""")

for field_name, coords in adobe_coords.items():
    x = coords['x']
    y = coords['y']
    w = coords['w']
    h = coords['h']
    x2 = x + w
    y2 = y + h
    
    # Create readable comment
    comment = field_name.replace('_', ' ').title()
    
    print(f"                '{field_name}': ({x}/{ref_width}, {y}/{ref_height}, {x2}/{ref_width}, {y2}/{ref_height}),  # {comment} x={x} y={y} w={w} h={h}")

print("            }")
print("\n" + "=" * 80)
