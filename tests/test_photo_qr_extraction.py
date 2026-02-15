"""
Test script to extract photo and QR from combined image
"""
import os
import sys

def test_extraction(image_path, output_dir='app/static/temp'):
    """Test photo and QR extraction from combined image"""
    
    # Add parent directory to path to import app modules
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    
    from app.utils.image_utils import detect_and_extract_photo_qr
    
    if not os.path.exists(image_path):
        print(f"❌ Image not found: {image_path}")
        print(f"\nUsage: python test_photo_qr_extraction.py <path_to_combined_image>")
        return
    
    # Create output directory if it doesn't exist
    os.makedirs(output_dir, exist_ok=True)
    
    print(f"\n{'='*70}")
    print(f"Testing Photo + QR Extraction")
    print(f"{'='*70}")
    print(f"Input image: {image_path}")
    print(f"Output directory: {output_dir}\n")
    
    # Run extraction
    photo_path, qr_path = detect_and_extract_photo_qr(image_path, output_dir)
    
    if photo_path and qr_path:
        print(f"\n{'='*70}")
        print(f"✅ EXTRACTION SUCCESSFUL!")
        print(f"{'='*70}")
        print(f"Photo saved to: {photo_path}")
        print(f"QR saved to: {qr_path}")
        print(f"\nYou can now view the extracted images in: {output_dir}")
    else:
        print(f"\n{'='*70}")
        print(f"❌ EXTRACTION FAILED!")
        print(f"{'='*70}")
        print(f"Please check the error messages above for details.")
    
    print(f"\n{'='*70}\n")

if __name__ == '__main__':
    # Check for command line argument
    if len(sys.argv) > 1:
        test_image = sys.argv[1]
    else:
        # Default test image path
        test_image = 'app/static/sample_photo_qr.png'
        print(f"No image path provided. Using default: {test_image}")
        print(f"Usage: python test_photo_qr_extraction.py <path_to_combined_image>\n")
    
    test_extraction(test_image)
