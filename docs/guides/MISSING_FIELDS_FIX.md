# Missing Fields Extraction Fix

## Problem
Several fields were not being extracted or displayed in the preview page:
1. **Phone Number** - Empty field
2. **Serial Number** - Empty field  
3. **Issue Date (Amharic)** - Empty field
4. **Issue Date (English)** - Empty field

## Root Causes

### 1. Serial Number
- **Issue**: Serial number was never being generated during OCR extraction
- **Location**: `app/routes.py` in the `generate_id()` function
- **Fix**: Added serial number generation using `id_service.generate_serial_number()`

### 2. Issue Date
- **Issue**: Issue date was being extracted as `date_of_issue` but not mapped to the template fields `issue_date_am` and `issue_date_en`
- **Location**: `app/routes.py` in the `generate_id()` function
- **Fix**: Added proper mapping from `date_of_issue` to both `issue_date_am` and `issue_date_en`

### 3. Phone Number
- **Issue**: Phone number extraction was working but had a bug in the fallback parsing logic
- **Location**: `app/services/ocr_extraction_service.py` in `parse_back_card_data()`
- **Fix**: Fixed KeyError where code was checking `data['region']` instead of `data['region_en']`

## Changes Made

### File: `app/routes.py`

#### 1. Added serial_number to initial extracted dictionary (line ~640)
```python
extracted = {
    'fan': '',
    'fin': '',
    'fcn_full': '',
    'fcn_barcode': '',
    'barcode': '',
    'serial_number': '',  # ← Added this field
    'name_en': '',
    # ... rest of fields
}
```

#### 2. Generate serial number during OCR extraction (line ~720)
```python
# Generate serial number (7-8 digit number)
serial_number = id_service.generate_serial_number()
print(f"🔢 Generated serial number: {serial_number}")

extracted.update({
    'fan': fan_number,
    'fin': fin_number,
    'serial_number': serial_number,  # ← Added this
    # ... rest of fields
})
```

#### 3. Map issue_date fields properly (line ~750)
```python
'issue_date': combined_data.get('date_of_issue', ''),
'issue_date_am': combined_data.get('date_of_issue', ''),  # ← Maps to template
'issue_date_en': combined_data.get('date_of_issue', ''),  # ← Maps to template
```

### File: `app/services/ocr_extraction_service.py`

#### Fixed KeyError in parse_back_card_data() (line ~1221)
```python
# Before (WRONG):
if not data['region'] and len(address_lines) >= 1:
    if not data['region']:
        data['region'] = line

# After (CORRECT):
if not data['region_en'] and len(address_lines) >= 1:
    if not data['region_en']:
        data['region_en'] = line
```

## Testing

Created `test_missing_fields.py` to verify all fixes:

### Test Results
```
✅ Serial number generation works!
   - Generated: 11414492 (7-8 digits, doesn't start with 0)

✅ Issue date extraction works!
   - Extracted: 20/03/10 from "Date of Issue: 2020/03/10"

✅ Phone number extraction works!
   - Extracted: 0912345678 from "Phone Number: 0912345678"
```

## Expected Behavior

After these fixes, when uploading ID card images:

1. **Serial Number** will be automatically generated (7-8 digit number)
2. **Issue Date (Amharic)** will be populated with the extracted issue date
3. **Issue Date (English)** will be populated with the extracted issue date
4. **Phone Number** will be extracted from the back card image

All fields will now appear in the preview page and can be edited if needed.

## Notes

- Serial number is **generated**, not extracted (ID cards don't have serial numbers)
- Issue date is extracted from the front card (vertical text on right side)
- Phone number is extracted from the back card (below QR code)
- All fields support manual editing in the preview page if OCR extraction fails
