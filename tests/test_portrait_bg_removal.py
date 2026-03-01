#!/usr/bin/env python3
"""
Test script specifically for portrait background removal to ensure faces are preserved.
"""

import os
import sys
import tempfile
from PIL import Image
import numpy as np

# Add the app directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'app'))

def create_portrait_test_image():
    """Create a test portrait image with white background."""
    # Create a 200x200 image with white background
    img = Image.new('RGB', (200, 200), (255, 255, 255))
    
    # Draw a simple face in the center
    from PIL import ImageDraw
    draw = ImageDraw.Draw(img)
    
    # Face (circle)
    draw.ellipse([60, 40, 140, 120], fill=(220, 180, 140))  # Skin tone
    
    # Eyes
    draw.ellipse([75, 60, 85, 70], fill=(0, 0, 0))  # Left eye
    draw.ellipse([115, 60, 125, 70], fill=(0, 0, 0))  # Right eye
    
    # Nose
    draw.ellipse([95, 80, 105, 90], fill=(200, 160, 120))  # Nose
    
    # Mouth
    draw.ellipse([90, 100, 110, 110], fill=(150, 50, 50))  # Mouth
    
    return img

def test_portrait_safe_removal():
    """Test the portrait-safe background removal method."""
    print("Testing portrait-safe background removal...")
    
    try:
        from services.onnx_bg_removal import remove_background_portrait_safe
        
        # Create test portrait
        test_img = create_portrait_test_image()
        
        # Apply portrait-safe background removal
        result = remove_background_portrait_safe(test_img)
        
        # Check if result is RGBA
        assert result.mode == 'RGBA', f"Expected RGBA mode, got {result.mode}"
        
        # Check if the face area is preserved (not transparent)
        # Get alpha channel
        alpha = result.split()[-1]
        alpha_array = np.array(alpha)
        
        # Face area should be visible (alpha > 0)
        # Check center area where face is
        center_alpha = alpha_array[80:120, 80:120]  # Center area
        face_visible = np.any(center_alpha > 0)
        assert face_visible, "Face area should be visible (not transparent)"
        
        # Background should be transparent
        # Check corners where background is
        corner_alpha = alpha_array[0:20, 0:20]  # Top-left corner
        background_transparent = np.all(corner_alpha == 0)
        assert background_transparent, "Background should be transparent"
        
        print("✅ Portrait-safe background removal test passed")
        return True
        
    except Exception as e:
        print(f"❌ Portrait-safe background removal test failed: {str(e)}")
        return False

def test_improved_simple_removal():
    """Test the improved simple background removal."""
    print("Testing improved simple background removal...")
    
    try:
        from services.onnx_bg_removal import remove_background_simple
        
        # Create test portrait
        test_img = create_portrait_test_image()
        
        # Apply simple background removal
        result = remove_background_simple(test_img, remove_white=True, remove_black=False)
        
        # Check if result is RGBA
        assert result.mode == 'RGBA', f"Expected RGBA mode, got {result.mode}"
        
        # Check if the face area is preserved
        alpha = result.split()[-1]
        alpha_array = np.array(alpha)
        
        # Face area should be visible
        center_alpha = alpha_array[80:120, 80:120]
        face_visible = np.any(center_alpha > 0)
        assert face_visible, "Face area should be visible"
        
        print("✅ Improved simple background removal test passed")
        return True
        
    except Exception as e:
        print(f"❌ Improved simple background removal test failed: {str(e)}")
        return False

def test_ultra_simple_removal():
    """Test the ultra-simple background removal."""
    print("Testing ultra-simple background removal...")
    
    try:
        from services.onnx_bg_removal import ONNXBackgroundRemoval
        
        # Create service instance
        bg_removal = ONNXBackgroundRemoval()
        
        # Create test portrait
        test_img = create_portrait_test_image()
        
        # Apply ultra-simple background removal
        result = bg_removal._ultra_simple_background_removal(test_img, remove_white=True, remove_black=False)
        
        # Check if result is RGBA
        assert result.mode == 'RGBA', f"Expected RGBA mode, got {result.mode}"
        
        # This method should be very conservative
        alpha = result.split()[-1]
        alpha_array = np.array(alpha)
        
        # Most of the image should still be visible (very conservative)
        visible_pixels = np.sum(alpha_array > 0)
        total_pixels = alpha_array.size
        visibility_ratio = visible_pixels / total_pixels
        
        # Should preserve most of the image (very conservative)
        assert visibility_ratio > 0.8, f"Ultra-simple method should preserve most of the image, got {visibility_ratio:.2f}"
        
        print("✅ Ultra-simple background removal test passed")
        return True
        
    except Exception as e:
        print(f"❌ Ultra-simple background removal test failed: {str(e)}")
        return False

def main():
    """Run all portrait-specific tests."""
    print("Portrait Background Removal Test Suite")
    print("=" * 45)
    
    tests = [
        test_portrait_safe_removal,
        test_improved_simple_removal,
        test_ultra_simple_removal
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
    
    print("=" * 45)
    print(f"Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All portrait tests passed!")
        print("The background removal should now preserve faces better.")
    else:
        print("⚠️  Some tests failed - check the output above")
    
    return passed == total

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)











