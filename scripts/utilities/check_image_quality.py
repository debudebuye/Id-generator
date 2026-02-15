"""
Check uploaded image quality and suggest improvements
"""
import cv2
import sys
import os

def check_image_quality(image_path):
    """Check if image is suitable for OCR"""
    print(f"\n{'='*60}")
    print(f"Checking image: {os.path.basename(image_path)}")
    print(f"{'='*60}")
    
    # Read image
    img = cv2.imread(image_path)
    if img is None:
        print("❌ Could not read image!")
        return False
    
    # Get dimensions
    height, width = img.shape[:2]
    print(f"📐 Dimensions: {width}x{height} pixels")
    
    # Check resolution
    min_width = 800
    min_height = 600
    if width < min_width or height < min_height:
        print(f"⚠️  Resolution too low! Recommended: at least {min_width}x{min_height}")
        print(f"   Current: {width}x{height}")
    else:
        print(f"✅ Resolution: Good")
    
    # Check if image is too small
    if width < 400 or height < 300:
        print("❌ Image is too small for reliable OCR")
        return False
    
    # Convert to grayscale
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    
    # Check brightness
    mean_brightness = gray.mean()
    print(f"💡 Brightness: {mean_brightness:.1f}/255")
    if mean_brightness < 50:
        print("⚠️  Image is too dark")
    elif mean_brightness > 200:
        print("⚠️  Image is too bright (overexposed)")
    else:
        print("✅ Brightness: Good")
    
    # Check contrast
    std_dev = gray.std()
    print(f"🎨 Contrast: {std_dev:.1f}")
    if std_dev < 30:
        print("⚠️  Low contrast - text may be hard to read")
    else:
        print("✅ Contrast: Good")
    
    # Check blur (Laplacian variance)
    laplacian = cv2.Laplacian(gray, cv2.CV_64F)
    blur_score = laplacian.var()
    print(f"🔍 Sharpness: {blur_score:.1f}")
    if blur_score < 100:
        print("⚠️  Image is blurry - may affect OCR accuracy")
    else:
        print("✅ Sharpness: Good")
    
    # Overall assessment
    print(f"\n{'='*60}")
    issues = []
    if width < min_width or height < min_height:
        issues.append("Low resolution")
    if mean_brightness < 50 or mean_brightness > 200:
        issues.append("Poor brightness")
    if std_dev < 30:
        issues.append("Low contrast")
    if blur_score < 100:
        issues.append("Blurry")
    
    if not issues:
        print("✅ Overall: Image quality is GOOD for OCR")
        return True
    else:
        print(f"⚠️  Overall: Image has issues: {', '.join(issues)}")
        print("\n💡 Suggestions:")
        print("   - Use a higher resolution camera/scanner")
        print("   - Ensure good lighting (natural light is best)")
        print("   - Hold camera steady to avoid blur")
        print("   - Place ID card on flat, contrasting background")
        print("   - Avoid shadows and reflections")
        return False

if __name__ == "__main__":
    # Check the uploaded images
    static_folder = os.path.join(os.path.dirname(__file__), 'app', 'static')
    
    images_to_check = [
        'photo_cropped.png',
        'front_cropped.png',
        'back_cropped.png'
    ]
    
    for img_name in images_to_check:
        img_path = os.path.join(static_folder, img_name)
        if os.path.exists(img_path):
            check_image_quality(img_path)
        else:
            print(f"\n❌ Image not found: {img_name}")
    
    print(f"\n{'='*60}")
    print("Image quality check complete!")
    print(f"{'='*60}\n")
