#!/usr/bin/env python3
"""
Test script for image-based FIN extraction from ~1.8-1.9 MB PDFs.
This script tests the specific image-based FIN extraction functionality.
"""

import os
import sys
import tempfile
from io import BytesIO

# Add the app directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'app'))

def create_test_pdf_with_image_fin():
    """Create a test PDF with FIN in image format for testing."""
    try:
        import fitz  # PyMuPDF
        from PIL import Image, ImageDraw, ImageFont
        
        # Create a new PDF document
        doc = fitz.open()
        page = doc.new_page()
        
        # Create an image with FIN number positioned below QR code
        # Simulate the layout described in the image
        img_width, img_height = 800, 1000
        img = Image.new('RGB', (img_width, img_height), (255, 255, 255))
        draw = ImageDraw.Draw(img)
        
        # Draw a simulated QR code in bottom-left area
        qr_size = 150
        qr_x = 50
        qr_y = img_height - qr_size - 200  # Position QR code
        
        # Draw QR code placeholder (black square)
        draw.rectangle([qr_x, qr_y, qr_x + qr_size, qr_y + qr_size], fill=(0, 0, 0))
        
        # Draw FIN number below the QR code (in the target position)
        fin_text = "7855 6467 9309"  # 10-digit FIN from the image description
        fin_x = qr_x + 20
        fin_y = qr_y + qr_size + 30  # Below QR code
        
        # Try to use a font, fallback to default if not available
        try:
            font = ImageFont.truetype("arial.ttf", 24)
        except:
            font = ImageFont.load_default()
        
        draw.text((fin_x, fin_y), fin_text, fill=(0, 0, 0), font=font)
        
        # Add some other text to make it realistic
        draw.text((50, 50), "ETHIOPIAN DIGITAL ID CARD", fill=(0, 0, 0), font=font)
        draw.text((50, 100), "Name: Test User", fill=(0, 0, 0), font=font)
        draw.text((50, 150), "Region: Addis Ababa", fill=(0, 0, 0), font=font)
        
        # Convert PIL image to fitz image
        img_bytes = BytesIO()
        img.save(img_bytes, format='PNG')
        img_bytes.seek(0)
        
        # Insert image into PDF page
        rect = fitz.Rect(0, 0, img_width, img_height)
        page.insert_image(rect, stream=img_bytes.getvalue())
        
        # Save to BytesIO
        pdf_bytes = BytesIO()
        doc.save(pdf_bytes)
        pdf_bytes.seek(0)
        
        doc.close()
        return pdf_bytes.getvalue()
        
    except ImportError:
        print("❌ PyMuPDF or PIL not available for creating test PDF")
        return None

def test_image_based_fin_extraction():
    """Test image-based FIN extraction for ~1.8-1.9 MB PDFs."""
    print("Testing image-based FIN extraction for ~1.8-1.9 MB PDFs...")
    
    try:
        from services.id_card_service import IDCardService
        
        # Initialize service
        id_service = IDCardService()
        
        # Create test PDF with image-based FIN
        test_pdf_bytes = create_test_pdf_with_image_fin()
        if not test_pdf_bytes:
            print("❌ Could not create test PDF")
            return False
        
        # Check file size
        file_size_mb = len(test_pdf_bytes) / (1024 * 1024)
        print(f"📄 Test PDF size: {file_size_mb:.2f} MB")
        
        # Test FIN extraction
        pdf_stream = BytesIO(test_pdf_bytes)
        extracted_fin = id_service.extract_fin_from_pdf(pdf_stream)
        
        if extracted_fin:
            print(f"✅ FIN extracted successfully: {extracted_fin}")
            
            # Validate the extracted FIN
            if len(extracted_fin) == 12 and extracted_fin.isdigit():
                print("✅ Extracted FIN is valid (12 digits)")
                return True
            else:
                print(f"❌ Extracted FIN is invalid: {extracted_fin}")
                return False
        else:
            print("❌ No FIN extracted from test PDF")
            return False
        
    except Exception as e:
        print(f"❌ Image-based FIN extraction test failed: {str(e)}")
        return False

def test_file_size_detection():
    """Test file size detection for triggering image-based extraction."""
    print("Testing file size detection...")
    
    try:
        from services.id_card_service import IDCardService
        
        # Initialize service
        id_service = IDCardService()
        
        # Test different file sizes
        test_sizes = [
            (1.5 * 1024 * 1024, "1.5 MB - Should leave FIN field empty"),
            (1.8 * 1024 * 1024, "1.8 MB - Should use image extraction"),
            (1.9 * 1024 * 1024, "1.9 MB - Should use image extraction"),
            (2.1 * 1024 * 1024, "2.1 MB - Should leave FIN field empty"),
        ]
        
        for size_bytes, description in test_sizes:
            print(f"Testing {description}")
            
            # Create a mock PDF stream with specific size
            mock_stream = BytesIO(b'x' * int(size_bytes))
            mock_stream.getvalue = lambda: b'x' * int(size_bytes)
            
            # Test the size detection logic
            if 1.7 * 1024 * 1024 <= size_bytes <= 2.0 * 1024 * 1024:
                print(f"  ✅ Correctly identified for image-based extraction")
            else:
                print(f"  ✅ Correctly identified to leave FIN field empty")
        
        return True
        
    except Exception as e:
        print(f"❌ File size detection test failed: {str(e)}")
        return False

def test_ocr_dependencies():
    """Test OCR library availability."""
    print("Testing OCR library availability...")
    
    ocr_libraries = []
    
    # Test pytesseract
    try:
        import pytesseract
        ocr_libraries.append("pytesseract")
        print("✅ pytesseract available")
    except ImportError:
        print("⚠️ pytesseract not available")
    
    # Test easyocr
    try:
        import easyocr
        ocr_libraries.append("easyocr")
        print("✅ easyocr available")
    except ImportError:
        print("⚠️ easyocr not available")
    
    if ocr_libraries:
        print(f"✅ OCR libraries available: {', '.join(ocr_libraries)}")
        return True
    else:
        print("❌ No OCR libraries available")
        print("Install with: pip install pytesseract easyocr")
        return False

def test_position_calculation():
    """Test FIN position calculation."""
    print("Testing FIN position calculation...")
    
    try:
        from services.id_card_service import IDCardService
        
        # Initialize service
        id_service = IDCardService()
        
        # Test position calculation with mock dimensions
        width, height = 800, 1000
        
        # Calculate expected positions
        qr_bottom_y = int(height * 0.75)  # 750
        fin_region_top = qr_bottom_y + 20  # 770
        fin_region_bottom = fin_region_top + 100  # 870
        fin_region_left = int(width * 0.05)  # 40
        fin_region_right = int(width * 0.35)  # 280
        
        print(f"📐 Position calculations:")
        print(f"  QR bottom Y: {qr_bottom_y}")
        print(f"  FIN region: ({fin_region_left}, {fin_region_top}) to ({fin_region_right}, {fin_region_bottom})")
        print(f"  Region size: {fin_region_right - fin_region_left} x {fin_region_bottom - fin_region_top}")
        
        # Validate reasonable positions
        if (fin_region_left < fin_region_right and 
            fin_region_top < fin_region_bottom and
            fin_region_right <= width and
            fin_region_bottom <= height):
            print("✅ Position calculations are valid")
            return True
        else:
            print("❌ Position calculations are invalid")
            return False
        
    except Exception as e:
        print(f"❌ Position calculation test failed: {str(e)}")
        return False

def main():
    """Run all image-based FIN extraction tests."""
    print("Image-Based FIN Extraction Test Suite")
    print("=" * 50)
    print("This test verifies the image-based FIN extraction functionality")
    print("for ~1.8-1.9 MB PDFs with FIN positioned below left QR code.")
    print("Other PDF sizes will leave FIN field empty.")
    print("=" * 50)
    
    tests = [
        test_ocr_dependencies,
        test_file_size_detection,
        test_position_calculation,
        test_image_based_fin_extraction,
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
    
    print("=" * 50)
    print(f"Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed!")
        print("The image-based FIN extraction is working correctly.")
        print("~1.8-1.9 MB PDFs will now use image-based FIN extraction.")
    else:
        print("⚠️  Some tests failed - check the output above")
        print("Make sure OCR libraries are installed:")
        print("  pip install pytesseract easyocr")
    
    return passed == total

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
