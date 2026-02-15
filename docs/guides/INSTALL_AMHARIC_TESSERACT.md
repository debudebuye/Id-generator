# Installing Amharic Language Data for Tesseract OCR

## Current Status
❌ **Amharic language data is NOT installed** (verified by diagnostic script)

Your Tesseract installation only has:
- ✅ English (eng)
- ⚠️ OSD (Orientation and Script Detection)

## Why Amharic Extraction Fails
Without Amharic language data, Tesseract cannot recognize Amharic characters (ወንድዬ ገመዳ ተሰማ) and instead outputs garbage text like "OVZR VDL th? :".

## Installation Steps

### Option 1: Automatic Installation (Recommended)
Run the installation script:
```bash
python install_amharic_tesseract.py
```

This script will:
1. Download the Amharic language data file
2. Copy it to the correct Tesseract directory
3. Verify the installation

### Option 2: Manual Installation

#### Step 1: Download Amharic Language Data
Download the file from GitHub:
- **URL**: https://github.com/tesseract-ocr/tessdata/raw/main/amh.traineddata
- **File name**: `amh.traineddata`
- **File size**: ~1.2 MB

#### Step 2: Locate Tesseract Installation Directory
Your Tesseract is installed at:
```
C:\Program Files\Tesseract-OCR\
```

The language data folder is:
```
C:\Program Files\Tesseract-OCR\tessdata\
```

#### Step 3: Copy the File
1. Copy the downloaded `amh.traineddata` file
2. Paste it into: `C:\Program Files\Tesseract-OCR\tessdata\`
3. You may need Administrator privileges

**Important**: Make sure the file is named exactly `amh.traineddata` (not `amh.traineddata.txt` or anything else)

#### Step 4: Verify Installation
Run the verification script:
```bash
python test_amharic_ocr.py
```

You should see:
```
✅ Amharic (amh) is INSTALLED
```

#### Step 5: Restart Flask App
After installing the language data, **restart your Flask application**:
1. Press `CTRL+C` to stop the Flask server
2. Run `python app.py` again

## Verification

After installation, run the diagnostic:
```bash
python test_amharic_ocr.py
```

Expected output:
```
============================================================
TESSERACT LANGUAGE CHECK
============================================================
✓ Tesseract version: 5.5.0.20241111

✓ Available languages (3):
  ✅ amh
  ✅ eng
     osd

============================================================
✅ Amharic (amh) is INSTALLED
✅ English (eng) is INSTALLED
============================================================
```

## Troubleshooting

### Issue: "Access Denied" when copying file
**Solution**: Run Command Prompt or PowerShell as Administrator

### Issue: File copied but still not detected
**Solution**: 
1. Check the file name is exactly `amh.traineddata`
2. Check the file is in the correct folder: `C:\Program Files\Tesseract-OCR\tessdata\`
3. Restart your Flask application
4. Run the diagnostic script again

### Issue: Amharic still shows as garbage after installation
**Solution**:
1. Verify installation with `python test_amharic_ocr.py`
2. Make sure you restarted the Flask app
3. Check the console logs for "✓ Extracted name (AM):" - it should show Amharic text, not garbage

## Expected Results After Installation

### Before (without Amharic):
```
✓ full_name: OVZR VDL th? :Wondiye Gemeda Tesema
✓ Extracted name (EN): OVZR VDL th? :
✓ Extracted name (EN): Wondiye Gemeda Tesema
```

### After (with Amharic):
```
✓ full_name: ወንድዬ ገመዳ ተሰማ | Wondiye Gemeda Tesema
✓ Extracted name (AM): ወንድዬ ገመዳ ተሰማ
✓ Extracted name (EN): Wondiye Gemeda Tesema
```

## Alternative: Use EasyOCR (Future Enhancement)

If Tesseract Amharic continues to have issues, we can switch to EasyOCR which has better Amharic support:

```bash
pip install easyocr
```

EasyOCR supports Amharic out of the box without additional language files.

## Need Help?

If you continue to have issues:
1. Run `python test_amharic_ocr.py` and share the output
2. Check if the file exists: `dir "C:\Program Files\Tesseract-OCR\tessdata\amh.traineddata"`
3. Verify file size is around 1.2 MB (not 0 bytes)
