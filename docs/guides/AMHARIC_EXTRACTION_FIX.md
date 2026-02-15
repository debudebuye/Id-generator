# Amharic Text Extraction Fix

## Issue
Amharic text is not being extracted. Instead, it's being read as garbage characters:
- Expected: `ወንድዬ ገመዳ ተሰማ`
- Actual: `OVZR VDL th? :`

## Root Cause
**Tesseract OCR does not have Amharic language data installed**, or it's not configured correctly.

## Solution: Install Amharic Language Data

### Step 1: Check Current Installation

Run the diagnostic script:
```bash
python check_tesseract_languages.py
```

This will show:
- ✅ Which languages are installed
- ❌ If Amharic (amh) is missing
- 🧪 Test Amharic recognition

### Step 2: Download Amharic Language Data

**Option A: Download from GitHub (Recommended)**

1. Go to: https://github.com/tesseract-ocr/tessdata
2. Download file: `amh.traineddata`
3. Direct link: https://github.com/tesseract-ocr/tessdata/raw/main/amh.traineddata

**Option B: Download Best Quality (Larger file)**

1. Go to: https://github.com/tesseract-ocr/tessdata_best
2. Download file: `amh.traineddata`
3. Direct link: https://github.com/tesseract-ocr/tessdata_best/raw/main/amh.traineddata

**Option C: Download Fast Version (Smaller file)**

1. Go to: https://github.com/tesseract-ocr/tessdata_fast
2. Download file: `amh.traineddata`
3. Direct link: https://github.com/tesseract-ocr/tessdata_fast/raw/main/amh.traineddata

### Step 3: Install Language Data

1. **Locate Tesseract installation directory**:
   ```
   C:\Program Files\Tesseract-OCR\
   ```

2. **Navigate to tessdata folder**:
   ```
   C:\Program Files\Tesseract-OCR\tessdata\
   ```

3. **Copy `amh.traineddata` to tessdata folder**:
   ```
   C:\Program Files\Tesseract-OCR\tessdata\amh.traineddata
   ```

4. **Verify installation**:
   - Check that file exists in tessdata folder
   - File size should be ~1-5 MB depending on version

### Step 4: Verify Installation

Run the diagnostic script again:
```bash
python check_tesseract_languages.py
```

You should now see:
```
✅ Amharic (amh) is INSTALLED
✅ Amharic recognition is WORKING!
```

### Step 5: Test with Actual ID Card

Upload the front card image again and check console logs for:
```
✓ Extracted name (AM): ወንድዬ ገመዳ ተሰማ
✓ Extracted name (EN): Wondiye Gemeda Tesema
```

## Alternative Solutions

### Option 1: Use EasyOCR (Better Amharic Support)

EasyOCR has better support for Amharic text:

```bash
pip install easyocr
```

```python
import easyocr

# Initialize reader
reader = easyocr.Reader(['en', 'am'])  # English and Amharic

# Read text
result = reader.readtext(image)

# Extract text
for (bbox, text, prob) in result:
    print(f"Text: {text}, Confidence: {prob}")
```

**Pros**:
- Better Amharic recognition
- No language data installation needed
- GPU acceleration support

**Cons**:
- Slower than Tesseract
- Larger download (~500MB on first run)
- Requires more memory

### Option 2: Use PaddleOCR

PaddleOCR is fast and supports multiple languages:

```bash
pip install paddleocr
```

```python
from paddleocr import PaddleOCR

# Initialize OCR
ocr = PaddleOCR(lang='en')  # English only, but fast

# Read text
result = ocr.ocr(image)

# Extract text
for line in result:
    for word_info in line:
        text = word_info[1][0]
        confidence = word_info[1][1]
        print(f"Text: {text}, Confidence: {confidence}")
```

**Pros**:
- Very fast
- Good accuracy
- Lightweight

**Cons**:
- Limited Amharic support
- May need custom training for Amharic

### Option 3: Use Google Cloud Vision API

Best accuracy but requires API key and costs money:

```bash
pip install google-cloud-vision
```

```python
from google.cloud import vision

# Initialize client
client = vision.ImageAnnotatorClient()

# Read image
with open(image_path, 'rb') as image_file:
    content = image_file.read()

image = vision.Image(content=content)

# Detect text
response = client.text_detection(image=image)
texts = response.text_annotations

# Extract text
if texts:
    print(f"Text: {texts[0].description}")
```

**Pros**:
- Best accuracy
- Supports many languages including Amharic
- No installation needed

**Cons**:
- Requires API key
- Costs money per request
- Requires internet connection

## Troubleshooting

### Issue 1: Amharic Still Not Working After Installation

**Check 1: Verify file location**
```bash
dir "C:\Program Files\Tesseract-OCR\tessdata\amh.traineddata"
```

**Check 2: Verify Tesseract can see it**
```bash
tesseract --list-langs
```

Should show:
```
List of available languages (2):
amh
eng
```

**Check 3: Test with simple command**
```bash
tesseract test_image.png output -l amh
```

### Issue 2: Permission Denied

If you can't copy to `C:\Program Files\`, you need administrator privileges:

1. Right-click on File Explorer
2. Select "Run as administrator"
3. Navigate to tessdata folder
4. Copy amh.traineddata

### Issue 3: Wrong Tesseract Installation

If Tesseract is installed in a different location:

1. Find Tesseract location:
   ```python
   import pytesseract
   print(pytesseract.pytesseract.tesseract_cmd)
   ```

2. Navigate to that directory
3. Find tessdata folder
4. Copy amh.traineddata there

### Issue 4: Multiple Tesseract Installations

If you have multiple Tesseract installations:

1. Check which one is being used:
   ```bash
   where tesseract
   ```

2. Make sure amh.traineddata is in the correct one

3. Or specify Tesseract path in code:
   ```python
   pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'
   ```

## Expected Results After Fix

### Before Fix:
```
✓ full_name: OVZR VDL th? :Wondiye Gemeda Tesema
✓ Extracted name (EN): Wondiye Gemeda Tesema
✗ Extracted name (AM): (empty)
```

### After Fix:
```
✓ full_name: ወንድዬ ገመዳ ተሰማ Wondiye Gemeda Tesema
✓ Extracted name (AM): ወንድዬ ገመዳ ተሰማ
✓ Extracted name (EN): Wondiye Gemeda Tesema
```

## Testing Checklist

- [ ] Run `python check_tesseract_languages.py`
- [ ] Verify Amharic (amh) is listed
- [ ] Test Amharic recognition with test image
- [ ] Upload front card image
- [ ] Check console logs for Amharic name extraction
- [ ] Verify preview page shows Amharic name
- [ ] Test with back card for Amharic address/nationality

## Additional Resources

### Tesseract Language Data Repositories:
- **Standard**: https://github.com/tesseract-ocr/tessdata
- **Best Quality**: https://github.com/tesseract-ocr/tessdata_best
- **Fast**: https://github.com/tesseract-ocr/tessdata_fast

### Tesseract Documentation:
- **Installation**: https://tesseract-ocr.github.io/tessdoc/Installation.html
- **Language Data**: https://tesseract-ocr.github.io/tessdoc/Data-Files.html
- **Improving Quality**: https://tesseract-ocr.github.io/tessdoc/ImproveQuality.html

### Alternative OCR Engines:
- **EasyOCR**: https://github.com/JaidedAI/EasyOCR
- **PaddleOCR**: https://github.com/PaddlePaddle/PaddleOCR
- **Google Cloud Vision**: https://cloud.google.com/vision/docs/ocr

## Summary

The Amharic extraction issue is caused by **missing Amharic language data in Tesseract**. 

**Quick Fix**:
1. Download `amh.traineddata` from GitHub
2. Copy to `C:\Program Files\Tesseract-OCR\tessdata\`
3. Restart application
4. Test extraction

**Alternative**: Use EasyOCR for better Amharic support without language data installation.

Once Amharic language data is installed, the system should extract Amharic text correctly!
