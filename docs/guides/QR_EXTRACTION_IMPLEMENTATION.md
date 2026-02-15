# QR Code Extraction Implementation

## Overview
Implemented QR code extraction from back ID card images. The system now automatically extracts the QR code region from the back card and displays it in the preview page.

## Changes Made

### 1. OCR Extraction Service (`app/services/ocr_extraction_service.py`)
Added two new methods to the `OCRExtractionService` class:

#### `extract_qr_code_region(image_path, output_path)`
- Extracts the QR code region from the back ID card image
- QR code is located at the top portion of the back card (10-65% of height)
- Saves the extracted QR region to the specified output path
- Returns the path to the extracted QR image

#### `decode_qr_code(image_path)`
- Decodes QR code data using pyzbar library (optional)
- Returns the decoded QR data as a string
- Gracefully handles case where pyzbar is not installed
- Useful for validation and debugging

### 2. Routes (`app/routes.py`)

#### Updated `generate_id()` function:
- Added QR code extraction after back card OCR processing
- Extracts QR code region and saves to `static/qr_extracted.png`
- Optionally decodes QR code data for logging/debugging
- Stores QR path in extracted data dictionary
- Added `qr_path` field to extracted data structure

#### Updated `preview()` function:
- Retrieves QR path from extracted data
- Converts absolute path to filename for template
- Passes QR filename to preview template
- Added timestamp parameter for cache busting

### 3. Preview Template (`app/templates/preview.html`)
- Already configured to display QR code when available
- Shows placeholder message when QR is not extracted
- Supports drag-and-drop QR code upload
- Includes download and upload buttons for QR code

## How It Works

1. **User uploads images**: Front, back, and profile photo
2. **OCR extraction runs**: System extracts text data from both cards
3. **QR extraction**: System automatically extracts QR code from back card
4. **Preview page**: Displays extracted QR code alongside other data
5. **User can**: View, download, or replace the extracted QR code

## QR Code Location
The QR code is extracted from the **top portion** of the back ID card:
- Vertical: 10% to 65% of image height
- Horizontal: 10% to 90% of image width

This region is optimized for Ethiopian Digital ID cards where the QR code is typically positioned at the top of the back card.

## Optional: QR Code Decoding

### Installing pyzbar
To enable QR code decoding (optional):
```bash
pip install pyzbar
```

### Without pyzbar
- QR code extraction still works
- QR image is saved and displayed
- Decoding is skipped with a warning message

### With pyzbar
- QR code is extracted AND decoded
- Decoded data is logged to console
- Useful for validation and debugging

## Testing

### Manual Testing
1. Upload front and back ID card images
2. Check console logs for QR extraction messages
3. Verify QR code appears in preview page
4. Test download and upload functionality

### Automated Testing
Run the test script:
```bash
python test_qr_extraction.py
```

Enter the path to a back ID card image when prompted.

## File Locations

### Extracted QR Code
- Saved to: `app/static/qr_extracted.png`
- Overwritten on each new extraction
- Displayed in preview page

### Source Files Modified
- `app/services/ocr_extraction_service.py` - Added QR extraction methods
- `app/routes.py` - Integrated QR extraction into workflow
- `test_qr_extraction.py` - Test script for QR extraction

## Success Criteria

✅ QR code is extracted from back card image
✅ QR code is saved to static folder
✅ QR code is displayed in preview page
✅ System handles missing QR codes gracefully
✅ Optional QR decoding with pyzbar
✅ No errors when pyzbar is not installed

## Future Enhancements

1. **QR Code Validation**: Validate QR data format
2. **QR Code Generation**: Generate QR code if not found
3. **Multiple QR Codes**: Handle cards with multiple QR codes
4. **QR Code Enhancement**: Improve QR image quality for better scanning
5. **QR Data Parsing**: Parse and display QR data fields

## Notes

- QR extraction is automatic when back card is uploaded
- Works alongside existing OCR text extraction
- Does not interfere with manual data entry
- QR code can be replaced by user if needed
- System continues to work even if QR extraction fails
