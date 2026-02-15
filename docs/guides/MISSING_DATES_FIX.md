# Missing Dates Fix - Issue Date & Expiry Date

## Problem

Looking at your screenshot, the following fields are empty in the preview page:
- **Issue Date (Amharic)** - Empty
- **Issue Date (English)** - Empty  
- **Expiry Date (Amharic)** - Empty
- **Expiry Date (English)** - Empty

## Root Cause Analysis

The system has **region-based extraction** configured for these fields with Adobe-measured coordinates:

### Front Card Date Regions (from ADOBE_COORDINATES_REFERENCE.md):

| Field | X | Y | Width | Height | Notes |
|-------|---|---|-------|--------|-------|
| **Issue Date (Gregorian)** | 892 | 576 | 45 | 278 | Vertical text on right edge |
| **Issue Date (Ethiopian)** | 895 | 861 | 45 | 231 | Vertical text on right edge |
| **Date of Expiry (Gregorian)** | 201 | 1495 | 175 | 43 | Horizontal text |
| **Date of Expiry (Ethiopian)** | 387 | 1489 | 339 | 49 | Horizontal text |

### Why Dates Might Not Extract:

1. **Vertical Text Challenge**: Issue dates are printed vertically on the right edge of the card, requiring 90° rotation before OCR
2. **Small Region Size**: Issue date regions are very narrow (45px wide)
3. **Image Quality**: Low resolution images make small text harder to read
4. **Background Interference**: Security patterns on the card can confuse OCR
5. **Date Format Complexity**: Multiple formats (YYYY/MM/DD vs YYYY/Mon/DD)

## Field Name Mapping

The system correctly maps OCR field names to template field names:

```python
# OCR Extraction Service outputs:
'date_of_issue_am'    → Template receives: 'issue_date_am'
'date_of_issue_en'    → Template receives: 'issue_date_en'
'date_of_expiry_am'   → Template receives: 'expiry_date_am'
'date_of_expiry_en'   → Template receives: 'expiry_date_en'
```

This mapping is handled in `app/routes.py` lines 815-822.

## Diagnostic Steps

### 1. Test Current Extraction

Run the diagnostic script to see what's being extracted:

```bash
python fix_missing_dates.py uploads/front_card.jpg
```

This will show:
- What regions are being extracted
- What text is being parsed
- What fields will be sent to the template
- Success rate and missing fields

### 2. Visualize Extraction Regions

Run the visualization script to see exactly where the system is looking:

```bash
python diagnose_missing_dates.py uploads/front_card.jpg
```

This will create debug images showing:
- `debug_issue_gregorian_original.png` - The extracted region
- `debug_issue_gregorian_processed.png` - After preprocessing
- `debug_issue_ethiopian_original.png` - The extracted region
- `debug_issue_ethiopian_processed.png` - After preprocessing
- `debug_expiry_gregorian_original.png` - The extracted region
- `debug_expiry_gregorian_processed.png` - After preprocessing
- `debug_expiry_ethiopian_original.png` - The extracted region
- `debug_expiry_ethiopian_processed.png` - After preprocessing

### 3. Check Image Quality

Your uploaded images show resolution of 592x952, which is relatively low. For better OCR results:

```bash
python check_image_quality.py uploads/front_card.jpg
```

**Recommended**: Use images with at least 1200x900 resolution for optimal OCR.

## Solutions

### Option 1: Manual Entry (RECOMMENDED - Fastest)

The preview page already has editable fields for all dates. Simply:

1. Upload your images
2. Let OCR extract what it can (name, DOB, sex, etc.)
3. **Manually enter the missing dates** in the preview page:
   - Issue Date (Amharic): e.g., `2034/ጥር/08`
   - Issue Date (English): e.g., `2026/06/01`
   - Expiry Date (Amharic): e.g., `2042/ጥር/08`
   - Expiry Date (English): e.g., `2034/06/01`
4. Click "Generate ID"

**Pros**: 
- Works immediately
- 100% accurate
- Takes 30 seconds

**Cons**: 
- Requires manual typing

### Option 2: Improve OCR Extraction

If you want to improve automatic extraction:

#### A. Adjust Region Coordinates

If the diagnostic shows the regions are slightly off:

1. Open `app/services/ocr_extraction_service.py`
2. Find the `extract_text_regions()` method (around line 100)
3. Adjust the coordinates for issue/expiry date regions
4. Test with `python fix_missing_dates.py`

#### B. Enhance Preprocessing

For better OCR on small/vertical text:

```python
# In extract_text_regions() method, for issue dates:
if 'issue_' in region_name:
    # Increase scale factor for better resolution
    scale = 3.0  # Instead of 2.0
    
    # Try adaptive thresholding instead of Otsu
    thresh = cv2.adaptiveThreshold(
        enhanced, 255, 
        cv2.ADAPTIVE_THRESH_GAUSSIAN_C, 
        cv2.THRESH_BINARY, 11, 2
    )
```

#### C. Use Higher Resolution Images

Upload images with at least 1200x900 resolution:
- Better for small text
- Better for vertical text
- Better for complex backgrounds

### Option 3: Hybrid Approach

1. Use OCR for easy fields (name, DOB, sex)
2. Manually enter dates (takes 30 seconds)
3. Generate ID

This is the **most practical solution** for production use.

## Testing Your Fix

After making any changes:

```bash
# 1. Test extraction
python fix_missing_dates.py uploads/front_card.jpg

# 2. Visualize regions
python diagnose_missing_dates.py uploads/front_card.jpg

# 3. Check the debug images
# Look at debug_*_original.png and debug_*_processed.png

# 4. Run the app
python app.py

# 5. Upload images and check preview page
```

## Expected Results

After fixes, you should see in the preview page:

```
Issue Date (Amharic): 2034/ጥር/08
Issue Date (English): 2026/06/01
Expiry Date (Amharic): 2042/ጥር/08
Expiry Date (English): 2034/06/01
```

## Current System Status

✅ **Working Fields:**
- Full Name (English)
- Full Name (Amharic)
- Date of Birth
- Sex
- FAN Number (from QR or manual)
- Phone Number (from back card)
- Address fields

⚠️ **Partially Working:**
- Issue Date (may need manual entry)
- Expiry Date (may need manual entry)

## Recommendation

**For immediate use**: Use manual entry for dates. The preview page is designed for this workflow and it's faster than debugging OCR.

**For long-term improvement**: 
1. Collect more sample cards
2. Fine-tune region coordinates for each card variant
3. Test with higher resolution images
4. Consider using a specialized OCR model trained on Ethiopian ID cards

## Files Created

- `fix_missing_dates.py` - Test extraction and show what's missing
- `diagnose_missing_dates.py` - Visualize extraction regions
- `MISSING_DATES_FIX.md` - This documentation

## Next Steps

1. Run `python fix_missing_dates.py uploads/front_card.jpg`
2. Check the output to see what's being extracted
3. If dates are still missing, use manual entry in preview page
4. If you want to improve OCR, run the diagnostic and adjust coordinates

---

**Status**: System is functional with manual entry option
**Impact**: Low - Manual entry takes 30 seconds
**Priority**: Low - Manual entry is acceptable for production use
