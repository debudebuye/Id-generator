# Image-Based FIN Extraction for ~1.8-1.9 MB PDFs

This document explains the specialized image-based FIN extraction feature designed specifically for PDFs that are approximately 1.8-1.9 MB in size, where the FIN number is positioned below the left QR code in image format.

## Overview

The system now includes intelligent FIN extraction that automatically detects PDFs of specific sizes (~1.8-1.9 MB) and uses image-based OCR extraction to find FIN numbers positioned below the left QR code. For all other PDF sizes, the FIN field remains empty and requires manual entry. This addresses the specific case where FIN numbers are embedded as images rather than selectable text.

### Key Features

- **Size-Based Detection**: Automatically detects PDFs in the 1.7-2.0 MB range
- **Image-Based Extraction**: Uses OCR to extract FIN from specific image regions
- **Fixed Position Targeting**: Focuses on the area below the left QR code
- **Dual OCR Support**: Uses pytesseract and easyocr for robust text extraction
- **Selective Processing**: Only processes ~1.8-1.9 MB PDFs, leaves others empty

## How It Works

### 1. File Size Detection

When a PDF is uploaded, the system checks its file size:

```python
if 1.7 * 1024 * 1024 <= file_size <= 2.0 * 1024 * 1024:  # 1.7MB to 2.0MB
    # Use image-based FIN extraction
    fin_from_image = self._extract_fin_from_image_position(doc)
else:
    # Leave FIN field empty for other sizes
    return None
```

### 2. Image-Based Extraction Process

For ~1.8-1.9 MB PDFs, the system:

1. **Converts PDF to High-Resolution Image**: Uses 2x zoom for better OCR accuracy
2. **Calculates Target Region**: Determines the area below the left QR code
3. **Crops FIN Region**: Extracts the specific area containing the FIN
4. **Applies OCR**: Uses OCR libraries to extract text from the image
5. **Validates Result**: Ensures the extracted text is a valid 12-digit FIN

### 3. Position Calculation

The system calculates the FIN region based on PDF dimensions:

```python
# Calculate position below left QR code
qr_bottom_y = int(height * 0.75)  # QR code bottom at ~75% of page height
fin_region_top = qr_bottom_y + 20  # 20 pixels below QR code
fin_region_bottom = fin_region_top + 100  # 100 pixels height for FIN region
fin_region_left = int(width * 0.05)  # Left side of page
fin_region_right = int(width * 0.35)  # Left third of page
```

## Technical Implementation

### OCR Libraries

The system supports two OCR libraries for maximum compatibility:

#### 1. pytesseract (Primary)
```python
import pytesseract
custom_config = r'--oem 3 --psm 6 -c tessedit_char_whitelist=0123456789 -'
text = pytesseract.image_to_string(image, config=custom_config)
```

#### 2. easyocr (Fallback)
```python
import easyocr
reader = easyocr.Reader(['en'])
results = reader.readtext(image)
text = ' '.join([result[1] for result in results])
```

### Image Processing

```python
# Convert PDF page to high-resolution image
mat = fitz.Matrix(2.0, 2.0)  # 2x zoom for better OCR
pix = page.get_pixmap(matrix=mat)

# Convert to PIL Image
img_data = pix.tobytes("png")
img = Image.open(io.BytesIO(img_data))

# Crop the FIN region
fin_region = img.crop((fin_region_left, fin_region_top, fin_region_right, fin_region_bottom))
```

## User Experience

### Automatic Detection

When a user uploads a ~1.8-1.9 MB PDF:

1. **Size Detection**: System shows "🔍 Detected ~1.8-1.9 MB PDF, extracting FIN from image position..."
2. **Processing**: OCR processes the image region
3. **Success**: "✅ FIN number extracted: 785564679309 (from image position)"
4. **Fallback**: If image extraction fails, falls back to text extraction

### Visual Feedback

The frontend provides specific feedback for image-based extraction:

```javascript
if (fileSizeMB >= 1.7 && fileSizeMB <= 2.0) {
  statusMessage = "🔍 Detected ~1.8-1.9 MB PDF, extracting FIN from image position...";
}
```

## Installation Requirements

### OCR Dependencies

Add these to `requirements.txt`:

```
pytesseract>=0.3.10
easyocr>=1.7.0
```

### System Dependencies

For pytesseract, you may need to install Tesseract OCR:

**Ubuntu/Debian:**
```bash
sudo apt-get install tesseract-ocr
```

**macOS:**
```bash
brew install tesseract
```

**Windows:**
Download and install from: https://github.com/UB-Mannheim/tesseract/wiki

## Testing

### Test Coverage

The test suite covers:

1. **OCR Library Availability**: Checks if pytesseract and easyocr are installed
2. **File Size Detection**: Verifies correct size-based routing
3. **Position Calculation**: Tests FIN region calculation
4. **Image-Based Extraction**: Tests actual FIN extraction from image regions

### Running Tests

```bash
python tests/test_image_fin_extraction.py
```

### Test PDF Creation

The test suite creates mock PDFs with:
- Simulated QR code in bottom-left area
- FIN number positioned below QR code
- Realistic layout matching the target format

## Performance Considerations

### Processing Time

- **Image Conversion**: ~0.5-1 second
- **OCR Processing**: ~2-5 seconds (depending on image complexity)
- **Total Time**: ~3-6 seconds for ~1.8-1.9 MB PDFs

### Resource Usage

- **Memory**: ~50-100MB additional during OCR processing
- **CPU**: Moderate usage during image processing and OCR
- **Storage**: Temporary image files (cleaned up automatically)

## Error Handling

### Common Scenarios

1. **OCR Library Missing**: Falls back to text-based extraction
2. **Poor Image Quality**: Returns None, falls back to text extraction
3. **No FIN in Region**: Falls back to text-based extraction
4. **Invalid FIN Format**: Ignores invalid patterns, continues searching

### Fallback Chain

```
Image-based extraction (for ~1.8-1.9 MB PDFs)
    ↓ (if fails)
Text-based extraction (for all PDFs)
    ↓ (if fails)
Manual entry (user input)
```

## Configuration

### Size Thresholds

Adjust the size detection thresholds:

```python
# Current: 1.7MB to 2.0MB
if 1.7 * 1024 * 1024 <= file_size <= 2.0 * 1024 * 1024:
    # Use image-based extraction
```

### Position Parameters

Customize the FIN region calculation:

```python
qr_bottom_y = int(height * 0.75)  # Adjust QR position
fin_region_top = qr_bottom_y + 20  # Adjust offset below QR
fin_region_bottom = fin_region_top + 100  # Adjust region height
fin_region_left = int(width * 0.05)  # Adjust left margin
fin_region_right = int(width * 0.35)  # Adjust right boundary
```

### OCR Configuration

Customize OCR settings:

```python
# pytesseract configuration
custom_config = r'--oem 3 --psm 6 -c tessedit_char_whitelist=0123456789 -'

# easyocr configuration
reader = easyocr.Reader(['en'])  # Add more languages if needed
```

## Troubleshooting

### Common Issues

1. **"No OCR library available"**
   - Install pytesseract: `pip install pytesseract`
   - Install easyocr: `pip install easyocr`
   - Install system Tesseract OCR

2. **"No FIN found in image position"**
   - Check if PDF layout matches expected format
   - Verify FIN is positioned below left QR code
   - Try adjusting position parameters

3. **Slow OCR processing**
   - Reduce image resolution (lower Matrix zoom)
   - Use smaller FIN region
   - Consider image preprocessing (contrast enhancement)

### Debug Mode

Enable detailed logging:

```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

### Manual Testing

Test with a real ~1.8-1.9 MB PDF:

1. Upload the PDF
2. Check console logs for extraction method
3. Verify FIN is extracted from correct position
4. Test with different PDF layouts

## Future Enhancements

Planned improvements include:

1. **Adaptive Position Detection**: Learn FIN position from multiple PDFs
2. **Image Preprocessing**: Enhance contrast and clarity before OCR
3. **Multiple Region Search**: Search multiple areas if primary region fails
4. **Confidence Scoring**: Rate OCR confidence and adjust accordingly
5. **Layout Recognition**: Detect different PDF layouts automatically

## Security Considerations

- **Image Processing**: PDFs are converted to images locally
- **OCR Processing**: No data sent to external services
- **Temporary Files**: Image files are cleaned up automatically
- **Memory Management**: Large images are processed efficiently

## Conclusion

The image-based FIN extraction feature provides a specialized solution for ~1.8-1.9 MB PDFs where FIN numbers are embedded as images. It combines intelligent size detection, precise position targeting, and robust OCR processing to deliver accurate FIN extraction while maintaining fallback mechanisms for reliability.

The system is designed to be efficient, user-friendly, and maintainable, with comprehensive error handling and testing coverage.
