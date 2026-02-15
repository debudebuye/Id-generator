from PIL import Image, ImageDraw, ImageFont
from typing import Tuple, List, Optional
import os
from ..config.settings import Config

def process_photo(photo_path: str, size: Tuple[int, int], remove_white: bool = False, remove_black: bool = False, use_onnx: bool = False) -> Image.Image:
    """Process a photo with optional background removal.
    
    Args:
        photo_path: Path to the photo file
        size: Target size for the photo
        remove_white: Whether to remove white backgrounds
        remove_black: Whether to remove black backgrounds
        use_onnx: Whether to use ONNX-based background removal
    """
    img = Image.open(photo_path).convert("RGBA")
    img = img.resize(size, Image.Resampling.LANCZOS)

    if use_onnx:
        # Use offline rembg-based background removal
        try:
            from ..services.offline_bg_removal import remove_background_offline
            result_img = remove_background_offline(photo_path)
            if result_img is not None:
                img = result_img.resize(size, Image.Resampling.LANCZOS)
                print("✅ Offline background removal completed successfully")
            else:
                print("⚠️ Offline background removal failed, using simple method")
                if remove_white or remove_black:
                    img = _simple_background_removal(img, remove_white, remove_black)
        except Exception as e:
            print(f"❌ Offline background removal failed: {str(e)}, using simple method")
            if remove_white or remove_black:
                img = _simple_background_removal(img, remove_white, remove_black)
    elif remove_white or remove_black:
        # Use simple color-based background removal
        img = _simple_background_removal(img, remove_white, remove_black)

    return img

def _simple_background_removal(img: Image.Image, remove_white: bool, remove_black: bool) -> Image.Image:
    """Simple color-based background removal."""
    data = img.getdata()
    new_data = []

    for pixel in data:
        r, g, b, a = pixel
        if remove_white and r > 200 and g > 200 and b > 200:
            new_data.append((255, 255, 255, 0))
        elif remove_black and r < 50 and g < 50 and b < 50:
            new_data.append((255, 255, 255, 0))
        else:
            new_data.append(pixel)

    img.putdata(new_data)
    return img

def wrap_text(draw: ImageDraw.ImageDraw, text: str, font: ImageFont.FreeTypeFont, max_width: int) -> List[str]:
    """Break text into lines that fit within max_width."""
    lines = []
    words = text.split()
    line = ""
    for word in words:
        test_line = f"{line} {word}".strip()
        width = draw.textlength(test_line, font=font)
        if width <= max_width:
            line = test_line
        else:
            lines.append(line)
            line = word
    if line:
        lines.append(line)
    return lines

def draw_text_with_alignment(
    draw: ImageDraw.ImageDraw,
    text: str,
    position: Tuple[int, int],
    font: ImageFont.FreeTypeFont,
    color: Tuple[int, int, int] = (0, 0, 0),
    align: str = "left",
    max_width: Optional[int] = None,
    bold: bool = False
) -> None:
    """Draw text with specified alignment and optional wrapping."""
    if max_width:
        lines = wrap_text(draw, text, font, max_width)
        y_offset = 0
        for line in lines:
            x, y = position[0], position[1] + y_offset
            if bold:
                # Simple faux-bold by overdrawing with 1px offsets
                draw.text((x, y), line, font=font, fill=color)
                draw.text((x + 1, y), line, font=font, fill=color)
                draw.text((x, y + 1), line, font=font, fill=color)
                draw.text((x + 1, y + 1), line, font=font, fill=color)
            else:
                draw.text((x, y), line, font=font, fill=color)
            y_offset += font.size + 5
    else:
        text_width = draw.textlength(text, font=font)
        if align == "center":
            pos = (position[0] - text_width // 2, position[1])
        elif align == "right":
            pos = (position[0] - text_width, position[1])
        else:
            pos = position
        if bold:
            draw.text(pos, text, font=font, fill=color)
            draw.text((pos[0] + 1, pos[1]), text, font=font, fill=color)
            draw.text((pos[0], pos[1] + 1), text, font=font, fill=color)
            draw.text((pos[0] + 1, pos[1] + 1), text, font=font, fill=color)
        else:
            draw.text(pos, text, font=font, fill=color)

def draw_rotated_text(
    draw: ImageDraw.ImageDraw,
    text: str,
    position: Tuple[int, int],
    font: ImageFont.FreeTypeFont,
    color: Tuple[int, int, int] = (0, 0, 0),
    angle: int = 90,
    bold: bool = False
) -> None:
    """Draw text rotated by specified angle."""
    # Determine size needed for text to avoid clipping
    temp_img = Image.new("RGBA", (1, 1), (255, 255, 255, 0))
    temp_draw = ImageDraw.Draw(temp_img)
    bbox = temp_draw.textbbox((0, 0), text, font=font)
    # Add generous padding to avoid any clipping after rotation
    padding = 20
    width = max(1, (bbox[2] - bbox[0]) + padding)
    height = max(1, (bbox[3] - bbox[1]) + padding)
    rotated_img = Image.new("RGBA", (width, height), (255, 255, 255, 0))
    rotated_draw = ImageDraw.Draw(rotated_img)
    if bold:
        rotated_draw.text((0, 0), text, font=font, fill=color)
        rotated_draw.text((1, 0), text, font=font, fill=color)
        rotated_draw.text((0, 1), text, font=font, fill=color)
        rotated_draw.text((1, 1), text, font=font, fill=color)
    else:
        rotated_draw.text((0, 0), text, font=font, fill=color)
    rotated_img = rotated_img.rotate(angle, expand=True)
    return rotated_img, position 


def extract_photo_and_qr_from_combined(combined_image_path: str, output_dir: str) -> Tuple[Optional[str], Optional[str]]:
    """
    Extract profile photo and QR code from a combined image.
    Assumes the photo is in the upper portion and QR is in the lower portion.
    
    Args:
        combined_image_path: Path to the combined image containing both photo and QR
        output_dir: Directory to save the extracted images
        
    Returns:
        Tuple of (photo_path, qr_path) or (None, None) if extraction fails
    """
    try:
        # Open the combined image
        img = Image.open(combined_image_path)
        width, height = img.size
        
        print(f"📸 Combined image size: {width}x{height}")
        
        # Split the image into two parts
        # Look for content in top half and bottom half
        # Assuming roughly 50% for photo (top) and 50% for QR (bottom)
        split_ratio = 0.5
        split_point = int(height * split_ratio)
        
        # Extract photo (top portion) - take middle 70% to avoid UI elements
        top_margin = int(height * 0.05)  # Skip top 5%
        photo_height = split_point - top_margin - int(height * 0.05)  # Skip bottom 5% of top half
        
        photo_img = img.crop((0, top_margin, width, top_margin + photo_height))
        
        # Crop to center region to remove side UI elements
        photo_width = photo_img.size[0]
        photo_center_crop = int(photo_width * 0.15)  # Remove 15% from each side
        photo_img = photo_img.crop((photo_center_crop, 0, photo_width - photo_center_crop, photo_img.size[1]))
        
        photo_filename = 'photo_extracted.png'
        photo_path = os.path.join(output_dir, photo_filename)
        photo_img.save(photo_path, 'PNG')
        print(f"✓ Extracted photo: {photo_path} ({photo_img.size[0]}x{photo_img.size[1]})")
        
        # Extract QR code (bottom portion) - take middle 70% to avoid UI elements
        qr_start = split_point + int(height * 0.05)  # Skip top 5% of bottom half
        qr_end = height - int(height * 0.05)  # Skip bottom 5%
        
        qr_img = img.crop((0, qr_start, width, qr_end))
        
        # Crop to center region to remove side UI elements
        qr_width = qr_img.size[0]
        qr_center_crop = int(qr_width * 0.15)  # Remove 15% from each side
        qr_img = qr_img.crop((qr_center_crop, 0, qr_width - qr_center_crop, qr_img.size[1]))
        
        qr_filename = 'qr_extracted.png'
        qr_path = os.path.join(output_dir, qr_filename)
        qr_img.save(qr_path, 'PNG')
        print(f"✓ Extracted QR: {qr_path} ({qr_img.size[0]}x{qr_img.size[1]})")
        
        return photo_path, qr_path
        
    except Exception as e:
        print(f"❌ Error extracting photo and QR from combined image: {e}")
        return None, None


def detect_content_region(img_cv, margin_percent=0.05):
    """
    Detect the actual content region in an image, excluding borders/UI elements.
    
    Args:
        img_cv: OpenCV image (BGR format)
        margin_percent: Percentage of image to use as margin for detection
        
    Returns:
        Tuple of (x, y, w, h) for the content bounding box
    """
    import cv2
    import numpy as np
    
    height, width = img_cv.shape[:2]
    gray = cv2.cvtColor(img_cv, cv2.COLOR_BGR2GRAY)
    
    # Apply threshold to find content
    _, thresh = cv2.threshold(gray, 240, 255, cv2.THRESH_BINARY_INV)
    
    # Find contours
    contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    
    if not contours:
        # No content detected, return full image
        return 0, 0, width, height
    
    # Find the largest contour (likely the main content)
    largest_contour = max(contours, key=cv2.contourArea)
    x, y, w, h = cv2.boundingRect(largest_contour)
    
    # Add small margin
    margin_x = int(width * margin_percent)
    margin_y = int(height * margin_percent)
    
    x = max(0, x - margin_x)
    y = max(0, y - margin_y)
    w = min(width - x, w + 2 * margin_x)
    h = min(height - y, h + 2 * margin_y)
    
    return x, y, w, h


def detect_and_extract_photo_qr(combined_image_path: str, output_dir: str) -> Tuple[Optional[str], Optional[str]]:
    """
    Extract profile photo and QR code from a combined mobile screenshot.
    Uses exact coordinates based on 591x1280px reference image from Adobe.
    
    Args:
        combined_image_path: Path to the combined image containing both photo and QR
        output_dir: Directory to save the extracted images
        
    Returns:
        Tuple of (photo_path, qr_path) or (None, None) if extraction fails
    """
    print("🔍 Starting photo + QR extraction with exact coordinates...")
    
    try:
        pil_img = Image.open(combined_image_path)
        width, height = pil_img.size
        print(f"   📸 Image size: {width}x{height}")
        
        # Reference dimensions from Adobe (591x1280px)
        ref_width = 591
        ref_height = 1280
        
        # Calculate scaling factors
        scale_x = width / ref_width
        scale_y = height / ref_height
        
        print(f"   📐 Scale factors: x={scale_x:.3f}, y={scale_y:.3f}")
        
        # Photo coordinates from Adobe (X:158, Y:254, W:279, H:370)
        photo_x = int(158 * scale_x)
        photo_y = int(254 * scale_y)
        photo_w = int(279 * scale_x)
        photo_h = int(370 * scale_y)
        
        print(f"   📷 Photo region: x={photo_x}, y={photo_y}, w={photo_w}, h={photo_h}")
        
        # Extract photo
        photo_img = pil_img.crop((
            photo_x,
            photo_y,
            photo_x + photo_w,
            photo_y + photo_h
        ))
        
        photo_filename = 'photo_extracted.png'
        photo_path = os.path.join(output_dir, photo_filename)
        photo_img.save(photo_path, 'PNG')
        print(f"   ✓ Extracted photo: {photo_img.size}")
        
        # QR code coordinates from Adobe (X:110, Y:672, W:372, H:374)
        qr_x = int(110 * scale_x)
        qr_y = int(672 * scale_y)
        qr_w = int(372 * scale_x)
        qr_h = int(374 * scale_y)
        
        print(f"   🔲 QR region: x={qr_x}, y={qr_y}, w={qr_w}, h={qr_h}")
        
        # Extract QR
        qr_img = pil_img.crop((
            qr_x,
            qr_y,
            qr_x + qr_w,
            qr_y + qr_h
        ))
        
        qr_filename = 'qr_extracted.png'
        qr_path = os.path.join(output_dir, qr_filename)
        qr_img.save(qr_path, 'PNG')
        print(f"   ✓ Extracted QR: {qr_img.size}")
        
        print("✅ Extraction successful using exact coordinates")
        return photo_path, qr_path
        
    except Exception as e:
        print(f"   ❌ Extraction failed: {e}")
        import traceback
        traceback.print_exc()
        return None, None


def extract_photo_qr_with_detection(combined_image_path: str, output_dir: str) -> Tuple[Optional[str], Optional[str]]:
    """
    Advanced extraction using QR code detection and content analysis.
    Detects the actual QR code location and extracts clean regions by finding white/light content areas.
    
    Args:
        combined_image_path: Path to the combined image containing both photo and QR
        output_dir: Directory to save the extracted images
        
    Returns:
        Tuple of (photo_path, qr_path) or (None, None) if extraction fails
    """
    try:
        import cv2
        import numpy as np
        
        # Read image
        img = cv2.imread(combined_image_path)
        if img is None:
            print(f"❌ Could not read image: {combined_image_path}")
            return None, None
        
        height, width = img.shape[:2]
        print(f"📸 Combined image size: {width}x{height}")
        
        # Convert to grayscale
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        
        # Detect white/light regions (where photo and QR are displayed on white background)
        # Threshold to find bright areas (UI elements are typically dark)
        _, white_mask = cv2.threshold(gray, 200, 255, cv2.THRESH_BINARY)
        
        # Find contours of white regions
        contours, _ = cv2.findContours(white_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        # Filter contours by size and find the two largest (photo and QR regions)
        min_area = (width * height) * 0.05  # At least 5% of image
        large_contours = []
        
        for contour in contours:
            area = cv2.contourArea(contour)
            if area > min_area:
                x, y, w, h = cv2.boundingRect(contour)
                large_contours.append((x, y, w, h, area, y))  # Include y for sorting
        
        # Sort by y-coordinate (top to bottom)
        large_contours.sort(key=lambda c: c[5])
        
        photo_region = None
        qr_region = None
        
        if len(large_contours) >= 2:
            # First large white region is likely the photo
            photo_region = large_contours[0][:4]
            # Second large white region is likely the QR
            qr_region = large_contours[1][:4]
            print(f"✓ Detected photo region: x={photo_region[0]}, y={photo_region[1]}, w={photo_region[2]}, h={photo_region[3]}")
            print(f"✓ Detected QR region: x={qr_region[0]}, y={qr_region[1]}, w={qr_region[2]}, h={qr_region[3]}")
        elif len(large_contours) == 1:
            # Only one large region found, try to split it
            single_region = large_contours[0]
            x, y, w, h, _, _ = single_region
            split_y = y + h // 2
            photo_region = (x, y, w, h // 2)
            qr_region = (x, split_y, w, h // 2)
            print(f"⚠️ Only one region found, splitting it")
        
        # Try QR code detection for more precise QR extraction
        qr_detector = cv2.QRCodeDetector()
        retval, decoded_info, points, straight_qrcode = qr_detector.detectAndDecodeMulti(gray)
        
        if retval and points is not None and len(points) > 0:
            # QR code detected! Use precise bounding box
            qr_points = points[0].astype(int)
            x_coords = qr_points[:, 0]
            y_coords = qr_points[:, 1]
            
            qr_x = max(0, int(np.min(x_coords)) - 10)
            qr_y = max(0, int(np.min(y_coords)) - 10)
            qr_w = min(width - qr_x, int(np.max(x_coords) - np.min(x_coords)) + 20)
            qr_h = min(height - qr_y, int(np.max(y_coords) - np.min(y_coords)) + 20)
            
            qr_region = (qr_x, qr_y, qr_w, qr_h)
            print(f"✓ QR code precisely detected at: x={qr_x}, y={qr_y}, w={qr_w}, h={qr_h}")
        
        # Use PIL for extraction
        pil_img = Image.open(combined_image_path)
        
        # Extract photo
        if photo_region:
            x, y, w, h = photo_region
            # Add small margin to ensure clean extraction
            margin = 5
            photo_img = pil_img.crop((
                max(0, x + margin),
                max(0, y + margin),
                min(width, x + w - margin),
                min(height, y + h - margin)
            ))
        else:
            # Fallback: use top 45% of image
            photo_img = pil_img.crop((
                int(width * 0.1),
                int(height * 0.05),
                int(width * 0.9),
                int(height * 0.45)
            ))
        
        photo_filename = 'photo_extracted.png'
        photo_path = os.path.join(output_dir, photo_filename)
        photo_img.save(photo_path, 'PNG')
        print(f"✓ Extracted photo: {photo_path} ({photo_img.size[0]}x{photo_img.size[1]})")
        
        # Extract QR
        if qr_region:
            x, y, w, h = qr_region
            # Add small margin
            margin = 5
            qr_img = pil_img.crop((
                max(0, x + margin),
                max(0, y + margin),
                min(width, x + w - margin),
                min(height, y + h - margin)
            ))
        else:
            # Fallback: use bottom 45% of image
            qr_img = pil_img.crop((
                int(width * 0.1),
                int(height * 0.55),
                int(width * 0.9),
                int(height * 0.95)
            ))
        
        qr_filename = 'qr_extracted.png'
        qr_path = os.path.join(output_dir, qr_filename)
        qr_img.save(qr_path, 'PNG')
        print(f"✓ Extracted QR: {qr_path} ({qr_img.size[0]}x{qr_img.size[1]})")
        
        return photo_path, qr_path
        
    except ImportError:
        print("⚠️ OpenCV not available")
        return None, None
    except Exception as e:
        print(f"❌ Error in QR detection extraction: {e}")
        import traceback
        traceback.print_exc()
        return None, None


def extract_actual_content_from_card(card_image_path: str, is_qr: bool = False) -> Optional[Image.Image]:
    """
    Extract the actual photo or QR content from a card image, removing all UI elements.
    
    Args:
        card_image_path: Path to the card image
        is_qr: True if extracting QR code, False if extracting photo
        
    Returns:
        PIL Image of just the content, or None if extraction fails
    """
    try:
        import cv2
        import numpy as np
        
        # Read image
        img = cv2.imread(card_image_path)
        if img is None:
            return None
        
        height, width = img.shape[:2]
        
        if is_qr:
            # For QR code: detect the actual QR pattern
            gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
            
            # Try QR detection first
            qr_detector = cv2.QRCodeDetector()
            retval, decoded_info, points, straight_qrcode = qr_detector.detectAndDecodeMulti(gray)
            
            if retval and points is not None and len(points) > 0:
                # QR detected! Extract it with small margin
                qr_points = points[0].astype(int)
                x = max(0, int(np.min(qr_points[:, 0])) - 10)
                y = max(0, int(np.min(qr_points[:, 1])) - 10)
                w = min(width - x, int(np.max(qr_points[:, 0]) - np.min(qr_points[:, 0])) + 20)
                h = min(height - y, int(np.max(qr_points[:, 1]) - np.min(qr_points[:, 1])) + 20)
                
                # Extract QR region
                qr_region = img[y:y+h, x:x+w]
                return Image.fromarray(cv2.cvtColor(qr_region, cv2.COLOR_BGR2RGB))
            
            # Fallback: detect dark rectangular region (QR code)
            _, thresh = cv2.threshold(gray, 127, 255, cv2.THRESH_BINARY_INV)
            contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            
            # Find largest square-ish contour
            for contour in sorted(contours, key=cv2.contourArea, reverse=True):
                area = cv2.contourArea(contour)
                if area < (width * height * 0.1):  # At least 10% of image
                    continue
                
                x, y, w, h = cv2.boundingRect(contour)
                aspect_ratio = float(w) / h
                
                # QR codes are roughly square
                if 0.8 <= aspect_ratio <= 1.2:
                    # Add small margin
                    margin = 10
                    x = max(0, x - margin)
                    y = max(0, y - margin)
                    w = min(width - x, w + 2 * margin)
                    h = min(height - y, h + 2 * margin)

                    # Extract QR region
                    qr_region = img[y:y+h, x:x+w]
                    return Image.fromarray(cv2.cvtColor(qr_region, cv2.COLOR_BGR2RGB))
            
            # If no QR found, return None
            return None
        
        else:
            # For photo: detect face or largest content region
            gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
            
            # Try face detection
            face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
            faces = face_cascade.detectMultiScale(gray, 1.1, 4)
            
            if len(faces) > 0:
                # Use the largest face
                x, y, w, h = max(faces, key=lambda f: f[2] * f[3])
                
                # Add margin around face
                margin_x = int(w * 0.3)
                margin_y = int(h * 0.4)
                
                x = max(0, x - margin_x)
                y = max(0, y - margin_y)
                w = min(width - x, w + 2 * margin_x)
                h = min(height - y, h + 2 * margin_y)
                
                # Extract photo region
                photo_region = img[y:y+h, x:x+w]
                return Image.fromarray(cv2.cvtColor(photo_region, cv2.COLOR_BGR2RGB))
            
            # Fallback: detect content region using edge detection
            edges = cv2.Canny(gray, 50, 150)
            contours, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            
            if contours:
                # Find largest contour
                largest_contour = max(contours, key=cv2.contourArea)
                x, y, w, h = cv2.boundingRect(largest_contour)
                
                # Add small margin
                margin = 10
                x = max(0, x - margin)
                y = max(0, y - margin)
                w = min(width - x, w + 2 * margin)
                h = min(height - y, h + 2 * margin)
                
                # Extract content region
                content_region = img[y:y+h, x:x+w]
                return Image.fromarray(cv2.cvtColor(content_region, cv2.COLOR_BGR2RGB))
            
            # If nothing detected, return None
            return None
    
    except ImportError:
        print("⚠️ OpenCV not available for content extraction")
        return None
    except Exception as e:
        print(f"❌ Error extracting content: {e}")
        import traceback
        traceback.print_exc()
        return None
