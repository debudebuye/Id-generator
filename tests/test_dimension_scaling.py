#!/usr/bin/env python3
"""
Test script to verify coordinate scaling works for different image dimensions
"""

def test_coordinate_scaling():
    """Test how coordinates scale for different image dimensions"""
    
    # Reference dimensions
    ref_width = 591
    ref_height = 1280
    ref_aspect = ref_width / ref_height
    
    # Test dimensions
    test_dimensions = [
        (553, 1200, "Current test image"),
        (591, 1280, "Reference image"),
        (720, 1600, "User's image"),
        (800, 1500, "Larger image"),
        (400, 900, "Smaller image"),
    ]
    
    # Amharic name region (as percentages)
    x1_pct = 85 / ref_width
    y1_pct = 664 / ref_height
    x2_pct = 490 / ref_width
    y2_pct = 686 / ref_height
    
    print("="*80)
    print("COORDINATE SCALING TEST FOR AMHARIC NAME REGION")
    print("="*80)
    print(f"\nReference: {ref_width}x{ref_height} (aspect ratio: {ref_aspect:.4f})")
    print(f"Region percentages: X({x1_pct:.4f} to {x2_pct:.4f}), Y({y1_pct:.4f} to {y2_pct:.4f})")
    print("\n" + "-"*80)
    
    for width, height, description in test_dimensions:
        aspect = width / height
        aspect_diff = abs(aspect - ref_aspect) / ref_aspect * 100
        
        # Scale coordinates
        x1_px = int(x1_pct * width)
        y1_px = int(y1_pct * height)
        x2_px = int(x2_pct * width)
        y2_px = int(y2_pct * height)
        
        region_width = x2_px - x1_px
        region_height = y2_px - y1_px
        
        # Determine if it will work well
        if aspect_diff < 5:
            status = "✅ EXCELLENT"
        elif aspect_diff < 10:
            status = "✓ GOOD"
        elif aspect_diff < 15:
            status = "⚠️ ACCEPTABLE"
        else:
            status = "❌ POOR"
        
        print(f"\n{description}: {width}x{height}")
        print(f"  Aspect ratio: {aspect:.4f} (diff: {aspect_diff:.2f}%)")
        print(f"  Scaled region: ({x1_px}, {y1_px}) to ({x2_px}, {y2_px})")
        print(f"  Region size: {region_width}x{region_height} pixels")
        print(f"  Status: {status}")
    
    print("\n" + "="*80)
    print("SUMMARY:")
    print("="*80)
    print("✅ EXCELLENT: < 5% aspect ratio difference - Perfect extraction")
    print("✓ GOOD: 5-10% difference - Should work well")
    print("⚠️ ACCEPTABLE: 10-15% difference - May have minor issues")
    print("❌ POOR: > 15% difference - Likely to have problems")
    print("="*80)

if __name__ == "__main__":
    test_coordinate_scaling()
