# Photo + QR Extraction Feature - UPDATED

## Overview
The system now intelligently extracts profile photos and QR codes from combined screenshots, automatically removing phone UI elements and focusing on the actual content.

## Problem Solved
When users upload screenshots from their phone showing both the profile photo and QR code, the system was including the entire phone UI (buttons, navigation, etc.). Now it intelligently detects and extracts only the actual photo and QR code content.

## How It Works

### Multi-Method Extraction Strategy

The system tries 3 different methods in order of sophistication:

#### Method 1: QR Detection-Based (Most Accurate)
- Uses OpenCV's QR code detector to precisely locate the QR code
- Calculates the split point based on QR location
- Extracts photo from above the QR with smart margins
- Removes 5% margins from top/bottom and 15% from sides to exclude UI elements

#### Method 2: White Card Detection (Good for UI Screenshots)
- Detects white/light rectangular regions (the content cards)
- Filters by size (must be at least 15% of image)
- Sorts by vertical position to identify photo card (top) and QR card (bottom)
- Applies 10% margins on all sides to remove UI elements
- Works great for screenshots with white content cards

#### Method 3: Simple Split with Margins (Fallback)
- Splits image at 50% height
- Removes 5% margins from top/bottom
- Removes 15% margins from left/right sides
- Reliable fallback when detection methods fail

### Upload Interface (index.html)
- **3 Column Layout**:
  - Column 1: Profile Photo + QR (combined upload)
  - Column 2: Front ID Card
  - Column 3: Back ID Card
- Drag & drop support for all columns
- Combined image sent as `cropped_photo_qr`

### Processing Flow

1. User uploads combined screenshot
2. Backend receives base64 image data
3. Image saved temporarily as `photo_qr_combined.png`
4. Extraction function tries methods in order:
   - QR detection → White card detection → Simple split
5. Two clean images created:
   - `photo_extracted.png` - Just the profile photo
   - `qr_extracted.png` - Just the QR code
6. Both images used in ID generation

## Example Output

### Input (Screenshot with UI):
```
┌─────────────────────────┐
│  Phone Status Bar       │ ← Removed
├─────────────────────────┤
│ ┌─────────────────────┐ │
│ │  Passport Photo     │ │
│ │ ┌───────────────┐   │ │
│ │ │               │   │ │ ← Extracted
│ │ │  Photo Here   │   │ │
│ │ │               │   │ │
│ │ └───────────────┘   │ │
│ │  [Buttons]          │ │ ← Removed
│ └─────────────────────┘ │
├─────────────────────────┤
│ ┌─────────────────────┐ │
│ │  QR Code            │ │
│ │ ┌───────────────┐   │ │
│ │ │  ▓▓▓▓▓▓▓▓▓▓  │   │ │ ← Extracted
│ │ │  ▓▓▓▓▓▓▓▓▓▓  │   │ │
│ │ └───────────────┘   │ │
│ │  [Buttons]          │ │ ← Removed
│ └─────────────────────┘ │
│  Phone Navigation       │ ← Removed
└─────────────────────────┘
```

### Output:
- Clean profile photo (no UI elements)
- Clean QR code (no UI elements)

## Testing

### Run the test script:
```bash
python test_photo_qr_extraction.py path/to/screenshot.png
```

### Expected Output:
```
======================================================================
Testing Photo + QR Extraction
======================================================================
Input image: path/to/screenshot.png
Output directory: app/static/temp

🔍 Starting intelligent photo + QR extraction...
   Method 1: QR detection-based extraction
   📸 Image size: 425x1024
   ✓ QR code detected at: x=120, y=650, w=280, h=280
   ✓ Extracted photo: (280, 350)
   ✓ Extracted QR: (280, 280)
✅ Extraction successful using QR detection method

======================================================================
✅ EXTRACTION SUCCESSFUL!
======================================================================
Photo saved to: app/static/temp/photo_extracted.png
QR saved to: app/static/temp/qr_extracted.png

You can now view the extracted images in: app/static/temp
======================================================================
```

## Files Modified

1. **app/templates/index.html**
   - Combined photo and QR into single upload field
   - Changed from `cropped_photo` + `cropped_qr` to `cropped_photo_qr`
   - Maintained 3-column layout with drag & drop

2. **app/routes_image_handler.py**
   - Updated `handle_cropped_images_in_generate_id()`
   - Processes `cropped_photo_qr` field
   - Calls extraction function to split combined image
   - Saves extracted photo and QR separately

3. **app/utils/image_utils.py**
   - Added `detect_and_extract_photo_qr()` - Main extraction function with 3 methods
   - Added `extract_photo_qr_with_detection()` - QR detection-based method
   - Added `extract_photo_and_qr_from_combined()` - Simple split fallback
   - All methods remove UI margins intelligently

4. **test_photo_qr_extraction.py**
   - Standalone test script
   - Tests extraction with any image
   - Shows detailed progress and results

## Configuration

### Adjusting Margins

If extraction is too aggressive or not enough, adjust margins in `image_utils.py`:

```python
# In extract_photo_qr_with_detection()
photo_margin_top = int(height * 0.05)      # Top margin (5%)
photo_margin_side = int(width * 0.15)      # Side margins (15%)

# In white card detection
margin_x = int(pw * 0.1)  # 10% horizontal margin
margin_y = int(ph * 0.1)  # 10% vertical margin

# In simple split
photo_center_crop = int(photo_width * 0.15)  # 15% from each side
```

### Adjusting Split Ratio

```python
# In extract_photo_and_qr_from_combined()
split_ratio = 0.5  # 50/50 split (adjust as needed)
```

## Dependencies

- **PIL/Pillow**: Required ✅ (already installed)
- **OpenCV (cv2)**: Required ✅ (installed via easyocr)
- **NumPy**: Required ✅ (installed via easyocr)

All dependencies are already available through existing packages!

## Error Handling

- Tries 3 methods automatically
- Falls back gracefully if one method fails
- Detailed logging for debugging
- Returns `(None, None)` only if all methods fail
- Continues ID generation even if extraction fails

## Advantages

1. **Smart Detection**: Automatically finds content regions
2. **UI Removal**: Removes phone interface elements
3. **Multiple Methods**: Tries 3 different approaches
4. **Robust**: Works with various screenshot formats
5. **No Manual Cropping**: Users don't need to crop images
6. **Automatic Fallback**: Always tries to extract something useful

## Usage in Production

Users simply:
1. Take screenshot showing both photo and QR
2. Upload to "Profile Photo + QR" column
3. System automatically extracts clean images
4. No manual cropping or editing needed!
