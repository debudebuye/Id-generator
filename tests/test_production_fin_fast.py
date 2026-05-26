#!/usr/bin/env python3
"""
Test FIN extraction with optimized fast OCR on production PDF
"""

import os
import sys
import time

# Add the project root to Python path
sys.path.insert(0, os.path.dirname(__file__))

from app.services.id_card_service import IDCardService

def test_production_fin_extraction():
    """Test FIN extraction on production PDF with timing"""
    print("Fast FIN Extraction Test - Production PDF")
    print("=" * 50)
    
    # Initialize service
    service = IDCardService()
    
    # Test file path (production PDF)
    test_pdf = "app/templates/cbac40b8-2574-4487-aedc-03638680c3ab.pdf"
    
    if not os.path.exists(test_pdf):
        print(f"❌ Test PDF not found: {test_pdf}")
        return False
    
    # Get file size
    file_size = os.path.getsize(test_pdf)
    print(f"📄 PDF file size: {file_size / (1024*1024):.2f} MB")
    print()
    
    print(f"🔍 Extracting FIN from: {test_pdf}")
    
    # Time the extraction
    start_time = time.time()
    
    try:
        fin = service.extract_fin_from_pdf(test_pdf)
        
        end_time = time.time()
        extraction_time = end_time - start_time
        
        if fin:
            print(f"✅ FIN extracted successfully: {fin}")
            print(f"📏 FIN length: {len(fin)} digits")
            print(f"⏱️ Extraction time: {extraction_time:.2f} seconds")
            
            # Validate FIN format
            if len(fin) == 12 and fin.isdigit():
                print("✅ FIN format is valid (12 digits)")
            else:
                print(f"⚠️ FIN format may be invalid: length={len(fin)}, all_digits={fin.isdigit()}")
            
            print()
            print("🎉 Test completed successfully!")
            print(f"🚀 Performance improvement: Extraction completed in {extraction_time:.2f} seconds")
            return True
        else:
            print("❌ FIN extraction failed")
            print(f"⏱️ Extraction time: {extraction_time:.2f} seconds")
            return False
            
    except Exception as e:
        end_time = time.time()
        extraction_time = end_time - start_time
        print(f"❌ Error during FIN extraction: {str(e)}")
        print(f"⏱️ Time before error: {extraction_time:.2f} seconds")
        return False

if __name__ == "__main__":
    success = test_production_fin_extraction()
    sys.exit(0 if success else 1)