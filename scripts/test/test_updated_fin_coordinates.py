#!/usr/bin/env python3
"""
Test script to verify the updated FIN coordinates work correctly.
"""

import os
import sys
from io import BytesIO

# Add the app directory to the path
sys.path.insert(0, os.path.dirname(__file__))

def test_fin_extraction_with_new_coordinates():
    """Test FIN extraction using the updated coordinates."""
    print("Testing FIN extraction with updated coordinates")
    print("=" * 50)
    
    try:
        from app.services.id_card_service import IDCardService
        
        # Initialize service
        service = IDCardService()
        
        # Test with the specific PDF file
        pdf_path = "app/templates/cbac40b8-2574-4487-aedc-03638680c3ab.pdf"
        
        if not os.path.exists(pdf_path):
            print(f"❌ PDF file not found: {pdf_path}")
            return False
        
        # Check file size
        file_size = os.path.getsize(pdf_path)
        file_size_mb = file_size / (1024 * 1024)
        print(f"📄 PDF file size: {file_size_mb:.2f} MB")
        
        if not (1.7 <= file_size_mb <= 2.0):
            print("⚠️ PDF size is not in the expected range (1.7-2.0 MB)")
            print("   FIN extraction may be skipped")
        
        # Extract FIN using updated coordinates
        print(f"\n🔍 Extracting FIN from: {pdf_path}")
        extracted_fin = service.extract_fin_from_pdf(pdf_path)
        
        if extracted_fin:
            print(f"✅ FIN extracted successfully: {extracted_fin}")
            print(f"📏 FIN length: {len(extracted_fin)} digits")
            
            # Validate FIN format
            if len(extracted_fin) == 12 and extracted_fin.isdigit():
                print("✅ FIN format is valid (12 digits)")
            else:
                print(f"⚠️ FIN format may be incorrect: {extracted_fin}")
            
            return True
        else:
            print("❌ No FIN extracted")
            print("Check the debug image 'temp_fin_region.png' to see the extracted region")
            return False
        
    except Exception as e:
        print(f"❌ Test failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Main test function."""
    print("FIN Extraction Test with Updated Coordinates")
    print("=" * 50)
    print("Testing with updated Photoshop coordinates:")
    print("  X: 2141")
    print("  Y: 1984") 
    print("  Width: 184")
    print("  Height: 26")
    print("=" * 50)
    
    success = test_fin_extraction_with_new_coordinates()
    
    if success:
        print("\n🎉 Test completed successfully!")
        print("The updated coordinates are working correctly.")
    else:
        print("\n❌ Test failed.")
        print("Check the following:")
        print("1. Tesseract OCR is installed and in PATH")
        print("2. The PDF file exists and is readable")
        print("3. The coordinates are correct for this specific PDF")
        print("4. Check 'temp_fin_region.png' for the extracted region")

if __name__ == "__main__":
    main()