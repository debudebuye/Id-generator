# Compact Format PDF Extraction

## Overview

The compact format is a new PDF extraction format designed for smaller PDF files (300 KB - 900 KB). This format is automatically detected based on file size and uses a streamlined extraction approach optimized for compact document layouts.

## File Size Detection

- **Target Range**: 300 KB to 900 KB
- **Auto-Detection**: When a PDF falls within this size range, the system automatically prioritizes the compact format extraction method
- **Fallback**: If compact format extraction fails, the system falls back to other formats (default, residential_sheger, demographic_format)

## Format Characteristics

The compact format expects:

1. **Bilingual Layout**: Data presented in Amharic | English format separated by pipe (|)
2. **Condensed Structure**: Fewer lines with combined information
3. **Standard Fields**:
   - FCN (16 digits)
   - Name (bilingual)
   - Date of Birth (bilingual)
   - Gender (bilingual)
   - Nationality (bilingual)
   - Phone number
   - Address fields (Region, Subcity, Woreda - bilingual)

## Field Mapping

```python
'compact_format': {
    'fcn': 0,           # Line 0: FCN number
    'name': 1,          # Line 1: Name (Amharic | English)
    'dob': 2,           # Line 2: Date of Birth (Amharic | English)
    'gender': 3,        # Line 3: Gender (Amharic | English)
    'nationality': 4,   # Line 4: Nationality (Amharic | English)
    'region': 5,        # Line 5: Region (Amharic | English)
    'subcity': 6,       # Line 6: Subcity (Amharic | English)
    'woreda': 7,        # Line 7: Woreda (Amharic | English)
    'phone': 8,         # Line 8: Phone number
    'photo_img_index': 0,  # First image: Photo
    'qr_img_index': 1      # Second image: QR code
}
```

## Extraction Logic

### 1. FCN Extraction
- Searches for 16-digit numeric sequences
- Formats as: XXXX XXXX XXXX XXXX

### 2. Name Extraction
- Looks for bilingual format: `አማርኛ ስም | English Name`
- Validates that left side contains Amharic characters
- Validates that right side contains only English letters

### 3. Date Extraction
- Expects format: `DD/MM/YYYY | YYYY/MM/DD`
- Left side: Gregorian date
- Right side: Ethiopian calendar date

### 4. Gender Extraction
- Expects format: `ወንድ | Male` or `ሴት | Female`

### 5. Nationality Extraction
- Searches for nationality label first
- Extracts bilingual values from subsequent lines
- Format: `ኢትዮጵያዊ | Ethiopian`

### 6. Address Extraction
- Region: Looks for `አዲስ አበባ | Addis Ababa`
- Subcity: Identifies by keywords (ክፍለ ከተማ, Sub City)
- Woreda: Identifies by keywords (ወረዳ, Woreda)

### 7. Phone Extraction
- Looks for 10 or 12 digit sequences
- Formats to international format: +251 XXX XXX XXX

## Usage

The compact format is automatically used when:

```python
# File size check in extract_pdf_data method
file_size_kb = file_size / 1024
if 300 <= file_size_kb <= 900:
    formats_to_try = ['compact_format', 'default', 'residential_sheger', 'demographic_format']
```

## Example PDF Structure

```
1234567890123456
አበበ በቀለ ገብሬ | Abebe Bekele Gebre
21/05/1999 | 2007/01/29
ወንድ | Male
ኢትዮጵያዊ | Ethiopian
0912345678
አዲስ አበባ | Addis Ababa
ለሚ ኩራ | Lemi Kura
ወረዳ 05 | Woreda 05
```

## Benefits

1. **Faster Processing**: Optimized for smaller file sizes
2. **Better Accuracy**: Tailored extraction logic for compact layouts
3. **Automatic Detection**: No manual format selection needed
4. **Fallback Support**: Gracefully falls back to other formats if needed

## Testing

To test the compact format:

1. Upload a PDF between 300-900 KB
2. Check console logs for: `🎯 File size in compact format range (300-900 KB)`
3. Verify extraction with: `✅ Compact format extraction completed`

## Troubleshooting

If compact format extraction fails:
- Check PDF structure matches expected bilingual format
- Verify file size is within 300-900 KB range
- Review console logs for specific extraction errors
- System will automatically try other formats as fallback
