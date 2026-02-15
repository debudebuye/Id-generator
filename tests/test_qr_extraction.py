"""
Test QR code extraction from back ID card image
"""
import os
import sys

# Add app directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'app'))

from services.ocr_extraction_service import OCRExtractionService

def test_qr_extraction():
    """Test QR code extraction"""
    print("=" * 60)
    print("Testing QR Code Extraction")
    print("=" * 60)
    
    # Initialize OCR service
    ocr_service = OCRExtractionService()
    
    # Test with a back card image (you'll need to provide the path)
    back_image_path = input("Enter path to back ID card image: ").strip()
    
    if not os.path.exists(back_image_path):
        print(f"❌ Image not found: {back_image_path}")
        return
    
    # Extract QR code region
    output_path = "test_qr_extracted.png"
    print(f"\n🔍 Extracting QR code from: {back_image_path}")
    
    qr_path = ocr_service.extract_qr_code_region(back_image_path, output_path)
    
    if qr_path:
        print(f"✅ QR code extracted successfully!")
        print(f"   Saved to: {qr_path}")
        
        # Try to decode QR code
        print(f"\n🔍 Attempting to decode QR code...")
        qr_data = ocr_service.decode_qr_code(qr_path)
        
        if qr_data:
            print(f"✅ QR code decoded successfully!")
            print(f"   Data length: {len(qr_data)} characters")
            print(f"   First 200 chars: {qr_data[:200]}")
        else:
            print("⚠️ QR code decoding failed or pyzbar not installed")
            print("   Install pyzbar with: pip install pyzbar")
    else:
        print("❌ QR code extraction failed")
    
    print("\n" + "=" * 60)

if __name__ == "__main__":
    test_qr_extraction()
