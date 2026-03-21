"""
Run this script to save the full PDF page as a high-res image.
Then open the saved image in Paint or any editor, hover over the
FAN number and barcode corners, and note the pixel coordinates.
"""
import fitz
from PIL import Image
import io

pdf_path = input("Drag your PDF here and press Enter (or type path): ").strip().strip('"')

doc = fitz.open(pdf_path)
page = doc[0]

# Render at 3x zoom
mat = fitz.Matrix(3.0, 3.0)
pix = page.get_pixmap(matrix=mat)
img = Image.open(io.BytesIO(pix.tobytes("png")))
w, h = img.size

out_path = "debug_full_page.png"
img.save(out_path)
doc.close()

print(f"\n✅ Saved: {out_path}")
print(f"   Image size: {w} x {h} pixels")
print(f"\nOpen '{out_path}' in Paint:")
print("  1. Hover over TOP-LEFT of the FAN number digits → note X, Y")
print("  2. Hover over BOTTOM-RIGHT of the barcode → note X, Y")
print("  3. Tell those 4 numbers to Kiro")
