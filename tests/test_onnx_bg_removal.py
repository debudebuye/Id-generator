#!/usr/bin/env python3
"""
Test script for ONNX background removal functionality.
"""

import os
import sys
import tempfile
from PIL import Image
import numpy as np

# Add the app directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'app'))

def create_test_image():
    """Create a simple test image with a white background."""
    # Create a 200x200 image with white background
    img = Image.new('RGB', (200, 200), (255, 255, 255))
    
    # Draw a simple shape (circle) in the center
    from PIL import ImageDraw
    draw = ImageDraw.Draw(img)
    draw.ellipse([50, 50, 150, 150], fill=(255, 0, 0))  # Red circle
    
    return img

def test_simple_background_removal():
    """Test simple color-based background removal."""
    print("Testing simple background removal...")
    
    try:
        from services.onnx_bg_removal import remove_background_simple
        
        # Create test image
        test_img = create_test_image()
        
        # Test white background removal
        result = remove_background_simple(test_img, remove_white=True, remove_black=False)
        
        # Check if result is RGBA
        assert result.mode == 'RGBA', f"Expected RGBA mode, got {result.mode}"
        
        # Check if background is transparent (alpha channel should be 0 for white areas)
        # Get alpha channel
        alpha = result.split()[-1]
        alpha_array = np.array(alpha)
        
        # White areas should be transparent (alpha = 0)
        white_areas = alpha_array == 0
        assert white_areas.any(), "White background should be removed (transparent)"
        
        print("✅ Simple background removal test passed")
        return True
        
    except Exception as e:
        print(f"❌ Simple background removal test failed: {str(e)}")
        return False

def test_onnx_background_removal():
    """Test ONNX-based background removal."""
    print("Testing ONNX background removal...")
    
    try:
        from services.onnx_bg_removal import remove_background_onnx
        
        # Create test image
        test_img = create_test_image()
        
        # Test ONNX background removal
        result = remove_background_onnx(test_img)
        
        # Check if result is RGBA
        assert result.mode == 'RGBA', f"Expected RGBA mode, got {result.mode}"
        
        print("✅ ONNX background removal test passed")
        return True
        
    except Exception as e:
        print(f"❌ ONNX background removal test failed: {str(e)}")
        print("This is expected if no ONNX model is available - fallback should work")
        return False

def test_id_service_integration():
    """Test ID service integration with ONNX."""
    print("Testing ID service integration...")
    
    try:
        from services.id_card_service import IDCardService
        
        # Initialize service
        id_service = IDCardService()
        
        # Create test data
        test_data = {
            'photo_bytes': create_test_image().tobytes(),
            'name_en': 'Test User',
            'name_am': 'ቴስት ተጠቃሚ',
            'fcn_full': '1234567890123456'
        }
        
        # Test photo data processing with ONNX
        photo_bytes = id_service.get_photo_data(
            test_data, 
            remove_white=False, 
            remove_black=False, 
            use_onnx=True
        )
        
        # Check if we get bytes back
        assert isinstance(photo_bytes, bytes), "Expected bytes from get_photo_data"
        assert len(photo_bytes) > 0, "Photo bytes should not be empty"
        
        print("✅ ID service integration test passed")
        return True
        
    except Exception as e:
        print(f"❌ ID service integration test failed: {str(e)}")
        return False

def test_fallback_behavior():
    """Test fallback behavior when ONNX is not available."""
    print("Testing fallback behavior...")
    
    try:
        from services.onnx_bg_removal import ONNXBackgroundRemoval
        
        # Create service with non-existent model path
        bg_removal = ONNXBackgroundRemoval(model_path="non_existent_model.onnx")
        
        # Test image
        test_img = create_test_image()
        
        # Should fall back to simple method
        result = bg_removal.remove_background_onnx(test_img)
        
        # Should still return a valid image
        assert result.mode == 'RGBA', f"Expected RGBA mode, got {result.mode}"
        assert result.size == test_img.size, "Size should be preserved"
        
        print("✅ Fallback behavior test passed")
        return True
        
    except Exception as e:
        print(f"❌ Fallback behavior test failed: {str(e)}")
        return False

def main():
    """Run all tests."""
    print("ONNX Background Removal Test Suite")
    print("=" * 40)
    
    tests = [
        test_simple_background_removal,
        test_onnx_background_removal,
        test_id_service_integration,
        test_fallback_behavior
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        try:
            if test():
                passed += 1
        except Exception as e:
            print(f"❌ Test {test.__name__} crashed: {str(e)}")
        print()
    
    print("=" * 40)
    print(f"Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed!")
    else:
        print("⚠️  Some tests failed - check the output above")
    
    return passed == total

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)











