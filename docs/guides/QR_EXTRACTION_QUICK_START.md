# QR Code Extraction - Quick Start Guide

## What's New?
The system now automatically extracts QR codes from the back ID card image and displays them in the preview page.

## How to Use

### 1. Upload Images
- Upload **Front ID card** image
- Upload **Back ID card** image  
- Upload **Profile photo**

### 2. Automatic Extraction
The system will automatically:
- Extract text data from both cards (OCR)
- **Extract QR code from back card** ✨ NEW
- Display all extracted data in preview page

### 3. Preview Page
You'll see:
- Profile photo
- **QR code** (extracted from back card) ✨ NEW
- All extracted text data (name, DOB, address, etc.)

### 4. QR Code Actions
In the preview page, you can:
- **View** the extracted QR code
- **Download** the QR code image
- **Upload** a different QR code if needed

## Technical Details

### QR Code Location
The QR code is extracted from the **top portion** of the back ID card (10-65% of image height).

### File Storage
- Extracted QR code is saved to: `app/static/qr_extracted.png`
- Automatically overwritten on each new extraction

### Optional: QR Decoding
To enable QR code data decoding (optional):
```bash
pip install pyzbar
```

This allows the system to read the data encoded in the QR code (useful for validation).

## Testing

### Quick Test
1. Run the Flask app: `python app.py`
2. Go to: `http://localhost:5000`
3. Upload front and back ID images
4. Check preview page for extracted QR code

### Test Script
```bash
python test_qr_extraction.py
```

## Troubleshooting

### QR Code Not Showing
- Check console logs for extraction errors
- Verify back card image is uploaded
- Ensure QR code is visible in back card image
- Check if `app/static/qr_extracted.png` exists

### QR Code Quality Issues
- Use high-resolution back card images
- Ensure QR code is not cropped or distorted
- Check lighting and contrast in original image

### pyzbar Warnings
- These are informational only
- QR extraction still works without pyzbar
- Install pyzbar to enable QR decoding

## Console Output

### Successful Extraction
```
🔍 Starting OCR extraction from ID card images...
📸 Using uploaded profile photo (not extracting from front ID)
📐 Image dimensions for QR extraction: 1200x800
✓ QR code region extracted and saved to: app/static/qr_extracted.png
✓ QR code extracted from back card: app/static/qr_extracted.png
✓ QR Code decoded: [QR data...]
✓ OCR Extraction complete
```

### Failed Extraction
```
📐 Image dimensions for QR extraction: 1200x800
❌ Error extracting QR code region: [error message]
⚠️ QR code extraction failed
```

## Next Steps

After QR extraction is working:
1. Test with multiple ID card samples
2. Verify QR code quality is acceptable
3. Consider implementing QR code validation
4. Add QR code generation as fallback

## Support

If you encounter issues:
1. Check console logs for error messages
2. Verify image file paths are correct
3. Ensure OpenCV and Tesseract are installed
4. Review `QR_EXTRACTION_IMPLEMENTATION.md` for details
