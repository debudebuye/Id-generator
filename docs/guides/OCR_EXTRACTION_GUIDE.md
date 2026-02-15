# OCR Data Extraction System - Complete Guide

## 🎯 Overview

The system has been updated to extract data directly from ID card images using OCR (Optical Character Recognition). No PDF or document upload is required anymore.

## 📋 What Was Implemented

### 1. **OCR Extraction Service** (`app/services/ocr_extraction_service.py`)
Complete OCR service that:
- ✅ Extracts profile photo from front ID card
- ✅ Extracts text from front ID (Name, FIN, DOB, Sex, Expiry)
- ✅ Extracts text from back ID (Phone, Nationality, Address)
- ✅ Parses and structures the extracted data
- ✅ Combines all data for preview

### 2. **Updated Routes** (`app/routes.py`)
- ✅ Removed PDF/DOC upload requirement
- ✅ Added OCR extraction in `generate_id()` function
- ✅ Processes front and back ID images
- ✅ Redirects to preview page with extracted data

### 3. **Error Handling** (`app/templates/error.html`)
- ✅ User-friendly error page
- ✅ Clear error messages
- ✅ Back to home button

## 🔄 New Workflow

```
1. User uploads 3 images:
   - Profile Photo (optional)
   - Front ID Image (required)
   - Back ID Image (required)

2. User crops images if needed

3. User clicks "Generate Digital ID"

4. System performs OCR extraction:
   - Extracts photo from front ID
   - Extracts text from both images
   - Parses data (FIN, Name, Address, etc.)

5. System shows preview page with:
   - Extracted photo
   - All extracted data fields
   - Edit options

6. User confirms and generates final ID
```

## 📊 Data Extracted

### From Front ID:
- ✅ Full Name (English & Amharic)
- ✅ FIN Number (format: 6915 7029 3596)
- ✅ Date of Birth
- ✅ Sex (Male/Female)
- ✅ Date of Expiry
- ✅ Profile Photo

### From Back ID:
- ✅ Phone Number
- ✅ Nationality (English & Amharic)
- ✅ Address (Region, Subcity, Woreda)

## 🚀 How to Use

### Step 1: Install Required Dependencies

```bash
pip install pytesseract opencv-python pillow
```

### Step 2: Install Tesseract OCR

**Windows:**
```bash
# Download from: https://github.com/UB-Mannheim/tesseract/wiki
# Install to: C:\Program Files\Tesseract-OCR\
```

**Mac:**
```bash
brew install tesseract
brew install tesseract-lang  # For Amharic support
```

**Linux:**
```bash
sudo apt-get install tesseract-ocr
sudo apt-get install tesseract-ocr-amh  # Amharic language pack
```

### Step 3: Configure Tesseract Path

The path is already configured in `app/__init__.py`:
```python
pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'
```

### Step 4: Test the System

1. Start Flask app:
```bash
python app.py
```

2. Open browser: `http://localhost:7003`

3. Upload ID card images:
   - Front ID image
   - Back ID image
   - Profile photo (optional)

4. Click "Generate Digital ID"

5. Check console for OCR extraction logs

6. View extracted data in preview page

## 🧪 Testing

### Test with Sample Images

Use the provided sample images:
- Front ID: Shows name, FIN, DOB, sex, expiry
- Back ID: Shows phone, nationality, address

### Expected Console Output:

```
✓ Processed uploaded images: {'photo': 'path/to/photo.png', 'front': 'path/to/front.png', 'back': 'path/to/back.png'}
🔍 Starting OCR extraction from ID card images...
✓ OCR Extraction complete
  - Photo: app/static/extracted_photo.png
  - Front data: {'full_name_en': 'ABDULKERIM MOHAMMED GOBANA', 'fin': '691570293596', ...}
  - Back data: {'phone_number': '0919264253', 'nationality_en': 'Ethiopian', ...}
✓ Data stored in session, redirecting to preview
```

## 🔧 Configuration

### Adjust Photo Extraction Region

In `ocr_extraction_service.py`, modify coordinates:

```python
def extract_photo_from_front(self, image_path: str, output_path: str):
    # Adjust these percentages based on your ID card layout
    photo_x = int(width * 0.15)  # 15% from left
    photo_y = int(height * 0.15)  # 15% from top
    photo_w = int(width * 0.35)   # 35% width
    photo_h = int(height * 0.45)  # 45% height
```

### Improve OCR Accuracy

```python
# In ocr_extraction_service.py
self.tesseract_config = '--oem 3 --psm 6'  # Change PSM mode

# PSM modes:
# 3 = Fully automatic page segmentation
# 6 = Uniform block of text
# 11 = Sparse text
```

### Add More Data Fields

```python
# In parse_front_card_data() or parse_back_card_data()
# Add new regex patterns:

# Example: Extract email
email_match = re.search(r'[\w\.-]+@[\w\.-]+\.\w+', line)
if email_match:
    data['email'] = email_match.group(0)
```

## 🐛 Troubleshooting

### Issue 1: Tesseract Not Found

**Error:** `TesseractNotFoundError`

**Solution:**
```python
# Check Tesseract installation
import pytesseract
print(pytesseract.get_tesseract_version())

# Update path in app/__init__.py
pytesseract.pytesseract.tesseract_cmd = r'YOUR_PATH_HERE'
```

### Issue 2: Poor OCR Accuracy

**Problem:** Extracted text is incorrect or missing

**Solutions:**
1. **Improve image quality:**
```python
# In preprocess_image()
# Increase contrast
clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8,8))
enhanced = clahe.apply(gray)
```

2. **Try different PSM modes:**
```python
self.tesseract_config = '--oem 3 --psm 11'  # For sparse text
```

3. **Resize image:**
```python
# Before OCR
img = cv2.resize(img, None, fx=2, fy=2, interpolation=cv2.INTER_CUBIC)
```

### Issue 3: Amharic Text Not Recognized

**Problem:** Amharic characters show as garbage

**Solution:**
```bash
# Install Amharic language pack
# Windows: Download from Tesseract GitHub
# Linux: sudo apt-get install tesseract-ocr-amh
# Mac: brew install tesseract-lang

# Verify installation
tesseract --list-langs
# Should show: amh
```

### Issue 4: Photo Not Extracted

**Problem:** Photo extraction returns None

**Solution:**
```python
# Adjust coordinates in extract_photo_from_front()
# Print debug info:
print(f"Image size: {width}x{height}")
print(f"Photo region: x={photo_x}, y={photo_y}, w={photo_w}, h={photo_h}")

# Save debug image
cv2.rectangle(img, (photo_x, photo_y), (photo_x+photo_w, photo_y+photo_h), (0,255,0), 2)
cv2.imwrite('debug_photo_region.png', img)
```

## 📈 Performance Tips

### 1. Optimize Image Processing

```python
# Reduce image size before OCR
max_width = 1500
if img.shape[1] > max_width:
    scale = max_width / img.shape[1]
    img = cv2.resize(img, None, fx=scale, fy=scale)
```

### 2. Cache OCR Results

```python
# Add caching to avoid re-processing
import hashlib
import json

def get_cache_key(image_path):
    with open(image_path, 'rb') as f:
        return hashlib.md5(f.read()).hexdigest()

# Check cache before OCR
cache_key = get_cache_key(image_path)
if cache_key in cache:
    return cache[cache_key]
```

### 3. Parallel Processing

```python
# Process front and back simultaneously
from concurrent.futures import ThreadPoolExecutor

with ThreadPoolExecutor(max_workers=2) as executor:
    front_future = executor.submit(extract_text_from_image, front_path)
    back_future = executor.submit(extract_text_from_image, back_path)
    
    front_text = front_future.result()
    back_text = back_future.result()
```

## 🎓 Next Steps

### 1. Improve Data Validation

```python
def validate_fin(fin):
    """Validate FIN format"""
    if not re.match(r'^\d{12}$', fin):
        raise ValueError("Invalid FIN format")
    return True

def validate_phone(phone):
    """Validate Ethiopian phone number"""
    if not re.match(r'^09\d{8}$', phone):
        raise ValueError("Invalid phone number")
    return True
```

### 2. Add Confidence Scores

```python
# Get OCR confidence
data = pytesseract.image_to_data(img, output_type=pytesseract.Output.DICT)
confidences = [int(conf) for conf in data['conf'] if conf != '-1']
avg_confidence = sum(confidences) / len(confidences)

if avg_confidence < 60:
    print("⚠️ Low OCR confidence, manual review recommended")
```

### 3. Manual Correction Interface

Add edit fields in preview page for users to correct OCR errors.

### 4. Machine Learning Enhancement

Train a custom model for Ethiopian ID cards for better accuracy.

## 📞 Support

### Check Logs

```bash
# Flask console shows:
- Image upload status
- OCR extraction progress
- Extracted data
- Errors and warnings
```

### Debug Mode

```python
# Enable debug output in ocr_extraction_service.py
DEBUG = True

if DEBUG:
    print(f"Raw OCR text:\n{text}")
    print(f"Parsed data: {data}")
```

## ✅ Summary

You now have a complete OCR-based data extraction system that:

✅ Extracts data from ID card images
✅ No PDF/DOC upload required
✅ Automatic photo extraction
✅ Supports English and Amharic
✅ Shows preview before generating ID
✅ Handles errors gracefully

**Ready to use!** Just restart Flask and test with your ID card images.

---

**Created:** 2025
**Version:** 1.0.0
**Status:** ✅ Ready for Testing
