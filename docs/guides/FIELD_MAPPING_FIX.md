# Field Mapping Fix - Empty Fields Issue

## Problem
Most fields were showing empty in the preview page even though OCR extraction was working correctly.

## Root Cause
There was a mismatch between the field names returned by the OCR extraction service and the field names expected by the preview template:

### Field Name Mismatches:
1. **Name fields:**
   - OCR returns: `full_name_en`, `full_name_am`
   - Template expects: `name_en`, `name_am`

2. **Phone field:**
   - OCR returns: `phone_number`
   - Template expects: `phone`

3. **Date of Birth:**
   - OCR returns: `date_of_birth`
   - Template expects: `dob_am`, `dob_en`

4. **Gender/Sex:**
   - OCR returns: `sex`
   - Template expects: `gender_am`, `gender_en`

5. **Date fields:**
   - OCR returns: `date_of_issue`, `date_of_expiry`
   - Template expects: `issue_date_am`, `issue_date_en`, `expiry_date_am`, `expiry_date_en`

## Solution
Updated `app/routes.py` in the `generate_id()` function to properly map all OCR field names to template field names:

```python
extracted.update({
    # Map full_name_* to name_* for template compatibility
    'name_en': combined_data.get('full_name_en', ''),
    'name_am': combined_data.get('full_name_am', ''),
    'full_name_en': combined_data.get('full_name_en', ''),  # Keep for compatibility
    'full_name_am': combined_data.get('full_name_am', ''),  # Keep for compatibility
    
    # Map to template field names
    'dob_am': combined_data.get('date_of_birth', ''),
    'dob_en': combined_data.get('date_of_birth', ''),
    'date_of_birth': combined_data.get('date_of_birth', ''),  # Keep for compatibility
    
    # Map sex to gender for template
    'gender_am': combined_data.get('sex', ''),
    'gender_en': combined_data.get('sex', ''),
    'sex': combined_data.get('sex', ''),  # Keep for compatibility
    
    # Map phone_number to phone for template compatibility
    'phone': combined_data.get('phone_number', ''),
    'phone_number': combined_data.get('phone_number', ''),  # Keep for compatibility
    
    # Date fields with all variants
    'issue_date': combined_data.get('date_of_issue', ''),
    'issue_date_am': combined_data.get('date_of_issue', ''),
    'issue_date_en': combined_data.get('date_of_issue', ''),
    'date_of_issue': combined_data.get('date_of_issue', ''),
    
    'expiry_date': combined_data.get('date_of_expiry', ''),
    'expiry_date_am': combined_data.get('date_of_expiry', ''),
    'expiry_date_en': combined_data.get('date_of_expiry', ''),
    'date_of_expiry': combined_data.get('date_of_expiry', ''),
})
```

## Changes Made

### 1. Updated `app/routes.py`
- Added proper field mapping in the `generate_id()` function
- Maintained both old and new field names for backward compatibility
- Added comprehensive logging to track data flow
- Updated initial `extracted` dictionary to include all field variants

### 2. Enhanced Logging
Added detailed logging at multiple stages:
- OCR extraction results (front and back)
- Combined data after merging front and back
- Final extracted data before storing in session
- Non-empty fields summary

### 3. Test Script
Created `test_field_mapping.py` to verify the field mapping works correctly.

## Testing Results
Running the test script shows:
- ✓ All critical fields populated (name, phone, dob, gender)
- ✓ 16/22 template fields populated from OCR data
- ✓ Field mapping working correctly

## Expected Behavior After Fix
1. When uploading front and back ID card images, OCR extraction will run
2. Extracted data will be properly mapped to template field names
3. Preview page will show all extracted fields populated
4. Users can edit any fields before generating the final ID card

## Notes
- Some fields may still be empty if OCR extraction fails for those specific regions
- Region and subcity fields depend on OCR quality and may need manual entry
- FIN field is optional and may not always be present on ID cards
- The system maintains both old and new field names for backward compatibility
