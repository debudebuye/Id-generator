"""
Check Tesseract OCR language support
"""
import pytesseract
import subprocess
import os

# Set Tesseract path for Windows
pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'

def check_tesseract_languages():
    """Check which languages are installed in Tesseract"""
    print("=" * 60)
    print("Tesseract Language Support Check")
    print("=" * 60)
    
    try:
        # Get Tesseract version
        version = pytesseract.get_tesseract_version()
        print(f"✓ Tesseract version: {version}")
        
        # Get list of available languages
        langs = pytesseract.get_languages(config='')
        print(f"\n✓ Available languages ({len(langs)}):")
        for lang in sorted(langs):
            print(f"  - {lang}")
        
        # Check for Amharic
        print("\n" + "=" * 60)
        if 'amh' in langs:
            print("✅ Amharic (amh) is INSTALLED")
        else:
            print("❌ Amharic (amh) is NOT INSTALLED")
            print("\nTo install Amharic language data:")
            print("1. Download from: https://github.com/tesseract-ocr/tessdata")
            print("2. Download file: amh.traineddata")
            print("3. Copy to: C:\\Program Files\\Tesseract-OCR\\tessdata\\")
            print("   (or your Tesseract installation directory)")
        
        # Check for English
        if 'eng' in langs:
            print("✅ English (eng) is INSTALLED")
        else:
            print("❌ English (eng) is NOT INSTALLED")
        
        print("=" * 60)
        
        # Test Amharic recognition
        if 'amh' in langs:
            print("\n🧪 Testing Amharic Recognition...")
            test_amharic_recognition()
        
    except Exception as e:
        print(f"❌ Error checking Tesseract: {e}")
        import traceback
        traceback.print_exc()

def test_amharic_recognition():
    """Test if Amharic recognition actually works"""
    try:
        import cv2
        import numpy as np
        from PIL import Image, ImageDraw, ImageFont
        
        # Create a test image with Amharic text
        print("Creating test image with Amharic text...")
        
        # Create white background
        img = np.ones((100, 400, 3), dtype=np.uint8) * 255
        
        # Add text using PIL (OpenCV doesn't support Amharic)
        pil_img = Image.fromarray(img)
        draw = ImageDraw.Draw(pil_img)
        
        # Try to use a font that supports Amharic
        try:
            # Try to find Amharic font
            font_paths = [
                "C:\\Windows\\Fonts\\ebrima.ttf",  # Ebrima supports Ethiopic
                "C:\\Windows\\Fonts\\nyala.ttf",   # Nyala is Ethiopic font
                "fonts/AbyssinicaSIL-Regular.ttf", # If you have it
            ]
            
            font = None
            for font_path in font_paths:
                if os.path.exists(font_path):
                    font = ImageFont.truetype(font_path, 40)
                    print(f"✓ Using font: {font_path}")
                    break
            
            if font is None:
                print("⚠️ No Amharic font found, using default")
                font = ImageFont.load_default()
            
            # Draw Amharic text
            amharic_text = "ወንድዬ ገመዳ ተሰማ"
            draw.text((10, 30), amharic_text, fill=(0, 0, 0), font=font)
            
            # Convert back to numpy array
            img = np.array(pil_img)
            
            # Save test image
            cv2.imwrite("test_amharic.png", img)
            print("✓ Test image saved: test_amharic.png")
            
            # Try to recognize it
            text = pytesseract.image_to_string(img, lang='amh', config='--oem 3 --psm 7')
            print(f"\n📝 OCR Result: '{text.strip()}'")
            
            if 'ወንድዬ' in text or 'ገመዳ' in text or 'ተሰማ' in text:
                print("✅ Amharic recognition is WORKING!")
            else:
                print("⚠️ Amharic recognition may not be working correctly")
                print("   Expected: ወንድዬ ገመዳ ተሰማ")
                print(f"   Got: {text.strip()}")
            
        except Exception as e:
            print(f"⚠️ Could not test Amharic recognition: {e}")
    
    except ImportError as e:
        print(f"⚠️ Missing required library: {e}")

if __name__ == "__main__":
    check_tesseract_languages()
