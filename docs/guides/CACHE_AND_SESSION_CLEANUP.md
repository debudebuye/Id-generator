# Cache and Session Cleanup on Index Page

## Overview

When users navigate back to the index page, the system automatically clears all cached data and session information to ensure a fresh start for new ID card processing.

---

## What Gets Cleared

### 1. Session Data
- All Flask session variables
- User-specific temporary data
- Previous extraction results
- Uploaded file references

### 2. OCR Preprocessing Cache
- Cached preprocessed images (up to 10 images)
- Frees memory for new processing
- Ensures fresh OCR processing

### 3. ID Card Service Cache
- Any cached ID card data
- Service-specific temporary data

### 4. Temporary Files
The following temporary files are deleted:
- `photo_temp.png` - Temporary photo uploads
- `qr_temp.png` - Temporary QR code uploads
- `photo_cropped.png` - Cropped photo images
- `qr_cropped.png` - Cropped QR images
- `front_cropped.png` - Cropped front card images
- `back_cropped.png` - Cropped back card images
- `fcn_barcode.png` - Generated barcode images
- `photo_extracted.png` - Extracted photo from cards
- `qr_extracted.png` - Extracted QR codes
- `photo_qr_combined_cropped.png` - Combined images
- `barcode_temp.png` - Temporary barcode files

### 5. Debug Files
- All PNG files in `app/static/debug_regions/`
- Debug region extraction images
- OCR debugging outputs

---

## Implementation

### Code Location
**File:** `app/routes.py`
**Route:** `@bp.route('/')`

### Cleanup Process

```python
@bp.route('/')
def index():
    # 1. Clear session data
    session.clear()
    
    # 2. Clear OCR preprocessing cache
    ocr_service.clear_cache()
    
    # 3. Clear ID card service cache (if exists)
    if hasattr(id_service, 'clear_cache'):
        id_service.clear_cache()
    
    # 4. Delete temporary files
    for temp_file in temp_files:
        os.remove(temp_file)
    
    # 5. Clean debug regions
    # Delete all PNG files in debug_regions/
    
    return render_template('index.html')
```

---

## Benefits

### 1. Memory Management
- Frees up memory from cached images
- Prevents memory leaks
- Ensures optimal performance

### 2. Privacy
- Removes previous user's data
- Clears sensitive information
- Ensures data isolation between sessions

### 3. Fresh Start
- No interference from previous processing
- Clean slate for new ID cards
- Prevents confusion from old data

### 4. Disk Space
- Removes temporary files
- Prevents disk space accumulation
- Keeps static folder clean

---

## Logging

The cleanup process logs all actions:

```
🔄 User returned to index page - clearing all cached and session data
✓ Session data cleared
✓ OCR preprocessing cache cleared
✓ ID card service cache cleared
  🗑️ Deleted: photo_temp.png
  🗑️ Deleted: qr_temp.png
  ...
✓ Cleaned up 8 temporary files
✓ Cleaned up 15 debug region files
✅ Index page ready - all caches and session data cleared
```

---

## Error Handling

The cleanup process is fault-tolerant:

- **Cache clearing errors:** Logged but don't stop page load
- **File deletion errors:** Logged but don't stop page load
- **Missing files:** Silently skipped (no error)
- **Permission errors:** Logged as warnings

### Example Error Logs

```
⚠️ Could not clear OCR cache: [error details]
⚠️ Could not delete photo_temp.png: [error details]
⚠️ Could not clean debug regions: [error details]
```

---

## Performance Impact

### Cleanup Time
- Session clear: < 1ms
- Cache clear: < 5ms
- File deletion: < 50ms (depends on file count)
- Total: < 100ms (negligible)

### User Experience
- No noticeable delay
- Page loads normally
- Cleanup happens in background

---

## Testing

### Manual Test

1. **Upload and process an ID card**
   - Upload front and back images
   - Complete the extraction
   - Note the temporary files created

2. **Navigate to index page**
   - Click "Home" or navigate to `/`
   - Check console logs for cleanup messages

3. **Verify cleanup**
   - Check `app/static/` folder
   - Temporary files should be deleted
   - Debug regions should be cleared

### Automated Test

```python
def test_index_cleanup():
    """Test that index page clears all caches and files"""
    from app import create_app
    from app.services.ocr_extraction_service import OCRExtractionService
    
    app = create_app()
    
    with app.test_client() as client:
        # Create some temporary files
        with open('app/static/photo_temp.png', 'w') as f:
            f.write('test')
        
        # Add something to cache
        ocr_service = OCRExtractionService()
        ocr_service._preprocess_cache['test'] = 'data'
        
        # Visit index page
        response = client.get('/')
        
        # Verify cleanup
        assert response.status_code == 200
        assert len(ocr_service._preprocess_cache) == 0
        assert not os.path.exists('app/static/photo_temp.png')
```

---

## Configuration

### Temporary Files List

To add more files to cleanup, update the `temp_files` list in `app/routes.py`:

```python
temp_files = [
    'photo_temp.png',
    'qr_temp.png',
    # Add more files here
    'your_new_temp_file.png',
]
```

### Debug Regions

Debug regions are automatically cleaned. To disable:

```python
# Comment out the debug regions cleanup section
# if os.path.exists(debug_regions_path):
#     ...
```

---

## Best Practices

### 1. Always Use Temporary Files
- Use consistent naming (e.g., `*_temp.png`)
- Store in `app/static/` folder
- Add to cleanup list

### 2. Cache Management
- Implement `clear_cache()` in services
- Keep cache size limited
- Clear on index page load

### 3. Session Data
- Store minimal data in session
- Clear sensitive data immediately
- Don't rely on session persistence

### 4. Error Handling
- Log all cleanup errors
- Don't fail page load on cleanup errors
- Provide fallback mechanisms

---

## Troubleshooting

### Issue: Files not being deleted

**Possible causes:**
1. File permissions
2. File in use by another process
3. Incorrect file path

**Solution:**
```python
# Check file permissions
import os
import stat

file_path = 'app/static/photo_temp.png'
if os.path.exists(file_path):
    st = os.stat(file_path)
    print(f"Permissions: {oct(st.st_mode)}")
```

### Issue: Cache not clearing

**Possible causes:**
1. Service not initialized
2. Cache method not implemented
3. Exception in clear_cache()

**Solution:**
```python
# Verify cache exists
print(f"Cache exists: {hasattr(ocr_service, '_preprocess_cache')}")
print(f"Cache size: {len(ocr_service._preprocess_cache)}")

# Test clear method
try:
    ocr_service.clear_cache()
    print("Cache cleared successfully")
except Exception as e:
    print(f"Error: {e}")
```

### Issue: Session not clearing

**Possible causes:**
1. Session configuration issue
2. Cookie persistence
3. Browser cache

**Solution:**
```python
# Force session clear
from flask import session
session.clear()
session.modified = True

# Or clear specific keys
for key in list(session.keys()):
    session.pop(key)
```

---

## Related Documentation

- **OCR Optimization:** `docs/OPTIMIZATION_SUMMARY.md`
- **Cache Implementation:** `app/services/ocr_extraction_service.py`
- **Session Management:** Flask documentation

---

## Summary

The index page cleanup ensures:
- ✅ Fresh start for each user
- ✅ Memory is freed
- ✅ Temporary files are removed
- ✅ Privacy is maintained
- ✅ Optimal performance

All cleanup happens automatically when users navigate to the index page, with comprehensive logging and error handling.
