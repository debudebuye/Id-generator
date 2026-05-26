"""
Update OCR extraction service with exact Adobe coordinates
"""

# Adobe coordinates from user (in pixels)
adobe_coords = {
    'full_name_am': {'x': 205, 'y': 1209, 'w': 675, 'h': 47},
    'full_name_en': {'x': 202, 'y': 1257, 'w': 675, 'h': 47},
    'dob_am': {'x': 197, 'y': 1339, 'w': 183, 'h': 47},
    'dob_en': {'x': 389, 'y': 1339, 'w': 409, 'h': 49},
    'sex_am': {'x': 201, 'y': 1413, 'w': 63, 'h': 49},
    'sex_en': {'x': 265, 'y': 1403, 'w': 125, 'h': 49},
    'expiry_am': {'x': 201, 'y': 1495, 'w': 175, 'h': 43},
    'expiry_en': {'x': 387, 'y': 1489, 'w': 339, 'h': 49},
    'fan': {'x': 321, 'y': 1577, 'w': 427, 'h': 27},
    'issue_am': {'x': 895, 'y': 861, 'w': 45, 'h': 231},
    'issue_en': {'x': 892, 'y': 576, 'w': 45, 'h': 278},
}

# Reference dimensions (from Adobe)
ref_width = 900  # Assuming standard card width
ref_height = 1650  # Adjusted based on max y coordinate (1577 + 27 = 1604, rounded up)

print("Adobe Coordinates to Percentage Conversion")
print("=" * 80)
print(f"Reference dimensions: {ref_width}x{ref_height}")
print()

# Convert to percentage-based regions
regions_code = "            regions = {\n"

for field_name, coords in adobe_coords.items():
    x1 = coords['x']
    y1 = coords['y']
    x2 = x1 + coords['w']
    y2 = y1 + coords['h']
    
    # Convert to percentages
    x1_pct = x1 / ref_width
    y1_pct = y1 / ref_height
    x2_pct = x2 / ref_width
    y2_pct = y2 / ref_height
    
    # Map field names to code names
    field_mapping = {
        'full_name_am': 'full_name_am',
        'full_name_en': 'full_name_en',
        'dob_am': 'dob_ethiopian',
        'dob_en': 'dob_gregorian',
        'sex_am': 'sex_am',
        'sex_en': 'sex_en',
        'expiry_am': 'expiry_ethiopian',
        'expiry_en': 'expiry_gregorian',
        'fan': 'fan_number',
        'issue_am': 'issue_ethiopian',
        'issue_en': 'issue_gregorian',
    }
    
    code_name = field_mapping.get(field_name, field_name)
    
    print(f"{field_name:20} -> {code_name:20}")
    print(f"  Adobe pixels: ({x1}, {y1}) to ({x2}, {y2})")
    print(f"  Percentages:  ({x1_pct:.4f}, {y1_pct:.4f}) to ({x2_pct:.4f}, {y2_pct:.4f})")
    print()
    
    # Generate code line
    comment = f"# {field_name.replace('_', ' ').title()} ({x1},{y1})-({x2},{y2})"
    regions_code += f"                '{code_name}': ({x1}/{ref_width}, {y1}/{ref_height}, {x2}/{ref_width}, {y2}/{ref_height}),  {comment}\n"

regions_code += "            }"

print("\n" + "=" * 80)
print("Python Code for OCR Service:")
print("=" * 80)
print(f"\n            ref_width = {ref_width}")
print(f"            ref_height = {ref_height}")
print()
print(regions_code)
print()
print("=" * 80)
