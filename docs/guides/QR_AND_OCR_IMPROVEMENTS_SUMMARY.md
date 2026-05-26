# QR and OCR Improvements Summary

## Issues Addressed

### Issue 1: QR Code Region Too Large ✅
**Problem**: QR extraction included extra content beyond the QR code

**Solution**:
- Reduced extraction region from Y(10-65%) to Y(8-45%)
- Centered horizontally from X(10-90%) to X(25-75%)
- Added OpenCV QR detector to automatically find QR code
- Falls back to predefined region if auto-detection fails

### Issue 2: OCR Extraction Poor Quality ⚠️
**Problem**: Most fields are empty or contain garbage text

**Root Causes**:
1. Image quality issues (blur, low resolution, poor lighting)
2. Region boundaries may not align perfectly with text
3. Amharic text recognition challenges
4. Text preprocessing not optimal for all card variations

**Partial Solutions Implemented**:
- Multiple preprocessing methods (bilateral, CLAHE, denoise)
- Region-based extraction with fallback to full-page OCR
- Bilingual text detection and separation
- Multiple regex patterns for flexible date parsing

**Still Needs Work**:
- Image quality enhancement (deskewing, super-resolution)
- Automatic text block detection
- Better region boundary adjustment
- More robust text parsing

## Changes Made

### File: `app/services/ocr_extraction_service.py`

#### 1. Improved QR Code Extraction
```python
def extract_qr_code_region(self, image_path: str, output_path: str):
    # Try OpenCV QR detector first
    qr_detector = cv2.QRCodeDetector()
    data, bbox, straight_qrcode = qr_detector.detectAndDecode(img)
    
    if bbox is not None:
        # Use detected bounding box with padding
        # Extract exact QR region
    else:
        # Fallback to smaller predefined region
        # Y: 8-45%, X: 25-75%
```

**Benefits**:
- More accurate QR extraction
- Smaller extracted region
- Automatic detection when possible
- Graceful fallback

## Debugging Tools Created

### 1. `debug_ocr_regions.py`
**Purpose**: Visualize extraction regions on ID card images

**Usage**:
```bash
python debug_ocr_regions.py
# Enter card type: front or back
# Enter image path
# Output: debug_front_regions.png or debug_back_regions.png
```

**Features**:
- Shows colored rectangles for each extraction region
- Labels each region
- Prints region coordinates
- Tests OCR extraction and shows results

### 2. `IMPROVING_OCR_EXTRACTION.md`
**Purpose**: Comprehensive guide for improving OCR

**Contents**:
- Current issues and solutions
- Debugging tools
- Recommendations for better results
- Common errors and fixes
- Performance optimization tips
- Alternative OCR engines

## Testing Results

### QR Code Extraction
✅ Region size reduced significantly
✅ OpenCV detector added
✅ Fallback mechanism works
⚠️ Still may include some extra content depending on card layout

### OCR Text Extraction
✅ FAN number extracted: `8205810214625375`
✅ Address extracted: `Addis Ababa, Woreda 10`
✅ Region extracted: `Addis Ababa`
✅ Woreda extracted: `Woreda 10`
❌ Name extraction poor: `"ste ps Date of Beth |"` (garbage)
❌ Date of birth: Empty
❌ Sex: Empty
❌ Date of expiry: Empty
❌ Date of issue: Empty
❌ Phone number: Empty
❌ Nationality: Empty

**Success Rate**: ~30% (4 out of 13 fields)

## Recommendations

### For Immediate Improvement

1. **Use Debug Tool**:
   ```bash
   python debug_ocr_regions.py
   ```
   - Check if regions align with actual text
   - Adjust region percentages if needed

2. **Improve Image Quality**:
   - Use higher resolution images (1200x800 minimum)
   - Ensure good lighting
   - Keep card flat and in focus
   - Avoid shadows and glare

3. **Manual Entry**:
   - System is designed for hybrid workflow
   - Users can manually enter missing fields in preview page
   - Auto-save feature saves changes automatically

### For Long-Term Improvement

1. **Add Deskewing**: Rotate images to correct orientation
2. **Add Super-Resolution**: Upscale low-res images
3. **Train Custom Model**: Train on Ethiopian ID cards specifically
4. **Use Better OCR Engine**: Try EasyOCR or PaddleOCR
5. **Add Validation**: Verify extracted data format
6. **Collect Training Data**: Build dataset of ID card images

## Current System Status

### What Works Well ✅
- Image upload (drag-and-drop and click)
- Image cropping with Cropper.js
- QR code extraction (improved region)
- Barcode generation from FAN
- FAN number extraction (16 digits)
- Address extraction (partial)
- Preview page with manual entry
- Auto-save functionality

### What Needs Improvement ⚠️
- OCR accuracy for most text fields
- Name extraction (both languages)
- Date extraction (all date fields)
- Phone number extraction
- Nationality extraction
- Region boundary alignment

### Workaround 💡
The system is designed as a **hybrid workflow**:
1. OCR extracts what it can (FAN, address, etc.)
2. User manually enters missing fields in preview page
3. Auto-save keeps data updated
4. Generate ID card with complete data

This approach provides:
- Faster data entry (some fields auto-filled)
- Accuracy (user verifies and corrects)
- Flexibility (works even when OCR fails)

## Next Steps

1. **Test with your specific ID cards**:
   - Run debug tool to see region alignment
   - Adjust regions if needed
   - Test with multiple card samples

2. **Improve image quality**:
   - Use better camera or scanner
   - Ensure proper lighting
   - Keep card flat and focused

3. **Consider alternative OCR**:
   - Try EasyOCR for better Amharic support
   - Test PaddleOCR for faster processing
   - Evaluate Google Cloud Vision API for best accuracy

4. **Collect feedback**:
   - Track which fields fail most often
   - Identify common OCR errors
   - Adjust preprocessing accordingly
