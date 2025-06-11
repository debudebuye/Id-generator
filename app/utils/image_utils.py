from PIL import Image, ImageDraw, ImageFont
from typing import Tuple, List, Optional
import os
from ..config.settings import Config

def process_photo(photo_path: str, size: Tuple[int, int], remove_white: bool = False, remove_black: bool = False) -> Image.Image:
    """Process a photo with optional background removal."""
    img = Image.open(photo_path).convert("RGBA")
    img = img.resize(size, Image.Resampling.LANCZOS)

    if remove_white or remove_black:
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
    max_width: Optional[int] = None
) -> None:
    """Draw text with specified alignment and optional wrapping."""
    if max_width:
        lines = wrap_text(draw, text, font, max_width)
        y_offset = 0
        for line in lines:
            draw.text((position[0], position[1] + y_offset), line, font=font, fill=color)
            y_offset += font.size + 5
    else:
        text_width = draw.textlength(text, font=font)
        if align == "center":
            pos = (position[0] - text_width // 2, position[1])
        elif align == "right":
            pos = (position[0] - text_width, position[1])
        else:
            pos = position
        draw.text(pos, text, font=font, fill=color)

def draw_rotated_text(
    draw: ImageDraw.ImageDraw,
    text: str,
    position: Tuple[int, int],
    font: ImageFont.FreeTypeFont,
    color: Tuple[int, int, int] = (0, 0, 0),
    angle: int = 90
) -> None:
    """Draw text rotated by specified angle."""
    rotated_img = Image.new("RGBA", (300, 45), (255, 255, 255, 0))
    rotated_draw = ImageDraw.Draw(rotated_img)
    rotated_draw.text((0, 0), text, font=font, fill=color)
    rotated_img = rotated_img.rotate(angle, expand=True)
    return rotated_img, position 