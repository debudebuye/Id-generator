# Region Mapping Fix

## Problem

The Adobe coordinates were correctly implemented in `extract_text_regions()`, but the extracted data wasn't being used properly because of a field name mismatch.

### What Was Wrong

1. **extract_text_regions()** returns regions with these names:
   - `full_name_am`, `full_name_en`
   - `dob_gregorian`, `dob_ethiopian`
   - `sex_am`, `sex_en`
   - `expiry_gregorian`, `expiry_ethiopian`
   - `issue_gregorian`, `issue_ethiopian`
   - `fan_number`

2. **parse_front_card_data()** was looking for OLD region names:
   - `full_name` (not `full_name_am` / `full_name_en`)
   - `date_of_birth` (not `dob_gregorian` / `dob_ethiopian`)
   - `sex` (not `sex_am` / `sex_en`)
   - `date_of_expiry` (not `expiry_gregorian` / `expiry_ethiopian`)
   - `date_of_issue` (not `issue_gregorian` / `issue_ethiopian`)

### Result

The regions were extracted correctly, but the parsing code couldn't find them because it was looking for the wrong field names. This caused most fields to appear empty.

## Solution

Updated `parse_front_card_data()` in `app/services/ocr_extraction_service.py` to:

1. Check for NEW region names first (`full_name_am`, `dob_gregorian`, etc.)
2. Fall back to OLD region names for backward compatibility
3. Properly extract bilingual data from separate regions

### Changes Made

#### Full Name Extraction
```python
# NEW: Check separate Amharic and English regions
if 'full_name_am' in regions and regions['full_name_am']:
    # Extract and clean Amharic name
    
if 'full_name_en' in regions and regions['full_name_en']:
    # Extract and clean English name

# OLD: Fallback for legacy 'full_name' region
if 'full_name' in regions and regions['full_name']:
    # Parse combined region
```

#### Date of Birth Extraction
```python
# NEW: Check separate Gregorian and Ethiopian regions
if 'dob_gregorian' in regions and regions['dob_gregorian']:
    # Extract Gregorian date
    
if 'dob_ethiopian' in regions and regions['dob_ethiopian']:
    # Extract Ethiopian date

# OLD: Fallback for legacy 'date_of_birth' region
```

#### Sex Extraction
```python
# NEW: Check separate Amharic and English regions
if 'sex_am' in regions and regions['sex_am']:
    # Extract Amharic sex (ወንድ/ሴት)
    
if 'sex_en' in regions and regions['sex_en']:
    # Extract English sex (Male/Female)

# OLD: Fallback for legacy 'sex' region
```

#### Expiry Date Extraction
```python
# NEW: Check separate Gregorian and Ethiopian regions
if 'expiry_gregorian' in regions and regions['expiry_gregorian']:
    # Extract Gregorian expiry date
    
if 'expiry_ethiopian' in regions and regions['expiry_ethiopian']:
    # Extract Ethiopian expiry date

# OLD: Fallback for legacy 'date_of_expiry' region
```

#### Issue Date Extraction
```python
# NEW: Check separate Gregorian and Ethiopian regions (vertical text)
if 'issue_gregorian' in regions and regions['issue_gregorian']:
    # Extract Gregorian issue date (rotated 90°)
    
if 'issue_ethiopian' in regions and regions['issue_ethiopian']:
    # Extract Ethiopian issue date (rotated 90°)

# OLD: Fallback for legacy 'date_of_issue' region
```

## Benefits

1. **Bilingual Support**: Properly extracts both Amharic and English versions of each field
2. **Precise Extraction**: Uses Adobe-measured coordinates for pixel-perfect accuracy
3. **Backward Compatible**: Still works with old region names if present
4. **Cleaner Data**: Separate regions mean less parsing complexity and fewer errors

## Testing

Run the test script to verify the fix:

```bash
python test_fixed_extraction.py path/to/front_card.jpg
```

Expected output:
- ✅ Full Name (English): [extracted name]
- ✅ Full Name (Amharic): [extracted name]
- ✅ DOB (Gregorian): [date]
- ✅ DOB (Ethiopian): [date]
- ✅ Sex (English): Male/Female
- ✅ Sex (Amharic): ወንድ/ሴት
- ✅ Expiry (Gregorian): [date]
- ✅ Expiry (Ethiopian): [date]
- ✅ Issue (Gregorian): [date]
- ✅ Issue (Ethiopian): [date]
- ✅ FAN Number: [15-16 digits]

## Files Modified

- `app/services/ocr_extraction_service.py` - Updated `parse_front_card_data()` method

## Files Created

- `test_fixed_extraction.py` - Test script to verify the fix
- `REGION_MAPPING_FIX.md` - This documentation

## Next Steps

If fields are still missing after this fix, the issue is likely:

1. **OCR Quality**: The text in those regions isn't being recognized
   - Solution: Adjust preprocessing (CLAHE, thresholding, etc.)
   - Solution: Try different Tesseract PSM modes

2. **Coordinate Accuracy**: The regions don't align with the actual card
   - Solution: Use `visualize_adobe_regions.py` to verify coordinates
   - Solution: Adjust coordinates if card dimensions differ

3. **Pattern Matching**: The regex patterns don't match the extracted text format
   - Solution: Print raw extracted text and adjust regex patterns
   - Solution: Add more flexible date/text parsing
