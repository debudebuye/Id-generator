# Issue Date & Phone Number Extraction Improvements

## Overview
Improved extraction of issue date from vertical text on front card and phone number from back card.

## Issue Date Extraction Improvements

### Problem
The issue date appears vertically on the right side of the front card in the format:
```
የመስጫ ቀን | Date Issued - 2018/06/02 | 2026/Feb/09
```

This contains:
- Amharic label: `የመስጫ ቀን` (Date Issued)
- English label: `Date Issued`
- Issue date: `2018/06/02`
- Another date: `2026/Feb/09` (possibly expiry in different format)

### Improvements Made

#### 1. Enhanced Vertical Text OCR (Line ~113)
**File**: `app/services/ocr_extraction_service.py`

- Added support for both English and Amharic in vertical text extraction
- Changed PSM mode from 7 (single line) to 6 (block of text) for better multi-line handling
- Added more rotation attempts with bilingual support
- Added debug output to show which candidate text contains date patterns

```python
# Try with both English and Amharic
config = '--oem 3 --psm 6'  # Block of text for vertical content
text_eng_amh = pytesseract.image_to_string(thresh, lang='eng+amh', config=config)
```

#### 2. Improved Date Parsing (Line ~407)
**File**: `app/services/ocr_extraction_service.py`

- Changed from single date extraction to finding ALL dates in the text
- When multiple dates found, use the FIRST one (issue date comes before expiry)
- Added better logging to show how many dates were found

```python
# Find all dates in the text
all_dates = []
for pattern in date_patterns:
    matches = re.findall(pattern, issue_text)
    all_dates.extend(matches)

if all_dates:
    # If multiple dates found, use the first one (issue date comes before expiry)
    extracted_date = all_dates[0]
    print(f"✓ Extracted issue date: {data['date_of_issue']} (from {len(all_dates)} dates found)")
```

#### 3. Enhanced Fallback Extraction (Line ~587)
**File**: `app/services/ocr_extraction_service.py`

- Added pattern to look for "Date Issued" or "የመስጫ ቀን" labels followed by a date
- This handles the specific format shown in the ID card

```python
# Look for "Date Issued" or "የመስጫ ቀን" followed by a date
issue_pattern = r'(?:Date Issued|የመስጫ\s*ቀን|Issued)[:\s\-]*(\d{4}/\d{2}/\d{2})'
issue_match = re.search(issue_pattern, text, re.IGNORECASE)
if issue_match:
    data['date_of_issue'] = issue_match.group(1)
    print(f"✓ Found issue date (with label): {data['date_of_issue']}")
```

## Phone Number Extraction

### Status
Phone number extraction logic was already working correctly. The previous fix resolved a KeyError bug in the fallback parsing.

### Current Implementation
- Extracts phone from back card region below QR code
- Supports multiple formats:
  - With label: `Phone: 0912345678`
  - Ethiopian mobile: `09xxxxxxxx`
  - International: `+251xxxxxxxxx`
  - Generic 10-digit: `0xxxxxxxxx`

## Testing

### Debug Script
Created `debug_issue_date_phone.py` to test extraction on actual uploaded images:

```bash
python debug_issue_date_phone.py
```

This will:
1. Look for uploaded front/back card images in `uploads/`, `static/`, or `temp/` folders
2. Extract regions and show raw OCR text
3. Parse the data and display extracted fields
4. Show issue date and phone number extraction results

### Expected Results

After uploading an ID card with the format shown in the sample image:

**Issue Date:**
- Should extract: `2018/06/02` (the first date from the vertical text)
- Will be displayed in both Amharic and English fields

**Phone Number:**
- Should extract: 10-digit phone number from back card
- Format: `0xxxxxxxxx`

## Next Steps

If extraction still fails:

1. **Run the debug script** to see what's being extracted:
   ```bash
   python debug_issue_date_phone.py
   ```

2. **Check the raw OCR output** to see if Tesseract is reading the vertical text correctly

3. **Adjust the region coordinates** if the vertical text area is not being captured:
   - File: `app/services/ocr_extraction_service.py`
   - Line: ~78
   - Current: `'date_of_issue': (0.85, 0.15, 0.98, 0.85)`

4. **Try different rotation angles** if the text orientation is different

5. **Improve preprocessing** if the image quality is affecting OCR accuracy

## Files Modified

1. `app/routes.py` - Added serial number generation and field mapping
2. `app/services/ocr_extraction_service.py` - Improved vertical text extraction and date parsing
3. `test_missing_fields.py` - Test script for basic functionality
4. `debug_issue_date_phone.py` - Debug script for actual image testing

## Summary

The extraction logic has been significantly improved to handle:
- Vertical text with mixed Amharic and English
- Multiple dates in the same text (extracts the first one)
- Various date formats and labels
- Better fallback mechanisms

The system should now successfully extract issue dates from the vertical text on Ethiopian Digital ID cards.
