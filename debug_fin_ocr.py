#!/usr/bin/env python3
"""
Debug script to test FIN OCR extraction
"""

import sys
import os
sys.path.append('.')

from app.services.id_card_service import IDCardService
import fitz
from PIL import Image
import io

def test_fin_extraction():
    print("🔍 Testing FIN OCR extraction...")
    
    # Test if Tesseract is working
    try:
        import pytesseract
        pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'
        version = pytesseract.get_tesseract_version()
        print(f"✅ Tesseract version: {version}")
    except Exception as e:
        print(f"❌ Tesseract error: {e}")
        return
    
    # Create a test image with FIN number
    img = Image.new('RGB', (400, 100), color='white')
    from PIL import ImageDraw, ImageFont
    draw = ImageDraw.Draw(img)
    
    try:
        # Try to use a font
        font = ImageFont.truetype("arial.ttf", 20)
    except:
        font = ImageFont.load_default()
    
    # Draw test FIN
    test_fin = "632430253608"
    draw.text((10, 30), f"FIN: {test_fin}", fill='black', font=font)
    
    # Save test image
    img.save("test_fin_image.png")
    print("📄 Created test image: test_fin_image.png")
    
    # Test OCR on this image
    try:
        text = pytesseract.image_to_string(img, config='--oem 3 --psm 8 -c tessedit_char_whitelist=0123456789')
        print(f"🔍 OCR result (numbers only): '{text.strip()}'")
        
        text_all = pytesseract.image_to_string(img, config='--oem 3 --psm 6')
        print(f"🔍 OCR result (all chars): '{text_all.strip()}'")
        
        if test_fin in text_all:
            print("✅ OCR can read the FIN correctly!")
        else:
            print("⚠️ OCR cannot read the FIN correctly")
            
    except Exception as e:
        print(f"❌ OCR test failed: {e}")

if __name__ == "__main__":
    test_fin_extraction()