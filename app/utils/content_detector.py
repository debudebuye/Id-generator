"""
Advanced content detection for extracting clean photo and QR from screenshots
"""
import cv2
import numpy as np
from PIL import Image
from typing import Tuple, Optional
import os


def find_largest_content_box(img_cv, min_area_percent=0.05):
    """
    Find the largest content box in an image region.
    
    Args:
        img_cv: OpenCV image (BGR)
        min_area_percent: Minimum area as percentage of total image
        
    Returns:
        Tuple of (x, y, w, h) or None
    """
    height, width = img_cv.shape[:2]
    gray = cv2.cvtColor(img_cv, cv2.COLOR_BGR2GRAY)
  