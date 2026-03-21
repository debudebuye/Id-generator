#!/usr/bin/env python3
"""
Test coordinate calculation for FIN region
"""

def test_coordinates():
    # Simulate image dimensions (typical PDF at 2x zoom)
    width = 2400  # Example width
    height = 3200  # Example height
    
    print(f"Image dimensions: {width}x{height}")
    
    # Current coordinates (85-95% down, 1-50% across)
    fin_region_top = int(height * 0.85)     # Start at ~85% of page height
    fin_region_bottom = int(height * 0.95)  # End at ~95% of page height  
    fin_region_left = int(width * 0.01)     # Very left side of page (1%)
    fin_region_right = int(width * 0.50)    # Left 50% of page
    
    print(f"Current FIN region:")
    print(f"  Top: {fin_region_top} ({fin_region_top/height*100:.1f}%)")
    print(f"  Bottom: {fin_region_bottom} ({fin_region_bottom/height*100:.1f}%)")
    print(f"  Left: {fin_region_left} ({fin_region_left/width*100:.1f}%)")
    print(f"  Right: {fin_region_right} ({fin_region_right/width*100:.1f}%)")
    print(f"  Region size: {fin_region_right-fin_region_left}x{fin_region_bottom-fin_region_top}")
    
    # Test other possible regions
    print("\nOther possible regions:")
    
    regions = [
        ("Lower area", 0.80, 0.90, 0.01, 0.50),
        ("Very bottom", 0.90, 1.0, 0.01, 0.50),
        ("Bottom left", 0.85, 0.95, 0.01, 0.30),
        ("Bottom center", 0.85, 0.95, 0.30, 0.70),
    ]
    
    for name, top_pct, bottom_pct, left_pct, right_pct in regions:
        top = int(height * top_pct)
        bottom = int(height * bottom_pct)
        left = int(width * left_pct)
        right = int(width * right_pct)
        
        print(f"{name}: ({left},{top}) to ({right},{bottom}) - {right-left}x{bottom-top}")

if __name__ == "__main__":
    test_coordinates()