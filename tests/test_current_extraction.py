"""
Test current extraction from the uploaded images
"""
import os
import sys

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Set Tesseract path
import pytesseract
pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'

# Now import the service directly
import cv2
import numpy as np
from PIL import Image
import re

# Import just what we need
from app.services.ocr_extraction_service import OCRExtractionService

# Test with the current uploaded images
front_image = r"app\static\front_cropped.png"
back_image = r"app\static\back_cropped.png"

print("=" * 70)
print("Testing Current Extraction")
print("=" * 70)
print()

service = OCRExtractionService()

print("FRONT CARD EXTRACTION:")
print("-" * 70)
front_data = service.parse_front_card_data("", front_image)
print()
print("Extracted Front Data:")
for key, value in front_data.items():
    print(f"  {key}: '{value}'")

print()
print()
print("BACK CARD EXTRACTION:")
print("-" * 70)
back_data = service.parse_back_card_data("", back_image)
print()
print("Extracted Back Data:")
for key, value in back_data.items():
    print(f"  {key}: '{value}'")

print()
print("=" * 70)
print("SUMMARY:")
print("=" * 70)
front_filled = sum(1 for v in front_data.values() if v)
back_filled = sum(1 for v in back_data.values() if v)
total_filled = front_filled + back_filled
total_fields = len(front_data) + len(back_data)

print(f"Front Card: {front_filled}/{len(front_data)} fields extracted")
print(f"Back Card: {back_filled}/{len(back_data)} fields extracted")
print(f"Total: {total_filled}/{total_fields} fields extracted")
print(f"Success Rate: {(total_filled/total_fields)*100:.1f}%")
