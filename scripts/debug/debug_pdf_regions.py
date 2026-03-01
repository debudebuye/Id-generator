#!/usr/bin/env python3
"""
Debug script to test PDF region extraction
"""

import sys
import os
sys.path.append('.')

import fitz
from PIL import Image
import io

def debug_pdf_regions(pdf_path):
    print(f"🔍 Debugging PDF regions for: {pdf_path}")
    
    if not os.path.exists(pdf_path):
        print(f"❌ PDF file not found: {pdf_path}")
        return
    
    try:
        # Open PDF
        doc = fitz.open(pdf_path)
        page = doc[0]
        
        # Convert to image
        mat = fitz.Matrix(2.0, 2.0)  # 2x zoom
        pix = page.get_pixmap(matrix=mat)
        img_data = pix.tobytes("png")
        img = Image.open(io.BytesIO(img_data))
        
        width, height = img.size
        print(f"📄 PDF image size: {width}x{height}")
        
        # Save full page image
        img.save("debug_full_page.png")
        print("📄 Saved full page: debug_full_page.png")
        
        # Test multiple regions
        regions = [
            ("Top area (FCN region)", 0.16, 0.20, 0.01, 0.45),
            ("Bottom area (FIN region)", 0.85, 0.95, 0.01, 0.50),
            ("Middle area", 0.40, 0.60, 0.01, 0.50),
            ("Lower middle", 0.70, 0.85, 0.01, 0.50),
            ("Very bottom", 0.90, 1.0, 0.01, 0.50),
        ]
        
        for name, top_pct, bottom_pct, left_pct, right_pct in regions:
            top = int(height * top_pct)
            bottom = int(height * bottom_pct)
            left = int(width * left_pct)
            right = int(width * right_pct)
            
            print(f"\n🔍 Testing {name}:")
            print(f"   Coordinates: left={left}, top={top}, right={right}, bottom={bottom}")
            
            # Crop region
            region = img.crop((left, top, right, bottom))
            filename = f"debug_region_{name.lower().replace(' ', '_')}.png"
            region.save(filename)
            print(f"   Saved: {filename}")
            
            # Test OCR on this region
            try:
                import pytesseract
                pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'
                
                text = pytesseract.image_to_string(region, config='--oem 3 --psm 6')
                print(f"   OCR result: '{text.strip()}'")
                
                # Look for numbers
                import re
                numbers = re.findall(r'\d{12,15}', text)
                if numbers:
                    print(f"   Found numbers: {numbers}")
                else:
                    print("   No 12-15 digit numbers found")
                    
            except Exception as e:
                print(f"   OCR error: {e}")
        
        doc.close()
        
    except Exception as e:
        print(f"❌ Error processing PDF: {e}")

if __name__ == "__main__":
    # You'll need to provide the path to your PDF
    pdf_path = input("Enter path to your PDF file: ").strip()
    if pdf_path:
        debug_pdf_regions(pdf_path)
    else:
        print("No PDF path provided")