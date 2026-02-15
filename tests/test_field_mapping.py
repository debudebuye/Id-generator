"""
Test script to verify field mapping between OCR extraction and template
"""

# Simulated OCR extraction output
ocr_front_data = {
    'full_name_en': 'GDACSL CPO7 AcaTK',
    'full_name_am': 'ታሪቅ ደሳ ከበደ',
    'date_of_birth': '05/10/1995',
    'sex': 'Female',
    'date_of_expiry': '2026/02/09',
    'date_of_issue': '2018/06/02',
    'fan': '9451925805478160',
    'barcode': ''
}

ocr_back_data = {
    'phone_number': '0912345678',
    'nationality_en': 'Ethiopian',
    'nationality_am': 'ኢትዮጵያዊ',
    'region_en': '',
    'region_am': '',
    'subcity_en': '',
    'subcity_am': '',
    'woreda_en': 'Damot Sore Woreda',
    'woreda_am': 'ደሞት',
    'address_en': '',
    'address_am': '',
    'fin': ''
}

# Combine data
combined_data = {**ocr_front_data, **ocr_back_data}

# Map to template fields (as done in routes.py)
extracted = {
    'fan': combined_data.get('fan', ''),
    'fin': combined_data.get('fin', ''),
    'fcn_full': combined_data.get('fan', ''),
    'serial_number': '18858370',
    
    # Map full_name_* to name_* for template compatibility
    'name_en': combined_data.get('full_name_en', ''),
    'name_am': combined_data.get('full_name_am', ''),
    'full_name_en': combined_data.get('full_name_en', ''),
    'full_name_am': combined_data.get('full_name_am', ''),
    
    'nationality_en': combined_data.get('nationality_en', 'Ethiopian'),
    'nationality_am': combined_data.get('nationality_am', 'ኢትዮጵያዊ'),
    
    'region_en': combined_data.get('region_en', ''),
    'region_am': combined_data.get('region_am', ''),
    'subcity_en': combined_data.get('subcity_en', ''),
    'subcity_am': combined_data.get('subcity_am', ''),
    'woreda_en': combined_data.get('woreda_en', ''),
    'woreda_am': combined_data.get('woreda_am', ''),
    
    # Map to template field names
    'dob_am': combined_data.get('date_of_birth', ''),
    'dob_en': combined_data.get('date_of_birth', ''),
    'birth_date': combined_data.get('date_of_birth', ''),
    'date_of_birth': combined_data.get('date_of_birth', ''),
    
    # Map sex to gender for template
    'gender_am': combined_data.get('sex', ''),
    'gender_en': combined_data.get('sex', ''),
    'sex': combined_data.get('sex', ''),
    
    'issue_date': combined_data.get('date_of_issue', ''),
    'issue_date_am': combined_data.get('date_of_issue', ''),
    'issue_date_en': combined_data.get('date_of_issue', ''),
    'date_of_issue': combined_data.get('date_of_issue', ''),
    
    'expiry_date': combined_data.get('date_of_expiry', ''),
    'expiry_date_am': combined_data.get('date_of_expiry', ''),
    'expiry_date_en': combined_data.get('date_of_expiry', ''),
    'date_of_expiry': combined_data.get('date_of_expiry', ''),
    
    # Map phone_number to phone for template compatibility
    'phone': combined_data.get('phone_number', ''),
    'phone_number': combined_data.get('phone_number', ''),
}

# Template fields that should be populated
template_fields = [
    'fin', 'region_am', 'region_en', 'subcity_am', 'subcity_en', 
    'woreda_am', 'woreda_en', 'nationality_am', 'nationality_en',
    'name_am', 'name_en', 'phone', 'dob_am', 'dob_en',
    'gender_am', 'gender_en', 'fcn_formatted', 'serial_number',
    'issue_date_am', 'issue_date_en', 'expiry_date_am', 'expiry_date_en'
]

print("=" * 80)
print("FIELD MAPPING TEST")
print("=" * 80)
print("\nOCR Extracted Data:")
print(f"  Front: {ocr_front_data}")
print(f"  Back: {ocr_back_data}")

print("\n" + "=" * 80)
print("Template Field Mapping:")
print("=" * 80)

populated_count = 0
empty_count = 0

for field in template_fields:
    value = extracted.get(field, '')
    status = "✓" if value else "✗"
    if value:
        populated_count += 1
        print(f"{status} {field:20s} = {value}")
    else:
        empty_count += 1
        print(f"{status} {field:20s} = (empty)")

print("\n" + "=" * 80)
print(f"Summary: {populated_count}/{len(template_fields)} fields populated")
print(f"Empty fields: {empty_count}")
print("=" * 80)

# Check for critical missing fields
critical_fields = ['name_en', 'name_am', 'phone', 'dob_am', 'gender_am']
missing_critical = [f for f in critical_fields if not extracted.get(f)]

if missing_critical:
    print(f"\n⚠️  WARNING: Critical fields missing: {missing_critical}")
else:
    print(f"\n✓ All critical fields populated!")
