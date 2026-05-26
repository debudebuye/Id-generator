"""
Test Amharic OCR extraction to verify language data is working
"""
import cv2
import numpy as np
import pytesseract
import platform

# Configure Tesseract path for Windows
if platform.system() == 'Windows':
    pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'

def test_amharic_languages():
    """Check if Amharic language is available"""
    print("=" * 60)
    print("TESSERACT LANGUAGE CHECK")
    print("=" * 60)
    
    try:
        # Get Tesseract version
        version = pytesseract.get_tesseract_version()
        print(f"✓ Tesseract version: {version}")
        
        # Get available languages
        langs = pytesseract.get_languages(config='')
        print(f"\n✓ Available languages ({len(langs)}):")
        for lang in sorted(langs):
            marker = "✅" if lang in ['amh', 'eng'] else "  "
            print(f"  {marker} {lang}")
        
        print("\n" + "=" * 60)
        if 'amh' in langs:
            print("✅ Amharic (amh) is INSTALLED")
        else:
            print("❌ Amharic (amh) is NOT INSTALLED")
            print("\nPlease install Amharic language data:")
            print("1. Download: https://github.com/tesseract-ocr/tessdata/raw/main/amh.traineddata")
            print("2. Copy to: C:\\Program Files\\Tesseract-OCR\\tessdata\\")
            return False
        
        if 'eng' in langs:
            print("✅ English (eng) is INSTALLED")
        else:
            print("❌ English (eng) is NOT INSTALLED")
        
        print("=" * 60)
        return True
        
    except Exception as e:
        print(f"❌ Error checking Tesseract: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_front_card_extraction():
    """Test extraction from the actual front card image"""
    print("\n" + "=" * 60)
    print("TESTING FRONT CARD EXTRACTION")
    print("=" * 60)
    
    # Check if front card image exists
    import os
    front_image_path = "app/static/front_cropped.png"
    
    if not os.path.exists(front_image_path):
        print(f"❌ Front card image not found: {front_image_path}")
        print("   Please upload a front card image first")
        return
    
    print(f"✓ Found front card image: {front_image_path}")
    
    # Read image
    img = cv2.imread(front_image_path)
    if img is None:
        print(f"❌ Could not read image")
        return
    
    height, width = img.shape[:2]
    print(f"📐 Image dimensions: {width}x{height}")
    
    # Extract name region (56-66% of height)
    name_y1 = int(height * 0.56)
    name_y2 = int(height * 0.66)
    name_x1 = int(width * 0.05)
    name_x2 = int(width * 0.95)
    
    name_region = img[name_y1:name_y2, name_x1:name_x2]
    
    print(f"\n📝 Extracting name region: Y({name_y1}-{name_y2}), X({name_x1}-{name_x2})")
    
    # Convert to grayscale and preprocess
    gray = cv2.cvtColor(name_region, cv2.COLOR_BGR2GRAY)
    
    # Resize for better OCR
    scale = 3.0
    gray = cv2.resize(gray, None, fx=scale, fy=scale, interpolation=cv2.INTER_CUBIC)
    
    # Apply preprocessing
    bilateral = cv2.bilateralFilter(gray, 9, 75, 75)
    _, thresh = cv2.threshold(bilateral, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    
    # Save preprocessed image for inspection
    cv2.imwrite("test_name_region_preprocessed.png", thresh)
    print(f"✓ Saved preprocessed image: test_name_region_preprocessed.png")
    
    # Test 1: English only
    print("\n" + "-" * 60)
    print("TEST 1: English only (lang='eng')")
    print("-" * 60)
    text_eng = pytesseract.image_to_string(thresh, lang='eng', config='--oem 3 --psm 6')
    print(f"Result:\n{text_eng}")
    
    # Test 2: Amharic only
    print("\n" + "-" * 60)
    print("TEST 2: Amharic only (lang='amh')")
    print("-" * 60)
    text_amh = pytesseract.image_to_string(thresh, lang='amh', config='--oem 3 --psm 6')
    print(f"Result:\n{text_amh}")
    
    # Test 3: Both languages
    print("\n" + "-" * 60)
    print("TEST 3: Both languages (lang='eng+amh')")
    print("-" * 60)
    text_both = pytesseract.image_to_string(thresh, lang='eng+amh', config='--oem 3 --psm 6')
    print(f"Result:\n{text_both}")
    
    # Test 4: Amharic first
    print("\n" + "-" * 60)
    print("TEST 4: Amharic first (lang='amh+eng')")
    print("-" * 60)
    text_amh_first = pytesseract.image_to_string(thresh, lang='amh+eng', config='--oem 3 --psm 6')
    print(f"Result:\n{text_amh_first}")
    
    # Analyze results
    print("\n" + "=" * 60)
    print("ANALYSIS")
    print("=" * 60)
    
    # Check if Amharic characters are present
    has_amharic_test2 = any('\u1200' <= c <= '\u137F' for c in text_amh)
    has_amharic_test3 = any('\u1200' <= c <= '\u137F' for c in text_both)
    has_amharic_test4 = any('\u1200' <= c <= '\u137F' for c in text_amh_first)
    
    print(f"Test 2 (amh only): {'✅ Has Amharic characters' if has_amharic_test2 else '❌ No Amharic characters'}")
    print(f"Test 3 (eng+amh): {'✅ Has Amharic characters' if has_amharic_test3 else '❌ No Amharic characters'}")
    print(f"Test 4 (amh+eng): {'✅ Has Amharic characters' if has_amharic_test4 else '❌ No Amharic characters'}")
    
    if has_amharic_test2 or has_amharic_test3 or has_amharic_test4:
        print("\n✅ Amharic OCR is WORKING!")
        print("   The OCR service should be updated to use the correct language configuration.")
    else:
        print("\n❌ Amharic OCR is NOT WORKING")
        print("   Possible issues:")
        print("   1. Amharic language data not properly installed")
        print("   2. Tesseract needs to be restarted")
        print("   3. Image quality is too poor for Amharic recognition")
    
    print("=" * 60)

if __name__ == "__main__":
    # Step 1: Check if Amharic is installed
    if test_amharic_languages():
        # Step 2: Test extraction from actual front card
        test_front_card_extraction()
    else:
        print("\n⚠️ Please install Amharic language data first")
