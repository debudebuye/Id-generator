# Amharic Name Extraction Fix

## Problem
During extraction, the first name was sometimes missing from Amharic names.

**Example:**
- Extracted: `አለሙ ሁሉቃ`
- Expected: `ሳራ አለሙ ሁሉቃ`

## Root Causes

1. **Narrow X-coordinate range**: Started at pixel 100, which cut off text on the left
2. **Insufficient width**: 378px width didn't capture full names
3. **No padding**: Text at region edges was being cut off
4. **Language priority**: English was prioritized over Amharic in OCR

## Solutions Applied

### 1. Extended Region Coordinates
**Before:**
```python
'full_name_am': (100, 664) to (478, 686)  # Width: 378px
```

**After:**
```python
'full_name_am': (85, 664) to (490, 686)   # Width: 405px
```
- Moved left edge from 100 → 85 (captures text starting earlier)
- Moved right edge from 478 → 490 (captures longer names)
- Total width increased by 27px (7% wider)

### 2. Added Padding
```python
if 'full_name' in region_name:
    padding_x = 5  # Add 5 pixels on left and right
    padding_y = 2  # Add 2 pixels on top and bottom
```
- Prevents text from being cut off at region boundaries
- Ensures complete character capture

### 3. Improved Amharic OCR Priority
**Before:**
```python
text = pytesseract.image_to_string(thresh, lang='eng+amh', config=config)
```

**After:**
```python
if '_am' in region_name or 'full_name_am' in region_name:
    text = pytesseract.image_to_string(thresh, lang='amh+eng', config=config)
```
- Amharic language is now prioritized for Amharic fields
- Improves recognition accuracy for Amharic characters

## Testing

Use the debug script to test different region sizes:

```bash
python debug_name_extraction.py app/static/front_cropped.png
```

This will:
1. Test 4 different region sizes
2. Show extracted text for each
3. Save debug images showing the exact regions being extracted

## Expected Results

After these changes:
- ✅ Full names captured (including first names)
- ✅ Better Amharic character recognition
- ✅ No text cut off at edges
- ✅ Works with various name lengths

## If Issues Persist

If names are still being cut off:

1. Run the debug script to see which region size works best
2. Check the debug images to see if the region is correctly positioned
3. Adjust coordinates further if needed:
   - Move left edge further left (e.g., 70 or 60)
   - Increase width (e.g., to 500 or 510)
   - Increase padding values

## Files Modified

- `app/services/ocr_extraction_service.py` - Updated coordinates and preprocessing
- `debug_name_extraction.py` - New debug tool for testing
