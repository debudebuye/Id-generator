#!/usr/bin/env python3
"""
Test the full FIN extraction process
"""

import sys
import os
sys.path.append('.')

from app.services.id_card_service import IDCardService
from io import BytesIO

def test_full_extraction():
    pdf_path = input("Enter path to your PDF file: ").strip()
    
    if not pdf_path:
        print("No PDF path provided")
        return
        
    if not os.path.exists(pdf_path):
        print(f"❌ PDF file not found: {pdf_path}")
        return
    
    # Check file size
    file_size = os.path.getsize(pdf_path)
    file_size_mb = file_size / (1024 * 1024)
    print(f"📄 PDF file size: {file_size_mb:.2f} MB")
    
    if not (1.7 <= file_size_mb <= 2.0):
        print("⚠️ PDF size is not in 1.7-2.0 MB range - this might be why FIN extraction is failing")
        print("   The system only processes PDFs in this size range")
        return
    
    # Test extraction
    service = IDCardService()
    
    print("\n🔍 Testing FIN extraction...")
    
    # Method 1: Direct file path
    print("\n--- Method 1: Direct file path ---")
    fin1 = service.extract_fin_from_pdf(pdf_path)
    print(f"Result: {fin1}")
    
    # Method 2: BytesIO stream (like web upload)
    print("\n--- Method 2: BytesIO stream ---")
    with open(pdf_path, 'rb') as f:
        pdf_bytes = f.read()
    
    pdf_stream = BytesIO(pdf_bytes)
    fin2 = service.extract_fin_from_pdf(pdf_stream)
    print(f"Result: {fin2}")
    
    if fin1 or fin2:
        print(f"\n✅ FIN extraction successful!")
        print(f"   File path method: {fin1}")
        print(f"   Stream method: {fin2}")
    else:
        print(f"\n❌ FIN extraction failed with both methods")
        print("   Check the debug images created:")
        print("   - temp_fin_region.png (shows the OCR region)")
        print("   - Look at the console output for OCR results")

if __name__ == "__main__":
    test_full_extraction()