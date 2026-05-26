"""
Test script to verify multi-dimension detection and coordinate mapping
"""

def test_dimension_detection():
    """Test dimension detection logic"""
    
    print("=" * 60)
    print("DIMENSION DETECTION TEST")
    print("=" * 60)
    
    # Test Case 1: Standard 900x1441 dimension
    print("\n📋 Test Case 1: Standard Dimension (900x1441)")
    width, height = 900, 1441
    aspect_ratio = width / height
    is_599x963 = 0.55 < aspect_ratio < 0.68 and 550 < width < 650 and 900 < height < 1050
    
    print(f"   Dimensions: {width}x{height}")
    print(f"   Aspect Ratio: {aspect_ratio:.3f}")
    print(f"   Detected as 599x963: {is_599x963}")
    print(f"   Expected: False ✓" if not is_599x963 else "   Expected: False ✗")
    
    # Calculate sex_am coordinates for 900x1441
    ref_width, ref_height = 900, 1441
    sex_am_x1 = int((103/ref_width) * width)
    sex_am_y1 = int((1034/ref_height) * height)
    sex_am_x2 = int((190/ref_width) * width)
    sex_am_y2 = int((1075/ref_height) * height)
    print(f"   sex_am region: ({sex_am_x1}, {sex_am_y1}) → ({sex_am_x2}, {sex_am_y2})")
    print(f"   sex_am size: {sex_am_x2-sex_am_x1}x{sex_am_y2-sex_am_y1}")
    
    # Test Case 2: Compact 599x963 dimension
    print("\n📋 Test Case 2: Compact Dimension (599x963)")
    width, height = 599, 963
    aspect_ratio = width / height
    is_599x963 = 0.55 < aspect_ratio < 0.68 and 550 < width < 650 and 900 < height < 1050
    
    print(f"   Dimensions: {width}x{height}")
    print(f"   Aspect Ratio: {aspect_ratio:.3f}")
    print(f"   Detected as 599x963: {is_599x963}")
    print(f"   Expected: True ✓" if is_599x963 else "   Expected: True ✗")
    
    # Calculate sex_am coordinates for 599x963 (using special coordinates)
    sex_ref_width, sex_ref_height = 599, 963
    sex_am_x1 = int((68/sex_ref_width) * width)
    sex_am_y1 = int((697/sex_ref_height) * height)
    sex_am_x2 = int((111/sex_ref_width) * width)
    sex_am_y2 = int((723/sex_ref_height) * height)
    print(f"   sex_am region: ({sex_am_x1}, {sex_am_y1}) → ({sex_am_x2}, {sex_am_y2})")
    print(f"   sex_am size: {sex_am_x2-sex_am_x1}x{sex_am_y2-sex_am_y1}")
    
    # Test Case 3: Similar to 599x963 (610x980)
    print("\n📋 Test Case 3: Similar Dimension (610x980)")
    width, height = 610, 980
    aspect_ratio = width / height
    is_599x963 = 0.55 < aspect_ratio < 0.68 and 550 < width < 650 and 900 < height < 1050
    
    print(f"   Dimensions: {width}x{height}")
    print(f"   Aspect Ratio: {aspect_ratio:.3f}")
    print(f"   Detected as 599x963: {is_599x963}")
    print(f"   Expected: True ✓" if is_599x963 else "   Expected: True ✗")
    
    # Calculate sex_am coordinates (should use 599x963 special coordinates)
    sex_ref_width, sex_ref_height = 599, 963
    sex_am_x1 = int((68/sex_ref_width) * width)
    sex_am_y1 = int((697/sex_ref_height) * height)
    sex_am_x2 = int((111/sex_ref_width) * width)
    sex_am_y2 = int((723/sex_ref_height) * height)
    print(f"   sex_am region: ({sex_am_x1}, {sex_am_y1}) → ({sex_am_x2}, {sex_am_y2})")
    print(f"   sex_am size: {sex_am_x2-sex_am_x1}x{sex_am_y2-sex_am_y1}")
    
    # Test Case 4: Different aspect ratio (800x1200)
    print("\n📋 Test Case 4: Different Aspect Ratio (800x1200)")
    width, height = 800, 1200
    aspect_ratio = width / height
    is_599x963 = 0.55 < aspect_ratio < 0.68 and 550 < width < 650 and 900 < height < 1050
    
    print(f"   Dimensions: {width}x{height}")
    print(f"   Aspect Ratio: {aspect_ratio:.3f}")
    print(f"   Detected as 599x963: {is_599x963}")
    print(f"   Expected: False ✓" if not is_599x963 else "   Expected: False ✗")
    
    # Calculate sex_am coordinates (should use default 900x1441)
    ref_width, ref_height = 900, 1441
    sex_am_x1 = int((103/ref_width) * width)
    sex_am_y1 = int((1034/ref_height) * height)
    sex_am_x2 = int((190/ref_width) * width)
    sex_am_y2 = int((1075/ref_height) * height)
    print(f"   sex_am region: ({sex_am_x1}, {sex_am_y1}) → ({sex_am_x2}, {sex_am_y2})")
    print(f"   sex_am size: {sex_am_x2-sex_am_x1}x{sex_am_y2-sex_am_y1}")
    
    # Test other fields always use 900x1441 reference
    print("\n" + "=" * 60)
    print("OTHER FIELDS TEST (Always use 900x1441 reference)")
    print("=" * 60)
    
    for test_name, (width, height) in [
        ("Standard 900x1441", (900, 1441)),
        ("Compact 599x963", (599, 963)),
        ("Similar 610x980", (610, 980))
    ]:
        print(f"\n📋 {test_name}")
        print(f"   Dimensions: {width}x{height}")
        
        # All fields use 900x1441 reference
        ref_width, ref_height = 900, 1441
        
        # full_name_am coordinates
        x1 = int((89/ref_width) * width)
        y1 = int((834/ref_height) * height)
        x2 = int((792/ref_width) * width)
        y2 = int((885/ref_height) * height)
        print(f"   full_name_am: ({x1}, {y1}) → ({x2}, {y2}), size: {x2-x1}x{y2-y1}")
        
        # dob_ethiopian coordinates
        x1 = int((93/ref_width) * width)
        y1 = int((964/ref_height) * height)
        x2 = int((292/ref_width) * width)
        y2 = int((1017/ref_height) * height)
        print(f"   dob_ethiopian: ({x1}, {y1}) → ({x2}, {y2}), size: {x2-x1}x{y2-y1}")
    
    print("\n" + "=" * 60)
    print("✅ All tests completed!")
    print("=" * 60)

if __name__ == "__main__":
    test_dimension_detection()
