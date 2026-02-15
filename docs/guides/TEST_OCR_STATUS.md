# OCR Data Extraction - Troubleshooting Guide

## 🔍 Issue: No Data Showing in Preview Page

### Possible Causes:

1. **Tesseract OCR Not Installed**
   - OCR extraction fails silently
   - Data fields remain empty

2. **Images Not Being Saved**
   - Cropped images not saved to disk
   - OCR has no images to process

3. **Session Data Not Persisting**
   - Data extracted but not stored in session
   - Preview page receives empty data

## ✅ Quick Fixes Applied:

### 1. Added Fallback Mode
The system now works even if OCR fails:
- If OCR fails, shows empty fields for manual entry
- User can still fill in data manually
- No error, just empty preview page

### 2. Better Error Handling
```python
# Now catches OCR errors and continues
try:
    extraction_result = ocr_service.extract_all_data(...)
except Exception as ocr_error:
    print(f"⚠️ OCR extraction failed: {ocr_error}")
    # Continue with empty fields
```

### 3. Debug Output
Added console logging to see what's happening:
```
✓ Processed uploaded images: {...}
🔍 Starting OCR extraction...
✓ OCR Extraction complete
✓ Data stored in session
```

## 🧪 Testing Steps:

### Step 1: Check Console Output

After uploading images, check Flask console for:

```
✓ Processed uploaded images: {'photo': 'path/to/photo.png', 'front': 'path/to/front.png', 'back': 'path/to/back.png'}
```

If you see this, images are being saved ✅

### Step 2: Check OCR Attempt

Look for:
```
🔍 Starting OCR extraction from ID card images...
```

If you see this, OCR is being attempted ✅

### Step 3: Check OCR Result

Look for either:
```
✓ OCR Extraction complete
  - Photo: app/static/extracted_photo.png
  - Front data: {'full_name_en': 'ABDULKERIM...', ...}
  - Back data: {'phone_number': '0919264253', ...}
```

OR:
```
⚠️ OCR extraction failed: [error message]
   Continuing with manual data entry...
```

### Step 4: Check Preview Data

Look for:
```
PREVIEW PAGE - Data received:
Extracted data keys: ['fin', 'name_en', 'name_am', ...]
Extracted data: {...}
```

## 🔧 Solutions Based on Console Output:

### If You See: "Tesseract not found"

**Solution:** Install Tesseract OCR

**Windows:**
```bash
# Download from: https://github.com/UB-Mannheim/tesseract/wiki
# Install to: C:\Program Files\Tesseract-OCR\
# Make sure to select "Amharic" language pack during installation
```

**Verify:**
```bash
tesseract --version
tesseract --list-langs  # Should show: amh, eng
```

### If You See: "No module named 'pytesseract'"

**Solution:** Install Python packages
```bash
pip install pytesseract opencv-python
```

### If You See: "No module named 'cv2'"

**Solution:** Install OpenCV
```bash
pip install opencv-python
```

### If OCR Works But No Data Extracted

**Possible Issues:**
1. Image quality too low
2. Text not recognized
3. Regex patterns not matching

**Solution:** Manual entry is available
- Preview page shows empty fields
- User can type in all data manually
- Click "Generate ID" when done

## 📋 Current Workflow:

```
1. User uploads images
   ↓
2. Images saved to app/static/
   ↓
3. Try OCR extraction
   ├─ Success → Fill fields with extracted data
   └─ Fail → Show empty fields for manual entry
   ↓
4. Show preview page
   ↓
5. User can edit/fill any field
   ↓
6. Generate ID
```

## 🎯 What to Check Now:

### 1. Restart Flask
```bash
python app.py
```

### 2. Upload Images
- Upload front ID
- Upload back ID
- Upload photo (optional)

### 3. Watch Console
Look for the debug output mentioned above

### 4. Check Preview Page
- Does it load?
- Are fields empty or filled?
- Can you type in the fields?

### 5. Report What You See

**If preview page is empty:**
- Copy the console output
- Check if images are in `app/static/` folder
- Try typing in the fields manually

**If preview page has data:**
- OCR is working! ✅
- Check if data is correct
- Edit any incorrect fields
- Generate ID

## 💡 Manual Entry Mode:

Even if OCR doesn't work, you can still use the system:

1. Upload images (for the photo)
2. Preview page shows empty fields
3. Manually type in:
   - FIN number
   - Name (English & Amharic)
   - Date of birth
   - Sex
   - Phone number
   - Address
   - Etc.
4. Click "Generate ID"

The system will use your manually entered data!

## 🚀 Next Steps:

1. **Test with current setup:**
   - Restart Flask
   - Upload images
   - Check console output
   - Report what you see

2. **If OCR fails:**
   - Install Tesseract (see above)
   - Restart Flask
   - Try again

3. **If still no data:**
   - Use manual entry mode
   - Type in all fields
   - Generate ID

---

**Status:** System updated to work with or without OCR
**Mode:** Fallback to manual entry if OCR fails
**Action Required:** Test and report console output
