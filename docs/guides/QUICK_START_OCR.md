# Quick Start - OCR Data Extraction

## ✅ What Was Done

1. ✅ Created OCR extraction service (`app/services/ocr_extraction_service.py`)
2. ✅ Updated routes to use OCR instead of PDF (`app/routes.py`)
3. ✅ Removed FIN and document upload from index page
4. ✅ Added drag-and-drop for all image uploads
5. ✅ Created error handling template

## 🚀 Quick Setup (3 Steps)

### Step 1: Install Tesseract OCR

**Windows:**
1. Download: https://github.com/UB-Mannheim/tesseract/wiki
2. Install to: `C:\Program Files\Tesseract-OCR\`
3. During installation, select "Additional language data" and check "Amharic"

**Verify installation:**
```bash
tesseract --version
tesseract --list-langs  # Should show: amh, eng
```

### Step 2: Install Python Dependencies

```bash
pip install pytesseract opencv-python
```

### Step 3: Restart Flask

```bash
python app.py
```

## 🧪 Test It

1. Open: http://localhost:7003
2. Upload your ID card images:
   - Front ID (required)
   - Back ID (required)
   - Profile photo (optional)
3. Click "Generate Digital ID"
4. Check console for extraction logs
5. View extracted data in preview page

## 📊 Expected Output

### Console:
```
✓ Processed uploaded images: {...}
🔍 Starting OCR extraction from ID card images...
✓ OCR Extraction complete
  - Photo: app/static/extracted_photo.png
  - Front data: {'full_name_en': 'ABDULKERIM MOHAMMED GOBANA', ...}
  - Back data: {'phone_number': '0919264253', ...}
✓ Data stored in session, redirecting to preview
```

### Preview Page Will Show:
- ✅ Extracted photo
- ✅ Full name (English & Amharic)
- ✅ FIN number
- ✅ Date of birth
- ✅ Sex
- ✅ Phone number
- ✅ Nationality
- ✅ Address
- ✅ Date of expiry

## 🐛 Troubleshooting

### Tesseract Not Found?
```python
# Check path in app/__init__.py (line ~30)
pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'
```

### Poor OCR Accuracy?
- Use high-quality images (300+ DPI)
- Ensure good lighting
- Avoid shadows and glare
- Keep text horizontal

### Amharic Not Working?
```bash
# Verify Amharic is installed
tesseract --list-langs

# Should show: amh
# If not, reinstall Tesseract with language packs
```

## 📁 Files Created/Modified

```
✅ app/services/ocr_extraction_service.py  (NEW)
✅ app/routes.py                           (MODIFIED)
✅ app/templates/index.html                (MODIFIED)
✅ app/templates/error.html                (NEW)
✅ app/routes_ocr.py                       (NEW - reference)
✅ OCR_EXTRACTION_GUIDE.md                 (NEW - docs)
✅ QUICK_START_OCR.md                      (NEW - this file)
```

## 🎯 What Changed

### Before:
- Upload PDF/DOC document
- Enter FIN manually
- Extract data from PDF

### After:
- Upload ID card images (front & back)
- OCR extracts all data automatically
- No manual FIN entry needed
- Photo extracted from front ID

## ✨ Ready!

Your system is now ready to extract data from ID card images using OCR. Just restart Flask and test it!

```bash
python app.py
```

Then open http://localhost:7003 and upload your ID card images!
