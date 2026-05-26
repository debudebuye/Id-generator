# Drag and Drop Fix for Index Page

## Issue
Images could not be dragged and dropped into the upload sections on the index page. The UI showed drag-and-drop zones, but the JavaScript event handlers were missing.

## Root Cause
The index.html template had:
- ✅ CSS styling for drag-and-drop (`.dragover`, `.drop-zone-overlay`)
- ✅ HTML structure for drop zones
- ❌ **Missing JavaScript event handlers** for drag and drop events

## Solution
Added complete drag-and-drop event handlers to handle:
1. Preventing default browser drag behaviors
2. Visual feedback when dragging over drop zones
3. File handling when images are dropped
4. Validation to ensure only image files are accepted

## Changes Made

### File: `app/templates/index.html`

Added drag-and-drop event handlers after the file input handlers:

```javascript
// Drag and Drop handlers
// Prevent default drag behaviors on the whole document
['dragenter', 'dragover', 'dragleave', 'drop'].forEach(eventName => {
  document.body.addEventListener(eventName, preventDefaults, false);
});

function preventDefaults(e) {
  e.preventDefault();
  e.stopPropagation();
}

// Setup drag and drop for each section
setupDragAndDrop('photoSection', 'photo');
setupDragAndDrop('frontSection', 'front');
setupDragAndDrop('backSection', 'back');

function setupDragAndDrop(sectionId, imageType) {
  const section = document.getElementById(sectionId);
  if (!section) return;

  // Highlight drop zone when dragging over it
  ['dragenter', 'dragover'].forEach(eventName => {
    section.addEventListener(eventName, function() {
      section.classList.add('dragover');
    }, false);
  });

  ['dragleave', 'drop'].forEach(eventName => {
    section.addEventListener(eventName, function() {
      section.classList.remove('dragover');
    }, false);
  });

  // Handle dropped files
  section.addEventListener('drop', function(e) {
    const dt = e.dataTransfer;
    const files = dt.files;

    if (files.length > 0) {
      const file = files[0];
      
      // Check if it's an image
      if (!file.type.startsWith('image/')) {
        alert('Please drop an image file');
        return;
      }

      // Create a fake event object to pass to handleImageUpload
      const fakeEvent = {
        target: {
          files: [file]
        }
      };

      handleImageUpload(fakeEvent, imageType);
    }
  }, false);
}
```

## How It Works

### 1. Prevent Default Browser Behavior
```javascript
['dragenter', 'dragover', 'dragleave', 'drop'].forEach(eventName => {
  document.body.addEventListener(eventName, preventDefaults, false);
});
```
- Prevents browser from opening the image in a new tab
- Stops event propagation to parent elements

### 2. Visual Feedback
```javascript
['dragenter', 'dragover'].forEach(eventName => {
  section.addEventListener(eventName, function() {
    section.classList.add('dragover');
  }, false);
});
```
- Adds `dragover` class when dragging over drop zone
- CSS changes border color and background to indicate drop zone is active
- Shows "Drop Photo Here" overlay

### 3. File Handling
```javascript
section.addEventListener('drop', function(e) {
  const dt = e.dataTransfer;
  const files = dt.files;
  
  if (files.length > 0) {
    const file = files[0];
    
    // Validate it's an image
    if (!file.type.startsWith('image/')) {
      alert('Please drop an image file');
      return;
    }
    
    // Pass to existing upload handler
    handleImageUpload(fakeEvent, imageType);
  }
}, false);
```
- Extracts dropped files from `dataTransfer` object
- Validates file is an image type
- Reuses existing `handleImageUpload()` function
- Opens cropper modal automatically

## Features

✅ **Drag and drop support** for all three upload sections:
   - Profile Photo
   - Front ID Image
   - Back ID Image

✅ **Visual feedback** when dragging:
   - Border changes to green
   - Background highlights
   - "Drop Here" overlay appears

✅ **File validation**:
   - Only accepts image files
   - Shows alert if non-image file is dropped

✅ **Seamless integration**:
   - Uses existing `handleImageUpload()` function
   - Opens cropper modal automatically
   - Same workflow as clicking "Upload" button

## User Experience

### Before Fix
1. User drags image to upload section
2. Nothing happens ❌
3. User must click "Upload" button

### After Fix
1. User drags image to upload section
2. Drop zone highlights (green border + overlay) ✨
3. User drops image
4. Cropper modal opens automatically ✅
5. User can crop and apply

## Testing

### Test Case 1: Drag Photo
1. Drag an image file over "Profile Photo" section
2. **Expected**: Section highlights with green border and "Drop Photo Here" overlay
3. Drop the image
4. **Expected**: Cropper modal opens with the image

### Test Case 2: Drag Front ID
1. Drag an image file over "Front ID Image" section
2. **Expected**: Section highlights
3. Drop the image
4. **Expected**: Cropper modal opens

### Test Case 3: Drag Back ID
1. Drag an image file over "Back ID Image" section
2. **Expected**: Section highlights
3. Drop the image
4. **Expected**: Cropper modal opens

### Test Case 4: Invalid File
1. Drag a PDF or text file over any section
2. Drop the file
3. **Expected**: Alert message "Please drop an image file"

### Test Case 5: Multiple Files
1. Drag multiple images at once
2. Drop them
3. **Expected**: Only first image is processed

## Browser Compatibility

✅ Chrome/Edge (Chromium)
✅ Firefox
✅ Safari
✅ Opera

## CSS Classes Used

- `.dragover` - Applied when dragging over drop zone
- `.drop-zone-overlay` - Overlay that appears during drag
- `.drop-zone-text` - Text shown in overlay

## Related Files

- `app/templates/index.html` - Added drag-and-drop handlers
- Existing CSS already supports drag-and-drop styling
- Existing `handleImageUpload()` function handles file processing

## Future Enhancements

1. **Multiple file upload**: Allow dropping multiple images at once
2. **Progress indicator**: Show upload progress for large files
3. **Drag preview**: Show thumbnail while dragging
4. **Paste support**: Allow pasting images from clipboard
5. **URL support**: Allow dropping image URLs
