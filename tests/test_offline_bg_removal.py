#!/usr/bin/env python3
"""
Test script for offline background removal using rembg library.
This script tests the offline background removal functionality.
"""

import os
import sys
import tempfile
from PIL import Image
import numpy as np

# Add the app directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'app'))

def create_test_portrait():
    """Create a test portrait image with white background."""
    # Create a 300x400 image with white background
    img = Image.new('RGB', (300, 400), (255, 255, 255))
    
    # Draw a simple face in the center
    from PIL import ImageDraw
    draw = ImageDraw.Draw(img)
    
    # Face (circle) - skin tone
    draw.ellipse([100, 80, 200, 180], fill=(220, 180, 140))
    
    # Eyes
    draw.ellipse([120, 110, 135, 125], fill=(0, 0, 0))  # Left eye
    draw.ellipse([165, 110, 180, 125], fill=(0, 0, 0))  # Right eye
    
    # Nose
    draw.ellipse([145, 140, 155, 150], fill=(200, 160, 120))
    
    # Mouth
    draw.ellipse([140, 160, 160, 170], fill=(150, 50, 50))
    
    # Hair
    draw.ellipse([90, 60, 210, 120], fill=(50, 30, 20))
    
    return img

def test_offline_background_removal():
    """Test the offline background removal service."""
    print("Testing offline background removal service...")
    
    try:
        from services.offline_bg_removal import OfflineBackgroundRemoval, is_offline_bg_removal_available
        
        # Check if service is available
        if not is_offline_bg_removal_available():
            print("❌ Offline background removal service not available")
            return False
        
        # Create service instance
        bg_removal = OfflineBackgroundRemoval()
        
        # Get model info
        info = bg_removal.get_model_info()
        print(f"📊 Model Info: {info}")
        
        # Create test image
        test_img = create_test_portrait()
        
        # Test background removal
        print("🔄 Testing background removal...")
        result_img = bg_removal.remove_background(test_img)
        
        if result_img is None:
            print("❌ Background removal returned None")
            return False
        
        # Check if result is RGBA
        assert result_img.mode == 'RGBA', f"Expected RGBA mode, got {result_img.mode}"
        
        # Check if background is transparent
        alpha = result_img.split()[-1]
        alpha_array = np.array(alpha)
        
        # White background areas should be transparent (alpha = 0)
        white_areas = alpha_array == 0
        if not white_areas.any():
            print("⚠️ Warning: No transparent areas found (background might not be removed)")
        
        # Face area should be visible (alpha > 0)
        center_alpha = alpha_array[100:200, 100:200]  # Center area where face is
        face_visible = np.any(center_alpha > 0)
        assert face_visible, "Face area should be visible (not transparent)"
        
        print("✅ Offline background removal test passed")
        return True
        
    except Exception as e:
        print(f"❌ Offline background removal test failed: {str(e)}")
        return False

def test_file_processing():
    """Test file-based background removal."""
    print("Testing file-based background removal...")
    
    try:
        from services.offline_bg_removal import OfflineBackgroundRemoval
        
        # Create service instance
        bg_removal = OfflineBackgroundRemoval()
        
        # Create test image and save to temporary file
        test_img = create_test_portrait()
        
        with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as temp_input:
            test_img.save(temp_input.name)
            input_path = temp_input.name
        
        try:
            # Test file processing
            success = bg_removal.remove_background_from_file(input_path)
            
            if not success:
                print("❌ File processing failed")
                return False
            
            # Check if output file was created
            output_path = input_path.replace('.png', '_nobg.png')
            if not os.path.exists(output_path):
                print("❌ Output file was not created")
                return False
            
            # Load and verify output
            output_img = Image.open(output_path)
            assert output_img.mode == 'RGBA', f"Expected RGBA mode, got {output_img.mode}"
            
            print("✅ File-based background removal test passed")
            return True
            
        finally:
            # Clean up temporary files
            if os.path.exists(input_path):
                os.unlink(input_path)
            output_path = input_path.replace('.png', '_nobg.png')
            if os.path.exists(output_path):
                os.unlink(output_path)
        
    except Exception as e:
        print(f"❌ File processing test failed: {str(e)}")
        return False

def test_bytes_processing():
    """Test bytes-based background removal."""
    print("Testing bytes-based background removal...")
    
    try:
        from services.offline_bg_removal import remove_background_to_bytes_offline
        
        # Create test image
        test_img = create_test_portrait()
        
        # Convert to bytes
        from io import BytesIO
        buffer = BytesIO()
        test_img.save(buffer, format='PNG')
        input_bytes = buffer.getvalue()
        
        # Test bytes processing
        result_bytes = remove_background_to_bytes_offline(input_bytes)
        
        if result_bytes is None:
            print("❌ Bytes processing returned None")
            return False
        
        # Convert back to image and verify
        result_img = Image.open(BytesIO(result_bytes))
        assert result_img.mode == 'RGBA', f"Expected RGBA mode, got {result_img.mode}"
        
        print("✅ Bytes-based background removal test passed")
        return True
        
    except Exception as e:
        print(f"❌ Bytes processing test failed: {str(e)}")
        return False

def test_id_service_integration():
    """Test integration with ID card service."""
    print("Testing ID service integration...")
    
    try:
        from services.id_card_service import IDCardService
        
        # Initialize service
        id_service = IDCardService()
        
        # Create test data
        test_data = {
            'photo_bytes': create_test_portrait().tobytes(),
            'name_en': 'Test User',
            'name_am': 'ቴስት ተጠቃሚ',
            'fcn_full': '1234567890123456'
        }
        
        # Test photo data processing with offline background removal
        photo_bytes = id_service.get_photo_data(
            test_data, 
            remove_white=False, 
            remove_black=False, 
            use_onnx=True  # This now uses offline rembg
        )
        
        # Check if we get bytes back
        assert isinstance(photo_bytes, bytes), "Expected bytes from get_photo_data"
        assert len(photo_bytes) > 0, "Photo bytes should not be empty"
        
        print("✅ ID service integration test passed")
        return True
        
    except Exception as e:
        print(f"❌ ID service integration test failed: {str(e)}")
        return False

def main():
    """Run all offline background removal tests."""
    print("Offline Background Removal Test Suite")
    print("=" * 45)
    print("This test will download the U²-Net model on first run.")
    print("The model will be cached locally for future use.")
    print("=" * 45)
    
    tests = [
        test_offline_background_removal,
        test_file_processing,
        test_bytes_processing,
        test_id_service_integration
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
        print("🎉 All tests passed!")
        print("The offline background removal is working correctly.")
        print("The system will now use rembg for high-quality background removal.")
    else:
        print("⚠️  Some tests failed - check the output above")
        print("Make sure rembg is installed: pip install rembg")
    
    return passed == total

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)










