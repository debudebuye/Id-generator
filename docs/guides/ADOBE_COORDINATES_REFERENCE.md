# Adobe Coordinates Reference

## ✅ Status: IMPLEMENTED

All Adobe-extracted coordinates have been successfully implemented in `app/services/ocr_extraction_service.py`.

## Reference Dimensions

- **Width**: 900px
- **Height**: 1650px

## Coordinate Mapping

All coordinates are in pixels (x, y, width, height) format from Adobe measurements.

### Front Card Fields

| Field | X | Y | Width | Height | Description |
|-------|---|---|-------|--------|-------------|
| **Full Name (Amharic)** | 205 | 1209 | 675 | 47 | ስም በአማርኛ |
| **Full Name (English)** | 202 | 1257 | 675 | 47 | Name in English |
| **Date of Birth (Gregorian)** | 197 | 1339 | 183 | 47 | DOB in Gregorian calendar |
| **Date of Birth (Ethiopian)** | 389 | 1339 | 409 | 49 | DOB in Ethiopian calendar |
| **Sex (Amharic)** | 201 | 1413 | 63 | 49 | ጾታ |
| **Sex (English)** | 265 | 1403 | 125 | 49 | Sex/Gender |
| **Date of Expiry (Gregorian)** | 201 | 1495 | 175 | 43 | Expiry date Gregorian |
| **Date of Expiry (Ethiopian)** | 387 | 1489 | 339 | 49 | Expiry date Ethiopian |
| **FAN Number** | 321 | 1577 | 427 | 27 | Fayda Account Number |
| **Issue Date (Gregorian)** | 892 | 576 | 45 | 278 | Vertical text on right edge |
| **Issue Date (Ethiopian)** | 895 | 861 | 45 | 231 | Vertical text on right edge |

## Implementation Details

### Code Location
`app/services/ocr_extraction_service.py` → `extract_text_regions()` method

### Coordinate Conversion
Coordinates are converted from reference dimensions to actual image dimensions:

```python

ref_width = 900
ref_height = 1650

# Convert to percentages
x1_percent = x / ref_width
y1_percent = y / ref_height
x2_percent = (x + width) / ref_width
y2_percent = (y + height) / ref_height

# Apply to actual image
x1_px = int(x1_percent * actual_width)
y1_px = int(y1_percent * actual_height)
```

### Region Dictionary

```python
regions = {
    'full_name_am': (205/900, 1209/1650, 880/900, 1256/1650),
    'full_name_en': (202/900, 1257/1650, 877/900, 1304/1650),
    'dob_gregorian': (197/900, 1339/1650, 380/900, 1386/1650),
    'dob_ethiopian': (389/900, 1339/1650, 798/900, 1388/1650),
    'sex_am': (201/900, 1413/1650, 264/900, 1462/1650),
    'sex_en': (265/900, 1403/1650, 390/900, 1452/1650),
    'expiry_gregorian': (201/900, 1495/1650, 376/900, 1538/1650),
    'expiry_ethiopian': (387/900, 1489/1650, 726/900, 1538/1650),
    'fan_number': (321/900, 1577/1650, 748/900, 1604/1650),
    'issue_gregorian': (892/900, 576/1650, 937/900, 854/1650),
    'issue_ethiopian': (895/900, 861/1650, 940/900, 1092/1650),
}
```

## OCR Preprocessing by Field Type

### FAN Number
- CLAHE enhancement (clipLimit=3.0)
- Otsu thresholding
- PSM 7 (single line)
- Whitelist: 0-9 only

### Issue Date (Vertical Text)
- Rotate 90° counterclockwise
- CLAHE enhancement (clipLimit=2.0)
- Otsu thresholding
- PSM 6 (uniform block of text)
- Languages: eng+amh

### Date Fields (DOB, Expiry)
- CLAHE enhancement (clipLimit=2.0)
- Otsu thresholding
- PSM 7 (single line)
- Languages: eng+amh

### Sex Field
- Bilateral filter (9, 75, 75)
- Otsu thresholding
- PSM 7 (single line)
- Languages: eng+amh

### Name Fields
- Bilateral filter (9, 75, 75)
- Otsu thresholding
- PSM 7 (single line)
- Languages: eng+amh

## Testing

### Verify Coordinates
```bash
python verify_adobe_coordinates.py
```

### Visualize Regions on Image
```bash
python visualize_adobe_regions.py <path_to_front_card_image>
```

### Test Extraction
```bash
python test_current_extraction.py
```

## Notes

1. **Vertical Text**: Issue dates are printed vertically on the right edge of the card. The code automatically rotates these regions 90° counterclockwise before OCR.

2. **Scaling**: All coordinates automatically scale to match the actual image dimensions, so they work with various image sizes.

3. **Bilingual Fields**: Most fields have both Amharic and English versions with separate coordinate regions.

4. **Precision**: These coordinates were measured directly from Adobe, ensuring pixel-perfect accuracy.

## Related Files

- `app/services/ocr_extraction_service.py` - Main implementation
- `verify_adobe_coordinates.py` - Verification script
- `visualize_adobe_regions.py` - Visualization tool
- `test_current_extraction.py` - Testing script
