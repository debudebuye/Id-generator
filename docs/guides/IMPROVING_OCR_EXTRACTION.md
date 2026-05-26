# Improving OCR Extraction

## Current Issues

### 1. QR Code Extraction
- **Problem**: QR region too large, includes extra content
- **Solution**: 
  - Reduced region from 10-65% to 8-45% of height
  - Centered horizontally (25-75% instead of 10-90%)
  - Added OpenCV QR detector to automatically find QR code
  - Falls back to predefined region if detection fails

### 2. OCR Text Extraction
- **Problem**: Many fields are empty or contain garbage text
- **Causes**:
  - Image quality issues (blur, low resolution, poor lighting)
  - Text orientation (some text may be rotated)
  - Font rendering (Amharic characters may not be recognized well)
  - Region boundaries may not align with actual text

## Solutions Implemented

### QR Code Extraction Improvements

#### 1. OpenCV QR Detector
```python
qr_detector = cv2.QRCodeDetector()
data, bbox, straight_qrcode = qr_detector.detectAndDecode(img)
```
- Automatically detects QR code location
- Extracts exact bounding box
- Adds 10% padding for safety
- Falls back to predefined region if detection fails

#### 2. Smaller Predefined Region
- Old: Y(10-65%), X(10-90%)
- New: Y(8-45%), X(25-75%)
- More focused on actual QR code location

### OCR Extraction Improvements Needed

#### 1. Image Quality Enhancement
**Current**: Basic preprocessing (bilateral filter, CLAHE, denoise)
**Needed**:
- Deskewing (rotate to correct orientation)
- Super-resolution (upscale low-res images)
- Adaptive thresholding per region
- Noise reduction specific to ID cards

#### 2. Region Boundary Adjustment
**Current**: Fixed percentages for all cards
**Needed**:
- Detect text blocks automatically
- Adjust regions based on card layout detection
- Handle variations in card design

#### 3. Better Text Parsing
**Current**: Regex patterns for specific formats
**Needed**:
- More flexible date parsing
- Better name extraction (handle multi-line names)
- Improved bilingual text separation
- Context-aware field detection

## Debugging Tools

### 1. Region Visualizer
```bash
python debug_ocr_regions.py
```
- Shows extraction regions overlaid on card image
- Helps identify if regions are correctly positioned
- Saves visualization to `debug_front_regions.png` or `debug_back_regions.png`

### 2. OCR Test Script
```bash
python test_qr_extraction.py
```
- Tests QR code extraction
- Shows extracted QR image
- Attempts to decode QR data

### 3. Barcode Test Script
```bash
python test_barcode_generation.py
```
- Tests barcode generation from FAN
- Verifies different FAN formats (15, 16, 17+ digits)

## Recommendations for Better OCR Results

### 1. Image Upload Guidelines
**For Users**:
- Use high-resolution images (at least 1200x800 pixels)
- Ensure good lighting (no shadows or glare)
- Keep card flat (no warping or bending)
- Capture full card (no cropping)
- Use clear, focused images (no blur)

### 2. Preprocessing Improvements
**For Developers**:
```python
# Add deskewing
def deskew_image(image):
    coords = np.column_stack(np.where(image > 0))
    angle = cv2.minAreaRect(coords)[-1]
    if angle < -45:
        angle = -(90 + angle)
    else:
        angle = -angle
    (h, w) = image.shape[:2]
    center = (w // 2, h // 2)
    M = cv2.getRotationMatrix2D(center, angle, 1.0)
    rotated = cv2.warpAffine(image, M, (w, h), 
                             flags=cv2.INTER_CUBIC, 
                             borderMode=cv2.BORDER_REPLICATE)
    return rotated

# Add super-resolution
def upscale_image(image, scale=2):
    sr = cv2.dnn_superres.DnnSuperResImpl_create()
    sr.readModel("ESPCN_x2.pb")  # Download model first
    sr.setModel("espcn", scale)
    return sr.upsample(image)
```

### 3. Region Detection
**For Developers**:
```python
# Detect text blocks automatically
def detect_text_blocks(image):
    # Use EAST text detector or similar
    detector = cv2.dnn.readNet("frozen_east_text_detection.pb")
    # Process image and detect text regions
    # Return bounding boxes for each text block
    pass
```

### 4. Post-Processing
**For Developers**:
```python
# Clean extracted text
def clean_text(text):
    # Remove special characters
    text = re.sub(r'[^\w\s\u1200-\u137F/-]', '', text)
    # Remove extra whitespace
    text = ' '.join(text.split())
    # Fix common OCR errors
    text = text.replace('0', 'O').replace('1', 'I')  # Context-dependent
    return text
```

## Testing Checklist

### QR Code Extraction
- [ ] QR code is fully visible in extracted image
- [ ] No extra content beyond QR code
- [ ] QR code can be scanned with phone
- [ ] QR data is decoded correctly (if pyzbar installed)

### OCR Text Extraction
- [ ] Name extracted correctly (both Amharic and English)
- [ ] Date of birth extracted correctly
- [ ] Sex extracted correctly
- [ ] Date of expiry extracted correctly
- [ ] Date of issue extracted correctly
- [ ] FAN number extracted correctly (15-16 digits)
- [ ] Phone number extracted correctly (10 digits)
- [ ] FIN number extracted correctly (12 digits)
- [ ] Nationality extracted correctly (both languages)
- [ ] Address extracted correctly (region, subcity, woreda)

## Common OCR Errors and Fixes

### Error 1: Empty Fields
**Cause**: Region boundaries don't align with text
**Fix**: Use debug tool to visualize regions and adjust percentages

### Error 2: Garbage Text
**Cause**: Poor image quality or wrong preprocessing
**Fix**: Try different preprocessing methods, improve image quality

### Error 3: Wrong Language
**Cause**: Tesseract not configured for Amharic
**Fix**: Ensure `lang='eng+amh'` is used in pytesseract calls

### Error 4: Numbers Misread
**Cause**: Similar-looking characters (0/O, 1/I, 5/S)
**Fix**: Use character whitelist for number-only fields

### Error 5: Date Format Issues
**Cause**: Multiple date formats on card
**Fix**: Try multiple regex patterns, prioritize Gregorian format

## Performance Optimization

### Current Performance
- Front card OCR: ~2-3 seconds
- Back card OCR: ~2-3 seconds
- QR extraction: ~0.5 seconds
- Total: ~5-7 seconds per ID card

### Optimization Opportunities
1. **Parallel Processing**: Extract front and back simultaneously
2. **Caching**: Cache preprocessed images
3. **GPU Acceleration**: Use CUDA for OpenCV operations
4. **Model Optimization**: Use faster OCR models (e.g., EasyOCR)
5. **Region Prioritization**: Extract critical fields first

## Alternative OCR Engines

### 1. EasyOCR
```python
import easyocr
reader = easyocr.Reader(['en', 'am'])
result = reader.readtext(image)
```
- Better accuracy for Amharic
- Slower than Tesseract
- GPU acceleration available

### 2. PaddleOCR
```python
from paddleocr import PaddleOCR
ocr = PaddleOCR(lang='en')
result = ocr.ocr(image)
```
- Very fast
- Good accuracy
- Supports many languages

### 3. Google Cloud Vision API
```python
from google.cloud import vision
client = vision.ImageAnnotatorClient()
response = client.text_detection(image=image)
```
- Best accuracy
- Requires API key
- Costs money per request

## Next Steps

1. **Test with more samples**: Collect diverse ID card images
2. **Adjust regions**: Use debug tool to fine-tune region boundaries
3. **Improve preprocessing**: Add deskewing and super-resolution
4. **Add validation**: Verify extracted data format
5. **User feedback**: Allow users to correct OCR errors
6. **Machine learning**: Train custom model for Ethiopian ID cards
