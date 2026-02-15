# Updated Index Page with Image Cropping Feature

## Overview
The index page has been completely updated with image upload and cropping functionality for:
- Profile Photo
- Front ID Image
- Back ID Image

## New Features

### 1. Image Upload with Cropping
- Users can upload images for photo, front ID, and back ID
- Each image opens in a cropping modal with Cropper.js
- Features include:
  - Drag to reposition
  - Resize crop area
  - Rotate left/right
  - Reset to original
  - Apply crop

### 2. Real-time Preview
- Uploaded images show in preview boxes
- Cropped images are displayed immediately after applying crop
- Visual feedback for each upload section

### 3. Base64 Image Storage
- Cropped images are converted to base64
- Stored in hidden form fields
- Sent to backend with form submission

## Files Created

### 1. `app/templates/index_updated.html`
Complete new index page with:
- Modern responsive design
- Image upload sections for photo, front, and back
- Cropper.js integration
- Modal for image cropping
- Form validation

### 2. `app/routes_image_handler.py`
Helper functions for backend image processing:
- `save_cropped_image()` - Saves base64 images to disk
- `handle_cropped_images_in_generate_id()` - Processes uploaded images

## Integration Steps

### Step 1: Update Routes
Add to your `app/routes.py` in the `generate_id()` function:

```python
from .routes_image_handler import handle_cropped_images_in_generate_id, save_cropped_image

@bp.route('/generate_id', methods=['POST'])
def generate_id():
    # ... existing validation code ...
    
    # Add this after FIN validation:
    uploaded_images = handle_cropped_images_in_generate_id()
    
    # Store image paths in extracted data
    if uploaded_images['photo']:
        extracted['photo_path'] = uploaded_images['photo']
    if uploaded_images['front']:
        extracted['front_path'] = uploaded_images['front']
    if uploaded_images['back']:
        extracted['back_path'] = uploaded_images['back']
    
    # ... rest of your code ...
```

### Step 2: Replace Index Page
```bash
# Backup original
copy app\templates\index.html app\templates\index_backup.html

# Use new version
copy app\templates\index_updated.html app\templates\index.html
```

### Step 3: Test the Features
1. Start your Flask app
2. Navigate to the index page
3. Upload images for photo, front, and back
4. Test cropping functionality
5. Submit form and verify images are saved

## Technical Details

### Frontend Technologies
- **Cropper.js v1.6.1** - Image cropping library
- **Font Awesome 6.4.0** - Icons
- **Inter Font** - Typography

### Image Processing
- Max image size: 10MB
- Output format: JPEG (90% quality)
- Max dimensions: 1200x1200px
- Aspect ratios:
  - Photo: 1:1 (square)
  - Front/Back: 16:10 (ID card ratio)

### Browser Compatibility
- Modern browsers (Chrome, Firefox, Safari, Edge)
- Requires JavaScript enabled
- FileReader API support

## Customization Options

### Change Aspect Ratios
In `index_updated.html`, modify the cropper initialization:

```javascript
cropper = new Cropper(cropImage, {
    aspectRatio: currentImageType === 'photo' ? 1 : 16 / 10, // Change these values
    // ... other options
});
```

### Change Image Quality
Modify the `applyCrop()` function:

```javascript
const croppedImageData = canvas.toDataURL('image/jpeg', 0.9); // 0.9 = 90% quality
```

### Add More Image Types
1. Add new upload section in HTML
2. Add new input handler in JavaScript
3. Add new hidden field for cropped data
4. Update backend handler

## Troubleshooting

### Images Not Saving
- Check `STATIC_FOLDER` path in config
- Verify write permissions
- Check console for errors

### Cropper Not Working
- Verify Cropper.js CDN is accessible
- Check browser console for errors
- Ensure image file is valid

### Form Not Submitting
- Check FIN validation (must be 12 digits)
- Verify document is uploaded
- Check browser console for JavaScript errors

## Next Steps

1. **Integrate with ID Generation**
   - Use uploaded images in ID card generation
   - Replace default photo with uploaded photo
   - Use front/back images as needed

2. **Add Image Validation**
   - Face detection for photos
   - ID card detection for front/back
   - Image quality checks

3. **Enhance UX**
   - Add loading indicators
   - Show upload progress
   - Add image preview zoom

4. **Security**
   - Add CSRF protection
   - Validate image content
   - Sanitize filenames
   - Limit upload rate

## Support
For issues or questions, check:
- Browser console for JavaScript errors
- Flask logs for backend errors
- Network tab for failed requests
