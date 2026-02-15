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