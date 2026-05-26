# Image Cropper Usage Guide

## ✅ Fixed Issues

The cropper has been updated to allow independent movement of the crop box and image.

## 🎮 How to Use the Cropper

### Basic Controls

1. **Move Crop Box**
   - Click and drag inside the crop box to move it
   - The crop box moves independently from the image

2. **Resize Crop Box**
   - Drag the corners to resize
   - Drag the edges to resize in one direction
   - Maintains aspect ratio (1:1 for photo, 16:10 for ID cards)

3. **Move Image**
   - Click the "Move Image" button to switch to move mode
   - Now you can drag the image behind the crop box
   - Click "Crop Mode" to switch back

4. **Double-Click Toggle**
   - Double-click anywhere to toggle between crop and move modes
   - Quick way to switch without using the button

### Advanced Controls

- **Rotate Left** - Rotate image 90° counter-clockwise
- **Rotate Right** - Rotate image 90° clockwise
- **Reset** - Reset to original image and crop area
- **Apply Crop** - Save the cropped image

### Mouse Controls

- **Scroll Wheel** - Zoom in/out on the image
- **Drag** - Move crop box (crop mode) or image (move mode)
- **Drag Corners** - Resize crop box
- **Double-Click** - Toggle crop/move mode

## 🎯 Cropper Settings

### Current Configuration

```javascript
viewMode: 0          // Crop box can extend beyond canvas
dragMode: 'crop'     // Start in crop mode
cropBoxMovable: true // Crop box can be moved
cropBoxResizable: true // Crop box can be resized
movable: true        // Image can be moved
zoomable: true       // Image can be zoomed
zoomOnWheel: true    // Zoom with mouse wheel
```

### Aspect Ratios

- **Photo**: 1:1 (square)
- **Front ID**: 16:10 (ID card ratio)
- **Back ID**: 16:10 (ID card ratio)

## 💡 Tips

1. **For Best Results:**
   - Start with crop mode to position the crop box
   - Switch to move mode to adjust image position
   - Use zoom to get the perfect framing

2. **Quick Workflow:**
   - Upload image
   - Drag crop box to desired area
   - Double-click to move image if needed
   - Adjust size by dragging corners
   - Click "Apply Crop"

3. **If Crop Box is Too Small:**
   - Click "Reset" to start over
   - Drag corners to make it larger
   - Use zoom to see details better

## 🐛 Troubleshooting

### Crop Box Won't Move
- Make sure you're in crop mode (button should say "Move Image")
- Click inside the crop box and drag
- Try double-clicking to toggle modes

### Image Won't Move
- Click "Move Image" button or double-click
- Button should change to "Crop Mode"
- Now drag the image

### Can't Resize Crop Box
- Make sure you're dragging the corners or edges
- The crop box maintains aspect ratio
- Try resetting if it's stuck

## 🎨 Visual Indicators

- **Crop Mode**: Button shows "Move Image" (gray)
- **Move Mode**: Button shows "Crop Mode" (green)
- **Crop Box**: Highlighted area with handles
- **Grid Lines**: Help with alignment
- **Center Cross**: Shows center of crop area

## ⌨️ Keyboard Shortcuts

While the cropper is open:
- **ESC** - Close cropper without saving
- **Double-Click** - Toggle crop/move mode

## 📱 Mobile Support

On mobile devices:
- Touch and drag to move crop box
- Pinch to zoom
- Tap corners to resize
- Double-tap to toggle modes

---

**Updated:** 2025
**Version:** 2.0.0
