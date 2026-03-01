#!/usr/bin/env python3
"""
Debug script for FIN extraction issues.
This script helps test and debug FIN extraction from PDFs.
"""

import os
import sys
from io import BytesIO

def test_fin_extraction():
    """Test FIN extraction with the current PDF."""
    print("FIN Extraction Debug Test")
    print("=" * 40)
    
    try:
        # Import the ID card service
        sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))
        from app.services.id_card_service import IDCardService
        
        # Initialize service
        id_service = IDCardService()
        
        # Test with a sample PDF file
        pdf_path = input("Enter the path to your PDF file (or press Enter to skip): ").strip()
        
        if not pdf_path or not os.path.exists(pdf_path):
            print("No valid PDF file provided. Testing with mock data...")
            
            # Test the OCR method directly
            print("\nTesting OCR configuration...")
            test_ocr_configs()
            return True
        
        print(f"Testing FIN extraction from: {pdf_path}")
        
        # Check file size
        file_size = os.path.getsize(pdf_path)
        file_size_mb = file_size / (1024 * 1024)
        print(f"File size: {file_size_mb:.2f} MB")
        
        if 1.7 * 1024 * 1024 <= file_size <= 2.0 * 1024 * 1024:
            print("✅ File size is in target range (~1.8-1.9 MB)")
            
            # Extract FIN
            with open(pdf_path, 'rb') as f:
                pdf_data = BytesIO(f.read())
                fin = id_service.extract_fin_from_pdf(pdf_data)
                
                if fin:
                    print(f"✅ FIN extracted: {fin}")
                    print(f"Expected FIN: 679571631281")
                    if fin == "679571631281":
                        print("🎉 CORRECT FIN EXTRACTED!")
                    else:
                        print("❌ INCORRECT FIN EXTRACTED!")
                        print("This indicates an OCR or positioning issue.")
                else:
                    print("❌ No FIN extracted")
                    print("This could be due to:")
                    print("1. OCR not installed properly")
                    print("2. Incorrect positioning")
                    print("3. Poor image quality")
        else:
            print(f"⚠️ File size ({file_size_mb:.2f} MB) is not in target range (1.7-2.0 MB)")
            print("FIN extraction will be skipped for this file size.")
        
        return True
        
    except Exception as e:
        print(f"❌ Test failed: {str(e)}")
        return False

def test_ocr_configs():
    """Test different OCR configurations."""
    print("\nTesting OCR Configurations:")
    print("-" * 30)
    
    try:
        import pytesseract
        from PIL import Image, ImageDraw, ImageFont
        
        # Create a test image with the expected FIN
        img = Image.new('RGB', (300, 100), color='white')
        draw = ImageDraw.Draw(img)
        
        try:
            font = ImageFont.truetype("arial.ttf", 24)
        except:
            font = ImageFont.load_default()
        
        # Draw the expected FIN number
        test_fin = "679571631281"
        draw.text((20, 30), test_fin, fill='black', font=font)
        
        # Test different OCR configurations
        configs = [
            ('Numbers only (PSM 6)', r'--oem 3 --psm 6 -c tessedit_char_whitelist=0123456789'),
            ('Numbers only (PSM 8)', r'--oem 3 --psm 8 -c tessedit_char_whitelist=0123456789'),
            ('Default (PSM 6)', r'--oem 3 --psm 6'),
            ('Default (PSM 8)', r'--oem 3 --psm 8'),
            ('Single word (PSM 7)', r'--oem 3 --psm 7'),
            ('Single text line (PSM 13)', r'--oem 3 --psm 13'),
        ]
        
        for config_name, config in configs:
            try:
                text = pytesseract.image_to_string(img, config=config)
                text = text.strip()
                print(f"{config_name:25}: '{text}'")
                
                if test_fin in text:
                    print(f"{'':25}  ✅ CORRECT!")
                elif text:
                    print(f"{'':25}  ⚠️  Different result")
                else:
                    print(f"{'':25}  ❌ No text detected")
                    
            except Exception as e:
                print(f"{config_name:25}: ERROR - {str(e)}")
        
        print("\nOCR Test Complete")
        
    except ImportError:
        print("❌ pytesseract not available")
        print("Please install Tesseract OCR first:")
        print("1. Download from: https://github.com/UB-Mannheim/tesseract/wiki")
        print("2. Install with 'Add to PATH' option checked")
        print("3. Restart your terminal/IDE")
    except Exception as e:
        print(f"❌ OCR test failed: {str(e)}")

def main():
    """Main debug function."""
    print("FIN Extraction Debug Tool")
    print("=" * 40)
    print("This tool helps debug FIN extraction issues.")
    print("Expected FIN: 679571631281")
    print("Extracted FIN: 509624074926 (incorrect)")
    print("=" * 40)
    
    success = test_fin_extraction()
    
    if not success:
        print("\n" + "=" * 40)
        print("TROUBLESHOOTING STEPS")
        print("=" * 40)
        print("1. Install Tesseract OCR:")
        print("   - Download from: https://github.com/UB-Mannheim/tesseract/wiki")
        print("   - Install with 'Add to PATH' option")
        print("   - Restart terminal/IDE")
        print()
        print("2. Check PDF quality:")
        print("   - Ensure PDF is clear and readable")
        print("   - FIN should be visible below QR code")
        print()
        print("3. Test with different PDF:")
        print("   - Try with another ~1.8-1.9 MB PDF")
        print("   - Check if issue is PDF-specific")
        print()
        print("4. Manual verification:")
        print("   - Open PDF and locate FIN manually")
        print("   - Verify FIN position matches expected location")

if __name__ == "__main__":
    main()
