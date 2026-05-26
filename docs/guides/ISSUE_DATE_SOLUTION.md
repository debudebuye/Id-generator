# Issue Date Extraction Solution

## What I See in Your Sample Image

Looking at your front card sample, I can clearly see:

### ✅ Successfully Visible Fields:
- **Full Name (Amharic)**: ፍራኦል ወርቅነህ ቡሰሪ
- **Full Name (English)**: Firaol Workineh Buseri
- **Date of Birth**: 01/05/2000 | 2008/Jan/10
- **Sex**: ወንድ | Male
- **Date of Expiry**: 2026/05/30 | 2034/Feb/07
- **FAN Number**: 5810785287530862

### ❓ Issue Date Location:
The **Issue Date is printed VERTICALLY** on the right edge of the card:
- **Visible text**: "2018/06/02 | 2026/Feb/09"
- **Position**: Right edge, running from top to bottom
- **Challenge**: Vertical text requires 90° rotation before OCR

## Why Issue Date Extraction Fails

1. **Vertical Text**: The text runs vertically (top to bottom) on a narrow strip
2. **Small Font**: The text is very small (45px wide region)
3. **Background Pattern**: The wavy security pattern interferes with OCR
4. **Rotation Required**: Must rotate 90° counterclockwise before reading

## The Fix

I've created a specialized test script to extract vertical issue dates:

### Test the Extraction:

```bash
# Save your front card image as front_card.jpg, then run:
python test_vertical_issue_date.py front_card.jpg
```

This script will:
1. Extract the vertical text region from the right edge
2. Rotate it 90° to make it horizontal
3. Try 4 different preprocessing methods
4. Parse the dates from the best result
5. Save debug images showing each step

### Expected Output:

```
✅ Successfully extracted issue dates!
   English: 2018/06/02
   Amharic: 2026/Feb/09
```

## Quick Manual Entry (30 seconds)

Since the issue date is clearly visible on your card, you can simply:

1. Upload your images
2. In the preview page, manually enter:
   - **Issue Date (English)**: `2018/06/02`
   - **Issue Date (Amharic)**: `2026/Feb/09`
3. Click "Generate ID"

## Improving Automatic Extraction

If you want the system to extract issue dates automatically, here are the improvements needed:

### 1. Increase Scale Factor

In `app/services/ocr_extraction_service.py`, line ~150:

```python
# Current:
scale = 2.0

# Change to:
scale = 3.0  # Better for small vertical text
```

### 2. Better Preprocessing for Vertical Text

In the `extract_text_regions()` method, for issue date regions:

```python
elif 'issue_' in region_name:
    # Rotate 90 degrees counterclockwise
    rotated = cv2.rotate(gray, cv2.ROTATE_90_COUNTERCLOCKWISE)
    
    # Increase scale for small text
    scale = 3.0  # Instead of 2.0
    rotated = cv2.resize(rotated, None, fx=scale, fy=scale, interpolation=cv2.INTER_CUBIC)
    
    # Apply CLAHE
    clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8,8))
    enhanced = clahe.apply(rotated)
    
    # Try adaptive thresholding (better for uneven lighting)
    thresh = cv2.adaptiveThreshold(
        enhanced, 255, 
        cv2.ADAPTIVE_THRESH_GAUSSIAN_C, 
        cv2.THRESH_BINARY, 11, 2
    )
    
    # OCR with PSM 6 (uniform block of text)
    config = '--oem 3 --psm 6'
    text = pytesseract.image_to_string(thresh, lang='eng+amh', config=config)
```

### 3. Adjust Region Coordinates

The Adobe coordinates might need slight adjustment based on your actual card dimensions. Test with:

```bash
python diagnose_missing_dates.py front_card.jpg
```

Check the debug images to see if the region is correctly positioned.

## Testing Your Card

To test with your actual front card image:

1. **Save the image**: Save your front card as `front_card.jpg` in the project root

2. **Run the test**:
   ```bash
   python test_vertical_issue_date.py front_card.jpg
   ```

3. **Check debug images**:
   - `debug_vertical_issue_original.png` - The extracted vertical strip
   - `debug_vertical_issue_rotated.png` - After rotation
   - `debug_vertical_issue_otsu.png` - Otsu thresholding
   - `debug_vertical_issue_adaptive.png` - Adaptive thresholding
   - `debug_vertical_issue_simple.png` - Simple thresholding
   - `debug_vertical_issue_inverted.png` - Inverted thresholding

4. **See which method works best** and update the code accordingly

## Expected Results

After implementing the fixes, the system should extract:

```python
{
    'date_of_issue_en': '2018/06/02',
    'date_of_issue_am': '2026/Feb/09',
    'date_of_expiry_en': '2026/05/30',
    'date_of_expiry_am': '2034/Feb/07'
}
```

Which will be mapped to the template as:

```python
{
    'issue_date_en': '2018/06/02',
    'issue_date_am': '2026/Feb/09',
    'expiry_date_en': '2026/05/30',
    'expiry_date_am': '2034/Feb/07'
}
```

## Recommendation

**For immediate use**: 
- Use manual entry for issue dates (takes 10 seconds)
- The dates are clearly visible on the card
- Manual entry is 100% accurate

**For long-term improvement**:
- Run the test script to see which preprocessing method works best
- Implement the improvements in the OCR service
- Test with multiple card samples to ensure consistency

## Files Created

- `test_vertical_issue_date.py` - Specialized test for vertical issue date extraction
- `ISSUE_DATE_SOLUTION.md` - This documentation

## Next Steps

1. Save your front card image as `front_card.jpg`
2. Run: `python test_vertical_issue_date.py front_card.jpg`
3. Check the debug images to see which method works best
4. Either:
   - Use manual entry (fastest)
   - Or implement the preprocessing improvements (for automation)

---

**Status**: Issue identified - vertical text extraction needs improvement
**Workaround**: Manual entry (10 seconds)
**Long-term fix**: Implement improved preprocessing for vertical text
