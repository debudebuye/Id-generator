#!/usr/bin/env python3
"""
Quick test script to debug FIN extraction positioning.
Run this with your PDF to see what region is being cropped.
"""

import os
import sys
from io import BytesIO

def test_positioning():
    """Test the positioning logic with your PDF."""
    print("FIN Extraction Positioning Test")
    print("=" * 40)
    
    try:
        # Import required modules
        sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))
        import fitz  # PyMuPDF
        from PIL import Image
        
        # Get PDF path from user
        pdf_path = input("Enter the path to your PDF file: ").strip()
        
        if not pdf_path or not os.path.exists(pdf_path):
            print("❌ PDF file not found!")
            return False
        
        print(f"📄 Testing with: {pdf_path}")
        
        # Open PDF
        doc = fitz.open(pdf_path)
        page = doc[0]  # First page
        
        # Convert page to image with high resolution
        mat = fitz.Matrix(2.0, 2.0)  # 2x zoom for better OCR
        pix = page.get_pixmap(matrix=mat)
        
        # Convert to PIL Image
        img_data = pix.tobytes("png")
        img = Image.open(BytesIO(img_data))
        
        width, height = img.size
        print(f"📐 Image size: {width}x{height}")
        
        # Test different positioning strategies
        strategies = [
            ("Current", 0.82, 5, 60, 0.01, 0.40),
            ("Higher", 0.80, 10, 80, 0.02, 0.45),
            ("Lower", 0.85, 5, 60, 0.01, 0.40),
            ("Wider", 0.82, 5, 60, 0.00, 0.50),
            ("Narrower", 0.82, 5, 60, 0.05, 0.30),
        ]
        
        for strategy_name, qr_y, offset, region_height, left_pct, right_pct in strategies:
            print(f"\n🔍 Testing strategy: {strategy_name}")
            
            # Calculate position
            qr_bottom_y = int(height * qr_y)
            fin_region_top = qr_bottom_y + offset
            fin_region_bottom = fin_region_top + region_height
            fin_region_left = int(width * left_pct)
            fin_region_right = int(width * right_pct)
            
            print(f"   Region: left={fin_region_left}, top={fin_region_top}, right={fin_region_right}, bottom={fin_region_bottom}")
            
            # Crop the region
            fin_region = img.crop((fin_region_left, fin_region_top, fin_region_right, fin_region_bottom))
            
            # Save cropped region
            debug_path = f"debug_fin_region_{strategy_name.lower()}.png"
            fin_region.save(debug_path)
            print(f"   ✅ Saved: {debug_path}")
            
            # Try OCR on this region
            try:
                import pytesseract
                text = pytesseract.image_to_string(fin_region, config='--oem 3 --psm 8 -c tessedit_char_whitelist=0123456789')
                text = text.strip()
                print(f"   OCR Result: '{text}'")
                
                if "679571631281" in text:
                    print(f"   🎉 FOUND CORRECT FIN!")
                elif text:
                    print(f"   ⚠️  Found other text: {text}")
                else:
                    print(f"   ❌ No text detected")
                    
            except Exception as e:
                print(f"   ❌ OCR failed: {str(e)}")
        
        doc.close()
        
        print(f"\n📁 Check the debug images to see which region contains the correct FIN:")
        print(f"   Expected FIN: 679571631281")
        print(f"   Incorrectly extracted: 509624074926")
        
        return True
        
    except Exception as e:
        print(f"❌ Test failed: {str(e)}")
        return False

if __name__ == "__main__":
    test_positioning()








