#!/usr/bin/env python3
"""
Check PDF file size to see if it meets the criteria
"""

import os

def check_pdf_size():
    pdf_path = input("Enter path to your PDF file: ").strip()
    
    if not pdf_path:
        print("No PDF path provided")
        return
        
    if not os.path.exists(pdf_path):
        print(f"❌ PDF file not found: {pdf_path}")
        return
    
    file_size = os.path.getsize(pdf_path)
    file_size_mb = file_size / (1024 * 1024)
    
    print(f"📄 PDF file: {pdf_path}")
    print(f"📄 File size: {file_size} bytes ({file_size_mb:.2f} MB)")
    
    # Check if it meets the criteria
    if 1.7 <= file_size_mb <= 2.0:
        print("✅ PDF size is in the 1.7-2.0 MB range - FIN extraction should be attempted")
    else:
        print("⚠️ PDF size is NOT in the 1.7-2.0 MB range - FIN extraction will be skipped")
        print("   The system only processes PDFs between 1.7-2.0 MB for FIN extraction")

if __name__ == "__main__":
    check_pdf_size()