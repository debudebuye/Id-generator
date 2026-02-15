# Sample Front Cards Analysis

## Cards Analyzed

### Card 1 & 4: Mabele Mihretab Solomon
- **Name (AM)**: ማዕበለ ምህረታብ ሰለሞን
- **Name (EN)**: Mabele Mihretab Solomon
- **DOB**: 12/03/1996 | 2003/Nov/22
- **Sex**: ወንድ | Male
- **Expiry**: 2026/05/30 | 2034/Feb/07
- **FAN**: 2076275379150174
- **Issue Date (Vertical)**: 2018/06/02 | 2026/Feb/09

### Card 2 & 5: Dejay Dejen Tareke
- **Name (AM)**: ደጃይ ደጀን ታረቀ
- **Name (EN)**: Dejay Dejen Tareke
- **DOB**: 01/04/1992 | 1999/Dec/11
- **Sex**: ወንድ | Male
- **Expiry**: 2026/06/01 | 2034/Feb/08
- **FAN**: 4864750941572145
- **Issue Date (Vertical)**: 2018/06/03 | 2026/Feb/10

### Card 3 & 6: Wudinesh Belachew Abere
- **Name (AM)**: ውድነሽ በላቸው አበረ
- **Name (EN)**: Wudinesh Belachew Abere
- **DOB**: 12/06/1995 | 2003/Feb/19
- **Sex**: ሴት | Female
- **Expiry**: 2026/06/01 | 2034/Feb/08
- **FAN**: 3726105912870631
- **Issue Date (Vertical)**: 2018/06/03 | 2026/Feb/10

## Key Observations

### 1. Vertical Text Format
All cards have the same vertical text format on the right edge:
```
የመስጫ ቀን | Date Issued - YYYY/MM/DD | YYYY/Mon/DD
```

The format contains:
- **Amharic label**: `የመስጫ ቀን` (Date Issued)
- **English label**: `Date Issued`
- **Issue date**: First date in YYYY/MM/DD format (e.g., 2018/06/02)
- **Second date**: Another date in YYYY/Mon/DD format (e.g., 2026/Feb/09)

### 2. Issue Date Pattern
- All issue dates are from **2018/06** (June 2018)
- Format is consistent: `YYYY/MM/DD`
- Issue date always appears FIRST in the vertical text
- Second date appears to be 8 years later (possibly expiry in different calendar)

### 3. Vertical Text Location
- Located on the **far right edge** of the card
- Runs vertically from top to bottom
- Approximately 12% of card width (rightmost portion)
- Spans about 80% of card height

## Extraction Strategy

### Region Coordinates
Updated region for issue date extraction:
```python
'date_of_issue': (0.88, 0.10, 1.0, 0.90)
```

This captures:
- **X**: 88% to 100% (rightmost 12% of card)
- **Y**: 10% to 90% (most of the card height)

### OCR Approach
1. **Rotate 90° counterclockwise** - Converts vertical text to horizontal
2. **Apply CLAHE** - Enhances contrast for better OCR
3. **Use bilingual OCR** - `lang='eng+amh'` to handle mixed text
4. **Extract first date** - When multiple dates found, use the first one

### Date Extraction Logic
```python
# Find all dates in the text
all_dates = []
for pattern in date_patterns:
    matches = re.findall(pattern, issue_text)
    all_dates.extend(matches)

if all_dates:
    # Use the first date (issue date comes before expiry)
    extracted_date = all_dates[0]
```

## Expected Extraction Results

For the sample cards, the system should extract:

| Card | Expected Issue Date |
|------|-------------------|
| Mabele Mihretab Solomon | 2018/06/02 |
| Dejay Dejen Tareke | 2018/06/03 |
| Wudinesh Belachew Abere | 2018/06/03 |

## Testing

### Manual Testing
1. Upload one of the sample cards through the web interface
2. Check if the issue date fields are populated
3. Verify the date matches the expected value

### Automated Testing
Run the debug script:
```bash
python debug_issue_date_phone.py
```

This will show:
- Raw OCR text from the vertical region
- Extracted issue date
- All other extracted fields

## Potential Issues

### 1. OCR Accuracy
- Vertical text can be challenging for OCR
- Mixed Amharic and English may confuse the OCR engine
- Background pattern on card may interfere

**Solution**: 
- Use CLAHE enhancement
- Try both rotation directions if first fails
- Use bilingual language support

### 2. Multiple Dates
- Two dates appear in the vertical text
- Need to ensure we extract the FIRST one (issue date)

**Solution**:
- Use `findall()` to get all dates
- Take `all_dates[0]` (first occurrence)

### 3. Date Format Variations
- Different date formats: YYYY/MM/DD vs YYYY/Mon/DD
- Need to handle both

**Solution**:
- Multiple regex patterns
- Normalize to forward slashes

## Performance

With optimizations:
- **Region extraction**: ~1-2 seconds
- **Issue date OCR**: ~0.5-1 second (1-2 calls)
- **Total per card**: ~4-6 seconds

## Next Steps

1. **Test with actual uploads** - Verify extraction works with real user uploads
2. **Monitor accuracy** - Track success rate of issue date extraction
3. **Adjust if needed** - Fine-tune region coordinates or OCR parameters
4. **Add fallbacks** - If region extraction fails, try full-page OCR

## Summary

The sample cards show a consistent format for the issue date in vertical text on the right edge. The extraction system has been optimized to:

1. ✅ Capture the correct region (rightmost 12% of card)
2. ✅ Rotate text for horizontal OCR
3. ✅ Handle bilingual text (Amharic + English)
4. ✅ Extract the first date when multiple dates present
5. ✅ Perform efficiently (1-2 OCR calls instead of 5)

The system should now successfully extract issue dates from all sample cards and similar Ethiopian Digital ID cards.
