from PIL import Image, ImageDraw, ImageFont, ImageStat, ImageFilter
import json
import os
import numpy as np
import barcode
from barcode.writer import ImageWriter
from typing import Dict, Optional, Tuple, List
import random
import fitz # PyMuPDF
from datetime import datetime, date # Needed for dob parsing in new logic
import time # For performance optimization
from dateutil.relativedelta import relativedelta # Added for date calculations
from io import BytesIO
from concurrent.futures import ThreadPoolExecutor
from io import BytesIO
import qrcode

from ..config.settings import Config
from ..utils.image_utils import process_photo, draw_text_with_alignment, draw_rotated_text
from ..utils.date_utils import get_id_dates, gregorian_to_ethiopian # Added gregorian_to_ethiopian
from .offline_bg_removal import remove_background_offline, remove_background_to_bytes_offline

# Configure Tesseract OCR path for Windows
try:
    import pytesseract
    import platform
    if platform.system() == 'Windows':
        # Set the path to tesseract executable
        pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'
except ImportError:
    pass

class IDCardService:
    # PDF_FORMAT_MAPPING defines line indices for default and image indices for all.
    # Residential Addis and Sheger now explicitly define image indices.
    # For residential formats, line numbers in mapping are illustrative as pattern-based parsing is used.
    PDF_FORMAT_MAPPING = {
        'default': {
            'fcn': 0,
            'name': 2,        # Name value line (after First, Middle, Surname label)
            'region': 4,      # Region value line (after Region/City Admin label)
            'dob': 6,         # Date of Birth value line (after Date of Birth label)
            'subcity': 8,     # Zone/Sub City value line (after Zone/Sub City label)
            'gender': 10,     # Sex value line (after Sex label)
            'woreda': 12,     # Woreda value line (after Woreda label)
            'nationality': 14, # Nationality value line (after Nationality label)
            'phone': 16,      # Phone value line (after Phone label)
            'photo_img_index': 1, # Index in images list for photo
            'qr_img_index': 2 # Index in images list for QR
        },

        'residential_sheger': {
            'fcn': 0,
            'name': 1,
            'dob': 2,
            'gender': 3,
            'nationality': 4,
            'phone': 5,
            'region': 6,
            'subcity': 7,
            'woreda': 8,
            'photo_img_index': 0, # Based on user's snippet for residential
            'qr_img_index': 1 # Based on user's snippet for residential
        },
        
        'demographic_format': {
            'fcn': 0,
            'name': 1,
            'dob': 2,
            'gender': 3,
            'nationality': 4,
            'phone': 5,
            'region': 6,
            'subcity': 7,
            'woreda': 8,
            'photo_img_index': 0, # Same as residential for now
            'qr_img_index': 1 # Same as residential for now
        },
        
        'compact_format': {
            'fcn': 0,
            'name': 1,
            'dob': 2,
            'gender': 3,
            'nationality': 4,
            'region': 5,
            'subcity': 6,
            'woreda': 7,
            'phone': 8,
            'photo_img_index': 0, # Compact format image positioning
            'qr_img_index': 1 # Compact format QR positioning
        },

        'large_format': {
            'fcn': 0,
            'name': 1,
            'dob': 2,
            'gender': 3,
            'nationality': 4,
            'phone': 5,
            'region': 6,
            'subcity': 7,
            'woreda': 8,
            'photo_img_index': 0,
            'qr_img_index': 1
        }
    }

    def __init__(self):
        self.config = Config()
        
    def cleanup_old_images(self, keep_current_files: List[str] = None):
        """Clean up old generated ID images to prevent disk space issues.
        
        Args:
            keep_current_files: List of current file names to keep (optional)
        """
        try:
            static_folder = self.config.STATIC_FOLDER
            if not os.path.exists(static_folder):
                return
                
            # Define patterns for files to clean up
            cleanup_patterns = [
                '*_Front_Color.png',
                '*_Front_Grayscale.png', 
                '*_Reverse_Color.png',
                '*_Reverse_Grayscale.png',
                '*_Mini_Front_Color.png',
                '*_Mini_Front_Grayscale.png',
                '*_Old_Front_Color.png',
                '*_Old_Front_Grayscale.png',
                '*_Old_Reverse_Color.png',
                '*_Old_Reverse_Grayscale.png'
            ]
            
            # Keep essential files
            keep_files = {
                'fcn_barcode.png',
                'photo_temp.png',
                'qr_temp.png'
            }
            
            # Add current files to keep list
            if keep_current_files:
                keep_files.update(keep_current_files)
            
            import glob
            total_cleaned = 0
            total_size_cleaned = 0
            
            for pattern in cleanup_patterns:
                files = glob.glob(os.path.join(static_folder, pattern))
                for file_path in files:
                    filename = os.path.basename(file_path)
                    
                    # Skip if this is a file we want to keep
                    if filename in keep_files:
                        continue
                        
                    try:
                        # Get file size before deletion
                        file_size = os.path.getsize(file_path)
                        
                        # Remove the file
                        os.remove(file_path)
                        total_cleaned += 1
                        total_size_cleaned += file_size
                        
                        print(f"Cleaned up: {filename} ({file_size / (1024*1024):.2f} MB)")
                        
                    except Exception as e:
                        print(f"Error cleaning up {filename}: {str(e)}")
            
            if total_cleaned > 0:
                print(f"✅ Cleanup completed: {total_cleaned} files removed, {total_size_cleaned / (1024*1024):.2f} MB freed")
            else:
                print("ℹ️ No old files to clean up")
                
        except Exception as e:
            print(f"Error during cleanup: {str(e)}")
    
    def manual_cleanup(self):
        """Manually trigger cleanup of all old generated images."""
        print("🧹 Starting manual cleanup of old generated images...")
        self.cleanup_old_images()
        print("✅ Manual cleanup completed!")
        
    def generate_serial_number(self) -> str:
        """Generate a 7-digit number not starting with 0."""
        return str(random.randint(7000000, 19999999))
    
    def format_phone_number(self, local_number: str) -> str:
        """Convert Ethiopian local number to international format."""
        number = local_number.strip().replace(" ", "")
        
        if number.startswith('0') and len(number) == 10:
            number = '+251' + number[1:]
        elif number.startswith('+251') and len(number) == 13:
            pass
        else:
            return local_number
            
        if number.startswith('+251') and len(number) == 13:
            return f"{number[:4]} {number[4:7]} {number[7:10]} {number[10:]}"
        
        return number
    
    def generate_barcode(self, fcn: str) -> Tuple[Optional[str], Optional[str]]:
        """Generate barcode for FCN number."""
        try:
            # Ensure we have exactly 16 digits
            if len(fcn) != self.config.FCN_LENGTH or not fcn.isdigit():
                raise ValueError("FCN must be 16 digits")
            
            clean_fcn = ''.join(c for c in fcn if c.isalnum())
            formatted_fcn_text = ' '.join([clean_fcn[i:i+4] for i in range(0, len(clean_fcn), 4)])
            
            fcn_barcode = barcode.get('code128', clean_fcn, writer=ImageWriter())
            barcode_filename = 'fcn_barcode.png' 
            barcode_full_path = os.path.join(self.config.STATIC_FOLDER, barcode_filename)
            
            fcn_barcode.save(barcode_full_path[:-4], options=self.config.BARCODE_OPTIONS)
            return barcode_filename, formatted_fcn_text
            
        except Exception as e:
            print(f"Barcode generation error: {str(e)}")
            return None, None

    def _parse_line(self, lines: List[str], index: int) -> Tuple[str, str]:
        """Helper to safely parse a line for Amharic and English parts."""
        try:
            print(f"    _parse_line called with index {index}, lines length: {len(lines)}")
            if index >= len(lines):
                print(f"    Index {index} out of range, returning empty strings")
                return "", ""
            
            line = lines[index].strip()
            print(f"    Line {index}: '{line}'")
            
            if not line:
                print(f"    Empty line, returning empty strings")
                return "", ""
            
            if '|' in line:
                parts = line.split('|', 1)
                print(f"    Split into {len(parts)} parts: {parts}")
                if len(parts) == 2:
                    result = parts[0].strip(), parts[1].strip()
                    print(f"    Returning: '{result[0]}' | '{result[1]}'")
                    return result
                else:
                    result = parts[0].strip(), parts[0].strip()
                    print(f"    Returning same for both: '{result[0]}' | '{result[1]}'")
                    return result
            
            # Handle single language lines - try to determine if it's Amharic or English
            # If it contains non-ASCII characters, it's likely Amharic
            if any(ord(c) > 127 for c in line):
                print(f"    No separator found, detected Amharic: '{line}' | '{line}'")
                return line, line  # Return same for both (Amharic detected)
            else:
                print(f"    No separator found, detected English: '{line}' | '{line}'")
                return line, line  # Return same for both (English detected)
        except IndexError as e:
            print(f"    IndexError in _parse_line: {str(e)}")
            return "", ""
        except Exception as e:
            print(f"    Unexpected error in _parse_line: {str(e)}")
            return "", ""

    def _is_valid_nationality_value(self, text):
        """Check if a text looks like a valid nationality value"""
        if not text or len(text.strip()) == 0:
            return False
        
        text = text.strip()
        
        # Basic length check - nationality shouldn't be too long or too short
        if len(text) < 2 or len(text) > 50:
            return False
        
        # Should not contain numbers (except maybe in rare cases)
        if any(char.isdigit() for char in text):
            return False
        
        # Should not contain too many special characters
        special_chars = sum(1 for char in text if not char.isalnum() and char not in [' ', '-', '.', "'"])
        if special_chars > 2:
            return False
        
        # Should not be too many words (max 3 words like "United States of America")
        words = text.split()
        if len(words) > 4:
            return False
        
        # Skip lines that are clearly not nationality values
        # Enhanced exclusion list with label indicators
        excluded_keywords = [
            "ክልል", "region", "ወረዳ", "woreda", "ከተማ", "city", "ስልክ", "phone", 
            "የትውልድ", "birth", "ቀን", "date", "ፕሮግራም", "program", "ፆታ", "sex",
            "መታወቂያ", "identity", "addis", "ababa", 
            "zone", "kebele", "address", "number", "card", "id",
            "self declared", "በተለያዩ መሰረት", "(amharic)", "(english)",
            "nationality (", "ዜግነት ("  # Specific patterns for labels with parentheses
        ]
        
        text_lower = text.lower()
        
        # Reject if text contains label indicators
        for keyword in excluded_keywords:
            if keyword in text_lower:
                return False
        
        # Reject if text is exactly one of the excluded keywords
        if text_lower.strip() in excluded_keywords:
            return False
        
        # Common nationality indicators (positive signals)
        nationality_indicators = [
            "united states", "ethiopia", "eritrea", "american", "british", "german", 
            "french", "italian", "sudanese", "kenyan", "somali", "canadian", "australian",
            "ኢትዮጵያ", "ኢትዮጵያዊ", "ኤርትራ", "ኤርትራዊ", "አሜሪካዊ"
        ]
        
        # If it matches known nationality patterns, it's likely valid
        if any(indicator in text_lower for indicator in nationality_indicators):
            return True
        
        # More lenient fallback: accept reasonable text that doesn't look like a label
        # Accept if it's a reasonable length and doesn't have too many words
        # Also accept if it's short (1-2 words) and 2-50 chars (covers most nationalities)
        if 2 <= len(text) <= 50:
            # Accept if it's 1-4 words (more lenient than before)
            if len(words) <= 4:
                # Additional check: make sure it's not just punctuation or special chars
                alnum_chars = sum(1 for c in text if c.isalnum())
                if alnum_chars >= 2:  # At least 2 alphanumeric characters
                    return True
        
        return False

    def _is_nationality_label_line(self, line: str) -> bool:
        """Check if a line contains the nationality label with flexible matching.
        
        Based on Ethiopian Digital ID Card PDF format, handles:
        - "ዜግነት / Nationality" (forward slash separator)
        - "ዜግነት | Nationality" (pipe separator)
        - "Nationality / ዜግነት" (reverse order)
        - Variations with different spacing and case
        - Lines containing both terms even without explicit separator
        - Lines with just "ዜግነት" or just "Nationality" (as fallback)
        
        Args:
            line: The line text to check
            
        Returns:
            True if the line appears to be a nationality label line
        """
        if not line:
            return False
        
        line_clean = line.strip()
        line_lower = line_clean.lower()
        
        # Check if line contains both Amharic and English terms (most reliable)
        has_amharic = "ዜግነት" in line_clean
        has_english = "nationality" in line_lower
        
        # Explicitly check for label metadata patterns like "Nationality (Amharic)" or "Nationality (English)"
        # Also check for variations with parentheses and capitalization
        if has_english:
            # Check for (Amharic), (English), (amharic), (english) patterns
            if ("(amharic)" in line_lower or "(english)" in line_lower or 
                "(Amharic)" in line_clean or "(English)" in line_clean or
                "( AMHARIC )" in line_clean.upper() or "( ENGLISH )" in line_clean.upper()):
                return True
            
            # Also check if line is essentially just "Nationality" (case-insensitive)
            # by checking if removing common metadata leaves just "nationality"
            test_line = line_lower.replace("(", "").replace(")", "").replace("amharic", "").replace("english", "").strip()
            test_line = test_line.replace(" ", "").strip()
            if test_line == "nationality":
                return True
        
        if has_amharic and has_english:
            return True
        
        # Check for common separator patterns with both terms
        separators = ["/", "|", ":"]
        for sep in separators:
            if sep in line_clean:
                parts = line_clean.split(sep, 1)
                if len(parts) == 2:
                    left = parts[0].strip()
                    right = parts[1].strip()
                    left_lower = left.lower()
                    right_lower = right.lower()
                    
                    # Check if either side contains the Amharic term and the other contains English
                    if (("ዜግነት" in left or "ዜግነት" in right) and 
                        ("nationality" in left_lower or "nationality" in right_lower)):
                        return True
        
        # More lenient fallback: check if line contains just "ዜግነት" or just "nationality"
        # But only if it's a short line (likely a label, not content)
        # Exclude common non-label words to avoid false positives
        if len(line_clean) <= 50:  # Labels are typically short (increased to handle "Nationality (Amharic)")
            excluded_in_label = ["ክልል", "region", "ወረዳ", "woreda", "ከተማ", "city", 
                               "የትውልድ", "birth", "date", "ስልክ", "phone", "ፆታ", "sex"]
            
            # If line contains just "ዜግነት" and doesn't contain excluded words, likely a label
            # Also check if the line is just the word "nationality" (with optional metadata)
            if (has_amharic and "ዜግነት" in line_clean and 
                not any(excluded in line_lower for excluded in excluded_in_label)):
                return True
            
            # If line contains "nationality" and doesn't contain excluded words, likely a label
            # This catches "Nationality", "Nationality (Amharic)", "Nationality (English)", etc.
            if (has_english and "nationality" in line_lower and 
                not any(excluded in line_lower for excluded in excluded_in_label)):
                # Make sure it's not a real nationality value - check if line is mostly just "nationality"
                # If the line contains only "nationality" plus optional parentheses content, it's a label
                cleaned_for_check = line_lower.replace("(", "").replace(")", "").replace("amharic", "").replace("english", "").strip()
                if cleaned_for_check in ["nationality", "nationality ", " nationality"]:
                    return True
        
        return False

    def _extract_nationality_below_label(self, lines: List[str]) -> Tuple[str, str]:
        """Extract nationality near the label 'ዜግነት | nationality' using a fuzzy line-based approach.

        - Matches the label if it contains both tokens ("nationality" or "ዜግነት"), ignoring order/spaces/case
        - If value appears on SAME line after a separator, parse it
        - Otherwise, look at the next 1-3 non-empty lines for the value
        - Returns canonical pair (amharic, english) or ("", "") if not found
        """

        def looks_like_label(text: str) -> bool:
            t = text.lower()
            # More comprehensive label detection
            return (("nationality" in t) or ("ዜግነት" in t) or 
                   ("(amharic)" in t and "nationality" in t) or 
                   ("(english)" in t and "nationality" in t) or
                   ("self declared" in t) or ("በተለያዩ መሰረት" in t))

        def parse_value(value_line: str) -> Tuple[str, str]:
            val = value_line.strip()
            if not val:
                return "", ""
            
            # Skip if this looks like a label line itself
            if looks_like_label(val):
                return "", ""
                
            if "|" in val:
                left, right = [p.strip() for p in val.split("|", 1)]
                # Validate both sides are actual nationality values
                if not (self._is_valid_nationality_value(left) and self._is_valid_nationality_value(right)):
                    return "", ""
                    
                # If left uses non-ASCII (likely Amharic) and right is ASCII (likely English)
                if any(ord(c) > 127 for c in left) and all(ord(c) < 128 for c in right):
                    return left, right
                # Or reversed order
                if any(ord(c) > 127 for c in right) and all(ord(c) < 128 for c in left):
                    return right, left
                # If both sides are same script, just return as-is with left as Amharic fallback
                return left, right
            # Single-language line: mirror to both sides if it's a valid nationality
            if self._is_valid_nationality_value(val):
                return val, val
            return "", ""

        print(f"_extract_nationality_below_label: Scanning {len(lines)} lines for nationality")
        
        for i, ln in enumerate(lines):
            s = ln.strip()
            if not s:
                continue
                
            print(f"  Line {i}: '{s}'")
            
            if looks_like_label(s):
                print(f"  Found nationality label at line {i}: '{s}'")
                
                # Same-line value after separators
                for sep in [":", "-", "—", "|"]:
                    if sep in s:
                        tail = s.split(sep, 1)[1].strip()
                        print(f"    Checking same-line value after '{sep}': '{tail}'")
                        am, en = parse_value(tail)
                        if am or en:
                            print(f"    Found same-line nationality: '{am}' | '{en}'")
                            return am or en, en or am
                
                # Look at next 1-5 non-empty lines for value (increased from 3 to 5)
                checked = 0
                j = i + 1
                print(f"    Looking for nationality value in next lines...")
                while j < len(lines) and checked < 5:
                    candidate = lines[j].strip()
                    j += 1
                    if not candidate:
                        continue
                        
                    print(f"      Candidate line {j-1}: '{candidate}'")
                    lower_cand = candidate.lower()
                    
                    # Skip if this is clearly another label/section
                    skip_keywords = [
                        "sex", "ፆታ", "date", "የትውልድ", "region", "city", "subcity", "zone", 
                        "woreda", "kebele", "phone", "ስልክ", "address", "ክልል", "ወረዳ", "ከተማ"
                    ]
                    if any(x in lower_cand for x in skip_keywords):
                        print(f"        Skipping - contains label keyword")
                        checked += 1
                        continue
                        
                    am, en = parse_value(candidate)
                    if am or en:
                        print(f"    Found nationality in next line: '{am}' | '{en}'")
                        return am or en, en or am
                    else:
                        print(f"        Not a valid nationality value")
                    checked += 1
                break
        
        print(f"_extract_nationality_below_label: No nationality found")
        return "", ""
        return "", ""

    def _extract_address_components(self, lines: List[str], region_index: int) -> Tuple[str, str, str, str]:
        """Extract subcity and woreda information with improved logic for Ethiopian address hierarchy."""
        subcity_am, subcity_en = "", ""
        woreda_am, woreda_en = ""
        
        print(f"Address extraction - Region index: {region_index}")
        print(f"Available lines around region:")
        for i in range(max(0, region_index - 1), min(len(lines), region_index + 6)):
            if i < len(lines):
                print(f"  Line {i}: '{lines[i]}'")
        
        # Enhanced pattern-based extraction for address components
        # Look for bilingual address lines in a wider range around the region
        search_start = max(0, region_index - 1)
        search_end = min(len(lines), region_index + 6)
        
        found_subcity = False
        found_woreda = False
        zone_candidate = None  # Track potential zone/subcity data
        
        for i in range(search_start, search_end):
            if i >= len(lines) or i == region_index:
                continue
                
            line = lines[i].strip()
            if not line:
                continue
                
            print(f"Analyzing line {i}: '{line}'")
            
            # Skip lines that are clearly not address components
            if any(keyword in line.lower() for keyword in ['phone', 'ስልክ', 'date', 'የትውልድ', 'sex', 'ፆታ', 'nationality', 'ዜግነት']):
                print(f"  Skipping non-address line")
                continue
            
            # Look for bilingual address lines with proper separator
            if '|' in line:
                parts = line.split('|', 1)
                if len(parts) == 2:
                    amharic_part = parts[0].strip()
                    english_part = parts[1].strip()
                    
                    # Skip empty parts
                    if not amharic_part or not english_part:
                        continue
                    
                    # Identify zone/subcity by keywords and patterns
                    zone_keywords_am = ['ዞን', 'ክልል', 'ክፍለ ከተማ']
                    zone_keywords_en = ['zone', 'sub city', 'subcity', 'sub-city']
                    
                    # Identify subcity/administration by keywords
                    subcity_keywords_am = ['ከተማ አስተዳደር', 'ክ/ከተማ', 'አስተዳደር']
                    subcity_keywords_en = ['city admin', 'administration', 'city administration', 'admin']
                    
                    # Identify woreda by keywords and patterns
                    woreda_keywords_am = ['ወረዳ', 'ቀበሌ', 'ወ/']
                    woreda_keywords_en = ['woreda', 'kebele', 'district']
                    
                    # Check if this is a zone (which should be treated as subcity in the form)
                    is_zone = (
                        any(keyword in amharic_part.lower() for keyword in zone_keywords_am) or
                        any(keyword in english_part.lower() for keyword in zone_keywords_en) or
                        # Common Ethiopian zones
                        any(zone_name in english_part for zone_name in ['East Wollega', 'West Wollega', 'North Shewa', 'South Wollega'])
                    )
                    
                    # Check if this is a subcity/administration
                    is_subcity_admin = (
                        any(keyword in amharic_part.lower() for keyword in subcity_keywords_am) or
                        any(keyword in english_part.lower() for keyword in subcity_keywords_en)
                    )
                    
                    # Check if this is a woreda
                    is_woreda = (
                        any(keyword in amharic_part.lower() for keyword in woreda_keywords_am) or
                        any(keyword in english_part.lower() for keyword in woreda_keywords_en) or
                        # Common Ethiopian woreda names
                        any(woreda_name in english_part for woreda_name in ['Gida Ayana', 'Nekemte', 'Shambu'])
                    )
                    
                    # Priority assignment logic for Ethiopian address hierarchy
                    if is_zone and not found_subcity:
                        # Zone should be mapped to subcity field in the form
                        subcity_am = amharic_part
                        subcity_en = english_part
                        found_subcity = True
                        print(f"  Found zone (mapped to subcity): '{subcity_am}' | '{subcity_en}'")
                    elif is_woreda and not found_woreda:
                        # Woreda is correctly mapped to woreda field
                        woreda_am = amharic_part
                        woreda_en = english_part
                        found_woreda = True
                        print(f"  Found woreda: '{woreda_am}' | '{woreda_en}'")
                    elif is_subcity_admin and not found_subcity and not zone_candidate:
                        # Only use administration if no zone was found
                        subcity_am = amharic_part
                        subcity_en = english_part
                        found_subcity = True
                        print(f"  Found subcity administration: '{subcity_am}' | '{subcity_en}'")
                    elif not found_subcity and not found_woreda:
                        # Store as potential zone candidate for later use
                        if not zone_candidate:
                            zone_candidate = (amharic_part, english_part)
                            print(f"  Stored as zone candidate: '{amharic_part}' | '{english_part}'")
            
            # Handle lines without separator (malformed lines)
            elif line and not any(char.isdigit() for char in line) and len(line) > 2:
                print(f"  Found line without separator: '{line}' - skipping as malformed")
                continue
        
        # If we have a zone candidate but no subcity, use the zone candidate
        if not found_subcity and zone_candidate:
            subcity_am, subcity_en = zone_candidate
            found_subcity = True
            print(f"  Using zone candidate as subcity: '{subcity_am}' | '{subcity_en}'")
        
        # Fallback to simple position-based extraction if pattern matching failed
        if not found_subcity or not found_woreda:
            print(f"Pattern matching incomplete, falling back to position-based extraction")
            
            if not found_subcity and region_index + 1 < len(lines):
                try:
                    fallback_subcity_am, fallback_subcity_en = self._parse_line(lines, region_index + 1)
                    if fallback_subcity_am and fallback_subcity_en:
                        subcity_am = fallback_subcity_am
                        subcity_en = fallback_subcity_en
                        print(f"  Fallback subcity from line {region_index + 1}: '{subcity_am}' | '{subcity_en}'")
                except Exception as e:
                    print(f"  Error in fallback subcity extraction: {str(e)}")
            
            if not found_woreda:
                # Try multiple positions for woreda due to potential malformed lines
                for offset in [2, 3, 4]:
                    if region_index + offset < len(lines):
                        try:
                            line_content = lines[region_index + offset].strip()
                            if '|' in line_content:
                                fallback_woreda_am, fallback_woreda_en = self._parse_line(lines, region_index + offset)
                                if fallback_woreda_am and fallback_woreda_en:
                                    # Validate this isn't duplicate subcity data
                                    if fallback_woreda_am != subcity_am:
                                        woreda_am = fallback_woreda_am
                                        woreda_en = fallback_woreda_en
                                        print(f"  Fallback woreda from line {region_index + offset}: '{woreda_am}' | '{woreda_en}'")
                                        break
                        except Exception as e:
                            print(f"  Error in fallback woreda extraction at offset {offset}: {str(e)}")
                            continue
        
        # Clean and validate the extracted data
        subcity_am = subcity_am.strip() if subcity_am else ""
        subcity_en = subcity_en.strip() if subcity_en else ""
        woreda_am = woreda_am.strip() if woreda_am else ""
        woreda_en = woreda_en.strip() if woreda_en else ""
        
        # Clean up generic labels that shouldn't be in the final address
        generic_labels_en = ['region', 'subcity', 'sub-city', 'woreda', 'city admin', 'administration']
        generic_labels_am = ['ክልል', 'ክፍለ ከተማ', 'ወረዳ', 'ከተማ አስተዳደር']
        
        # Clean subcity field if it contains only generic labels
        if subcity_en and any(label in subcity_en.lower() for label in generic_labels_en) and len(subcity_en) < 20:
            print(f"  Clearing subcity_en generic label: '{subcity_en}'")
            subcity_en = ""
        if subcity_am and any(label in subcity_am for label in generic_labels_am) and len(subcity_am) < 20:
            print(f"  Clearing subcity_am generic label: '{subcity_am}'")
            subcity_am = ""
        
        # Clean woreda field if it contains only generic labels
        if woreda_en and any(label in woreda_en.lower() for label in generic_labels_en) and len(woreda_en) < 15:
            print(f"  Clearing woreda_en generic label: '{woreda_en}'")
            woreda_en = ""
        if woreda_am and any(label in woreda_am for label in generic_labels_am) and len(woreda_am) < 15:
            print(f"  Clearing woreda_am generic label: '{woreda_am}'")
            woreda_am = ""
        
        # Ensure we have at least some data by copying between languages if needed
        if subcity_am and not subcity_en:
            subcity_en = subcity_am
        elif subcity_en and not subcity_am:
            subcity_am = subcity_en
            
        if woreda_am and not woreda_en:
            woreda_en = woreda_am
        elif woreda_en and not woreda_am:
            woreda_am = woreda_en
        
        # Final validation: ensure we don't have identical content
        if subcity_am == woreda_am and subcity_am:
            print(f"ERROR: Subcity and woreda have identical content: '{subcity_am}'")
            # Clear woreda if they're identical
            woreda_am, woreda_en = "", ""
        
        # Debug logging
        print(f"Final address extraction result:")
        print(f"  Subcity: '{subcity_am}' | '{subcity_en}'")
        print(f"  Woreda: '{woreda_am}' | '{woreda_en}'")
        
        return subcity_am, subcity_en, woreda_am, woreda_en

    def get_photo_data(self, data: Dict, remove_white: bool = False, remove_black: bool = False, use_onnx: bool = False) -> bytes:
        """Return photo image bytes from provided data or create a placeholder.
        
        Supports:
        - data['photo_bytes']: raw bytes
        - data['photo_b64']: base64-encoded string
        - data['photo']: file path relative or absolute
        Falls back to a transparent placeholder if nothing available.
        
        Args:
            data: Dictionary containing photo data
            remove_white: Whether to remove white backgrounds
            remove_black: Whether to remove black backgrounds
            use_onnx: Whether to use ONNX-based background removal
        """
        try:
            # 1) Raw bytes
            if data.get('photo_bytes'):
                if isinstance(data['photo_bytes'], bytes):
                    photo_bytes = data['photo_bytes']
                else:
                    photo_bytes = data['photo_bytes'].encode('utf-8')
                
                # Apply background removal if requested
                if remove_white or remove_black or use_onnx:
                    photo_bytes = self._apply_background_removal(photo_bytes, remove_white, remove_black, use_onnx)
                
                return photo_bytes
            
            # 2) Base64 encoded
            if data.get('photo_b64'):
                import base64
                photo_bytes = base64.b64decode(data['photo_b64'])
                
                # Apply background removal if requested
                if remove_white or remove_black or use_onnx:
                    photo_bytes = self._apply_background_removal(photo_bytes, remove_white, remove_black, use_onnx)
                
                return photo_bytes
            
            # 3) File path
            if data.get('photo'):
                photo_path = data['photo']
                if not os.path.isabs(photo_path):
                    photo_path = os.path.join(self.config.STATIC_FOLDER, photo_path)
                if os.path.exists(photo_path):
                    with open(photo_path, 'rb') as f:
                        photo_bytes = f.read()
                    
                    # Apply background removal if requested
                    if remove_white or remove_black or use_onnx:
                        photo_bytes = self._apply_background_removal(photo_bytes, remove_white, remove_black, use_onnx)
                    
                    return photo_bytes
            
            # 4) Fallback: create transparent placeholder
            placeholder = Image.new('RGBA', (200, 260), (255, 255, 255, 0))
            buffer = BytesIO()
            placeholder.save(buffer, format='PNG')
            return buffer.getvalue()
            
        except Exception as e:
            print(f"Error getting photo data: {str(e)}")
            # Return transparent placeholder on error
            placeholder = Image.new('RGBA', (200, 260), (255, 255, 255, 0))
            buffer = BytesIO()
            placeholder.save(buffer, format='PNG')
            return buffer.getvalue()
    
    def _apply_background_removal(self, photo_bytes: bytes, remove_white: bool, remove_black: bool, use_onnx: bool) -> bytes:
        """Apply background removal to photo bytes.
        
        Args:
            photo_bytes: Raw photo bytes
            remove_white: Whether to remove white backgrounds
            remove_black: Whether to remove black backgrounds
            use_onnx: Whether to use offline rembg-based background removal
            
        Returns:
            Processed photo bytes
        """
        try:
            if use_onnx:
                # Use offline rembg-based background removal
                print("🔄 Using offline background removal (rembg)...")
                processed_bytes = remove_background_to_bytes_offline(photo_bytes)
                if processed_bytes is not None:
                    print("✅ Offline background removal completed successfully")
                    return processed_bytes
                else:
                    print("⚠️ Offline background removal failed, using simple method")
                    # Fall back to simple method
                    return self._apply_simple_background_removal(photo_bytes, remove_white, remove_black)
            else:
                # Use simple color-based background removal
                return self._apply_simple_background_removal(photo_bytes, remove_white, remove_black)
            
        except Exception as e:
            print(f"❌ Error applying background removal: {str(e)}")
            # Return original bytes if processing fails
            return photo_bytes
    
    def _apply_simple_background_removal(self, photo_bytes: bytes, remove_white: bool, remove_black: bool) -> bytes:
        """Apply simple color-based background removal to photo bytes."""
        try:
            # Convert bytes to PIL Image
            image = Image.open(BytesIO(photo_bytes))
            
            # Simple color-based background removal
            if remove_white or remove_black:
                img_array = np.array(image)
                
                if image.mode != 'RGBA':
                    if image.mode == 'RGB':
                        img_array = np.concatenate([img_array, np.full((*img_array.shape[:2], 1), 255, dtype=np.uint8)], axis=2)
                    else:
                        image = image.convert('RGBA')
                        img_array = np.array(image)
                
                # Create alpha channel
                alpha = np.ones(img_array.shape[:2], dtype=np.uint8) * 255
                
                if remove_white:
                    # Remove white/light backgrounds
                    white_threshold = 220
                    white_mask = np.all(img_array[:, :, :3] > white_threshold, axis=2)
                    alpha[white_mask] = 0
                
                if remove_black:
                    # Remove black/dark backgrounds
                    black_threshold = 30
                    black_mask = np.all(img_array[:, :, :3] < black_threshold, axis=2)
                    alpha[black_mask] = 0
                
                # Apply alpha channel
                img_array[:, :, 3] = alpha
                image = Image.fromarray(img_array, 'RGBA')
            
            # Convert back to bytes
            buffer = BytesIO()
            image.save(buffer, format='PNG')
            return buffer.getvalue()
            
        except Exception as e:
            print(f"Error applying simple background removal: {str(e)}")
            return photo_bytes

    def generate_qr_code(self, data: Dict, include_nationality: bool = True) -> bytes:
        """Generate QR code PNG bytes from extracted data."""
        try:
            # Create QR content with key fields
            qr_content = []
            
            # Always include these fields
            if data.get('name_en'):
                qr_content.append(f"Name: {data['name_en']}")
            if data.get('fcn_full'):
                qr_content.append(f"FCN: {data['fcn_full']}")
            if data.get('dob_en'):
                qr_content.append(f"DOB: {data['dob_en']}")
            if data.get('gender_en'):
                qr_content.append(f"Gender: {data['gender_en']}")
            if data.get('phone'):
                qr_content.append(f"Phone: {data['phone']}")
            if data.get('region_en'):
                qr_content.append(f"Region: {data['region_en']}")
            if data.get('subcity_en'):
                qr_content.append(f"Subcity: {data['subcity_en']}")
            if data.get('woreda_en'):
                qr_content.append(f"Woreda: {data['woreda_en']}")
            
            # Include nationality if requested
            if include_nationality and data.get('nationality_en'):
                qr_content.append(f"Nationality: {data['nationality_en']}")
            
            # Join all fields
            qr_text = "\n".join(qr_content)
            
            # Generate QR code
            qr = qrcode.QRCode(
                version=1,
                error_correction=qrcode.constants.ERROR_CORRECT_L,
                box_size=10,
                border=4,
            )
            qr.add_data(qr_text)
            qr.make(fit=True)
            
            # Create image
            qr_image = qr.make_image(fill_color="black", back_color="white")
            
            # Convert to bytes
            buffer = BytesIO()
            qr_image.save(buffer, format='PNG')
            return buffer.getvalue()
            
        except Exception as e:
            print(f"Error generating QR code: {str(e)}")
            # Return empty QR on error
            placeholder = Image.new('RGBA', (200, 200), (255, 255, 255, 0))
            buffer = BytesIO()
            placeholder.save(buffer, format='PNG')
            return buffer.getvalue()

    def _validate_address_data(self, subcity_am: str, subcity_en: str, woreda_am: str, woreda_en: str) -> Tuple[str, str, str, str]:
        """Validate and clean address data to ensure consistency with Ethiopian address hierarchy."""
        print(f"Validating address data:")
        print(f"  Input subcity: '{subcity_am}' | '{subcity_en}'")
        print(f"  Input woreda: '{woreda_am}' | '{woreda_en}'")
        
        # Remove any empty or invalid entries
        if not subcity_am or subcity_am.strip() == "":
            subcity_am = ""
        if not subcity_en or subcity_en.strip() == "":
            subcity_en = ""
        if not woreda_am or woreda_am.strip() == "":
            woreda_am = ""
        if not woreda_en or woreda_en.strip() == "":
            woreda_en = ""
        
        # Clean up generic labels that shouldn't be in the final address
        generic_labels_en = ['region', 'subcity', 'sub-city', 'woreda', 'city admin', 'administration', 'zone', 'sub city']
        generic_labels_am = ['ክልል', 'ክፍለ ከተማ', 'ወረዳ', 'ከተማ አስተዳደር', 'ዞን', 'አስተዳደር']
        
        # Clean subcity field if it contains only generic labels
        if subcity_en and len(subcity_en) < 25:
            # Only clear if it's exactly a generic label, not if it contains additional content
            if subcity_en.lower().strip() in ['region', 'subcity', 'sub-city', 'city admin', 'administration', 'zone', 'sub city']:
                print(f"  Clearing subcity_en generic label: '{subcity_en}'")
                subcity_en = ""
        if subcity_am and len(subcity_am) < 25:
            # Only clear if it's exactly a generic label, not if it contains additional content
            if subcity_am.strip() in ['ክልል', 'ክፍለ ከተማ', 'ወረዳ', 'ከተማ አስተዳደር', 'ዞን', 'አስተዳደር']:
                print(f"  Clearing subcity_am generic label: '{subcity_am}'")
                subcity_am = ""
        
        # Clean woreda field if it contains only generic labels
        if woreda_en and len(woreda_en) < 20:
            # Only clear if it's exactly a generic label, not if it contains additional content
            if woreda_en.lower().strip() in ['woreda', 'administration', 'admin', 'kebele']:
                print(f"  Clearing woreda_en generic label: '{woreda_en}'")
                woreda_en = ""
        if woreda_am and len(woreda_am) < 20:
            # Only clear if it's exactly a generic label, not if it contains additional content  
            if woreda_am.strip() in ['ወረዳ', 'አስተዳደር', 'ቀበሌ']:
                print(f"  Clearing woreda_am generic label: '{woreda_am}'")
                woreda_am = ""
        
        # If we have Amharic but no English, try to use Amharic for both
        if subcity_am and not subcity_en:
            subcity_en = subcity_am
        if woreda_am and not woreda_en:
            woreda_en = woreda_am
        
        # If we have English but no Amharic, try to use English for both
        if subcity_en and not subcity_am:
            subcity_am = subcity_en
        if woreda_en and not woreda_am:
            woreda_am = woreda_en
        
        # Check for content that looks like it's in the wrong field
        # If subcity contains "Administration" but woreda doesn't, they might be swapped
        if (subcity_am and woreda_am and 
            'administration' in subcity_en.lower() and 
            'administration' not in woreda_en.lower() and
            len(woreda_am) > len(subcity_am)):
            print(f"  Detected possible field swap - subcity has 'administration' but woreda is longer")
            # Swap them
            subcity_am, woreda_am = woreda_am, subcity_am
            subcity_en, woreda_en = woreda_en, subcity_en
            print(f"  Swapped fields after validation")
        
        # Ensure we don't have the same value for subcity and woreda
        if subcity_am == woreda_am and subcity_am:
            print(f"  ERROR: Subcity and woreda have identical content: '{subcity_am}'")
            # If they're the same, one is probably wrong, clear woreda
            woreda_am = ""
            woreda_en = ""
            print(f"  Cleared woreda to avoid duplication")
        
        # Final validation logging
        print(f"Address validation result:")
        print(f"  Subcity: '{subcity_am}' | '{subcity_en}'")
        print(f"  Woreda: '{woreda_am}' | '{woreda_en}'")
        
        return subcity_am, subcity_en, woreda_am, woreda_en

    def _extract_default_pdf_data(self, doc: fitz.Document, lines: List[str], images: List[Tuple], fin_number: str) -> Dict:
        """Extract data from default PDF format."""
        line_indices = self.PDF_FORMAT_MAPPING['default']
        
        # Ensure lines are padded for safe access
        max_index = max(line_indices.values())
        if len(lines) <= max_index:
            lines += [""] * (max_index + 1 - len(lines))

        # Extract FCN and validate (with robust fallback search)
        fcn_raw = lines[line_indices['fcn']].strip() if line_indices.get('fcn') is not None else ''
        fcn = ''.join(ch for ch in fcn_raw if ch.isdigit())
        if len(fcn) != self.config.FCN_LENGTH:
            # Fallback: scan all lines for the first 16-digit sequence, accommodating labels like "FCN: 3084..."
            print(f"Default format: FCN not found at expected index; attempting fallback scan...")
            found_digits = None
            for idx, line in enumerate(lines):
                digits = ''.join(ch for ch in line if ch.isdigit())
                if len(digits) >= self.config.FCN_LENGTH:
                    found_digits = digits[:self.config.FCN_LENGTH]
                    print(f"  Fallback FCN candidate found on line {idx}: '{line[:50]}...' -> '{found_digits}'")
                    break
            if found_digits and len(found_digits) == self.config.FCN_LENGTH:
                fcn = found_digits
            else:
                raise ValueError(f"Invalid FCN number. Must be {self.config.FCN_LENGTH} digits. Extracted: '{fcn_raw}' -> '{fcn}' (Length: {len(fcn)})")

        # Initialize fields for pattern-first parsing
        name_am = ""; name_en = ""
        dob_am = ""; dob_en_raw = ""
        gender_am = ""; gender_en = ""
        nationality_am = ""; nationality_en = ""
        phone = ""

        # Pattern-first overrides: scan the whole page for bilingual lines and key markers
        # This improves accuracy for default PDFs whose layout varies slightly.
        try:
            def split_pair(s: str):
                parts = s.split('|', 1)
                return parts[0].strip(), parts[1].strip() if len(parts) == 2 else (s.strip(), "")

            def is_english_name(s: str) -> bool:
                s_clean = s.replace(" ", "").replace("-", "").replace(".", "")
                if not s_clean.isalpha():
                    return False
                banned = ["region", "zone", "sub", "city", "admin", "administration", "woreda", "kebele", "sex", "nationality", "disclaimer", "demographic", "id card"]
                return len(s.split()) >= 2 and not any(b in s.lower() for b in banned)

            known_regions_en = [
                "Addis Ababa", "Amhara", "Oromia", "Tigray", "Afar", "Somali", "Benishangul", "Sidama", "Gambella", "Harari", "SNNP"
            ]

            pattern_region_am = pattern_region_en = ""
            pattern_subcity_am = pattern_subcity_en = ""
            pattern_woreda_am = pattern_woreda_en = ""
            pattern_name_am = pattern_name_en = ""
            pattern_gender_am = pattern_gender_en = ""
            pattern_nat_am = pattern_nat_en = ""
            pattern_dob_am = pattern_dob_en = ""
            pattern_phone = ""

            import re
            dob_ddmmyyyy = re.compile(r"\b\d{1,2}/\d{1,2}/\d{4}\b")
            dob_yyyymmdd = re.compile(r"\b\d{4}/\d{1,2}/\d{1,2}\b")

            for ln in lines:
                # FCN (keep existing if already parsed)
                # Names (bilingual, no digits)
                if '|' in ln and not any(ch.isdigit() for ch in ln):
                    left, right = split_pair(ln)
                    if not pattern_name_en and any(ord(c) > 127 for c in left) and is_english_name(right):
                        pattern_name_am, pattern_name_en = left, right
                        continue
                    # Address candidates
                    if not pattern_region_en and any(r in ln for r in known_regions_en):
                        l, r = split_pair(ln)
                        pattern_region_am, pattern_region_en = l, r
                        continue
                    if not pattern_subcity_en and any(x in ln.lower() for x in ["zone", "subcity", "sub city"]):
                        l, r = split_pair(ln)
                        # Skip if this looks like a label (contains only the keyword)
                        if (any(r.lower().strip() == label for label in ["zone", "subcity", "sub city"]) or
                            "zone/sub city" in r.lower() or "city admin" in r.lower()):
                            continue  # This is likely a label, not a value
                        pattern_subcity_am, pattern_subcity_en = l, r
                        continue
                    if not pattern_woreda_en and any(x in ln.lower() for x in ["woreda", "administration", "admin", "kebele"]):
                        l, r = split_pair(ln)
                        # Skip if this looks like a label (short and contains only the keyword)
                        if (r.lower().strip() in ["woreda", "administration", "admin", "kebele"] or
                            (len(r.strip()) < 15 and r.lower().strip() == "woreda")):
                            continue  # This is likely a label, not a value
                        pattern_woreda_am, pattern_woreda_en = l, r
                        continue
                # DOB bilingual
                if not pattern_dob_en:
                    if '|' in ln and '/' in ln:
                        l, r = split_pair(ln)
                        if '/' in l and '/' in r:
                            pattern_dob_am, pattern_dob_en = l.strip(), r.strip()
                            continue
                    # Also handle a single line that contains both formats regardless of order
                    if dob_ddmmyyyy.search(ln) and dob_yyyymmdd.search(ln):
                        # Assume left is Ethiopian (YYYY/MM/DD) and right is Gregorian (DD/MM/YYYY) when split exists
                        if '|' in ln:
                            l, r = split_pair(ln)
                            pattern_dob_am = dob_yyyymmdd.search(l).group(0) if dob_yyyymmdd.search(l) else l.strip()
                            pattern_dob_en = dob_ddmmyyyy.search(r).group(0) if dob_ddmmyyyy.search(r) else r.strip()
                        else:
                            # If no explicit split, choose by ordering in text
                            g_en = dob_ddmmyyyy.search(ln).group(0)
                            e_am = dob_yyyymmdd.search(ln).group(0)
                            pattern_dob_am, pattern_dob_en = e_am, g_en
                        continue
                # Gender bilingual
                if '|' in ln and not pattern_gender_en and any(x in ln for x in ["ወንድ", "ሴት", "Male", "Female"]):
                    l, r = split_pair(ln)
                    if l in ["ወንድ", "ሴት"] and r in ["Male", "Female"]:
                        pattern_gender_am, pattern_gender_en = l, r
                        continue
                # Nationality bilingual - extract as-is without hardcoded mappings
                if '|' in ln and not pattern_nat_en:
                    l, r = split_pair(ln)
                    # Check if it looks like a nationality value (not a label)
                    if (l and r and len(l) <= 50 and len(r) <= 50 and
                        l.lower() not in ["nationality", "ዜግነት"] and
                        r.lower() not in ["nationality", "ዜግነት"] and
                        not any(char.isdigit() for char in l + r) and
                        # Skip lines that contain label indicators
                        not any(indicator in ln.lower() for indicator in ["(amharic)", "(english)", "self declared", "በተለያዩ መሰረት"]) and
                        # Use the validation function to ensure it's a valid nationality value
                        self._is_valid_nationality_value(l) and self._is_valid_nationality_value(r)):
                        pattern_nat_am, pattern_nat_en = l, r
                        continue
                # Nationality English-only line - extract as-is
                if not pattern_nat_en:
                    # Check if line contains "nationality" label - skip it
                    if ("nationality" in ln.lower() and len(ln.strip()) <= 50) or any(indicator in ln.lower() for indicator in ["(amharic)", "(english)", "self declared"]):
                        continue
                    # Otherwise, treat single English word as potential nationality
                    words = ln.strip().split()
                    if len(words) == 1 and len(words[0]) <= 50 and words[0].isalpha() and self._is_valid_nationality_value(words[0]):
                        pattern_nat_en = words[0]
                        pattern_nat_am = words[0]  # Keep same until translation available
                        continue
                # Nationality Amharic-only line - extract as-is
                if not pattern_nat_am:
                    # Check if line contains "ዜግነት" label - skip it
                    if ("ዜግነት" in ln and len(ln.strip()) <= 50) or any(indicator in ln.lower() for indicator in ["በተለያዩ መሰረት"]):
                        continue
                    # Otherwise, treat single Amharic word as potential nationality
                    if any(ord(c) > 127 for c in ln) and len(ln.strip()) <= 50 and self._is_valid_nationality_value(ln.strip()):
                        pattern_nat_am = ln.strip()
                        pattern_nat_en = ln.strip()  # Keep same until translation available
                        continue
                # Phone (10 digits typical)
                digits = ln.replace(" ", "")
                if not pattern_phone and digits.isdigit() and 9 <= len(digits) <= 13:
                    pattern_phone = ln.strip()

            # Apply pattern overrides when found
            if pattern_name_en and pattern_name_am:
                name_en, name_am = pattern_name_en, pattern_name_am
                print(f"Default format: Applied pattern name: '{name_am}' | '{name_en}'")
            if pattern_dob_en and pattern_dob_am:
                dob_en_raw, dob_am = pattern_dob_en, pattern_dob_am
                print(f"Default format: Applied pattern DOB: '{dob_am}' | '{dob_en_raw}'")
            if pattern_gender_en and pattern_gender_am:
                gender_en, gender_am = pattern_gender_en, pattern_gender_am
                print(f"Default format: Applied pattern gender: '{gender_am}' | '{gender_en}'")
            if pattern_nat_en and pattern_nat_am:
                nationality_en, nationality_am = pattern_nat_en, pattern_nat_am
                print(f"Default format: Applied pattern nationality: '{nationality_am}' | '{nationality_en}'")
            if pattern_phone:
                phone = self.format_phone_number(pattern_phone)
                print(f"Default format: Applied pattern phone: '{phone}'")
            if pattern_region_en and pattern_region_am:
                region_en, region_am = pattern_region_en, pattern_region_am
                print(f"Default format: Applied pattern region: '{region_am}' | '{region_en}'")
            if pattern_subcity_en and pattern_subcity_am:
                subcity_en, subcity_am = pattern_subcity_en, pattern_subcity_am
                print(f"Default format: Applied pattern subcity: '{subcity_am}' | '{subcity_en}'")
            if pattern_woreda_en and pattern_woreda_am:
                woreda_en, woreda_am = pattern_woreda_en, pattern_woreda_am
                print(f"Default format: Applied pattern woreda: '{woreda_am}' | '{woreda_en}'")
        except Exception as _:
            pass

        # Fallback: detect unlabeled bilingual nationality line (e.g., "Eritrea | Eritrea")
        if not nationality_en and not nationality_am:
            try:
                excluded_words = [
                    "region", "zone", "subcity", "sub city", "city", "admin", "administration", "woreda", "kebele",
                    "sex", "nationality", "phone", "date", "demographic", "disclaimer", "address"
                ]
                for ln in lines:
                    if '|' in ln and not any(ch.isdigit() for ch in ln):
                        left, right = [p.strip() for p in ln.split('|', 1)]
                        left_ascii = all(ord(c) < 128 for c in left.replace(' ', ''))
                        right_ascii = all(ord(c) < 128 for c in right.replace(' ', ''))
                        # Skip obvious labels/addresses
                        if any(w in ln.lower() for w in excluded_words):
                            continue
                        # Heuristic: both sides ASCII words and similar → nationality
                        if left and right and left_ascii and right_ascii:
                            if left.lower() == right.lower():
                                nationality_en = right
                                nationality_am = left
                                break
            except Exception:
                pass

        # Debug: Log the PDF structure around address fields
        print(f"PDF structure debug - All lines:")
        for i, line in enumerate(lines):
            print(f"  Line {i}: '{line}'")
        
        # Extract address components with improved label-based logic
        try:
            # Initialize address variables
            region_am, region_en = "", ""
            subcity_am, subcity_en = "", ""
            woreda_am, woreda_en = "", ""
            
            # Use label-based extraction - look for specific labels and extract the next line
            i = 0
            while i < len(lines):
                line = lines[i].strip().lower()
                original_line = lines[i].strip()
                
                # Check for region label
                if ('region' in line and ('city' in line or 'admin' in line)) or ('ክልል' in original_line and ('ከተማ' in original_line or 'አስተዳደር' in original_line)):
                    print(f"Found region label at line {i}: '{original_line}'")
                    if i + 1 < len(lines):
                        next_line = lines[i + 1].strip()
                        if '|' in next_line:
                            parts = next_line.split('|', 1)
                            region_am = parts[0].strip()
                            region_en = parts[1].strip()
                        else:
                            region_am = next_line
                            region_en = next_line
                        print(f"Region extracted: '{region_am}' | '{region_en}'")
                        i += 2  # Skip the value line
                        continue
                
                # Check for subcity/zone label
                elif ('zone' in line and ('sub' in line or 'city' in line)) or ('ዞን' in original_line and 'ክፍለ' in original_line):
                    print(f"Found subcity/zone label at line {i}: '{original_line}'")
                    if i + 1 < len(lines):
                        next_line = lines[i + 1].strip()
                        if '|' in next_line:
                            parts = next_line.split('|', 1)
                            subcity_am = parts[0].strip()
                            subcity_en = parts[1].strip()
                        else:
                            subcity_am = next_line
                            subcity_en = next_line
                        print(f"Subcity extracted: '{subcity_am}' | '{subcity_en}'")
                        i += 2  # Skip the value line
                        continue
                
                # Check for woreda label (be more specific to avoid false matches)
                elif (line == 'woreda' or 'ወረዳ' in original_line) and len(original_line) < 30:
                    print(f"Found woreda label at line {i}: '{original_line}'")
                    if i + 1 < len(lines):
                        next_line = lines[i + 1].strip()
                        if '|' in next_line:
                            parts = next_line.split('|', 1)
                            woreda_am = parts[0].strip()
                            woreda_en = parts[1].strip()
                        else:
                            woreda_am = next_line
                            woreda_en = next_line
                        print(f"Woreda extracted: '{woreda_am}' | '{woreda_en}'")
                        i += 2  # Skip the value line
                        continue
                
                i += 1
            
            # If label-based extraction didn't work completely, try pattern-based as fallback
            if not region_am or not region_en or not subcity_am or not subcity_en or not woreda_am or not woreda_en:
                print("Label-based extraction incomplete, trying pattern-based fallback...")
                
                # Pattern-based fallback for missing fields
                for line in lines:
                    if '|' in line and not any(char.isdigit() for char in line):
                        parts = line.split('|', 1)
                        left = parts[0].strip()
                        right = parts[1].strip()
                        
                        # Check if this looks like a region (known regions)
                        known_regions = ['Addis Ababa', 'Amhara', 'Oromia', 'Tigray', 'Afar', 'Somali', 'SNNP', 'Sidama', 'Gambella', 'Harari', 'Benishangul']
                        if not region_en and any(region in right for region in known_regions):
                            region_am, region_en = left, right
                            print(f"Pattern-based region: '{region_am}' | '{region_en}'")
                            continue
                        
                        # Check if this looks like a zone/subcity (contains "Zone" or similar)
                        if not subcity_en and ('zone' in right.lower() or 'wollo' in right.lower() or 'wollega' in right.lower()):
                            subcity_am, subcity_en = left, right
                            print(f"Pattern-based subcity: '{subcity_am}' | '{subcity_en}'")
                            continue
                        
                        # Check if this looks like a woreda (shorter names, specific patterns)
                        if not woreda_en and len(right) < 20 and not any(keyword in right.lower() for keyword in ['zone', 'region', 'admin', 'city']):
                            # Additional validation - make sure it's not a date, sex, or other field
                            if not any(keyword in right.lower() for keyword in ['male', 'female', 'birth', 'phone', 'nationality']):
                                woreda_am, woreda_en = left, right
                                print(f"Pattern-based woreda: '{woreda_am}' | '{woreda_en}'")
                                continue
                
                # Additional pattern-based search specifically for woreda with numbers
                if not woreda_am or not woreda_en:
                    print("Still missing woreda, trying number-based pattern search...")
                    for i, line in enumerate(lines):
                        print(f"  Checking line {i}: '{line}'")
                        if '|' in line:
                            parts = line.split('|', 1)
                            left = parts[0].strip()
                            right = parts[1].strip()
                            
                            # Look for woreda patterns with numbers (like "ወረዳ 06 | Woreda 06")
                            if (('ወረዳ' in left or 'woreda' in right.lower()) and 
                                any(c.isdigit() for c in line)):
                                woreda_am, woreda_en = left, right
                                print(f"Number-based woreda pattern found at line {i}: '{woreda_am}' | '{woreda_en}'")
                                break
                            
                            # Also look for lines that start with numbers and might be woreda
                            # (like "06 | 06" which could be woreda number)
                            elif (left.strip().isdigit() and right.strip().isdigit() and 
                                  left.strip() == right.strip() and len(left.strip()) <= 3):
                                # Check if previous line was woreda label
                                if i > 0 and ('ወረዳ' in lines[i-1] or 'woreda' in lines[i-1].lower()):
                                    woreda_am = f"ወረዳ {left}"
                                    woreda_en = f"Woreda {right}"
                                    print(f"Found woreda number at line {i} with label at {i-1}: '{woreda_am}' | '{woreda_en}'")
                                    break
            
            # Validate and clean address data
            subcity_am, subcity_en, woreda_am, woreda_en = self._validate_address_data(
                subcity_am, subcity_en, woreda_am, woreda_en
            )
            
        except Exception as e:
            print(f"Error in address extraction: {str(e)}")
            print(f"Falling back to simple extraction...")
            try:
                region_am, region_en = self._parse_line(lines, line_indices['region'])
                print(f"  Region extracted: '{region_am}' | '{region_en}'")
            except Exception as e2:
                print(f"  Error extracting region: {str(e2)}")
                region_am, region_en = "", ""
            
            try:
                subcity_am, subcity_en = self._parse_line(lines, line_indices['subcity'])
                print(f"  Subcity extracted: '{subcity_am}' | '{subcity_en}'")
            except Exception as e2:
                print(f"  Error extracting subcity: {str(e2)}")
                subcity_am, subcity_en = "", ""
            
            try:
                woreda_am, woreda_en = self._parse_line(lines, line_indices['woreda'])
                print(f"  Woreda extracted from line {line_indices['woreda']}: '{woreda_am}' | '{woreda_en}'")
                
                # Check if woreda looks like it's actually a label or malformed data
                if (not woreda_am or not woreda_en or 
                    woreda_am == woreda_en and 'woreda' in woreda_en.lower() and len(woreda_en) < 15):
                    print(f"  Woreda appears to be a label or malformed, searching for actual value...")
                    
                    # Search for woreda value in nearby lines
                    found_woreda = False
                    search_range = range(max(0, line_indices['woreda'] - 2), min(len(lines), line_indices['woreda'] + 5))
                    
                    for search_idx in search_range:
                        if search_idx == line_indices['woreda']:
                            continue  # Skip the original line we already tried
                            
                        try:
                            candidate_line = lines[search_idx].strip()
                            print(f"    Checking line {search_idx}: '{candidate_line}'")
                            
                            if '|' in candidate_line:
                                candidate_am, candidate_en = self._parse_line(lines, search_idx)
                                
                                # Check if this looks like a woreda value (not a label)
                                woreda_indicators = ['woreda', 'ወረዳ', 'kebele', 'ቀበሌ']
                                has_woreda_keyword = any(indicator in candidate_line.lower() for indicator in woreda_indicators)
                                
                                # If it has woreda keyword and looks like a value (contains numbers or is longer than just "woreda")
                                if (has_woreda_keyword and 
                                    (any(c.isdigit() for c in candidate_line) or 
                                     len(candidate_am) > 10 or len(candidate_en) > 10)):
                                    woreda_am, woreda_en = candidate_am, candidate_en
                                    print(f"    Found woreda value at line {search_idx}: '{woreda_am}' | '{woreda_en}'")
                                    found_woreda = True
                                    break
                                    
                                # Also check for lines that might be woreda values without explicit keywords
                                elif (not has_woreda_keyword and candidate_am and candidate_en and
                                      candidate_am != candidate_en and
                                      len(candidate_am) < 30 and len(candidate_en) < 30 and
                                      not any(skip_word in candidate_line.lower() for skip_word in 
                                             ['phone', 'date', 'birth', 'sex', 'nationality', 'region', 'zone', 'subcity'])):
                                    # This might be a woreda value without explicit labeling
                                    woreda_am, woreda_en = candidate_am, candidate_en
                                    print(f"    Found potential woreda value at line {search_idx}: '{woreda_am}' | '{woreda_en}'")
                                    found_woreda = True
                                    break
                                    
                        except Exception as search_e:
                            print(f"    Error checking line {search_idx}: {str(search_e)}")
                            continue
                    
                    if not found_woreda:
                        print(f"  Could not find woreda value, keeping original or clearing")
                        # If original was clearly a label, clear it
                        if woreda_am == woreda_en and 'woreda' in woreda_en.lower() and len(woreda_en) < 15:
                            woreda_am, woreda_en = "", ""
                        
            except Exception as e2:
                print(f"  Error extracting woreda: {str(e2)}")
                woreda_am, woreda_en = "", ""

        # Parse DOB to desired format (support DD/MM/YYYY and YYYY/MM/DD).
        # Required output:
        # - dob_am: DD/MM/YYYY (numeric) - 4 digit year
        # - dob_en: YYYY/Mon/DD
        dob_en = ""
        if (dob_en_raw and '|' in dob_en_raw) or (dob_am and '/' in dob_am):
            left = (dob_am or '').strip()    # Amharic side from PDF
            right = (dob_en_raw or '').strip()  # English side from PDF
            # Amharic from LEFT (numeric DD/MM/YYYY) - ensure 4 digit year
            try:
                if left and left.split('/')[0].isdigit() and len(left.split('/')[0]) == 4:
                    y, m, d = left.split('/')
                    # Ensure 4 digit year for Amharic DOB
                    full_year = int(y)
                    if full_year < 100:  # If it's a 2-digit year, infer the century
                        # Use the English date to determine the century
                        if right and right.split('/')[0].isdigit() and len(right.split('/')[0]) == 4:
                            english_year = int(right.split('/')[0])
                            century = (english_year // 100) * 100
                            full_year = century + full_year
                    dob_am = f"{int(d):02d}/{int(m):02d}/{full_year:04d}"
                elif left and len(left.split('/')) == 3:
                    d, m, y = left.split('/')
                    # Ensure 4 digit year for Amharic DOB
                    full_year = int(y)
                    if full_year < 100:  # If it's a 2-digit year, infer the century
                        # Use the English date to determine the century
                        if right and right.split('/')[0].isdigit() and len(right.split('/')[0]) == 4:
                            english_year = int(right.split('/')[0])
                            century = (english_year // 100) * 100
                            full_year = century + full_year
                    dob_am = f"{int(d):02d}/{int(m):02d}/{full_year:04d}"
            except Exception:
                pass
            # English from RIGHT → YYYY/Mon/DD
            try:
                if right and right.split('/')[0].isdigit() and len(right.split('/')[0]) == 4:
                    dob_en = datetime.strptime(right, "%Y/%m/%d").strftime("%Y/%b/%d")
                elif right and len(right.split('/')) == 3:
                    dob_en = datetime.strptime(right, "%d/%m/%Y").strftime("%Y/%b/%d")
                else:
                    dob_en = right
            except Exception:
                dob_en = right
        else:
            # Try DD/MM/YYYY first, then YYYY/MM/DD
            try:
                dob_en = datetime.strptime(dob_en_raw, "%d/%m/%Y").strftime("%Y/%b/%d")
            except ValueError:
                try:
                    dob_en = datetime.strptime(dob_en_raw, "%Y/%m/%d").strftime("%Y/%b/%d")
                except ValueError:
                    dob_en = dob_en_raw # Fallback if parsing fails

        # Final fallback: if subcity or woreda missing, use fixed indices
        if (not subcity_am or not subcity_en) and line_indices.get('subcity') is not None:
            try:
                s_am, s_en = self._parse_line(lines, line_indices['subcity'])
                if not subcity_am: subcity_am = s_am
                if not subcity_en: subcity_en = s_en
                print(f"  Subcity fallback from fixed index: '{subcity_am}' | '{subcity_en}'")
            except Exception:
                pass
        if (not woreda_am or not woreda_en) and line_indices.get('woreda') is not None:
            try:
                w_am, w_en = self._parse_line(lines, line_indices['woreda'])
                if not woreda_am: woreda_am = w_am
                if not woreda_en: woreda_en = w_en
                print(f"  Woreda fallback from fixed index: '{woreda_am}' | '{woreda_en}'")
            except Exception:
                pass

        # Override nationality by reading the line directly below the label if present
        # This is especially important for default format where line indices might not be accurate
        try:
            nat_am_label, nat_en_label = self._extract_nationality_below_label(lines)
            if nat_am_label or nat_en_label:
                print(f"Default format: Found nationality using label-based extraction: '{nat_am_label}' | '{nat_en_label}'")
                # Mirror if only one side detected
                nat_am_final = nat_am_label or nat_en_label
                nat_en_final = nat_en_label or nat_am_label
                nationality_am = nat_am_final or nationality_am
                nationality_en = nat_en_final or nationality_en
            else:
                print(f"Default format: Label-based nationality extraction found nothing")
        except Exception as e:
            print(f"Default format: Error in label-based nationality extraction: {str(e)}")
            pass

        # If still no nationality found, try extracting from the fixed line index as last resort
        if not nationality_am and not nationality_en:
            try:
                line_nat_am, line_nat_en = self._parse_line(lines, line_indices['nationality'])
                print(f"Default format: Trying fixed line index {line_indices['nationality']}: '{line_nat_am}' | '{line_nat_en}'")
                # Only use if it doesn't look like a label
                if (line_nat_am and not self._is_nationality_label_line(line_nat_am) and 
                    self._is_valid_nationality_value(line_nat_am)):
                    nationality_am = line_nat_am
                if (line_nat_en and not self._is_nationality_label_line(line_nat_en) and 
                    self._is_valid_nationality_value(line_nat_en)):
                    nationality_en = line_nat_en
                print(f"Default format: After fixed line validation: '{nationality_am}' | '{nationality_en}'")
            except Exception as e:
                print(f"Default format: Error extracting from fixed line index: {str(e)}")
                pass

        # Normalize nationality: if one side found, fill the other
        if nationality_en and not nationality_am:
            nationality_am = nationality_en
        if nationality_am and not nationality_en:
            nationality_en = nationality_am

        dates = get_id_dates()
        
        # Prepare base extracted data
        extracted_data = {
            "fcn_full": fcn,
            "name_am": name_am,
            "name_en": name_en,
            "dob_am": dob_am,
            "dob_en": dob_en,
            "gender_am": gender_am,
            "gender_en": gender_en,
            "nationality_am": nationality_am,
            "nationality_en": nationality_en,
            "phone": phone,
            "region_am": region_am,
            "region_en": region_en,
            "subcity_am": subcity_am,
            "subcity_en": subcity_en,
            "woreda_am": woreda_am,
            "woreda_en": woreda_en,
            "issue_date_en": dates['issue_date_greg'],
            "issue_date_am": dates['issue_date_eth'],
            "expiry_date_en": dates['expiry_date_greg'],
            "expiry_date_am": dates['expiry_date_eth'],
            "fin": fin_number,
            "serial_number": self.generate_serial_number(),
        }

        # Extract images specific to default format (original behavior)
        photo_idx = self.PDF_FORMAT_MAPPING['default']['photo_img_index']
        qr_idx = self.PDF_FORMAT_MAPPING['default']['qr_img_index']
        
        print(f"PDF extraction - Found {len(images)} images, photo_idx={photo_idx}, qr_idx={qr_idx}")
        # Use robust classifier to detect photo and QR
        photo_bytes, qr_bytes = self._detect_photo_and_qr(doc, images)
        try:
            if not photo_bytes and len(images) > photo_idx:
                photo_bytes = doc.extract_image(images[photo_idx][0])['image']
            if photo_bytes:
                photo_img = Image.open(BytesIO(photo_bytes)).convert("RGBA")
                photo_path = os.path.join(self.config.STATIC_FOLDER, 'photo_temp.png')
                photo_img.save(photo_path)
                extracted_data["photo"] = 'static/photo_temp.png' 
                print(f"Successfully extracted photo: {photo_path} ({photo_img.size})")
        except Exception as e:
            print(f"Error extracting photo: {str(e)}")
        
        try:
            if not qr_bytes and len(images) > qr_idx:
                qr_bytes = doc.extract_image(images[qr_idx][0])['image']
            if qr_bytes:
                qr_img = Image.open(BytesIO(qr_bytes)).convert("RGBA")
                qr_path = os.path.join(self.config.STATIC_FOLDER, 'qr_temp.png')
                qr_img.save(qr_path)
                extracted_data["qr_path"] = 'static/qr_temp.png' 
                print(f"Successfully extracted QR: {qr_path} ({qr_img.size})")
        except Exception as e:
            print(f"Error extracting QR: {str(e)}")

        return extracted_data



    def _extract_residential_sheger_pdf_data(self, doc: fitz.Document, lines: List[str], images: List[Tuple], fin_number: str) -> Dict:
        """Extract data from Residential Sheger PDF format using line-based approach like default format."""
        line_indices = self.PDF_FORMAT_MAPPING['residential_sheger']
        
        # Ensure lines are padded for safe access
        max_index = max(line_indices.values())
        if len(lines) <= max_index:
            lines += [""] * (max_index + 1 - len(lines))

        # Initialize extracted data with empty values
        extracted = {
            "fcn": "",
            "name_am": "",
            "name_en": "",
            "dob_greg": "",
            "dob_eth": "",
            "gender_am": "",
            "gender_en": "",
            "nationality_am": "",
            "nationality_en": "",
            "phone": "",
            "region_am": "",
            "region_en": "",
            "subcity_am": "",
            "subcity_en": "",
            "woreda_am": "",
            "woreda_en": ""
        }


        
        # Find data by patterns rather than fixed positions
        for i, line in enumerate(lines):
            line_cleaned = line.replace(" ", "")
            
            # Debug: Print what we're checking
            if len(line_cleaned) > 10:  # Only print longer lines to avoid spam
                print(f"Checking line {i}: '{line[:50]}...' (cleaned: '{line_cleaned[:20]}...')")
            
            # FCN extraction with multiple formats (allow labels and mixed characters)
            digits_only = ''.join(ch for ch in line if ch.isdigit())
            if len(digits_only) >= self.config.FCN_LENGTH:
                digits_16 = digits_only[:self.config.FCN_LENGTH]
                if digits_16.isdigit():
                    extracted["fcn"] = ' '.join([digits_16[j:j+4] for j in range(0, len(digits_16), 4)])
                    print(f"Found FCN: '{extracted['fcn']}' from line {i}")
            elif "/" in line and any(char.isdigit() for char in line):  # Date detection
                if extracted["dob_greg"] == "":
                    extracted["dob_greg"] = line
                    print(f"Found DOB Greg: '{line}'")
                else:
                    extracted["dob_eth"] = line
                    print(f"Found DOB Eth: '{line}'")
            elif "|" in line and any(x in line for x in ["Male", "Female", "ወንድ", "ሴት"]):
                # Handle bilingual gender line
                left, right = [p.strip() for p in line.split("|", 1)]
                if left in ["ወንድ", "ሴት"] and right in ["Male", "Female"]:
                    extracted["gender_am"] = left
                    extracted["gender_en"] = right
                    print(f"Found gender pair: '{left}' | '{right}'")
            elif line.strip() in ["ሴት", "ወንድ"]:
                extracted["gender_am"] = line.strip()
                print(f"Found gender AM: '{line.strip()}'")
                if i+1 < len(lines) and lines[i+1].strip() in ["Female", "Male"]:
                    extracted["gender_en"] = lines[i+1].strip()
                    print(f"Found gender EN: '{lines[i+1].strip()}'")

            elif line.replace(" ", "").isdigit() and len(line.replace(" ", "")) == 10:
                extracted["phone"] = line.strip()
                print(f"Found phone: '{line.strip()}'")
        
        # Extract nationality using enhanced label-based approach (same as demographic format)
        if not extracted["nationality_am"] and not extracted["nationality_en"]:
            nationality_found = False
            print(f"Residential: Starting nationality extraction...")
            
            # DIRECT EXTRACTION: Use lines 47 and 48 directly for nationality (Amharic at 47, English at 48)
            if len(lines) > 48:
                line47 = lines[47].strip() if 47 < len(lines) and lines[47] else ""
                line48 = lines[48].strip() if 48 < len(lines) and lines[48] else ""
                
                print(f"Residential: Directly checking lines 47-48 for nationality...")
                print(f"Residential: Line 47: '{line47}'")
                print(f"Residential: Line 48: '{line48}'")
                
                if line47 and line48:
                    # Determine which is Amharic and which is English
                    line47_has_amharic = any(ord(c) > 127 for c in line47)
                    line48_has_amharic = any(ord(c) > 127 for c in line48)
                    line47_is_english = all(ord(c) < 128 for c in line47)
                    line48_is_english = all(ord(c) < 128 for c in line48)
                    
                    # Line 47 is typically Amharic, Line 48 is typically English
                    if line47_has_amharic and line48_is_english:
                        extracted["nationality_am"] = line47
                        extracted["nationality_en"] = line48
                        nationality_found = True
                        print(f"Residential: ✅ Directly extracted nationality from lines 47-48: '{line47}' | '{line48}'")
                    elif line47_is_english and line48_has_amharic:
                        # Reverse order
                        extracted["nationality_am"] = line48
                        extracted["nationality_en"] = line47
                        nationality_found = True
                        print(f"Residential: ✅ Directly extracted nationality from lines 47-48 (reversed): '{line48}' | '{line47}'")
                    else:
                        # Fallback: if validation passes, use them anyway
                        if self._is_valid_nationality_value(line47) or self._is_valid_nationality_value(line48):
                            # Assume line 47 is Amharic if it has non-ASCII, otherwise use as English
                            if line47_has_amharic:
                                extracted["nationality_am"] = line47
                                extracted["nationality_en"] = line48 if line48 else line47
                            elif line48_has_amharic:
                                extracted["nationality_am"] = line48
                                extracted["nationality_en"] = line47
                            else:
                                # Both might be English, use line 47 as Amharic (mirror), line 48 as English
                                extracted["nationality_am"] = line47
                                extracted["nationality_en"] = line48
                            nationality_found = True
                            print(f"Residential: ✅ Directly extracted nationality from lines 47-48 (fallback): '{extracted['nationality_am']}' | '{extracted['nationality_en']}'")
                elif line47:
                    # Only line 47 has data, use for both
                    extracted["nationality_am"] = line47
                    extracted["nationality_en"] = line47
                    nationality_found = True
                    print(f"Residential: ✅ Directly extracted nationality from line 47 only: '{line47}'")
                elif line48:
                    # Only line 48 has data, use for both
                    extracted["nationality_am"] = line48
                    extracted["nationality_en"] = line48
                    nationality_found = True
                    print(f"Residential: ✅ Directly extracted nationality from line 48 only: '{line48}'")
            
            # Only continue with complex pattern matching if direct extraction from lines 47-48 didn't work
            if not nationality_found:
                # First, try direct pattern matching: look for consecutive valid nationality values
                # This handles cases where nationality values exist but label is far away or missing
                print(f"Residential: Direct extraction from lines 47-48 failed, trying pattern matching...")
                for i in range(len(lines) - 1):
                    line1 = lines[i].strip() if i < len(lines) else ""
                    line2 = lines[i + 1].strip() if i + 1 < len(lines) else ""
                    
                    # Debug: Log when we're checking lines 47-48
                    if i == 47:
                        print(f"Residential: 🔍 DEBUG - Checking pair at index {i} (lines {i}-{i+1}): '{line1}' | '{line2}'")
                        print(f"Residential: 🔍 DEBUG - Line1 valid: {self._is_valid_nationality_value(line1) if line1 else False}")
                        print(f"Residential: 🔍 DEBUG - Line2 valid: {self._is_valid_nationality_value(line2) if line2 else False}")
                    
                    if not line1 or not line2:
                        if i == 47:
                            print(f"Residential: 🔍 DEBUG - Skipping empty lines at index {i}")
                        continue
                    
                    # Check if both lines are valid nationality values
                    if self._is_valid_nationality_value(line1) and self._is_valid_nationality_value(line2):
                        if i == 47:
                            print(f"Residential: 🔍 DEBUG - Lines {i}-{i+1} passed validation check!")
                        line1_has_amharic = any(ord(c) > 127 for c in line1)
                        line2_has_amharic = any(ord(c) > 127 for c in line2)
                        line1_is_english = all(ord(c) < 128 for c in line1)
                        line2_is_english = all(ord(c) < 128 for c in line2)
                        
                        if i == 47:
                            print(f"Residential: 🔍 DEBUG - Line1 Amharic: {line1_has_amharic}, English: {line1_is_english}")
                            print(f"Residential: 🔍 DEBUG - Line2 Amharic: {line2_has_amharic}, English: {line2_is_english}")
                            print(f"Residential: 🔍 DEBUG - Bilingual pair condition: {(line1_has_amharic and line2_is_english) or (line1_is_english and line2_has_amharic)}")
                        
                        # If one is Amharic and one is English, we found a bilingual pair
                        if (line1_has_amharic and line2_is_english) or (line1_is_english and line2_has_amharic):
                            if i == 47:
                                print(f"Residential: 🔍 DEBUG - Bilingual pair detected at lines {i}-{i+1}!")
                            if line1_has_amharic and line2_is_english:
                                extracted["nationality_am"] = line1
                                extracted["nationality_en"] = line2
                                print(f"Residential: ✅ Found consecutive nationality values at lines {i}-{i+1}: '{line1}' | '{line2}'")
                                print(f"Residential: 🔍 DEBUG - IMMEDIATELY AFTER SETTING: am='{extracted['nationality_am']}', en='{extracted['nationality_en']}'")
                            else:
                                extracted["nationality_am"] = line2
                                extracted["nationality_en"] = line1
                                print(f"Residential: ✅ Found consecutive nationality values at lines {i}-{i+1}: '{line2}' | '{line1}'")
                                print(f"Residential: 🔍 DEBUG - IMMEDIATELY AFTER SETTING: am='{extracted['nationality_am']}', en='{extracted['nationality_en']}'")
                            nationality_found = True
                            print(f"Residential: 🔍 DEBUG - nationality_found set to True, breaking loop")
                            break
                        else:
                            if i == 47:
                                print(f"Residential: 🔍 DEBUG - Lines {i}-{i+1} are valid but don't form bilingual pair (both Amharic or both English)")
                    else:
                        if i == 47:
                            val1 = self._is_valid_nationality_value(line1) if line1 else False
                            val2 = self._is_valid_nationality_value(line2) if line2 else False
                            print(f"Residential: 🔍 DEBUG - Validation failed for lines {i}-{i+1}: line1={val1}, line2={val2}")
            
            # If direct pattern matching found nationality, skip label-based extraction
            if nationality_found:
                print(f"Residential: Direct pattern matching succeeded, skipping label-based extraction")
                print(f"Residential: 🔍 DEBUG - After loop, nationality values: am='{extracted['nationality_am']}', en='{extracted['nationality_en']}'")
            else:
                # Fall back to label-based extraction
                print(f"Residential: Direct pattern matching failed, trying label-based extraction...")
                print(f"Residential: 🔍 DEBUG - Loop completed without finding nationality, current values: am='{extracted['nationality_am']}', en='{extracted['nationality_en']}'")
            
            if not nationality_found:
                for i, line in enumerate(lines):
                    line_clean = line.strip()
                    if not line_clean:
                        continue
                    
                    # Very flexible nationality label detection
                    has_nationality_label = False
                    
                    # Check for Amharic nationality label "ዜግነት"
                    if "ዜግነት" in line_clean:
                        has_nationality_label = True
                        print(f"Residential: Found Amharic nationality label 'ዜግነት' at line {i}: '{line_clean}'")
                    
                    # Check for English nationality label (use 'if' not 'elif' to catch both)
                    if "nationality" in line_clean.lower():
                        has_nationality_label = True
                        print(f"Residential: Found English nationality label at line {i}: '{line_clean}'")
                    
                    if has_nationality_label:
                        # Method 1: Look for nationality values in the next few lines (Ethiopian ID format: Amharic then English)
                        print(f"Residential: Looking for nationality values in next lines after label...")
                        
                        # Check for the specific Ethiopian ID format: Label, then Amharic value, then English value
                        if i + 2 < len(lines):
                            line1 = lines[i + 1].strip()
                            line2 = lines[i + 2].strip()
                            
                            print(f"Residential: Checking potential nationality line {i + 1}: '{line1}'")
                            print(f"Residential: Checking potential nationality line {i + 2}: '{line2}'")
                            
                            # Check if we have valid nationality values on consecutive lines
                            if (self._is_valid_nationality_value(line1) and 
                                self._is_valid_nationality_value(line2)):
                                
                                # Determine which is Amharic and which is English based on character sets
                                line1_has_amharic = any(ord(c) > 127 for c in line1)
                                line2_has_amharic = any(ord(c) > 127 for c in line2)
                                line1_is_english = all(ord(c) < 128 for c in line1)
                                line2_is_english = all(ord(c) < 128 for c in line2)
                                
                                if line1_has_amharic and line2_is_english:
                                    # Perfect match: Amharic then English (like ኢትዮጵያዊ -> Ethiopian)
                                    extracted["nationality_am"] = line1
                                    extracted["nationality_en"] = line2
                                    print(f"Residential: ✅ Found bilingual nationality (Amharic->English): '{line1}' | '{line2}'")
                                    nationality_found = True
                                elif line1_is_english and line2_has_amharic:
                                    # Reverse order: English then Amharic
                                    extracted["nationality_am"] = line2
                                    extracted["nationality_en"] = line1
                                    print(f"Residential: ✅ Found bilingual nationality (English->Amharic): '{line1}' | '{line2}'")
                                    nationality_found = True
                                elif line1_is_english and line2_is_english:
                                    # Both English (like "United States" -> "United States")
                                    extracted["nationality_am"] = line1
                                    extracted["nationality_en"] = line2 if line2 != line1 else line1
                                    print(f"Residential: ✅ Found English nationality values: '{line1}' | '{line2}'")
                                    nationality_found = True
                        
                        # Fallback: Check each line individually
                        if not nationality_found:
                            for j in range(i + 1, min(i + 5, len(lines))):
                                if j >= len(lines):
                                    break
                                
                                value_line = lines[j].strip()
                                if not value_line:
                                    continue
                                
                                print(f"Residential: Checking line {j}: '{value_line}'")
                                
                                # Check if this line contains a nationality value
                                if self._is_valid_nationality_value(value_line):
                                    # Check for bilingual format (value | value) on same line
                                    if "|" in value_line:
                                        val_parts = value_line.split("|", 1)
                                        if len(val_parts) == 2:
                                            val_left, val_right = [p.strip() for p in val_parts]
                                            if val_left and val_right and self._is_valid_nationality_value(val_left) and self._is_valid_nationality_value(val_right):
                                                extracted["nationality_am"] = val_left
                                                extracted["nationality_en"] = val_right
                                                print(f"Residential: ✅ Found bilingual nationality (same line): '{val_left}' | '{val_right}'")
                                                nationality_found = True
                                                break
                                    
                                    # Single nationality value - use for both fields
                                    else:
                                        extracted["nationality_am"] = value_line
                                        extracted["nationality_en"] = value_line
                                        print(f"Residential: ✅ Found single nationality: '{value_line}'")
                                        nationality_found = True
                                        break
                                else:
                                    print(f"Residential: Line {j} rejected - not a valid nationality value")
                        
                        if nationality_found:
                            break
                        
                        # Method 2: Check if nationality value is on the same line (fallback)
                        if not nationality_found and ("|" in line_clean or ":" in line_clean or "\t" in line_clean):
                            print(f"Residential: Trying same-line extraction as fallback...")
                            # Try different separators
                            separators = ["|", ":", "\t"]
                            for sep in separators:
                                if sep in line_clean:
                                    parts = line_clean.split(sep, 1)
                                    if len(parts) == 2:
                                        left, right = [p.strip() for p in parts]
                                        
                                        # Check which part has the label and which has the value
                                        if ("ዜግነት" in left or "nationality" in left.lower()) and right:
                                            # Value is on the right
                                            if self._is_valid_nationality_value(right):
                                                extracted["nationality_am"] = right
                                                extracted["nationality_en"] = right
                                                print(f"Residential: ✅ Found nationality (same line, right): '{right}'")
                                                nationality_found = True
                                                break
                                        
                                        elif ("ዜግነት" in right or "nationality" in right.lower()) and left:
                                            # Value is on the left
                                            if self._is_valid_nationality_value(left):
                                                extracted["nationality_am"] = left
                                                extracted["nationality_en"] = left
                                                print(f"Residential: ✅ Found nationality (same line, left): '{left}'")
                                                nationality_found = True
                                                break
                            
                            if nationality_found:
                                break
                        
                        # If we found a nationality label but no value, stop searching
                        if not nationality_found:
                            print(f"Residential: Found nationality label but no valid value")
                            break
            
            # Simple fallback: try the existing method if primary extraction failed
            if not extracted["nationality_am"] and not extracted["nationality_en"]:
                print(f"Residential: Primary extraction failed, trying simple fallback...")
                
                try:
                    nat_am_label, nat_en_label = self._extract_nationality_below_label(lines)
                    if nat_am_label or nat_en_label:
                        if self._is_valid_nationality_value(nat_am_label) or self._is_valid_nationality_value(nat_en_label):
                            extracted["nationality_am"] = nat_am_label or nat_en_label
                            extracted["nationality_en"] = nat_en_label or nat_am_label
                            print(f"Residential: ✅ Nationality from fallback method: '{extracted['nationality_am']}' | '{extracted['nationality_en']}'")
                except Exception as e:
                    print(f"Residential: Fallback method failed: {e}")
            
            # If still no nationality found, show debug info and leave empty
            if not extracted["nationality_am"] and not extracted["nationality_en"]:
                print(f"Residential: ❌ No nationality found after all methods")
                print(f"Residential: 🔍 Debug - Lines containing potential nationality keywords:")
                
                # Show lines that might contain nationality for debugging
                nationality_keywords = ["ዜግነት", "nationality", "ኢትዮጵያ", "ethiop", "ኤርትራ", "eritrea", 
                                       "united states", "american", "british", "german", "french", "italian", 
                                       "sudanese", "kenyan", "somali", "usa", "america"]
                
                for i, line in enumerate(lines):
                    line_clean = line.strip()
                    if any(keyword in line_clean.lower() for keyword in nationality_keywords):
                        print(f"Residential: 🔍 Line {i}: '{line_clean}'")
                
                print(f"Residential: No nationality found - leaving empty")

        # Simple fallback: try the existing method if primary extraction failed
        if not extracted["nationality_am"] and not extracted["nationality_en"]:
            print(f"Residential: Primary extraction failed, trying simple fallback...")
            
            try:
                nat_am_label, nat_en_label = self._extract_nationality_below_label(lines)
                if nat_am_label or nat_en_label:
                    if self._is_valid_nationality_value(nat_am_label) or self._is_valid_nationality_value(nat_en_label):
                        extracted["nationality_am"] = nat_am_label or nat_en_label
                        extracted["nationality_en"] = nat_en_label or nat_am_label
                        print(f"Residential: ✅ Nationality from fallback method: '{extracted['nationality_am']}' | '{extracted['nationality_en']}'")
            except Exception as e:
                print(f"Residential: Fallback method failed: {e}")
        
        # If still no nationality found, show debug info and leave empty
        if not extracted["nationality_am"] and not extracted["nationality_en"]:
            print(f"Residential: ❌ No nationality found after all methods")
            print(f"Residential: 🔍 Debug - Lines containing potential nationality keywords:")
            
            # Show lines that might contain nationality for debugging
            nationality_keywords = ["ዜግነት", "nationality", "ኢትዮጵያ", "ethiop", "ኤርትራ", "eritrea", 
                                   "united states", "american", "british", "german", "french", "italian", 
                                   "sudanese", "kenyan", "somali", "usa", "america"]
            
            for i, line in enumerate(lines):
                line_clean = line.strip()
                if any(keyword in line_clean.lower() for keyword in nationality_keywords):
                    print(f"Residential: 🔍 Line {i}: '{line_clean}'")
            
            print(f"Residential: No nationality found - leaving empty")

        # If still no nationality found, leave it empty (don't default to Ethiopian)
        if not extracted["nationality_am"] and not extracted["nationality_en"]:
            print(f"Residential: No nationality found - leaving empty")
        
        # Debug: Print what we extracted
        print(f"Residential Sheger extraction results:")
        print(f"  FCN: '{extracted['fcn']}'")
        print(f"  Name EN: '{extracted['name_en']}'")
        print(f"  Name AM: '{extracted['name_am']}'")
        print(f"  Phone: '{extracted['phone']}'")
        print(f"  Gender: '{extracted['gender_am']}' / '{extracted['gender_en']}'")
        print(f"  Nationality: '{extracted['nationality_am']}' / '{extracted['nationality_en']}'")
        print(f"  Address: '{extracted['region_am']}' / '{extracted['region_en']}' | '{extracted['subcity_am']}' / '{extracted['subcity_en']}' | '{extracted['woreda_am']}' / '{extracted['woreda_en']}'")
        
        # Improved address field extraction (pattern-based bilingual lines)
        address_fields = []
        collecting_address = False
        
        for i, line in enumerate(lines):
            # Start collecting when we hit phone number (address follows phone)
            if extracted["phone"] and line.strip() == extracted["phone"].strip():
                collecting_address = True
                continue
            
            if collecting_address:
                # Stop collecting if we hit the FCN number or name
                if (line.replace(" ", "").isdigit() and len(line.replace(" ", "")) == self.config.FCN_LENGTH) or "ምስጋና" in line:
                        break
                if line.strip():
                    address_fields.append(line.strip())

        # First pass: direct bilingual matching for address
        if not extracted["region_en"] or not extracted["woreda_en"]:
            for ln in lines:
                if "|" not in ln:
                    continue
                left, right = [p.strip() for p in ln.split("|", 1)]
                # Region (look for known region names in English part)
                if not extracted["region_en"] and any(k in right for k in ["Addis Ababa", "Amhara", "Oromia", "Tigray", "Afar", "Somali", "Sidama", "Gambella", "Harari", "SNNP"]):
                    extracted["region_am"], extracted["region_en"] = left, right
                    continue
                # Subcity/Zone
                if not extracted["subcity_en"] and any(k in right.lower() for k in ["zone", "sub city", "subcity"]):
                    extracted["subcity_am"], extracted["subcity_en"] = left, right
                    continue
                # Woreda/Administration
                if not extracted["woreda_en"] and any(k in right.lower() for k in ["woreda", "administration", "admin", "kebele"]):
                    extracted["woreda_am"], extracted["woreda_en"] = left, right
                    continue

        # Process collected address fields (fallback when phone-anchored block works)
        if len(address_fields) >= 6:
            # Region is typically the first two lines (Amharic then English)
            extracted["region_am"] = address_fields[0]
            extracted["region_en"] = address_fields[1]
            
            # Subcity is typically lines 2-3 (Amharic then English)
            extracted["subcity_am"] = address_fields[2]
            extracted["subcity_en"] = address_fields[3]
            
            # Woreda is typically lines 4-5 (Amharic then English)
            extracted["woreda_am"] = address_fields[4]
            extracted["woreda_en"] = address_fields[5]

        # Fallback nationality extraction if none found
        if not extracted["nationality_am"] and not extracted["nationality_en"]:
            try:
                nat_am_label, nat_en_label = self._extract_nationality_below_label(lines)
                if nat_am_label or nat_en_label:
                    # Validate that this is not region, program title, or other non-nationality content
                    combined = (nat_am_label + " " + nat_en_label).lower()
                    if not any(keyword in combined for keyword in 
                               ["ክልል", "region", "ወረዳ", "woreda", "ከተማ", "city", "ፕሮግራም", "program", 
                                "መታወቂያ", "identity", "ብሔራዊ", "national", "የትውልድ", "birth", "ስልክ", "phone"]):
                        # Extract any nationality as-is (no hardcoded mappings)
                        extracted["nationality_am"] = nat_am_label or nat_en_label
                        extracted["nationality_en"] = nat_en_label or nat_am_label
                        print(f"Residential: Nationality from fallback label method: '{extracted['nationality_am']}' | '{extracted['nationality_en']}'")
            except Exception:
                pass
        
        # If still no nationality found, leave it empty (don't default to Ethiopian)
        if not extracted["nationality_am"] and not extracted["nationality_en"]:
            print(f"Residential: No nationality found - leaving empty")
        
        # Debug: Print what we extracted
        print(f"Residential Sheger extraction results:")
        print(f"  FCN: '{extracted['fcn']}'")
        print(f"  Name EN: '{extracted['name_en']}'")
        print(f"  Name AM: '{extracted['name_am']}'")
        print(f"  Phone: '{extracted['phone']}'")
        print(f"  Gender: '{extracted['gender_am']}' / '{extracted['gender_en']}'")
        print(f"  Nationality: '{extracted['nationality_am']}' / '{extracted['nationality_en']}'")
        print(f"  Address: '{extracted['region_am']}' / '{extracted['region_en']}' | '{extracted['subcity_am']}' / '{extracted['subcity_en']}' | '{extracted['woreda_am']}' / '{extracted['woreda_en']}'")
        
        # Improved address field extraction (pattern-based bilingual lines)
        address_fields = []
        collecting_address = False
        
        for i, line in enumerate(lines):
            # Start collecting when we hit phone number (address follows phone)
            if extracted["phone"] and line.strip() == extracted["phone"].strip():
                collecting_address = True
                continue
            
            if collecting_address:
                # Stop collecting if we hit the FCN number or name
                if (line.replace(" ", "").isdigit() and len(line.replace(" ", "")) == self.config.FCN_LENGTH) or "ምስጋና" in line:
                        break
                if line.strip():
                    address_fields.append(line.strip())

        # First pass: direct bilingual matching for address
        if not extracted["region_en"] or not extracted["woreda_en"]:
            for ln in lines:
                if "|" not in ln:
                    continue
                left, right = [p.strip() for p in ln.split("|", 1)]
                # Region (look for known region names in English part)
                if not extracted["region_en"] and any(k in right for k in ["Addis Ababa", "Amhara", "Oromia", "Tigray", "Afar", "Somali", "Sidama", "Gambella", "Harari", "SNNP"]):
                    extracted["region_am"], extracted["region_en"] = left, right
                    continue
                # Subcity/Zone
                if not extracted["subcity_en"] and any(k in right.lower() for k in ["zone", "sub city", "subcity"]):
                    extracted["subcity_am"], extracted["subcity_en"] = left, right
                    continue
                # Woreda/Administration
                if not extracted["woreda_en"] and any(k in right.lower() for k in ["woreda", "administration", "admin", "kebele"]):
                    extracted["woreda_am"], extracted["woreda_en"] = left, right
                    continue

        # Process collected address fields (fallback when phone-anchored block works)
        if len(address_fields) >= 6:
            # Region is typically the first two lines (Amharic then English)
            extracted["region_am"] = address_fields[0]
            extracted["region_en"] = address_fields[1]
            
            # Subcity is typically lines 2-3 (Amharic then English)
            extracted["subcity_am"] = address_fields[2]
            extracted["subcity_en"] = address_fields[3]
            
            # Woreda is typically lines 4-5 (Amharic then English)
            extracted["woreda_am"] = address_fields[4]
            extracted["woreda_en"] = address_fields[5]
        elif len(address_fields) >= 4:
            # Fallback pattern if fewer lines
            extracted["region_am"] = address_fields[0]
            if any(c in address_fields[1] for c in ["ክ", "ፍ", "ለ"]):  # Amharic subcity markers
                extracted["subcity_am"] = address_fields[1]
                if "Sub" in address_fields[2]:  # English subcity marker
                    extracted["subcity_en"] = address_fields[2]
                    extracted["woreda_am"] = address_fields[3]
                else:
                    extracted["woreda_am"] = address_fields[2]
            else:
                extracted["region_en"] = address_fields[1]
                extracted["subcity_am"] = address_fields[2]
                extracted["subcity_en"] = address_fields[3]

        # Final safeguard: look near the end only if names are still missing
        if not extracted["name_en"] or not extracted["name_am"]:
            for i in range(len(lines)-1, -1, -1):
                candidate = lines[i].strip()
                if "|" in candidate or any(ch.isdigit() for ch in candidate) or "/" in candidate:
                    continue
                lower_cand = candidate.lower()
                # Exclude address/labels
                if any(word in lower_cand for word in ["region", "zone", "sub city", "city", "admin", "administration", "woreda", "kebele", "sex", "nationality", "demographic", "disclaimer"]):
                    continue
                if candidate.replace(" ", "").replace("-", "").replace(".", "").isalpha() and len(candidate.split()) >= 2:
                    if not extracted["name_en"]:
                        extracted["name_en"] = candidate
                        if i > 0 and any(ord(c) > 127 for c in lines[i-1]):
                            extracted["name_am"] = lines[i-1].strip()
                    break
        
        # Parse dates with residential-specific mapping
        # Goal:
        # - Amharic -> DD/MM/YY (numeric)
        # - English -> YYYY/Mon/DD
        dob_greg = extracted["dob_greg"]
        dob_am_formatted = ""
        dob_en_formatted = ""

        # Identify which captured string is DD/MM/YYYY and which is YYYY/MM/DD
        cand1 = (extracted.get("dob_greg") or "").strip()
        cand2 = (extracted.get("dob_eth") or "").strip()

        import re
        is_ddmmyyyy = lambda s: bool(re.match(r"^\d{1,2}/\d{1,2}/\d{4}$", s))
        is_yyyymmdd = lambda s: bool(re.match(r"^\d{4}/\d{1,2}/\d{1,2}$", s))

        ddmmyyyy_val = cand1 if is_ddmmyyyy(cand1) else (cand2 if is_ddmmyyyy(cand2) else "")
        yyyymmdd_val = cand1 if is_yyyymmdd(cand1) else (cand2 if is_yyyymmdd(cand2) else "")

        # Format Amharic (DD/MM/YYYY) - ensure 4 digit year
        if ddmmyyyy_val:
            try:
                d, m, y = ddmmyyyy_val.split('/')
                # Ensure 4 digit year for Amharic DOB
                full_year = int(y)
                dob_am_formatted = f"{int(d):02d}/{int(m):02d}/{full_year:04d}"
            except Exception:
                dob_am_formatted = ddmmyyyy_val
        # If not found, try to coerce from YYYY/MM/DD
        elif yyyymmdd_val:
            try:
                y, m, d = yyyymmdd_val.split('/')
                # Ensure 4 digit year for Amharic DOB
                full_year = int(y)
                dob_am_formatted = f"{int(d):02d}/{int(m):02d}/{full_year:04d}"
            except Exception:
                dob_am_formatted = yyyymmdd_val

        # Format English (YYYY/Mon/DD)
        if yyyymmdd_val:
            try:
                dob_en_formatted = datetime.strptime(yyyymmdd_val, "%Y/%m/%d").strftime("%Y/%b/%d")
            except Exception:
                dob_en_formatted = yyyymmdd_val
        elif ddmmyyyy_val:
            try:
                dob_en_formatted = datetime.strptime(ddmmyyyy_val, "%d/%m/%Y").strftime("%Y/%b/%d")
            except Exception:
                dob_en_formatted = ddmmyyyy_val

        # Generate dates
        today_gregorian = date.today()
        eth_issue = gregorian_to_ethiopian(today_gregorian)
        issue_date_eth = f"{eth_issue[0]}/{eth_issue[1]:02d}/{eth_issue[2]:02d}"
        issue_date_greg = today_gregorian.strftime("%Y/%b/%d")

        expiry_gregorian = today_gregorian + relativedelta(years=8)
        eth_expiry = gregorian_to_ethiopian(expiry_gregorian)
        expiry_date_eth = f"{eth_expiry[0]}/{eth_expiry[1]:02d}/{eth_expiry[2]:02d}"
        expiry_date_greg = expiry_gregorian.strftime("%Y/%b/%d")

        # Format the extracted data for the template
        print(f"Residential: 🔍 DEBUG - BEFORE creating processed_data, extracted nationality: am='{extracted['nationality_am']}', en='{extracted['nationality_en']}'")
        processed_data = {
            "photo": None,
            "fcn_formatted": extracted["fcn"],
            "fcn_full": extracted["fcn"].replace(" ", ""),
            "name_am": extracted["name_am"],
            "name_en": extracted["name_en"],
            "dob_am": dob_am_formatted or extracted["dob_eth"],
            "dob_en": dob_en_formatted or dob_greg,
            "gender_am": extracted["gender_am"],
            "gender_en": extracted["gender_en"],
            "nationality_am": extracted["nationality_am"],
            "nationality_en": extracted["nationality_en"],
            "phone": self.format_phone_number(extracted["phone"]),
            "region_am": extracted["region_am"],
            "region_en": extracted["region_en"],
            "subcity_am": extracted["subcity_am"],
            "subcity_en": extracted["subcity_en"],
            "woreda_am": extracted["woreda_am"],
            "woreda_en": extracted["woreda_en"],
            "issue_date_en": issue_date_greg,
            "issue_date_am": issue_date_eth,
            "expiry_date_en": expiry_date_greg,
            "expiry_date_am": expiry_date_eth,
            "fin": fin_number,
            "serial_number": self.generate_serial_number(),
        }

        # Extract images
        photo_idx = self.PDF_FORMAT_MAPPING['residential_sheger']['photo_img_index']
        qr_idx = self.PDF_FORMAT_MAPPING['residential_sheger']['qr_img_index']

        # Robust classifier for residential as well
        det_photo, det_qr = self._detect_photo_and_qr(doc, images)
        if not det_photo and len(images) > photo_idx:
            det_photo = doc.extract_image(images[photo_idx][0])['image']
        if det_photo:
            with open(os.path.join(self.config.STATIC_FOLDER, 'photo_temp.png'), 'wb') as f:
                f.write(det_photo)
            processed_data["photo"] = 'static/photo_temp.png'

        if not det_qr and len(images) > qr_idx:
            det_qr = doc.extract_image(images[qr_idx][0])['image']
        if det_qr:
            with open(os.path.join(self.config.STATIC_FOLDER, 'qr_temp.png'), 'wb') as f:
                f.write(det_qr)
            processed_data["qr_path"] = 'static/qr_temp.png'

        print(f"Residential: 🔍 DEBUG - BEFORE RETURN, processed_data nationality: am='{processed_data['nationality_am']}', en='{processed_data['nationality_en']}'")
        return processed_data

    def _detect_photo_and_qr(self, doc: fitz.Document, images: List[Tuple]) -> Tuple[Optional[bytes], Optional[bytes]]:
        """Classify embedded images into (photo, qr) using heuristics that work for residential PDFs."""
        best_qr = (None, -1.0)  # (bytes, score)
        best_photo = (None, -1.0)

        def qr_score(im: Image.Image) -> float:
            # High contrast black/white, near-square, high edge density
            w, h = im.size
            if w == 0 or h == 0:
                return -1.0
            aspect = w / max(h, 1)
            im_g = im.convert('L').resize((128, 128))
            stat = ImageStat.Stat(im_g)
            mean = stat.mean[0]
            # Binarization contrast proxy
            bw = im_g.point(lambda p: 255 if p > mean else 0)
            hist = bw.histogram()
            black = hist[0]
            white = hist[-1]
            bw_ratio = (black + white) / max(sum(hist), 1)
            # Edge density
            edges = im_g.filter(ImageFilter.FIND_EDGES)
            edge_mean = ImageStat.Stat(edges).mean[0] / 255.0
            square_bonus = 1.0 - min(abs(1.0 - aspect), 0.5)
            return bw_ratio * 0.6 + edge_mean * 0.3 + square_bonus * 0.1

        def _skin_ratio(im: Image.Image) -> float:
            # Approximate skin detection on a downscaled center crop (fast, no deps)
            try:
                w, h = im.size
                if w < 10 or h < 10:
                    return 0.0
                # center crop to avoid borders
                left = int(w * 0.15); right = int(w * 0.85)
                top = int(h * 0.15); bottom = int(h * 0.85)
                crop = im.convert('RGB').crop((left, top, right, bottom)).resize((96, 128))
                hsv = crop.convert('HSV')
                pixels = list(hsv.getdata())
                total = len(pixels)
                skin = 0
                for (hue, sat, val) in pixels:
                    # Normalize to [0,1]
                    H = hue / 255.0; S = sat / 255.0; V = val / 255.0
                    # Simple skin-range rule of thumb
                    if (0.0 <= H <= 0.15 or 0.9 <= H <= 1.0) and 0.15 <= S <= 0.7 and 0.35 <= V <= 0.98:
                        skin += 1
                return skin / max(total, 1)
            except Exception:
                return 0.0

        def photo_score(im: Image.Image) -> float:
            # Prefer portrait orientation, color variance, mid-tones, and skin-tone presence
            w, h = im.size
            if w == 0 or h == 0:
                return -1.0
            aspect = w / max(h, 1)
            portrait = 1.0 if h > w else 0.0
            im_rgb = im.convert('RGB').resize((128, 128))
            var = sum(ImageStat.Stat(im_rgb).var) / 3.0
            var_norm = min(var / 1000.0, 1.0)
            # Penalize extreme black/white content
            im_g = im_rgb.convert('L')
            hist = im_g.histogram()
            total = max(sum(hist), 1)
            low = sum(hist[:32]) / total
            high = sum(hist[-32:]) / total
            midtone = 1.0 - (low + high)
            skin = _skin_ratio(im)
            square_penalty = max(0.0, 1.0 - min(abs(1.0 - aspect), 1.0))  # lower if square
            return portrait * 0.45 + var_norm * 0.2 + midtone * 0.15 + skin * 0.3 - square_penalty * 0.1

        for img in images:
            try:
                xref = img[0]
                data = doc.extract_image(xref)
                img_bytes = data['image']
                with Image.open(BytesIO(img_bytes)) as im:
                    qs = qr_score(im)
                    ps = photo_score(im)
                    if qs > best_qr[1]:
                        best_qr = (img_bytes, qs)
                    if ps > best_photo[1]:
                        best_photo = (img_bytes, ps)
            except Exception:
                continue

        return best_photo[0], best_qr[0]

    def _extract_demographic_format_pdf_data(self, doc: fitz.Document, lines: List[str], images: List[Tuple], fin_number: str) -> Dict:
        """Extract data from demographic format PDF using line-based approach like default format."""
        line_indices = self.PDF_FORMAT_MAPPING['demographic_format']
        
        # Ensure lines are padded for safe access
        max_index = max(line_indices.values())
        if len(lines) <= max_index:
            lines += [""] * (max_index + 1 - len(lines))

        extracted = {
            "fcn": "",
            "name_am": "",
            "name_en": "",
            "dob_greg": "",
            "dob_eth": "",
            "gender_am": "",
            "gender_en": "",
            "nationality_am": "",
            "nationality_en": "",
            "phone": "",
            "region_am": "",
            "region_en": "",
            "subcity_am": "",
            "subcity_en": "",
            "woreda_am": "",
            "woreda_en": ""
        }


        
        # Extract FCN
        for line in lines:
            line_cleaned = line.replace(" ", "")
            if line_cleaned.isdigit() and len(line_cleaned) == self.config.FCN_LENGTH:
                extracted["fcn"] = ' '.join([line_cleaned[j:j+4] for j in range(0, len(line_cleaned), 4)])
                break
        
        # Extract name with flexible pattern matching
        for i, line in enumerate(lines):
            line_clean = line.strip()
            
            # Skip empty lines, numbers, and very short lines
            if not line_clean or len(line_clean) < 3 or line_clean.isdigit():
                continue
                
            # Look for English names (contains only letters, spaces, and possibly dots)
            if (line_clean.replace(" ", "").replace(".", "").isalpha() and 
                len(line_clean.split()) >= 2 and 
                not any(char in line_clean for char in ["/", "|", "የ", "ኢ", "ብ", "ፕ", "ሮ", "ግ", "ራ", "ም"])):
                
                # Check if this looks like a proper name (not an address or label)
                if not any(word.lower() in ["subcity", "woreda", "region", "address", "phone", "date"] for word in line_clean.split()):
                    extracted["name_en"] = line_clean
                    
                    # Look for Amharic name in adjacent lines
                    for offset in [-1, 1]:
                        check_idx = i + offset
                        if 0 <= check_idx < len(lines):
                            check_line = lines[check_idx].strip()
                            # Check if it contains Amharic characters
                            if check_line and any(ord(char) > 127 for char in check_line):
                                # Verify it's not just a label or address
                                if (len(check_line.split()) >= 2 and 
                                    not any(char in check_line for char in ["/", "|", "የ", "ኢ", "ብ", "ፕ", "ሮ", "ግ", "ራ", "ም"]) and
                                    not any(word in check_line for word in ["ወረዳ", "Woreda", "ለሚ", "Lemi", "አራዳ", "Arada"])):
                                    extracted["name_am"] = check_line
                                    break
                    break
            
            # Look for Amharic names (contains Amharic characters)
            elif any(ord(char) > 127 for char in line_clean):
                # Check if it looks like a name (not a label or address)
                if (len(line_clean.split()) >= 2 and 
                    not any(char in line_clean for char in ["/", "|", "የ", "ኢ", "ብ", "ፕ", "ሮ", "ግ", "ራ", "ም"]) and
                    not any(word in line_clean for word in ["ወረዳ", "Woreda", "ለሚ", "Lemi", "አራዳ", "Arada"])):
                    
                    extracted["name_am"] = line_clean
                    
                    # Look for English name in adjacent lines
                    for offset in [-1, 1]:
                        check_idx = i + offset
                        if 0 <= check_idx < len(lines):
                            check_line = lines[check_idx].strip()
                            # Check if it contains only English letters and spaces
                            if (check_line and 
                                check_line.replace(" ", "").replace(".", "").isalpha() and
                                len(check_line.split()) >= 2 and
                                not any(word.lower() in ["subcity", "woreda", "region", "address", "phone", "date"] for word in check_line.split())):
                                extracted["name_en"] = check_line
                                break
                    break
        
        # Extract dates with better logic
        date_lines = []
        for line in lines:
            if "/" in line and any(char.isdigit() for char in line):
                date_lines.append(line.strip())
        
        # Handle combined date format like "21/05/1999 | 2007/01/29"
        for date_line in date_lines:
            if "|" in date_line:
                parts = date_line.split("|")
                if len(parts) == 2:
                    greg_part = parts[0].strip()
                    eth_part = parts[1].strip()
                    extracted["dob_greg"] = greg_part
                    extracted["dob_eth"] = eth_part
                    break
            else:
                # Handle single dates
                if "/" in date_line:
                    parts = date_line.split("/")
                    if len(parts) == 3:
                        # If first part is 2 digits, likely Gregorian (DD/MM/YYYY)
                        if len(parts[0]) == 2 and len(parts[2]) == 4:
                            extracted["dob_greg"] = date_line
                        # If first part is 4 digits, likely Ethiopian (YYYY/MM/DD)
                        elif len(parts[0]) == 4 and len(parts[2]) == 2:
                            extracted["dob_eth"] = date_line
                        # If we can't determine, assign based on position
                        elif extracted["dob_greg"] == "":
                            extracted["dob_greg"] = date_line
                        else:
                            extracted["dob_eth"] = date_line
        
        # If we still don't have dates, try the original logic
        if not extracted["dob_greg"] and not extracted["dob_eth"] and len(date_lines) >= 2:
            extracted["dob_greg"] = date_lines[0]
            extracted["dob_eth"] = date_lines[1]
        elif len(date_lines) == 1:
            extracted["dob_greg"] = date_lines[0]
        
        # Extract gender with improved logic
        for i, line in enumerate(lines):
            line_clean = line.strip()
            if line_clean in ["ሴት", "ወንድ"]:
                extracted["gender_am"] = line_clean
                # Look for English gender in next few lines
                for j in range(i+1, min(i+4, len(lines))):
                    next_line = lines[j].strip()
                    if next_line in ["Female", "Male"]:
                        extracted["gender_en"] = next_line
                        break
                # If no English found, set based on Amharic
                if not extracted["gender_en"]:
                    if line_clean == "ወንድ":
                        extracted["gender_en"] = "Male"
                    elif line_clean == "ሴት":
                        extracted["gender_en"] = "Female"
                break
        
        # Extract nationality using very flexible label-based approach
        nationality_found = False
        print(f"Demographic: Starting nationality extraction...")
        
        for i, line in enumerate(lines):
            line_clean = line.strip()
            if not line_clean:
                continue
            
            # Very flexible nationality label detection
            has_nationality_label = False
            
            # Check for Amharic nationality label "ዜግነት"
            if "ዜግነት" in line_clean:
                has_nationality_label = True
                print(f"Demographic: Found Amharic nationality label 'ዜግነት' at line {i}: '{line_clean}'")
            
            # Check for English nationality label
            elif "nationality" in line_clean.lower():
                has_nationality_label = True
                print(f"Demographic: Found English nationality label at line {i}: '{line_clean}'")
            
            if has_nationality_label:
                # Method 1: Look for nationality values in the next few lines (Ethiopian ID format: Amharic then English)
                print(f"Demographic: Looking for nationality values in next lines after label...")
                
                # Check for the specific Ethiopian ID format: Label, then Amharic value, then English value
                if i + 2 < len(lines):
                    line1 = lines[i + 1].strip()
                    line2 = lines[i + 2].strip()
                    
                    print(f"Demographic: Checking potential nationality line {i + 1}: '{line1}'")
                    print(f"Demographic: Checking potential nationality line {i + 2}: '{line2}'")
                    
                    # Check if we have valid nationality values on consecutive lines
                    if (self._is_valid_nationality_value(line1) and 
                        self._is_valid_nationality_value(line2)):
                        
                        # Determine which is Amharic and which is English based on character sets
                        line1_has_amharic = any(ord(c) > 127 for c in line1)
                        line2_has_amharic = any(ord(c) > 127 for c in line2)
                        line1_is_english = all(ord(c) < 128 for c in line1)
                        line2_is_english = all(ord(c) < 128 for c in line2)
                        
                        if line1_has_amharic and line2_is_english:
                            # Perfect match: Amharic then English (like ኢትዮጵያዊ -> Ethiopian)
                            extracted["nationality_am"] = line1
                            extracted["nationality_en"] = line2
                            print(f"Demographic: ✅ Found bilingual nationality (Amharic->English): '{line1}' | '{line2}'")
                            nationality_found = True
                        elif line1_is_english and line2_has_amharic:
                            # Reverse order: English then Amharic
                            extracted["nationality_am"] = line2
                            extracted["nationality_en"] = line1
                            print(f"Demographic: ✅ Found bilingual nationality (English->Amharic): '{line1}' | '{line2}'")
                            nationality_found = True
                        elif line1_is_english and line2_is_english:
                            # Both English (like "United States" -> "United States")
                            extracted["nationality_am"] = line1
                            extracted["nationality_en"] = line2 if line2 != line1 else line1
                            print(f"Demographic: ✅ Found English nationality values: '{line1}' | '{line2}'")
                            nationality_found = True
                
                # Fallback: Check each line individually
                if not nationality_found:
                    for j in range(i + 1, min(i + 5, len(lines))):
                        if j >= len(lines):
                            break
                        
                        value_line = lines[j].strip()
                        if not value_line:
                            continue
                        
                        print(f"Demographic: Checking line {j}: '{value_line}'")
                        
                        # Check if this line contains a nationality value
                        if self._is_valid_nationality_value(value_line):
                            # Check for bilingual format (value | value) on same line
                            if "|" in value_line:
                                val_parts = value_line.split("|", 1)
                                if len(val_parts) == 2:
                                    val_left, val_right = [p.strip() for p in val_parts]
                                    if val_left and val_right and self._is_valid_nationality_value(val_left) and self._is_valid_nationality_value(val_right):
                                        extracted["nationality_am"] = val_left
                                        extracted["nationality_en"] = val_right
                                        print(f"Demographic: ✅ Found bilingual nationality (same line): '{val_left}' | '{val_right}'")
                                        nationality_found = True
                                        break
                            
                            # Single nationality value - use for both fields
                            else:
                                extracted["nationality_am"] = value_line
                                extracted["nationality_en"] = value_line
                                print(f"Demographic: ✅ Found single nationality: '{value_line}'")
                                nationality_found = True
                                break
                        else:
                            print(f"Demographic: Line {j} rejected - not a valid nationality value")
                
                if nationality_found:
                    break
                
                # Method 2: Check if nationality value is on the same line (fallback)
                if not nationality_found and ("|" in line_clean or ":" in line_clean or "\t" in line_clean):
                    print(f"Demographic: Trying same-line extraction as fallback...")
                    # Try different separators
                    separators = ["|", ":", "\t"]
                    for sep in separators:
                        if sep in line_clean:
                            parts = line_clean.split(sep, 1)
                            if len(parts) == 2:
                                left, right = [p.strip() for p in parts]
                                
                                # Check which part has the label and which has the value
                                if ("ዜግነት" in left or "nationality" in left.lower()) and right:
                                    # Value is on the right
                                    if self._is_valid_nationality_value(right):
                                        extracted["nationality_am"] = right
                                        extracted["nationality_en"] = right
                                        print(f"Demographic: ✅ Found nationality (same line, right): '{right}'")
                                        nationality_found = True
                                        break
                                
                                elif ("ዜግነት" in right or "nationality" in right.lower()) and left:
                                    # Value is on the left
                                    if self._is_valid_nationality_value(left):
                                        extracted["nationality_am"] = left
                                        extracted["nationality_en"] = left
                                        print(f"Demographic: ✅ Found nationality (same line, left): '{left}'")
                                        nationality_found = True
                                        break
                    
                    if nationality_found:
                        break
                
                # If we found a nationality label but no value, stop searching
                if not nationality_found:
                    print(f"Demographic: Found nationality label but no valid value")
                    break
        
        # Simple fallback: try the existing method if primary extraction failed
        if not extracted["nationality_am"] and not extracted["nationality_en"]:
            print(f"Demographic: Primary extraction failed, trying simple fallback...")
            
            try:
                nat_am_label, nat_en_label = self._extract_nationality_below_label(lines)
                if nat_am_label or nat_en_label:
                    if self._is_valid_nationality_value(nat_am_label) or self._is_valid_nationality_value(nat_en_label):
                        extracted["nationality_am"] = nat_am_label or nat_en_label
                        extracted["nationality_en"] = nat_en_label or nat_am_label
                        print(f"Demographic: ✅ Nationality from fallback method: '{extracted['nationality_am']}' | '{extracted['nationality_en']}'")
            except Exception as e:
                print(f"Demographic: Fallback method failed: {e}")
        
        # If still no nationality found, show debug info and leave empty
        if not extracted["nationality_am"] and not extracted["nationality_en"]:
            print(f"Demographic: ❌ No nationality found after all methods")
            print(f"Demographic: 🔍 Debug - Lines containing potential nationality keywords:")
            
            # Show lines that might contain nationality for debugging
            nationality_keywords = ["ዜግነት", "nationality", "ኢትዮጵያ", "ethiop", "ኤርትራ", "eritrea", 
                                   "united states", "american", "british", "german", "french", "italian", 
                                   "sudanese", "kenyan", "somali", "usa", "america"]
            
            for i, line in enumerate(lines):
                line_clean = line.strip()
                if any(keyword in line_clean.lower() for keyword in nationality_keywords):
                    print(f"Demographic: 🔍 Line {i}: '{line_clean}'")
            
            print(f"Demographic: No nationality found - leaving empty")
        
        # Extract phone
        for line in lines:
            if line.replace(" ", "").isdigit() and len(line.replace(" ", "")) == 10:
                extracted["phone"] = line.strip()
                break
        
        # Extract address fields with improved logic        
        for i, line in enumerate(lines):
            line_clean = line.strip()
            
            # Skip if line is just digits (FCN) or too short
            if line_clean.replace(" ", "").isdigit() and len(line_clean.replace(" ", "")) == 16:
                continue
            if len(line_clean) < 3:
                continue            
            # Check for specific address content first
            if "አዲስ አበባ" in line_clean:
                extracted["region_am"] = "አዲስ አበባ"
                extracted["region_en"] = "Addis Ababa"
            elif "Addis Ababa" in line_clean:
                extracted["region_en"] = "Addis Ababa"
                if not extracted["region_am"]:
                    extracted["region_am"] = "አዲስ አበባ"
            elif "ለሚ ኩራ" in line_clean:
                extracted["subcity_am"] = "ለሚ ኩራ"
                extracted["subcity_en"] = "Lemi Kura"
            elif "Lemi Kura" in line_clean:
                extracted["subcity_en"] = "Lemi Kura"
                if not extracted["subcity_am"]:
                    extracted["subcity_am"] = "ለሚ ኩራ"
            elif "ወረዳ" in line_clean and any(c.isdigit() for c in line_clean):
                # Extract woreda number - look for 2-digit numbers
                import re
                numbers = re.findall(r'\d+', line_clean)
                if numbers:
                    woreda_num = numbers[0]
                    extracted["woreda_am"] = f"ወረዳ {woreda_num}"
                    extracted["woreda_en"] = f"Woreda {woreda_num}"
            elif "Woreda" in line_clean and any(c.isdigit() for c in line_clean):
                # Extract woreda number - look for 2-digit numbers
                import re
                numbers = re.findall(r'\d+', line_clean)
                if numbers:
                    woreda_num = numbers[0]
                    extracted["woreda_en"] = f"Woreda {woreda_num}"
                    if not extracted["woreda_am"]:
                        extracted["woreda_am"] = f"ወረዳ {woreda_num}"
        
        print(f"  region_am: '{extracted['region_am']}'")
        print(f"  region_en: '{extracted['region_en']}'")
        print(f"  subcity_am: '{extracted['subcity_am']}'")
        print(f"  subcity_en: '{extracted['subcity_en']}'")
        print(f"  woreda_am: '{extracted['woreda_am']}'")
        print(f"  woreda_en: '{extracted['woreda_en']}'")
        
        # Parse dates
        dob_greg = extracted["dob_greg"]
        # Initialize date variables
        issue_date_eth = ""
        issue_date_greg = ""
        expiry_date_eth = ""
        expiry_date_greg = ""
        
        if extracted["dob_greg"] and not extracted["dob_greg"].startswith("000"):
            # Check if it's still the combined format
            if "|" in extracted["dob_greg"]:
                parts = extracted["dob_greg"].split("|")
                if len(parts) == 2:
                    greg_part = parts[0].strip()
                    try:
                        # Try DD/MM/YYYY format first
                        dob_greg_obj = datetime.strptime(greg_part, "%d/%m/%Y")
                        dob_greg = dob_greg_obj.strftime("%Y/%b/%d")
                    except ValueError:
                        dob_greg = greg_part  # Keep original if parsing fails
            else:
                try:
                    # Try DD/MM/YYYY format first
                    dob_greg_obj = datetime.strptime(extracted["dob_greg"], "%d/%m/%Y")
                    dob_greg = dob_greg_obj.strftime("%Y/%b/%d")
                except ValueError:
                    try:
                        # Try YYYY/MM/DD format
                        dob_greg_obj = datetime.strptime(extracted["dob_greg"], "%Y/%m/%d")
                        dob_greg = dob_greg_obj.strftime("%Y/%b/%d")
                    except ValueError:
                        dob_greg = extracted["dob_greg"]  # Keep original if parsing fails
        else:
            # Generate dates
            today_gregorian = date.today()
            eth_issue = gregorian_to_ethiopian(today_gregorian)
            issue_date_eth = f"{eth_issue[0]}/{eth_issue[1]:02d}/{eth_issue[2]:02d}"
            issue_date_greg = today_gregorian.strftime("%Y/%b/%d")
            
            expiry_gregorian = today_gregorian + relativedelta(years=8)
            eth_expiry = gregorian_to_ethiopian(expiry_gregorian)
            expiry_date_eth = f"{eth_expiry[0]}/{eth_expiry[1]:02d}/{eth_expiry[2]:02d}"
            expiry_date_greg = expiry_gregorian.strftime("%Y/%b/%d")
        
        # Debug: Print extracted data
        print(f"  dob_eth: '{extracted['dob_eth']}'")
        print(f"  dob_greg: '{extracted['dob_greg']}'")
        print(f"  fcn: '{extracted['fcn']}'")
        print(f"  name_am: '{extracted['name_am']}'")
        print(f"  name_en: '{extracted['name_en']}'")
        
        # Format the extracted data
        processed_data = {
            "photo": None,
            "fcn_formatted": extracted["fcn"],
            "fcn_full": extracted["fcn"].replace(" ", ""),
            "name_am": extracted["name_am"],
            "name_en": extracted["name_en"],
            "dob_am": extracted["dob_eth"],
            "dob_en": dob_greg,
            "gender_am": extracted["gender_am"],
            "gender_en": extracted["gender_en"],
            "nationality_am": extracted["nationality_am"],
            "nationality_en": extracted["nationality_en"],
            "phone": self.format_phone_number(extracted["phone"]),
            "region_am": extracted["region_am"],
            "region_en": extracted["region_en"],
            "subcity_am": extracted["subcity_am"],
            "subcity_en": extracted["subcity_en"],
            "woreda_am": extracted["woreda_am"],
            "woreda_en": extracted["woreda_en"],
            "issue_date_en": issue_date_greg,
            "issue_date_am": issue_date_eth,
            "expiry_date_en": expiry_date_greg,
            "expiry_date_am": expiry_date_eth,
            "fin": extracted["fcn"].replace(" ", ""),  # Use extracted FCN from PDF
            "serial_number": self.generate_serial_number(),
        }
        
        # Fix date assignments - swap them to match expected format
        processed_data["dob_am"] = dob_greg  # Gregorian date for Amharic field
        processed_data["dob_en"] = extracted["dob_eth"]  # Ethiopian date for English field
        
        print(f"  dob_am: '{processed_data['dob_am']}'")
        print(f"  dob_en: '{processed_data['dob_en']}'")
        print(f"  fin: '{processed_data['fin']}'")        

        
        # Extract images
        photo_idx = self.PDF_FORMAT_MAPPING['demographic_format']['photo_img_index']
        qr_idx = self.PDF_FORMAT_MAPPING['demographic_format']['qr_img_index']
        
        if len(images) > photo_idx:
            photo_bytes = doc.extract_image(images[photo_idx][0])['image']
            photo_img = Image.open(BytesIO(photo_bytes)).convert("RGBA")
            photo_img.save(os.path.join(self.config.STATIC_FOLDER, 'photo_temp.png'))
            processed_data["photo"] = 'static/photo_temp.png'
        
        if len(images) > qr_idx:
            qr_bytes = doc.extract_image(images[qr_idx][0])['image']
            qr_img = Image.open(BytesIO(qr_bytes)).convert("RGBA")
            qr_img.save(os.path.join(self.config.STATIC_FOLDER, 'qr_temp.png'))
            processed_data["qr_path"] = 'static/qr_temp.png'
        
        # Final woreda extraction attempt - try to find any remaining address-like information
        if not extracted["woreda_am"] and not extracted["woreda_en"]:
            print("Woreda still missing, trying final extraction attempt...")
            for i, line in enumerate(lines):
                line_clean = line.strip()
                # Skip if already processed or too short
                if len(line_clean) < 3 or any(c.isdigit() for c in line_clean):
                    continue
                
                # Look for any line that might be woreda (not region, not subcity, not just labels)
                if (line_clean and 
                    "አዲስ አበባ" not in line_clean and 
                    "Addis Ababa" not in line_clean and
                    line_clean not in ["ወረዳ", "Woreda", "ወረዳ/", "Woreda/", "ወረዳ / Woreda", "ወረዳ/Woreda"] and
                    not any(subcity in line_clean for subcity in ["ለሚ ኩራ", "Lemi Kura", "አራዳ", "Arada", "ቂርቆስ", "Kirkos", "የካ", "Yeka", "አዲስ ከተማ", "Addis Ketema", "ልደታ", "Lideta", "ቦሌ", "Bole", "ኮልፌ ከራን", "Kolfe Keranio", "ንፋስ ስልክ ላፍቶ", "Nifas Silk Lafto", "ሰራበተ", "Serabeta"])):
                    
                    if "|" in line_clean:
                        parts = line_clean.split("|")
                        if len(parts) == 2:
                            amharic_part = parts[0].strip()
                            english_part = parts[1].strip()
                            # Validate that we have actual content, not just labels
                            if (len(amharic_part) > 2 and len(english_part) > 2 and
                                amharic_part not in ["ወረዳ", "ወረዳ/"] and 
                                english_part not in ["Woreda", "Woreda/"]):
                                extracted["woreda_am"] = amharic_part
                                extracted["woreda_en"] = english_part
                                print(f"Final woreda extraction: '{amharic_part}' | '{english_part}' from line {i}")
                                break
                    else:
                        # Single language line - validate content
                        if len(line_clean) > 3 and line_clean not in ["ወረዳ", "Woreda"]:
                            if any('\u1200' <= c <= '\u137F' for c in line_clean):  # Amharic
                                extracted["woreda_am"] = line_clean
                                print(f"Final woreda extraction (Amharic): '{line_clean}' from line {i}")
                            else:
                                extracted["woreda_en"] = line_clean
                                print(f"Final woreda extraction (English): '{line_clean}' from line {i}")
                            break
        
        # Log final woreda extraction results
        print(f"Final woreda extraction results:")
        print(f"  woreda_am: '{extracted.get('woreda_am', '')}'")
        print(f"  woreda_en: '{extracted.get('woreda_en', '')}'")
        
        return processed_data
    
    def _check_missing_fields(self, data: Dict) -> List[str]:
        """Check for missing critical fields in extracted data."""
        missing_fields = []
        critical_fields = ['gender_am', 'gender_en', 'nationality_am', 'nationality_en', 
                          'region_am', 'region_en', 'subcity_am', 'subcity_en', 
                          'woreda_am', 'woreda_en', 'phone', 'dob_am', 'fin', 'name_am', 'name_en']
        
        for field in critical_fields:
            if not data.get(field) or data.get(field).strip() == "":
                missing_fields.append(field)
        return missing_fields
    def _extract_compact_format_pdf_data(self, doc: fitz.Document, lines: List[str], images: List[Tuple], fin_number: str) -> Dict:
        """Extract data from compact format PDF (300KB-900KB file size) with sequential line structure."""
        line_indices = self.PDF_FORMAT_MAPPING['compact_format']

        print("🔍 Using compact format extraction (300KB-900KB PDF)")
        print(f"🔍 Total lines in PDF: {len(lines)}")
        
        # Debug: Print lines around data area (40-60)
        print("🔍 Lines 40-60 (data area):")
        for i in range(40, min(61, len(lines))):
            print(f"  Line {i}: '{lines[i]}'")


        extracted = {
            "fcn": "",
            "name_am": "",
            "name_en": "",
            "dob_greg": "",
            "dob_eth": "",
            "gender_am": "",
            "gender_en": "",
            "nationality_am": "",
            "nationality_en": "",
            "phone": "",
            "region_am": "",
            "region_en": "",
            "subcity_am": "",
            "subcity_en": "",
            "woreda_am": "",
            "woreda_en": ""
        }

        # Extract FCN - look for 16-digit number
        for i, line in enumerate(lines):
            line_cleaned = line.replace(" ", "")
            if line_cleaned.isdigit() and len(line_cleaned) == self.config.FCN_LENGTH:
                extracted["fcn"] = ' '.join([line_cleaned[j:j+4] for j in range(0, len(line_cleaned), 4)])
                print(f"✅ Compact: FCN found at line {i}: {extracted['fcn']}")

                # After FCN, expect name on next lines
                if i + 1 < len(lines) and i + 2 < len(lines):
                    # Check if next line is Amharic name
                    next_line = lines[i + 1].strip()
                    next_next_line = lines[i + 2].strip()

                    if any(ord(c) > 127 for c in next_line) and len(next_line.split()) >= 2:
                        extracted["name_am"] = next_line
                        print(f"✅ Compact: Amharic name found at line {i+1}: {next_line}")

                    if all(ord(c) < 128 or c == ' ' for c in next_next_line) and len(next_next_line.split()) >= 2:
                        extracted["name_en"] = next_next_line
                        print(f"✅ Compact: English name found at line {i+2}: {next_next_line}")
                break

        # Extract dates - look for date with | separator (after FCN)
        # Handle both single-line and split-line date formats
        for i, line in enumerate(lines):
            if i > 41:  # Only look after FCN line
                # Case 1: Date on single line with pipe separator
                if '|' in line and '/' in line:
                    parts = line.split('|')
                    if len(parts) == 2:
                        left, right = parts[0].strip(), parts[1].strip()
                        # Check if both sides have date format
                        if '/' in left and '/' in right and left.count('/') == 2 and right.count('/') == 2:
                            # Skip if this is a label line
                            if ("Date of Birth" not in line and "የትውልድ ቀን" not in line and
                                "Zone" not in line and "ዞን" not in line and
                                "Region" not in line and "ክልል" not in line):
                                # Verify it looks like a date (has digits)
                                if any(c.isdigit() for c in left) and any(c.isdigit() for c in right):
                                    extracted["dob_greg"] = left
                                    extracted["dob_eth"] = right
                                    print(f"✅ Compact: DOB found at line {i}: {left} | {right}")
                                    break
                
                # Case 2: Date split across two lines (first line has date, second line has "| date")
                if '/' in line and line.count('/') == 2 and i + 1 < len(lines):
                    next_line = lines[i + 1].strip()
                    if next_line.startswith('|') and '/' in next_line:
                        date1 = line.strip()
                        date2 = next_line.replace('|', '').strip()
                        if date2.count('/') == 2:
                            extracted["dob_greg"] = date1
                            extracted["dob_eth"] = date2
                            print(f"✅ Compact: DOB found (split) at lines {i}-{i+1}: {date1} | {date2}")
                            break
        
        # Fallback: Check if date is split across two lines
        if not extracted["dob_greg"]:
            for i in range(42, 50):  # After FCN, before region
                if i < len(lines) and i + 1 < len(lines):
                    line1 = lines[i].strip()
                    line2 = lines[i + 1].strip()
                    # Check if line1 is a date and line2 starts with |
                    if ('/' in line1 and line1.count('/') == 2 and 
                        line2.startswith('|') and '/' in line2):
                        date_part2 = line2.replace('|', '').strip()
                        if date_part2.count('/') == 2:
                            extracted["dob_greg"] = line1
                            extracted["dob_eth"] = date_part2
                            print(f"✅ Compact: DOB found (split lines) at lines {i}-{i+1}: {line1} | {date_part2}")
                            break

        # Extract gender - look for ሴት/ወንድ followed by Female/Male
        for i, line in enumerate(lines):
            line_clean = line.strip()
            if line_clean in ["ሴት", "ወንድ"]:
                extracted["gender_am"] = line_clean
                print(f"✅ Compact: Amharic gender found at line {i}: {line_clean}")

                # Look for English gender in next few lines
                for j in range(i + 1, min(i + 4, len(lines))):
                    next_line = lines[j].strip()
                    if next_line in ["Female", "Male"]:
                        extracted["gender_en"] = next_line
                        print(f"✅ Compact: English gender found at line {j}: {next_line}")
                        break
                break

        # Extract nationality - look for ኢትዮጵያዊ followed by Ethiopian
        for i, line in enumerate(lines):
            line_clean = line.strip()
            if line_clean == "ኢትዮጵያዊ":
                extracted["nationality_am"] = line_clean
                print(f"✅ Compact: Amharic nationality found at line {i}: {line_clean}")

                # Look for English nationality in next line
                if i + 1 < len(lines):
                    next_line = lines[i + 1].strip()
                    if next_line == "Ethiopian":
                        extracted["nationality_en"] = next_line
                        print(f"✅ Compact: English nationality found at line {i+1}: {next_line}")
                break

        # Extract phone - look for 10-digit number (not FCN)
        for i, line in enumerate(lines):
            line_clean = line.replace(" ", "").replace("+", "").replace("-", "")
            if line_clean.isdigit() and len(line_clean) == 10:
                extracted["phone"] = line.strip()
                print(f"✅ Compact: Phone found at line {i}: {line.strip()}")
                break

        # Extract region - look for ኦሮሚያ/Oromia or አዲስ አበባ/Addis Ababa
        known_regions_am = ["ኦሮሚያ", "አዲስ አበባ", "አማራ", "ትግራይ", "ደቡብ", "ሲዳማ", "አፋር", "ሶማሌ"]
        known_regions_en = ["Oromia", "Addis Ababa", "Amhara", "Tigray", "South", "Sidama", "Afar", "Somali"]

        for i, line in enumerate(lines):
            line_clean = line.strip()
            if line_clean in known_regions_am:
                extracted["region_am"] = line_clean
                print(f"✅ Compact: Amharic region found at line {i}: {line_clean}")

                # Look for English region in next line
                if i + 1 < len(lines):
                    next_line = lines[i + 1].strip()
                    if next_line in known_regions_en:
                        extracted["region_en"] = next_line
                        print(f"✅ Compact: English region found at line {i+1}: {next_line}")
                break

        # Extract subcity - look for lines with "ከተማ አስተዳደር" or "City Administration" (after region)
        for i, line in enumerate(lines):
            if i > 46 and ("ከተማ አስተዳደር" in line or "City Administration" in line):  # After region
                # Skip if this is just a label
                if ("ዞን/ከተማ አስተዳደር/ክፍለ ከተማ" in line or "Zone/City Admin/Sub City" in line or
                    "ክልል/ከተማ አስተዳደር" in line or "Region/City Admin" in line):
                    continue
                
                # Check if it's a bilingual line with actual subcity name
                if "|" in line:
                    parts = line.split("|")
                    if len(parts) == 2:
                        left, right = parts[0].strip(), parts[1].strip()
                        # Must have actual subcity name (not just labels)
                        if (len(left) > 10 and len(right) > 10 and
                            "ዞን" not in left and "Zone" not in right):
                            extracted["subcity_am"] = left
                            extracted["subcity_en"] = right
                            print(f"✅ Compact: Subcity found at line {i}: {left} | {right}")
                            break
        
        # Fallback: If subcity not found, look for any bilingual line between region and nationality
        # Also handle split-line format (Amharic on one line, English on next)
        if not extracted["subcity_am"] and extracted["region_am"]:
            print("🔍 Looking for subcity in fallback mode...")
            for i in range(47, 55):  # Between region (46-47) and nationality (53-54)
                if i < len(lines):
                    line = lines[i]
                    print(f"  Checking line {i}: '{line}'")
                    
                    # Case 1: Bilingual on same line with pipe
                    if "|" in line and len(line) > 20:
                        parts = line.split("|")
                        if len(parts) == 2:
                            left, right = parts[0].strip(), parts[1].strip()
                            # Skip gender and other known fields
                            if (left not in ["ወንድ", "ሴት", "|"] and right not in ["Male", "Female", ""] and
                                "Date" not in line and "ቀን" not in line and
                                len(left) > 3 and len(right) > 3):
                                extracted["subcity_am"] = left
                                extracted["subcity_en"] = right
                                print(f"✅ Compact: Subcity found (fallback) at line {i}: {left} | {right}")
                                break
                    
                    # Case 2: Amharic on one line, English on next line
                    if (i + 1 < len(lines) and 
                        any(ord(c) > 127 for c in line) and 
                        len(line.strip()) > 2 and
                        line.strip() not in ["ወንድ", "ሴት", "|"]):
                        next_line = lines[i + 1].strip()
                        if (all(ord(c) < 128 or c == ' ' for c in next_line) and 
                            len(next_line) > 2 and
                            next_line not in ["Male", "Female"] and
                            not next_line.isdigit()):
                            extracted["subcity_am"] = line.strip()
                            extracted["subcity_en"] = next_line
                            print(f"✅ Compact: Subcity found (split) at lines {i}-{i+1}: {line.strip()} | {next_line}")
                            break

        # Extract woreda - look for woreda name (usually after subcity)
        for i, line in enumerate(lines):
            line_clean = line.strip()
            # Skip labels and empty lines
            if not line_clean or "ወረዳ" in line_clean or "Woreda" in line_clean:
                if "|" in line_clean and "ወረዳ/ከተማ አስተዳደር/ቀበሌ" not in line_clean:
                    # This might be a woreda value with separator
                    parts = line_clean.split("|")
                    if len(parts) == 2:
                        left, right = parts[0].strip(), parts[1].strip()
                        if len(left) > 2 and len(right) > 2:
                            extracted["woreda_am"] = left
                            extracted["woreda_en"] = right
                            print(f"✅ Compact: Woreda found at line {i}: {left} | {right}")
                            break
                continue

            # Look for woreda name (after nationality, before phone)
            if (extracted["nationality_am"] and not extracted["woreda_am"] and 
                any(ord(c) > 127 for c in line_clean) and len(line_clean) > 2 and
                i > 53 and i < 56):  # Between nationality (52-53) and phone (56)
                # Check if next line is English translation
                if i + 1 < len(lines):
                    next_line = lines[i + 1].strip()
                    if (all(ord(c) < 128 or c == ' ' or c == '-' for c in next_line) and 
                        len(next_line) > 2 and not next_line.isdigit() and
                        "Digital ID" not in next_line and "Issue Date" not in next_line):
                        extracted["woreda_am"] = line_clean
                        extracted["woreda_en"] = next_line
                        print(f"✅ Compact: Woreda found at lines {i}-{i+1}: {line_clean} | {next_line}")
                        break
        
        # Fallback: If woreda not found, look for any Amharic text after nationality
        if not extracted["woreda_am"] and extracted["nationality_am"]:
            print("🔍 Looking for woreda in fallback mode...")
            for i in range(54, 57):  # After nationality, before phone
                if i < len(lines) and i + 1 < len(lines):
                    line_clean = lines[i].strip()
                    next_line = lines[i + 1].strip()
                    print(f"  Checking lines {i}-{i+1}: '{line_clean}' | '{next_line}'")
                    # Check if it's Amharic followed by English
                    if (any(ord(c) > 127 for c in line_clean) and 
                        all(ord(c) < 128 or c == ' ' or c == '-' for c in next_line) and
                        len(line_clean) > 2 and len(next_line) > 2 and
                        not line_clean.isdigit() and not next_line.isdigit() and
                        "Digital ID" not in next_line and "Issue" not in next_line):
                        extracted["woreda_am"] = line_clean
                        extracted["woreda_en"] = next_line
                        print(f"✅ Compact: Woreda found (fallback) at lines {i}-{i+1}: {line_clean} | {next_line}")
                        break

        # Parse dates
        dob_greg = extracted["dob_greg"]
        issue_date_eth = ""
        issue_date_greg = ""
        expiry_date_eth = ""
        expiry_date_greg = ""

        if extracted["dob_greg"]:
            try:
                dob_greg_obj = datetime.strptime(extracted["dob_greg"], "%d/%m/%Y")
                dob_greg = dob_greg_obj.strftime("%Y/%b/%d")
            except ValueError:
                try:
                    dob_greg_obj = datetime.strptime(extracted["dob_greg"], "%Y/%m/%d")
                    dob_greg = dob_greg_obj.strftime("%Y/%b/%d")
                except ValueError:
                    dob_greg = extracted["dob_greg"]

        # Generate issue and expiry dates
        today_gregorian = date.today()
        eth_issue = gregorian_to_ethiopian(today_gregorian)
        issue_date_eth = f"{eth_issue[0]}/{eth_issue[1]:02d}/{eth_issue[2]:02d}"
        issue_date_greg = today_gregorian.strftime("%Y/%b/%d")

        expiry_gregorian = today_gregorian + relativedelta(years=8)
        eth_expiry = gregorian_to_ethiopian(expiry_gregorian)
        expiry_date_eth = f"{eth_expiry[0]}/{eth_expiry[1]:02d}/{eth_expiry[2]:02d}"
        expiry_date_greg = expiry_gregorian.strftime("%Y/%b/%d")

        # Format the extracted data
        processed_data = {
            "photo": None,
            "fcn_formatted": extracted["fcn"],
            "fcn_full": extracted["fcn"].replace(" ", ""),
            "name_am": extracted["name_am"],
            "name_en": extracted["name_en"],
            "dob_am": dob_greg,
            "dob_en": extracted["dob_eth"],
            "gender_am": extracted["gender_am"],
            "gender_en": extracted["gender_en"],
            "nationality_am": extracted["nationality_am"],
            "nationality_en": extracted["nationality_en"],
            "phone": self.format_phone_number(extracted["phone"]) if extracted["phone"] else "",
            "region_am": extracted["region_am"],
            "region_en": extracted["region_en"],
            "subcity_am": extracted["subcity_am"],
            "subcity_en": extracted["subcity_en"],
            "woreda_am": extracted["woreda_am"],
            "woreda_en": extracted["woreda_en"],
            "issue_date_en": issue_date_greg,
            "issue_date_am": issue_date_eth,
            "expiry_date_en": expiry_date_greg,
            "expiry_date_am": expiry_date_eth,
            "fin": extracted["fcn"].replace(" ", ""),
            "serial_number": self.generate_serial_number(),
        }

        # Extract images
        photo_idx = self.PDF_FORMAT_MAPPING['compact_format']['photo_img_index']
        qr_idx = self.PDF_FORMAT_MAPPING['compact_format']['qr_img_index']

        if len(images) > photo_idx:
            photo_bytes = doc.extract_image(images[photo_idx][0])['image']
            photo_img = Image.open(BytesIO(photo_bytes)).convert("RGBA")
            photo_img.save(os.path.join(self.config.STATIC_FOLDER, 'photo_temp.png'))
            processed_data["photo"] = 'static/photo_temp.png'

        if len(images) > qr_idx:
            qr_bytes = doc.extract_image(images[qr_idx][0])['image']
            qr_img = Image.open(BytesIO(qr_bytes)).convert("RGBA")
            qr_img.save(os.path.join(self.config.STATIC_FOLDER, 'qr_temp.png'))
            processed_data["qr_path"] = 'static/qr_temp.png'

        print(f"✅ Compact format extraction completed")
        print(f"📊 Extraction summary:")
        print(f"  FCN: {extracted['fcn']}")
        print(f"  Name AM: {extracted['name_am']}")
        print(f"  Name EN: {extracted['name_en']}")
        print(f"  DOB: {extracted['dob_greg']} | {extracted['dob_eth']}")
        print(f"  Gender: {extracted['gender_am']} | {extracted['gender_en']}")
        print(f"  Nationality: {extracted['nationality_am']} | {extracted['nationality_en']}")
        print(f"  Phone: {extracted['phone']}")
        print(f"  Region: {extracted['region_am']} | {extracted['region_en']}")
        print(f"  Subcity: {extracted['subcity_am']} | {extracted['subcity_en']}")
        print(f"  Woreda: {extracted['woreda_am']} | {extracted['woreda_en']}")

        return processed_data

    
    def _merge_missing_fields(self, original_data: Dict, fallback_data: Dict, missing_fields: List[str]) -> Dict:
        """Merge missing fields from fallback data into original data."""
        merged_data = original_data.copy()        
        for field in missing_fields:
            if fallback_data.get(field) and fallback_data[field].strip():
                merged_data[field] = self._clean_field_value(fallback_data[field])
        # Always merge name fields from fallback data if they exist
        if fallback_data.get('name_am') and fallback_data['name_am'].strip():
            merged_data['name_am'] = self._clean_field_value(fallback_data['name_am'])        
        if fallback_data.get('name_en') and fallback_data['name_en'].strip():
            merged_data['name_en'] = self._clean_field_value(fallback_data['name_en'])        
        # Always merge fin field from fallback data if it exists
        if fallback_data.get('fin') and fallback_data['fin'].strip():
            # Don't clean the fin field - it should be the raw FCN
            merged_data['fin'] = fallback_data['fin'].strip()        
        # Always merge dob_en field from fallback data if it exists
        if fallback_data.get('dob_en') and fallback_data['dob_en'].strip():
            merged_data['dob_en'] = self._clean_field_value(fallback_data['dob_en'])        
        # Clean existing fields that might have issues
        for field in ['region_am', 'region_en', 'subcity_am', 'subcity_en', 'woreda_am', 'woreda_en']:
            if merged_data.get(field):
                merged_data[field] = self._clean_field_value(merged_data[field])
        
        # Special handling for region_am to extract "አዲስ አበባ" from concatenated strings
        if merged_data.get('region_am') and '/' in merged_data['region_am']:
            if 'አዲስ አበባ' in merged_data['region_am']:
                merged_data['region_am'] = 'አዲስ አበባ'        
        return merged_data
    
    def _clean_field_value(self, value: str) -> str:
        """Clean extracted field values by removing unwanted patterns and normalizing."""
        if not value:
            return ""
        
        cleaned = value.strip()
        
        # Remove common placeholder patterns
        placeholders = ["Woreda/City Admin/Kebel", "ሀ/ካ/ሸገር", "ካ/ሸገር"]
        for placeholder in placeholders:
            if placeholder in cleaned:
                cleaned = cleaned.replace(placeholder, "").strip()
        
        # Handle concatenated data (e.g., "ሀ/ካ/ሸገር/አዲስ አበባ/አዲስ አበባ")
        if '/' in cleaned and len(cleaned.split('/')) > 3:
            parts = cleaned.split('/')
            # Look for meaningful parts
            meaningful_parts = []
            for part in parts:
                part = part.strip()
                if part and not part.replace(' ', '').isdigit() and len(part.replace(' ', '')) != 16:
                    if any(keyword in part for keyword in ['አዲስ አበባ', 'Addis Ababa', 'ለሚ ኩራ', 'Lemi Kura', 'ወረዳ', 'Woreda']):
                        meaningful_parts.append(part)
            
            if meaningful_parts:
                cleaned = meaningful_parts[0]  # Take the first meaningful part
        
        # Remove extra spaces
        cleaned = ' '.join(cleaned.split())
        
        # Reject 16-digit numeric strings (FCNs) from address fields, but allow them for fin field
        if cleaned.replace(' ', '').isdigit() and len(cleaned.replace(' ', '')) == 16:
            # Check if this is being called for the fin field specifically
            import inspect
            frame = inspect.currentframe()
            if frame and frame.f_back and 'fin' in str(frame.f_back.f_locals):
                return cleaned  # Allow FCN for fin field
            return ""  # Reject FCN for address fields
        
        return cleaned

    def extract_fin_from_pdf(self, pdf_input) -> Optional[str]:
        """
        Extract FIN number from PDF document.
        For PDFs around 1.8-1.9 MB, extracts FIN from fixed position below left QR code.
        For other PDFs, uses text-based extraction.
        
        Args:
            pdf_input: PDF file path or BytesIO stream
            
        Returns:
            Extracted FIN number (12 digits) or None if not found
        """
        try:
            # Handle both file path and BytesIO input
            if isinstance(pdf_input, str):
                doc = fitz.open(pdf_input)
                file_size = os.path.getsize(pdf_input)
            else:
                doc = fitz.open(stream=pdf_input, filetype="pdf")
                file_size = len(pdf_input.getvalue()) if hasattr(pdf_input, 'getvalue') else 0
            
            try:
                # Extract FIN for PDFs in 1-2 MB range
                if 1.0 * 1024 * 1024 <= file_size <= 2.0 * 1024 * 1024:  # 1.0MB to 2.0MB
                    print(f"📄 Detected 1-2 MB PDF ({file_size / (1024*1024):.2f} MB), extracting FIN from image position")
                    fin_from_image = self._extract_fin_from_image_position(doc)
                    if fin_from_image:
                        return fin_from_image
                    else:
                        print("⚠️ Image-based extraction failed, leaving FIN field empty")
                        return None
                else:
                    # For all other file sizes, leave FIN field empty
                    print(f"📄 PDF size ({file_size / (1024*1024):.2f} MB) is not in 1-2 MB range, leaving FIN field empty")
                    return None
                
            finally:
                doc.close()
                
        except Exception as e:
            print(f"❌ Error extracting FIN from PDF: {str(e)}")
            return None
    
    def _extract_fin_from_image_position(self, doc: fitz.Document) -> Optional[str]:
        """
        Extract FIN from fixed position below left QR code in image-based PDFs.
        Uses OCR if available, otherwise falls back to text extraction from PDF.
        
        Args:
            doc: PyMuPDF document object
            
        Returns:
            Extracted FIN number (12 digits) or None if not found
        """
        try:
            # First try OCR-based extraction
            fin_from_ocr = self._try_ocr_extraction(doc)
            if fin_from_ocr:
                return fin_from_ocr
            
            # If OCR fails, try text-based extraction as fallback
            print("🔄 OCR failed, trying text-based extraction as fallback...")
            fin_from_text = self._extract_fin_from_text(doc)
            if fin_from_text:
                print(f"✅ FIN extracted from text fallback: {fin_from_text}")
                return fin_from_text
            
            print("⚠️ No FIN found in image position or text")
            return None
            
        except Exception as e:
            print(f"❌ Error extracting FIN from image position: {str(e)}")
            return None
    
    def _try_ocr_extraction(self, doc: fitz.Document) -> Optional[str]:
        """
        Try OCR-based extraction from image region.
        
        Args:
            doc: PyMuPDF document object
            
        Returns:
            Extracted FIN number (12 digits) or None if OCR fails
        """
        try:
            page = doc[0]  # First page
            
            # Convert page to image with high resolution
            mat = fitz.Matrix(2.0, 2.0)  # 2x zoom for better OCR
            pix = page.get_pixmap(matrix=mat)
            
            # Convert to PIL Image
            img_data = pix.tobytes("png")
            from PIL import Image
            import io
            img = Image.open(io.BytesIO(img_data))
            
            # Define the region where FIN is located using exact Photoshop coordinates
            # User provided updated exact coordinates from Photoshop: x: 2141, y: 1984, width: 184, height: 26
            width, height = img.size
            
            # Use exact coordinates provided by user from Photoshop
            # These coordinates are from original PDF, so scale them for 2x image
            fin_x = 2141 // 2  # Scale down from original PDF coordinates
            fin_y = 1984 // 2  # Scale down from original PDF coordinates
            fin_width = 184 // 2  # Scale down from original PDF coordinates
            fin_height = 26 // 2  # Scale down from original PDF coordinates
            
            # Define exact FIN region using provided coordinates with expansion for full FIN
            # Expand the region significantly to capture the complete 12-digit FIN number
            padding_x = 100  # Much more horizontal padding to capture full 12-digit FIN
            padding_y = 20   # Vertical padding for better OCR
            fin_region_left = max(0, int(fin_x) - padding_x)
            fin_region_right = min(width, int(fin_x + fin_width) + padding_x)
            fin_region_top = max(0, int(fin_y) - padding_y)
            fin_region_bottom = min(height, int(fin_y + fin_height) + padding_y)
            
            print(f"🔍 Using updated Photoshop coordinates: x={fin_x}, y={fin_y}, width={fin_width}, height={fin_height}")
            print(f"🔍 Scaled region: left={fin_region_left}, top={fin_region_top}, right={fin_region_right}, bottom={fin_region_bottom}")
            print(f"🔍 Image size: {width}x{height}")
            
            # Crop the FIN region
            fin_region = img.crop((fin_region_left, fin_region_top, fin_region_right, fin_region_bottom))
            
            # Save cropped region for debugging (optional)
            try:
                debug_path = "temp_fin_region.png"
                fin_region.save(debug_path)
                print(f"🔍 Saved cropped region to: {debug_path}")
            except Exception as e:
                print(f"⚠️ Could not save debug image: {str(e)}")
            
            # Use OCR to extract text from the region
            fin_text = self._ocr_extract_text(fin_region)
            
            print(f"🔍 OCR extracted text from region: '{fin_text}'")
            
            if fin_text:
                # Look for FIN pattern in extracted text with multiple patterns
                import re
                
                # Extract all digits from the OCR text and try to form a FIN
                all_digits = re.findall(r'\d+', fin_text)
                print(f"🔍 All digit groups found: {all_digits}")
                
                # Try to combine digits to form a 12-digit FIN
                combined_digits = ''.join(all_digits)
                print(f"🔍 Combined digits: '{combined_digits}'")
                
                # Look for 12-digit sequences in the combined digits
                if len(combined_digits) >= 12:
                    # Try different starting positions to find a valid 12-digit FIN
                    for i in range(len(combined_digits) - 11):
                        potential_fin = combined_digits[i:i+12]
                        if len(potential_fin) == 12 and potential_fin.isdigit():
                            print(f"✅ Potential FIN found: {potential_fin}")
                            return potential_fin
                
                # If we have 8 digits, it might be a partial FIN - let's accept it for now
                elif len(combined_digits) == 8:
                    print(f"⚠️ Found 8-digit partial FIN: {combined_digits}")
                    print(f"   This might be part of the full 12-digit FIN")
                    # For now, let's pad it to make it 12 digits (this is temporary)
                    # In a real scenario, you'd want to expand the region more
                    padded_fin = combined_digits.ljust(12, '0')
                    print(f"✅ Using padded FIN: {padded_fin}")
                    return combined_digits  # Return the 8-digit number we found
                
                # Special handling for the specific pattern we're seeing
                # We're getting numbers like "583547", "383547", "983547" - these might be parts of the FIN
                if len(all_digits) >= 1:
                    # Try combining the largest digit groups
                    sorted_digits = sorted(all_digits, key=len, reverse=True)
                    print(f"🔍 Sorted digit groups by length: {sorted_digits}")
                    
                    # Look for 6-digit numbers that might be half of a 12-digit FIN
                    six_digit_numbers = [d for d in all_digits if len(d) == 6]
                    if len(six_digit_numbers) >= 2:
                        # Try combining two 6-digit numbers
                        combined_fin = six_digit_numbers[0] + six_digit_numbers[1]
                        if len(combined_fin) == 12:
                            print(f"✅ Found 12-digit FIN from two 6-digit parts: {combined_fin}")
                            return combined_fin
                    
                    # Try different combinations of available digits
                    for i in range(min(4, len(sorted_digits))):
                        for j in range(i+1, min(4, len(sorted_digits))):
                            combined = sorted_digits[i] + sorted_digits[j]
                            if len(combined) >= 8:  # At least 8 digits might be part of FIN
                                print(f"🔍 Trying combination: {sorted_digits[i]} + {sorted_digits[j]} = {combined}")
                                # Add more digits if available
                                for k in range(j+1, len(sorted_digits)):
                                    extended = combined + sorted_digits[k]
                                    if len(extended) == 12:
                                        print(f"✅ Found 12-digit FIN: {extended}")
                                        return extended
                                # If we have exactly 12 digits from two parts, use it
                                if len(combined) == 12:
                                    print(f"✅ Found 12-digit FIN from two parts: {combined}")
                                    return combined
                
                # Try different FIN patterns - focus on 12-digit FINs (as confirmed by user)
                patterns = [
                    r'(\d{12})',           # Any 12 digits (most likely to match)
                    r'FIN[:\s]*(\d{12})',  # FIN: 632430253608 (12 digits)
                    r'(\d{4}[\s\-]?\d{4}[\s\-]?\d{4})',  # 4-4-4 format
                    r'(\d{3}[\s\-]?\d{3}[\s\-]?\d{3}[\s\-]?\d{3})',  # 3-3-3-3 format
                    r'(\d{6}[\s\-]?\d{6})',  # 6-6 format
                ]
                
                for pattern in patterns:
                    matches = re.findall(pattern, fin_text)
                    for match in matches:
                        clean_fin = re.sub(r'[\s\-]', '', match)
                        if (len(clean_fin) == 12 or len(clean_fin) == 15) and clean_fin.isdigit():
                            print(f"✅ FIN extracted from OCR pattern '{pattern}': {clean_fin}")
                            return clean_fin
                
                print(f"⚠️ No valid FIN found in OCR text: '{fin_text}'")
            
            return None
            
        except Exception as e:
            print(f"❌ OCR extraction failed: {str(e)}")
            return None
    
    def _ocr_extract_text(self, image) -> Optional[str]:
        """
        Extract text from image using Tesseract OCR with optimized preprocessing.
        Fast version that only uses the most effective methods.
        
        Args:
            image: PIL Image object
            
        Returns:
            Extracted text or None if OCR fails
        """
        try:
            import pytesseract
            from PIL import ImageEnhance, ImageFilter
            import re
            
            # Configure Tesseract path for Windows
            import platform
            if platform.system() == 'Windows':
                pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'
            
            # Fast preprocessing - only use the most effective methods
            # Scale up the image for better OCR (3x scaling works best)
            scaled_image = image.resize((image.width * 3, image.height * 3), Image.LANCZOS)
            
            # Convert to grayscale and enhance contrast (this method works well)
            gray_image = scaled_image.convert('L')
            enhancer = ImageEnhance.Contrast(gray_image)
            contrast_image = enhancer.enhance(2.0)
            
            # Apply sharpening filter (this also works well)
            sharp_image = contrast_image.filter(ImageFilter.SHARPEN)
            
            # Only use the most effective OCR configurations for numbers
            # Based on logs, numbers_only_line and numbers_only_block work best
            fast_configs = [
                ('numbers_only_line', '--oem 3 --psm 7 -c tessedit_char_whitelist=0123456789'),
                ('numbers_only_block', '--oem 3 --psm 6 -c tessedit_char_whitelist=0123456789'),
                ('uniform_block', '--oem 3 --psm 6'),  # Fallback for full text
            ]
            
            # Try contrast enhanced image first (it found the FIN in logs)
            for config_name, config in fast_configs:
                try:
                    text = pytesseract.image_to_string(contrast_image, config=config).strip()
                    print(f"🔍 OCR contrast_enhanced + {config_name}: '{text}'")
                    
                    if text:
                        # Check for 12-digit numbers first (highest priority)
                        twelve_digit_match = re.search(r'\d{12}', text)
                        if twelve_digit_match:
                            print(f"🎯 Found 12-digit FIN: {twelve_digit_match.group()}")
                            return text
                        
                except Exception as e:
                    print(f"⚠️ OCR contrast_enhanced + {config_name} failed: {str(e)}")
                    continue
            
            # If contrast enhanced didn't work, try sharpened image
            for config_name, config in fast_configs:
                try:
                    text = pytesseract.image_to_string(sharp_image, config=config).strip()
                    print(f"🔍 OCR sharpened + {config_name}: '{text}'")
                    
                    if text:
                        # Check for 12-digit numbers first (highest priority)
                        twelve_digit_match = re.search(r'\d{12}', text)
                        if twelve_digit_match:
                            print(f"🎯 Found 12-digit FIN: {twelve_digit_match.group()}")
                            return text
                        
                except Exception as e:
                    print(f"⚠️ OCR sharpened + {config_name} failed: {str(e)}")
                    continue
            
            # Final fallback: try original scaled image with best config
            try:
                text = pytesseract.image_to_string(scaled_image, config='--oem 3 --psm 6 -c tessedit_char_whitelist=0123456789').strip()
                print(f"🔍 OCR scaled_fallback: '{text}'")
                
                if text:
                    twelve_digit_match = re.search(r'\d{12}', text)
                    if twelve_digit_match:
                        print(f"🎯 Found 12-digit FIN in fallback: {twelve_digit_match.group()}")
                        return text
                    # Return any text with digits as last resort
                    elif any(c.isdigit() for c in text):
                        print(f"⚠️ Returning fallback text with digits: '{text}'")
                        return text
                        
            except Exception as e:
                print(f"⚠️ Fallback OCR failed: {str(e)}")
            
            print("⚠️ Fast OCR extraction failed to find 12-digit FIN")
            return None
            
        except ImportError:
            print("❌ pytesseract not available - install with: pip install pytesseract")
            return None
        except Exception as e:
            print(f"❌ OCR extraction error: {str(e)}")
            return None
    
    def _extract_fin_from_text(self, doc: fitz.Document) -> Optional[str]:
        """
        Extract FIN from PDF text content.
        
        Args:
            doc: PyMuPDF document object
            
        Returns:
            Extracted FIN number (12 digits) or None if not found
        """
        try:
            # Extract text from all pages
            full_text = ""
            for page_num in range(len(doc)):
                page = doc[page_num]
                full_text += page.get_text() + "\n"
            
            print(f"📄 Extracted text length: {len(full_text)} characters")
            
            # Debug: Show first 500 characters of extracted text
            debug_text = full_text[:500].replace('\n', ' ').strip()
            print(f"📄 First 500 characters: {debug_text}")
            
            # Debug: Show more text to find FIN patterns
            print(f"📄 Full text length: {len(full_text)} characters")
            if len(full_text) > 1000:
                print(f"📄 Text around position 1000: {full_text[800:1200].replace(chr(10), ' ').strip()}")
            
            # Look for FIN patterns in the text with priority order
            # Based on the image, we need to look for specific patterns
            fin_patterns = [
                r'FIN[:\s]*(\d{15})',  # FIN: 572680186346580 (15 digits)
                r'FIN[:\s]*(\d{12})',  # FIN: 632430253608 (12 digits)
                r'FIN[:\s]*(\d{4}[\s\-]?\d{4}[\s\-]?\d{4})',  # FIN: 1234-5678-9012
                r'FOR[:\s]*(\d{15})',  # FOR: 572680186346580 (15 digits)
                r'FOR[:\s]*(\d{12})',  # FOR: 632430253608 (12 digits)
                r'FOR[:\s]*(\d{4}[\s\-]?\d{4}[\s\-]?\d{4})',  # FOR: 1234-5678-9012
            ]
            
            import re
            for pattern in fin_patterns:
                matches = re.findall(pattern, full_text, re.IGNORECASE)
                for match in matches:
                    # Clean the match (remove spaces and dashes)
                    clean_match = re.sub(r'[\s\-]', '', match)
                    
                    # Validate it's exactly 12 or 15 digits
                    if (len(clean_match) == 12 or len(clean_match) == 15) and clean_match.isdigit():
                        print(f"✅ FIN extracted from text with pattern '{pattern}': {clean_match}")
                        return clean_match
            
            # If no explicit FIN/FOR found, look for FCN patterns (16 digits) as fallback
            fcn_patterns = [
                r'FCN[:\s]*(\d{16})',  # FCN: 1234567890123456
                r'PCM[:\s]*(\d{16})',  # PCM: 1234567890123456
            ]
            
            for pattern in fcn_patterns:
                matches = re.findall(pattern, full_text, re.IGNORECASE)
                for match in matches:
                    if len(match) == 16 and match.isdigit():
                        # Extract last 12 digits as FIN
                        fin_from_fcn = match[-12:]
                        print(f"✅ FIN extracted from FCN/PCM pattern '{pattern}': {fin_from_fcn}")
                        return fin_from_fcn
            
            # Last resort: Look for any 15-digit or 12-digit number, but be selective
            fifteen_digit_pattern = r'\b(\d{15})\b'
            twelve_digit_pattern = r'\b(\d{12})\b'
            
            matches_12 = re.findall(twelve_digit_pattern, full_text)
            
            # Filter out common false positives and prioritize certain patterns
            false_positives = [
                '000000000000', '111111111111', '123456789012', '987654321098',
                '000000000001', '111111111110', '123456789013', '987654321099'
            ]
            
            for match in matches_12:
                if (match.isdigit() and len(match) == 12 and 
                    match not in false_positives and
                    not match.startswith('000') and  # Avoid numbers starting with 000
                    not match.endswith('000')):     # Avoid numbers ending with 000
                    print(f"✅ 12-digit number found in text: {match}")
                    return match
            
            print("⚠️ No valid FIN number found in PDF text")
            return None
            
        except Exception as e:
            print(f"❌ Error extracting FIN from text: {str(e)}")
            return None
    
    def _extract_large_format_pdf_data(self, doc: fitz.Document, lines: list, images: list, fin_number: str) -> dict:
        """Extract data from large format PDF (~1.8 MB, filename with 3 capital letters).

        Observed line structure (from logs):
          line 43: name_en  (e.g. 'Hiwot Elias Mekonnen')
          line 44: FCN      (16 digits)
          line 45: dob_greg (YYYY/MM/DD)
          line 46: dob_eth  (DD/MM/YYYY)
          line 47: gender_en
          line 48: nationality_en
          line 49: phone
          line 50: region_en
          line 51: subcity_en
          line 52: woreda_en
          line 53: name_am
          line 54: gender_am
          line 55: nationality_am
        """
        import re as _re

        def safe(idx):
            return lines[idx].strip() if idx < len(lines) else ''

        # --- FCN ---
        fcn_raw = ''
        for ln in lines:
            digits = ''.join(c for c in ln if c.isdigit())
            if len(digits) == self.config.FCN_LENGTH:
                fcn_raw = digits
                break
        if not fcn_raw:
            raise ValueError("large_format: FCN not found")
        fcn_full = fcn_raw  # store raw 16 digits; formatting happens in generate_barcode

        # Find the FCN line index to anchor all other fields
        fcn_idx = next((i for i, ln in enumerate(lines)
                        if ''.join(c for c in ln if c.isdigit()) == fcn_raw), None)
        if fcn_idx is None:
            raise ValueError("large_format: cannot anchor FCN line")

        name_en        = safe(fcn_idx - 1)
        dob_greg_raw   = safe(fcn_idx + 1)
        dob_eth_raw    = safe(fcn_idx + 2)
        gender_en      = safe(fcn_idx + 3)
        nationality_en = safe(fcn_idx + 4)
        phone_raw      = safe(fcn_idx + 5)
        region_en      = safe(fcn_idx + 6)
        subcity_en     = safe(fcn_idx + 7)
        woreda_en      = safe(fcn_idx + 8)
        name_am        = safe(fcn_idx + 9)
        gender_am      = safe(fcn_idx + 10)
        nationality_am = safe(fcn_idx + 11)
        region_am      = safe(fcn_idx + 12)
        subcity_am     = safe(fcn_idx + 13)
        woreda_am      = safe(fcn_idx + 14)

        valid_gender_en = {'male', 'female'}
        valid_gender_am = {'ወንድ', 'ሴት'}
        if gender_en.lower() not in valid_gender_en:
            gender_en = ''
        if gender_am not in valid_gender_am:
            gender_am = ''

        # Validate nationality — reject if it looks like a gender or label
        def _bad_nat(v):
            return not v or v.lower() in valid_gender_en or v in valid_gender_am
        if _bad_nat(nationality_en):
            nationality_en = ''
        if _bad_nat(nationality_am):
            nationality_am = ''

        # Phone: keep only digit strings of 9-13 chars
        phone = phone_raw if phone_raw.replace(' ', '').isdigit() and 9 <= len(phone_raw.replace(' ', '')) <= 13 else ''
        if phone:
            phone = self.format_phone_number(phone)

        # DOB parsing
        dob_en = ''
        dob_am = ''
        try:
            if dob_greg_raw:
                dob_en = datetime.strptime(dob_greg_raw, "%Y/%m/%d").strftime("%Y/%b/%d")
        except Exception:
            dob_en = dob_greg_raw
        try:
            if dob_eth_raw:
                parts = dob_eth_raw.split('/')
                if len(parts) == 3:
                    d, m, y = parts
                    dob_am = f"{int(d):02d}/{int(m):02d}/{int(y):04d}"
        except Exception:
            dob_am = dob_eth_raw

        dates = get_id_dates()

        extracted_data = {
            'fcn_full':        fcn_full,
            'name_en':         name_en,
            'name_am':         name_am,
            'dob_en':          dob_en,
            'dob_am':          dob_am,
            'gender_en':       gender_en,
            'gender_am':       gender_am,
            'nationality_en':  nationality_en,
            'nationality_am':  nationality_am,
            'phone':           phone,
            'region_en':       region_en,
            'region_am':       region_am,
            'subcity_en':      subcity_en,
            'subcity_am':      subcity_am,
            'woreda_en':       woreda_en,
            'woreda_am':       woreda_am,
            'issue_date_en':   dates['issue_date_greg'],
            'issue_date_am':   dates['issue_date_eth'],
            'expiry_date_en':  dates['expiry_date_greg'],
            'expiry_date_am':  dates['expiry_date_eth'],
            'fin':             fin_number,
            'serial_number':   self.generate_serial_number(),
        }

        # Extract photo and QR
        photo_bytes, qr_bytes = self._detect_photo_and_qr(doc, images)
        try:
            if photo_bytes:
                photo_img = Image.open(BytesIO(photo_bytes)).convert("RGBA")
                photo_path = os.path.join(self.config.STATIC_FOLDER, 'photo_temp.png')
                photo_img.save(photo_path)
                extracted_data['photo'] = 'static/photo_temp.png'
        except Exception as e:
            print(f"large_format: error extracting photo: {e}")
        try:
            if qr_bytes:
                qr_img = Image.open(BytesIO(qr_bytes)).convert("RGBA")
                qr_path = os.path.join(self.config.STATIC_FOLDER, 'qr_temp.png')
                qr_img.save(qr_path)
                extracted_data['qr_path'] = 'static/qr_temp.png'
        except Exception as e:
            print(f"large_format: error extracting QR: {e}")

        print(f"large_format extraction results:")
        print(f"  FCN: '{' '.join([fcn_full[i:i+4] for i in range(0,16,4)])}'")

        print(f"  Name EN: '{name_en}' | AM: '{name_am}'")
        print(f"  DOB: '{dob_en}' / '{dob_am}'")
        print(f"  Gender: '{gender_en}' / '{gender_am}'")
        print(f"  Nationality: '{nationality_en}' / '{nationality_am}'")
        print(f"  Phone: '{phone}'")
        print(f"  Region: '{region_en}' / '{region_am}' | Subcity: '{subcity_en}' / '{subcity_am}' | Woreda: '{woreda_en}' / '{woreda_am}'")

        return extracted_data

    def extract_pdf_data(self, pdf_input, fin_number: str, pdf_format: str = 'auto') -> Dict:
        """Extract data from PDF file or stream with automatic format detection and fallback."""
        # Handle both file path and BytesIO input
        if isinstance(pdf_input, str):
            doc = fitz.open(pdf_input)
            file_size = os.path.getsize(pdf_input)
            pdf_filename = os.path.basename(pdf_input)
        else:
            doc = fitz.open(stream=pdf_input, filetype="pdf")
            # Get file size from BytesIO
            pdf_input.seek(0, 2)  # Seek to end
            file_size = pdf_input.tell()
            pdf_input.seek(0)  # Reset to beginning
            pdf_filename = getattr(pdf_input, 'name', '') or ''
            
        try:
            page = doc[0]
            text = page.get_text()
            images = page.get_images(full=True)
            lines = [line.strip() for line in text.strip().split('\n') if line.strip()]

            extracted_data = {}
            used_format = None
            
            # Check file size and prioritize compact format for 300KB-900KB PDFs
            file_size_kb = file_size / 1024
            file_size_mb = file_size_kb / 1024
            print(f"📄 PDF file size: {file_size_kb:.2f} KB ({file_size_mb:.2f} MB)")

            # Detect large format: ~1.8 MB and filename has exactly 3 consecutive capital letters
            import re as _re
            basename_no_ext = os.path.splitext(os.path.basename(pdf_filename))[0]
            has_three_caps = bool(_re.search(r'[A-Z]{3}', basename_no_ext))
            is_large_size = 1500 <= file_size_kb <= 2100  # ~1.8 MB range

            # Try formats in order based on file size / filename heuristics
            if pdf_format == 'large_format':
                print("🎯 User selected large_format explicitly")
                formats_to_try = ['large_format', 'residential_sheger', 'default', 'demographic_format', 'compact_format']
            elif pdf_format not in ('auto', None, '') and pdf_format in self.PDF_FORMAT_MAPPING:
                print(f"🎯 User selected format: {pdf_format}")
                formats_to_try = [pdf_format] + [f for f in ['default', 'residential_sheger', 'demographic_format', 'compact_format', 'large_format'] if f != pdf_format]
            elif has_three_caps and is_large_size:
                print(f"🎯 Filename '{pdf_filename}' has 3 capital letters and size ~1.8 MB, trying large_format first")
                formats_to_try = ['large_format', 'residential_sheger', 'default', 'demographic_format', 'compact_format']
            elif 300 <= file_size_kb <= 900:
                print("🎯 File size in compact format range (300-900 KB), trying compact format first")
                formats_to_try = ['compact_format', 'default', 'residential_sheger', 'demographic_format']
            else:
                formats_to_try = ['default', 'residential_sheger', 'demographic_format', 'compact_format']
            
            for format_type in formats_to_try:
                try:
                    if format_type == 'default':
                        extracted_data = self._extract_default_pdf_data(doc, lines, images, fin_number)
                    elif format_type == 'residential_sheger':
                        extracted_data = self._extract_residential_sheger_pdf_data(doc, lines, images, fin_number)
                    elif format_type == 'demographic_format':
                        extracted_data = self._extract_demographic_format_pdf_data(doc, lines, images, fin_number)
                    elif format_type == 'compact_format':
                        extracted_data = self._extract_compact_format_pdf_data(doc, lines, images, fin_number)
                    elif format_type == 'large_format':
                        extracted_data = self._extract_large_format_pdf_data(doc, lines, images, fin_number)
                    
                    # Check if extraction was successful by validating key fields
                    # For residential_sheger and large_format, accept FCN with at least one name present (EN or AM)
                    if format_type in ('residential_sheger', 'large_format'):
                        if (extracted_data.get('fcn_full') and 
                            (extracted_data.get('name_en') or extracted_data.get('name_am'))):
                            used_format = format_type
                            print(f"Successfully extracted data using {format_type} format")
                            break
                        else:
                            print(f"Format {format_type} failed validation (need fcn_full and a name), trying next format...")
                            continue
                    else:
                        # For other formats, require both names
                        if (extracted_data.get('fcn_full') and 
                            extracted_data.get('name_en') and 
                            extracted_data.get('name_am')):
                            used_format = format_type
                            print(f"Successfully extracted data using {format_type} format")
                            break
                        else:
                            print(f"Format {format_type} failed validation, trying next format...")
                            continue
                        
                except Exception as e:
                    print(f"Format {format_type} failed with error: {str(e)}, trying next format...")
                    continue
            
            if not used_format:
                raise ValueError("All PDF formats failed to extract valid data. Please check your document.")

            # Add format information to extracted data
            extracted_data['used_format'] = used_format
            
            # Pattern-only mode: disable all cross-format fallbacks/merges
            if used_format in ('residential_sheger', 'large_format'):
                pass
            
            # Common barcode generation after data is extracted
            barcode_filename, formatted_fcn = self.generate_barcode(extracted_data['fcn_full'])
            if barcode_filename:
                extracted_data['fcn_barcode'] = barcode_filename
                extracted_data['fcn_formatted'] = formatted_fcn
            else:
                extracted_data['fcn_barcode'] = None
                extracted_data['fcn_formatted'] = extracted_data['fcn_full'] # Fallback if barcode fails

            return extracted_data
        finally:
            doc.close()

    def generate_id_card(self, data: Dict, city_option: str = 'default', remove_white: bool = False, remove_black: bool = False, generate_front_only: bool = False, generate_reverse_only: bool = False, generate_mini_id: bool = False, generate_old_id: bool = False, use_onnx_bg: bool = False) -> Dict[str, str]:
        """Generate ID card images (optimized for speed)."""
        try:
            # Performance optimization: Cache frequently used data
            start_time = time.time()
            
            # Pre-cache template sizes to avoid repeated Image.open() calls
            if not hasattr(self, '_template_cache'):
                self._template_cache = {}
            
            if 'normal_size' not in self._template_cache:
                self._template_cache['normal_size'] = Image.open(self.config.TEMPLATE_IMG).size
            if 'mini_size' not in self._template_cache and hasattr(self.config, 'MINI_TEMPLATE_IMG'):
                self._template_cache['mini_size'] = Image.open(self.config.MINI_TEMPLATE_IMG).size
            # Use appropriate address positions based on ID type
            if generate_old_id:
                address_positions = self.config.OLD_ADDRESS_POSITIONS.get(city_option, self.config.OLD_ADDRESS_POSITIONS['default'])
            elif generate_mini_id:
                address_positions = self.config.MINI_ADDRESS_POSITIONS.get(city_option, self.config.MINI_ADDRESS_POSITIONS['default'])
            else:
                address_positions = self.config.ADDRESS_POSITIONS.get(city_option, self.config.ADDRESS_POSITIONS['default'])

            # If mini or old is requested, prepare appropriate layout
            normal_w, normal_h = self._template_cache['normal_size']
            
            # Select template based on ID type
            if generate_old_id:
                template_img_path = self.config.OLD_TEMPLATE_IMG
                template_json_path = self.config.OLD_TEMPLATE_JSON
                print(f"Using OLD template: {template_img_path}")
            elif generate_mini_id:
                template_img_path = self.config.MINI_TEMPLATE_IMG
                template_json_path = self.config.MINI_TEMPLATE_JSON
                print(f"Using MINI template: {template_img_path}")
            else:
                template_img_path = self.config.TEMPLATE_IMG
                template_json_path = self.config.TEMPLATE_JSON
                print(f"Using NORMAL template: {template_img_path}")
            
            # Load template JSON
            with open(template_json_path, encoding='utf-8') as f:
                front_template_json = json.load(f)
            
            used_address_positions_front = address_positions['front']
            mini_photo_conf = None
            mini_qr_conf = None
            name = data.get('name_en', '').replace(' ', '_')
            photo_path = os.path.join(self.config.STATIC_FOLDER, 'photo_temp.png')
            qr_path = os.path.join(self.config.STATIC_FOLDER, 'qr_temp.png')
            barcode_path = data.get('fcn_barcode')
            barcode_full_path = os.path.join(self.config.STATIC_FOLDER, barcode_path) if barcode_path else None

            # Check if we have extracted photo and QR data from PDF
            if data.get('photo') and os.path.exists(os.path.join(self.config.STATIC_FOLDER, data['photo'].replace('static/', ''))):
                # Use the extracted photo from PDF
                photo_path = os.path.join(self.config.STATIC_FOLDER, data['photo'].replace('static/', ''))
                print(f"Using extracted photo from PDF: {photo_path}")
            else:
                # Generate photo data if not available
                photo_bytes = self.get_photo_data(data, remove_white, remove_black)
                photo_img = Image.open(BytesIO(photo_bytes)).convert("RGBA")
                photo_img.save(photo_path)
                print(f"Generated photo data and saved to: {photo_path}")
            
            # Check for uploaded QR code first (qr_temp.png from upload_qr endpoint)
            if os.path.exists(qr_path):
                # Use the uploaded QR code (either from PDF extraction or manual upload)
                print(f"Using existing QR code from: {qr_path}")
            elif data.get('qr_path') and os.path.exists(os.path.join(self.config.STATIC_FOLDER, data['qr_path'].replace('static/', ''))):
                # Use the extracted QR from PDF (if path is specified in data)
                qr_path = os.path.join(self.config.STATIC_FOLDER, data['qr_path'].replace('static/', ''))
                print(f"Using extracted QR from PDF: {qr_path}")
            else:
                # Generate QR data if not available
                qr_bytes = self.generate_qr_code(data, include_nationality=False)
                qr_img = Image.open(BytesIO(qr_bytes)).convert("RGBA")
                qr_img.save(qr_path)
                print(f"Generated QR data and saved to: {qr_path}")
            
            # Preload and process photo once per size (optimized)
            photo_large = process_photo(photo_path, self.config.PHOTO_SIZES['large'], remove_white, remove_black, use_onnx_bg) if os.path.exists(photo_path) else None
            photo_small = process_photo(photo_path, self.config.PHOTO_SIZES['small'], remove_white, remove_black, use_onnx_bg) if os.path.exists(photo_path) else None
            photo_reverse_large = process_photo(photo_path, self.config.PHOTO_SIZES['reverse_large'], remove_white, remove_black, use_onnx_bg) if os.path.exists(photo_path) else None
            photo_reverse_small = process_photo(photo_path, self.config.PHOTO_SIZES['reverse_small'], remove_white, remove_black, use_onnx_bg) if os.path.exists(photo_path) else None

            def make_front(color: bool):
                template = Image.open(template_img_path).convert("RGBA")
                # Ensure template canvas is normal size for mini
                if template.size != (normal_w, normal_h):
                    template = template.resize((normal_w, normal_h), Image.LANCZOS)
                draw = ImageDraw.Draw(template)
                for field in front_template_json['fields']:
                    key = field.get("key")
                    if key in used_address_positions_front:
                        continue
                    content = data.get(key, field.get("label", ""))
                    pos = tuple(field["position"])
                    color_val = tuple(field.get("color", (0, 0, 0)))
                    align = field.get("align", "left")
                    font_spec = field["font"]
                    if key.endswith('_am'):
                        has_digit = any(c.isdigit() for c in content)
                        is_latin_only = all(ord(c) < 128 for c in content if not c.isspace())
                        if has_digit or is_latin_only:
                            font = ImageFont.truetype(self.config.ENGLISH_FONT_PATH, font_spec["size"])
                        else:
                            font = ImageFont.truetype(self.config.AMHARIC_FONT_PATH, font_spec["size"])
                    else:
                        font = ImageFont.truetype(self.config.ENGLISH_FONT_PATH, font_spec["size"])
                    if key in ["issue_date_am", "issue_date_en"]:
                        rotated_img, pos2 = draw_rotated_text(draw, content, pos, font, color_val)
                        template.paste(rotated_img, pos2, rotated_img)
                    else:
                        max_width = field.get("wrap_width")
                        draw_text_with_alignment(draw, content, pos, font, color_val, align, max_width)
                fs = getattr(self.config, 'ADDRESS_FONT_SIZES', {'front': {'am': 48, 'en': 50}}).get('front', {'am': 48, 'en': 50})
                font_am = ImageFont.truetype(self.config.AMHARIC_FONT_PATH, fs.get('am', 48))
                font_en = ImageFont.truetype(self.config.ENGLISH_FONT_PATH, fs.get('en', 50))
                for key, pos in used_address_positions_front.items():
                    content = data.get(key, '')
                    font = font_am if key.endswith('_am') else font_en
                    max_width = getattr(self.config, 'TEXT_MAX_WIDTH', {}).get('front', {}).get(key, None)
                    draw_text_with_alignment(draw, content, tuple(pos), font, (0, 0, 0), "left", max_width)
                # Paste photo
                if photo_large:
                    print(f"Pasting large photo: {photo_large.size}")
                    if generate_mini_id and mini_photo_conf:
                        # Scale photo to mini configuration
                        size = tuple(mini_photo_conf.get('size', (200, 260)))
                        pos_xy = tuple(mini_photo_conf.get('position', (50, 60)))
                        src = photo_large if color else photo_large.convert('LA').convert('RGBA')
                        img = src.resize(size)
                        template.paste(img, pos_xy, img)
                    else:
                        img = photo_large if color else photo_large.convert('LA').convert('RGBA')
                        template.paste(img, (128, 250), img)
                else:
                    print(f"Warning: photo_large is None or empty")
                if photo_small:
                    print(f"Pasting small photo: {photo_small.size}")
                    img = photo_small if color else photo_small.convert('LA').convert('RGBA')
                    template.paste(img, (1493, 860), img)
                else:
                    print(f"Warning: photo_small is None or empty")
                if os.path.exists(qr_path):
                    print(f"Pasting QR code from: {qr_path}")
                    if generate_mini_id and mini_qr_conf:
                        qr_img = Image.open(qr_path).resize(tuple(mini_qr_conf.get('size', (300, 300))))
                        template.paste(qr_img, tuple(mini_qr_conf.get('position', (50, 50))))
                    else:
                        qr_img = Image.open(qr_path).resize((934, 937))
                        template.paste(qr_img, (2875, 90))
                else:
                    print(f"Warning: QR path does not exist: {qr_path}")
                if barcode_full_path and os.path.exists(barcode_full_path):
                    barcode_img = Image.open(barcode_full_path)
                    gray = barcode_img.convert('L')
                    bbox = gray.point(lambda x: 0 if x > 250 else 255, '1').getbbox()
                    if bbox:
                        barcode_img = barcode_img.crop(bbox)
                    barcode_img = barcode_img.resize((487, 87))
                    template.paste(barcode_img, (857, 930))
                    font = ImageFont.truetype(self.config.ENGLISH_FONT_PATH, 42)
                    text_width = draw.textlength(data['fcn_formatted'], font=font)
                    center_x = 850 + (500 - text_width) // 2
                    draw.text((center_x, 878), data['fcn_formatted'], font=font, fill=(0, 0, 0))
                return template

            def make_reverse(color: bool):
                reverse_template = Image.open(self.config.REVERSE_TEMPLATE_IMG).convert("RGBA")
                data_layer = Image.new("RGBA", reverse_template.size, (255, 255, 255, 0))
                draw_data = ImageDraw.Draw(data_layer)
                with open(self.config.REVERSE_TEMPLATE_JSON, encoding='utf-8') as f:
                    reverse_json = json.load(f)
                for field in reverse_json['fields']:
                    key = field.get("key")
                    if key in address_positions['reverse']:
                        continue
                    content = data.get(key, field.get("label", ""))
                    pos = tuple(field["position"])
                    color_val = tuple(field.get("color", (0, 0, 0)))
                    align = field.get("align", "left")
                    font_spec = field["font"]
                    if key.endswith('_am'):
                        has_digit = any(c.isdigit() for c in content)
                        is_latin_only = all(ord(c) < 128 for c in content if not c.isspace())
                        if has_digit or is_latin_only:
                            font = ImageFont.truetype(self.config.ENGLISH_FONT_PATH, font_spec["size"])
                        else:
                            font = ImageFont.truetype(self.config.AMHARIC_FONT_PATH, font_spec["size"])
                    else:
                        font = ImageFont.truetype(self.config.ENGLISH_FONT_PATH, font_spec["size"])
                    if key in ["issue_date_am", "issue_date_en"]:
                        rotated_img, pos2 = draw_rotated_text(draw_data, content, pos, font, color_val)
                        data_layer.paste(rotated_img, pos2, rotated_img)
                    else:
                        max_width = field.get("wrap_width")
                        draw_text_with_alignment(draw_data, content, pos, font, color_val, align, max_width)
                fs_rev = getattr(self.config, 'ADDRESS_FONT_SIZES', {'reverse': {'am': 34, 'en': 34}}).get('reverse', {'am': 34, 'en': 34})
                font_am = ImageFont.truetype(self.config.AMHARIC_FONT_PATH, fs_rev.get('am', 34))
                font_en = ImageFont.truetype(self.config.ENGLISH_FONT_PATH, fs_rev.get('en', 34))
                for key, pos in address_positions['reverse'].items():
                    content = data.get(key, '')
                    font = font_am if key.endswith('_am') else font_en
                    max_width = getattr(self.config, 'TEXT_MAX_WIDTH', {}).get('reverse', {}).get(key, None)
                    draw_text_with_alignment(draw_data, content, tuple(pos), font, (0, 0, 0), "left", max_width)
                if photo_reverse_large:
                    img = photo_reverse_large if color else photo_reverse_large.convert('LA').convert('RGBA')
                    reverse_template.paste(img, (1978, 170), img)
                if photo_reverse_small:
                    img = photo_reverse_small if color else photo_reverse_small.convert('LA').convert('RGBA')
                    reverse_template.paste(img, (1398, 510), img)
                if os.path.exists(qr_path):
                    qr_img = Image.open(qr_path).resize((530, 530))
                    reverse_template.paste(qr_img, (180, 70))
                if barcode_full_path and os.path.exists(barcode_full_path):
                    barcode_img = Image.open(barcode_full_path)
                    gray = barcode_img.convert('L')
                    bbox = gray.point(lambda x: 0 if x > 250 else 255, '1').getbbox()
                    if bbox:
                        barcode_img = barcode_img.crop(bbox)
                    barcode_img = barcode_img.resize((287, 62))
                    reverse_template.paste(barcode_img, (1578, 536))
                    font = ImageFont.truetype(self.config.ENGLISH_FONT_PATH, 22)
                    text_width = draw_data.textlength(data['fcn_formatted'], font=font)
                    center_x = 700 + (120 - text_width) // 2
                    draw_data.text((center_x, 512), data['fcn_formatted'], font=font, fill=(0, 0, 0))
                flipped_data = data_layer.transpose(Image.FLIP_LEFT_RIGHT)
                reverse_template.alpha_composite(flipped_data)
                return reverse_template

            # Generate ID cards based on type requested
            if generate_front_only:
                # Only generate front cards (2 cards: color and grayscale)
                print("Generating ONLY front cards...")
                with ThreadPoolExecutor() as executor:
                    futures = {
                        'front_color': executor.submit(make_front, True),
                        'front_bw': executor.submit(make_front, False)
                    }
                    results = {k: f.result() for k, f in futures.items()}

                # Save images
                color_filename = f"{name}_Front_Color.png"
                bw_filename = f"{name}_Front_Grayscale.png"
                results['front_color'].save(os.path.join(self.config.STATIC_FOLDER, color_filename))
                results['front_bw'].save(os.path.join(self.config.STATIC_FOLDER, bw_filename))

                return {
                    'front_color': color_filename,
                    'front_bw': bw_filename,
                    'city_option': city_option
                }
            elif generate_reverse_only:
                # Only generate reverse cards (2 cards: color and grayscale)
                print("Generating ONLY reverse cards...")
                with ThreadPoolExecutor() as executor:
                    futures = {
                        'reverse': executor.submit(make_reverse, True),
                        'reverse_bw': executor.submit(make_reverse, False)
                    }
                    results = {k: f.result() for k, f in futures.items()}

                # Save images
                reverse_filename = f"{name}_Reverse_Color.png"
                bw_filename_reverse = f"{name}_Reverse_Grayscale.png"
                results['reverse'].save(os.path.join(self.config.STATIC_FOLDER, reverse_filename))
                results['reverse_bw'].save(os.path.join(self.config.STATIC_FOLDER, bw_filename_reverse))

                return {
                    'reverse': reverse_filename,
                    'reverse_bw': bw_filename_reverse,
                    'city_option': city_option
                }
            elif generate_old_id:
                # Only generate old ID cards (4 cards)
                print("Generating ONLY old ID cards...")
                old_files = self._generate_old_id_cards(data, remove_white, remove_black, city_option, use_onnx_bg)
                old_files['city_option'] = city_option
                return old_files
            elif generate_mini_id:
                # Only generate mini ID cards with default reverse (4 cards)
                print("Generating ONLY mini ID cards with default reverse...")
                
                # Generate mini front cards
                mini_files = self._generate_mini_id_cards(data, remove_white, remove_black, city_option, use_onnx_bg)
                
                # Generate default reverse cards
                with ThreadPoolExecutor() as executor:
                    futures = {
                        'reverse': executor.submit(make_reverse, True),
                        'reverse_bw': executor.submit(make_reverse, False)
                    }
                    results = {k: f.result() for k, f in futures.items()}

                # Save reverse images
                reverse_filename = f"{name}_Reverse_Color.png"
                bw_filename_reverse = f"{name}_Reverse_Grayscale.png"
                results['reverse'].save(os.path.join(self.config.STATIC_FOLDER, reverse_filename))
                results['reverse_bw'].save(os.path.join(self.config.STATIC_FOLDER, bw_filename_reverse))

                # Combine mini front and default reverse
                all_files = {
                    'reverse': reverse_filename,
                    'reverse_bw': bw_filename_reverse,
                    'city_option': city_option
                }
                all_files.update(mini_files)
                
                return all_files
            else:
                # Generate normal ID cards (4 cards)
                print("Generating normal ID cards...")
                # Parallel image generation
                with ThreadPoolExecutor() as executor:
                    futures = {
                        'front_color': executor.submit(make_front, True),
                        'front_bw': executor.submit(make_front, False),
                        'reverse': executor.submit(make_reverse, True),
                        'reverse_bw': executor.submit(make_reverse, False)
                    }
                    results = {k: f.result() for k, f in futures.items()}

                # Save images
                color_filename = f"{name}_Front_Color.png"
                bw_filename = f"{name}_Front_Grayscale.png"
                reverse_filename = f"{name}_Reverse_Color.png"
                bw_filename_reverse = f"{name}_Reverse_Grayscale.png"
                results['front_color'].save(os.path.join(self.config.STATIC_FOLDER, color_filename))
                results['front_bw'].save(os.path.join(self.config.STATIC_FOLDER, bw_filename))
                results['reverse'].save(os.path.join(self.config.STATIC_FOLDER, reverse_filename))
                results['reverse_bw'].save(os.path.join(self.config.STATIC_FOLDER, bw_filename_reverse))

                # Combine all generated files
                all_files = {
                    'front_color': color_filename,
                    'front_bw': bw_filename,
                    'reverse': reverse_filename,
                    'reverse_bw': bw_filename_reverse,
                    'city_option': city_option
                }
                
                # Performance timing
                end_time = time.time()
                print(f"✅ ID generation completed in {end_time - start_time:.2f} seconds")
                
                # Clean up old images after successful generation
                current_files = list(all_files.values())
                self.cleanup_old_images(keep_current_files=current_files)

                # Track successful ID generation
                self._track_id_generation(data)

                return all_files
        except Exception as e:
            print(f"Error generating ID card: {str(e)}")
            raise 

    def _track_id_generation(self, data: Dict):
        """Track successful ID generation for daily reports."""
        try:
            from .daily_report_service import DailyReportService
            
            # Extract user info from data (you may need to adjust this based on your data structure)
            user_id = data.get('user_id') or data.get('telegram_user_id')
            username = data.get('username') or data.get('name_en', 'Unknown User')
            
            if user_id:
                daily_service = DailyReportService()
                stats = daily_service.increment_id_count(user_id, username)
                print(f"✅ ID generation tracked: User {username} (ID: {user_id}) - Today: {stats['today_count']}, Total: {stats['total_count']}")
            else:
                print("⚠️ No user ID found in data, skipping tracking")
                
        except Exception as e:
            print(f"Error tracking ID generation: {str(e)}")

    def _ensure_mini_layout(self, address_positions: Dict[str, Dict]) -> Dict:
        """Create or reuse a mini template JSON describing positions scaled from normal template."""
        try:
            # If json exists, reuse and extract QR/photo from security_features
            if os.path.exists(self.config.MINI_TEMPLATE_JSON):
                with open(self.config.MINI_TEMPLATE_JSON, encoding='utf-8') as f:
                    mini_json = json.load(f)
                
                # Extract QR and photo configurations from security_features
                security_features = mini_json.get('graphics', {}).get('security_features', {})
                
                # Get QR configuration
                qr_config = security_features.get('qr_code', {})
                qr_conf = {
                    'position': qr_config.get('position', [1840, 65]),
                    'size': qr_config.get('size', [540, 550])
                }
                
                # Get photo configurations
                photo_config = security_features.get('photo', {})
                photo_small_config = security_features.get('photo_small', {})
                
                photo_conf = {
                    'position': photo_config.get('position', [128, 324]),
                    'size': photo_config.get('size', [550, 735])
                }
                
                # Extract address positions from JSON fields, but prefer settings (address_positions) when provided
                address_front = {}
                for field in mini_json.get('fields', []):
                    key = field.get('key')
                    if key in ['region_am', 'region_en', 'subcity_am', 'subcity_en', 'woreda_am', 'woreda_en']:
                        address_front[key] = field.get('position', [0, 0])

                # Override with positions supplied from settings for the selected city (ensures changes reflect)
                if address_positions and 'front' in address_positions:
                    for k, v in address_positions['front'].items():
                        address_front[k] = v
                
                # Create the layout structure expected by the generation code
                layout = {
                    'fields': mini_json.get('fields', []),
                    'address_front': address_front,
                    'photo': photo_conf,
                    'qr': qr_conf
                }
                
                return layout

            # Build scaled layout from normal template/json
            normal_img = Image.open(self.config.TEMPLATE_IMG)
            normal_w, normal_h = normal_img.size
            if not os.path.exists(self.config.MINI_TEMPLATE_IMG):
                # If mini template image missing, fall back to normal sizing
                mini_w, mini_h = int(normal_w * 0.4), int(normal_h * 0.4)
            else:
                mini_img = Image.open(self.config.MINI_TEMPLATE_IMG)
                mini_w, mini_h = mini_img.size

            scale_x = mini_w / float(normal_w)
            scale_y = mini_h / float(normal_h)
            scale = min(scale_x, scale_y)

            with open(self.config.TEMPLATE_JSON, encoding='utf-8') as f:
                normal_json = json.load(f)

            # Scale non-address fields
            addr_keys = set(address_positions['front'].keys())
            mini_fields = []
            for field in normal_json['fields']:
                key = field.get('key')
                if key in addr_keys:
                    continue
                pos = field['position']
                scaled_pos = [int(pos[0] * scale_x), int(pos[1] * scale_y)]
                font_spec = field['font']
                scaled_size = max(10, int(font_spec['size'] * scale))
                mini_fields.append({
                    'key': key,
                    'label': field.get('label', ''),
                    'position': scaled_pos,
                    'font': { 'size': scaled_size },
                    'color': field.get('color', [0, 0, 0]),
                    'align': field.get('align', 'left'),
                    'wrap_width': int(field.get('wrap_width', 0) * scale_x) if field.get('wrap_width') else None
                })

            # Scale address positions
            mini_address_front = {
                key: [int(pos[0] * scale_x), int(pos[1] * scale_y)]
                for key, pos in address_positions['front'].items()
            }

            # Scale photo and qr positions
            photo_pos_normal = (128, 250)
            photo_size_normal = self.config.PHOTO_SIZES['large']
            photo_conf = {
                'position': [int(photo_pos_normal[0] * scale_x), int(photo_pos_normal[1] * scale_y)],
                'size': [max(40, int(photo_size_normal[0] * scale)), max(40, int(photo_size_normal[1] * scale))]
            }

            qr_pos_normal = (2875, 90)
            qr_size_normal = (934, 937)
            qr_conf = {
                'position': [int(qr_pos_normal[0] * scale_x), int(qr_pos_normal[1] * scale_y)],
                'size': [max(40, int(qr_size_normal[0] * scale)), max(40, int(qr_size_normal[1] * scale))]
            }

            mini_json = {
                'fields': mini_fields,
                'address_front': mini_address_front,
                'photo': photo_conf,
                'qr': qr_conf
            }

            # Persist for later tweaking
            try:
                with open(self.config.MINI_TEMPLATE_JSON, 'w', encoding='utf-8') as mf:
                    json.dump(mini_json, mf, ensure_ascii=False, indent=2)
            except Exception as _:
                pass

            return mini_json
        except Exception as e:
            print(f"Error preparing mini layout: {str(e)}")
            # Fallback sensible defaults
            return {
                'fields': [],
                'address_front': address_positions['front'],
                'photo': {'position': [128, 180], 'size': [200, 260]},
                'qr': {'position': [1840, 65], 'size': [540, 550]}
            }

    def _generate_mini_id_cards(self, data: Dict, remove_white: bool = False, remove_black: bool = False, city_option: str = 'default', use_onnx_bg: bool = False) -> Dict[str, str]:
        """Render mini front cards using mini template but export at normal size."""
        try:
            name = (data.get('name_en') or 'ID').replace(' ', '_')
            normal_w, normal_h = Image.open(self.config.TEMPLATE_IMG).size
            # Prepare mini layout scaled up to normal canvas
            base_positions = (
                self.config.MINI_ADDRESS_POSITIONS.get(city_option)
                or self.config.ADDRESS_POSITIONS.get(city_option)
                or self.config.MINI_ADDRESS_POSITIONS.get('default')
                or self.config.ADDRESS_POSITIONS.get('default', {})
            )
            mini_layout = self._ensure_mini_layout(base_positions)
            if os.path.exists(self.config.MINI_TEMPLATE_IMG):
                mini_w, mini_h = Image.open(self.config.MINI_TEMPLATE_IMG).size
                template_base = self.config.MINI_TEMPLATE_IMG
            else:
                mini_w, mini_h = normal_w, normal_h
                template_base = self.config.TEMPLATE_IMG
            scale_up_x = normal_w / float(mini_w)
            scale_up_y = normal_h / float(mini_h)

            # Build scaled fields json
            scaled_fields = []
            for field in mini_layout.get('fields', []):
                pos = field.get('position', [0, 0])
                wrap_width = field.get('wrap_width')
                font_spec = field.get('font', {})
                scaled_fields.append({
                    'key': field.get('key'),
                    'label': field.get('label', ''),
                    'position': [int(pos[0] * scale_up_x), int(pos[1] * scale_up_y)],
                    'font': { 'size': max(10, int(font_spec.get('size', 12) * max(scale_up_x, scale_up_y))) },
                    'color': field.get('color', [0, 0, 0]),
                    'align': field.get('align', 'left'),
                    'wrap_width': int(wrap_width * scale_up_x) if wrap_width else None
                })

            used_address_positions_front = {
                k: [int(v[0] * scale_up_x), int(v[1] * scale_up_y)]
                for k, v in mini_layout.get('address_front', {}).items()
            }
            raw_photo = mini_layout.get('photo') or {}
            photo_conf = {
                'position': [int((raw_photo.get('position', [128, 180])[0]) * scale_up_x),
                             int((raw_photo.get('position', [1493, 860])[1]) * scale_up_y)],
                'size': [int((raw_photo.get('size', [200, 260])[0]) * scale_up_x),
                         int((raw_photo.get('size', [200, 260])[1]) * scale_up_y)]
            }
            raw_qr = mini_layout.get('qr') or {}
            qr_conf = {
                'position': [int((raw_qr.get('position', [50, 50])[0]) * scale_up_x),
                             int((raw_qr.get('position', [50, 50])[1]) * scale_up_y)],
                'size': [int((raw_qr.get('size', [300, 300])[0]) * scale_up_x),
                         int((raw_qr.get('size', [300, 300])[1]) * scale_up_y)]
            }

            # Preprocess photo
            photo_path = os.path.join(self.config.STATIC_FOLDER, 'photo_temp.png')
            src_photo = process_photo(photo_path, tuple(photo_conf['size']), remove_white, remove_black, use_onnx_bg) if os.path.exists(photo_path) else None
            src_photo_small = process_photo(photo_path, self.config.PHOTO_SIZES['small'], remove_white, remove_black, use_onnx_bg) if os.path.exists(photo_path) else None
            qr_path = os.path.join(self.config.STATIC_FOLDER, 'qr_temp.png')
            barcode_path = data.get('fcn_barcode')
            barcode_full_path = os.path.join(self.config.STATIC_FOLDER, barcode_path) if barcode_path else None

            def render_front(color: bool) -> Image.Image:
                canvas = Image.open(template_base).convert('RGBA')
                if canvas.size != (normal_w, normal_h):
                    canvas = canvas.resize((normal_w, normal_h), Image.LANCZOS)
                draw = ImageDraw.Draw(canvas)
                # Draw text fields
                for field in scaled_fields:
                    key = field['key']
                    if key in used_address_positions_front:
                        continue
                    content = data.get(key, field.get('label', ''))
                    pos = tuple(field['position'])
                    color_val = tuple(field.get('color', (0, 0, 0)))
                    align = field.get('align', 'left')
                    font_size = field['font']['size']
                    font = ImageFont.truetype(
                        self.config.AMHARIC_FONT_PATH if key.endswith('_am') else self.config.ENGLISH_FONT_PATH,
                        font_size
                    )
                    # Bold Amharic date fields on mini ID
                    is_amharic_date = key in ["issue_date_am", "expiry_date_am", "dob_am"]
                    # Handle rotated text for issue dates
                    if key in ["issue_date_am", "issue_date_en"]:
                        rotated_img, pos2 = draw_rotated_text(draw, content, pos, font, color_val, 90, bold=is_amharic_date)
                        # Ensure rotated text is fully within canvas bounds
                        new_x = max(0, min(pos2[0], canvas.width - rotated_img.width))
                        new_y = max(0, min(pos2[1], canvas.height - rotated_img.height))
                        canvas.paste(rotated_img, (new_x, new_y), rotated_img)
                    else:
                        max_width = field.get('wrap_width')
                        draw_text_with_alignment(draw, content, pos, font, color_val, align, max_width, bold=is_amharic_date)
                # Address
                mini_fonts = getattr(self.config, 'MINI_ADDRESS_FONT_SIZES', {'front': {'am': 36, 'en': 38}}).get('front', {'am': 36, 'en': 38})
                font_am = ImageFont.truetype(self.config.AMHARIC_FONT_PATH, mini_fonts.get('am', 36))
                font_en = ImageFont.truetype(self.config.ENGLISH_FONT_PATH, mini_fonts.get('en', 38))
                for key, pos in used_address_positions_front.items():
                    content = data.get(key, '')
                    font = font_am if key.endswith('_am') else font_en
                    max_width = getattr(self.config, 'MINI_TEXT_MAX_WIDTH', {}).get('front', {}).get(key, None) or getattr(self.config, 'TEXT_MAX_WIDTH', {}).get('front', {}).get(key, None)
                    draw_text_with_alignment(draw, content, tuple(pos), font, (0, 0, 0), "left", max_width)
                # Photo
                if src_photo:
                    img = src_photo if color else src_photo.convert('LA').convert('RGBA')
                    canvas.paste(img, tuple(photo_conf['position']), img)
                # Small Photo
                if src_photo_small:
                    img = src_photo_small if color else src_photo_small.convert('LA').convert('RGBA')
                    canvas.paste(img, (1493, 860), img)
                # QR
                if os.path.exists(qr_path):
                    qr_img = Image.open(qr_path).resize(tuple(qr_conf['size']))
                    canvas.paste(qr_img, tuple(qr_conf['position']))
                # Barcode with text
                if barcode_full_path and os.path.exists(barcode_full_path):
                    barcode_img = Image.open(barcode_full_path)
                    gray = barcode_img.convert('L')
                    bbox = gray.point(lambda x: 0 if x > 250 else 255, '1').getbbox()
                    if bbox:
                        barcode_img = barcode_img.crop(bbox)
                    barcode_img = barcode_img.resize((450, 87))
                    canvas.paste(barcode_img, (860, 910))
                    font = ImageFont.truetype(self.config.ENGLISH_FONT_PATH, 42)
                    text_width = draw.textlength(data['fcn_formatted'], font=font)
                    center_x = 835 + (500 - text_width) // 2
                    draw.text((center_x, 853), data['fcn_formatted'], font=font, fill=(0, 0, 0))
                return canvas

            img_color = render_front(True)
            img_bw = render_front(False)
            mini_color_filename = f"{name}_Mini_Front_Color.png"
            mini_bw_filename = f"{name}_Mini_Front_Grayscale.png"
            img_color.save(os.path.join(self.config.STATIC_FOLDER, mini_color_filename))
            img_bw.save(os.path.join(self.config.STATIC_FOLDER, mini_bw_filename))
            
            # Clean up old images after successful generation
            current_files = [mini_color_filename, mini_bw_filename]
            self.cleanup_old_images(keep_current_files=current_files)
            
            return {
                'mini_front_color': mini_color_filename,
                'mini_front_bw': mini_bw_filename
            }
        except Exception as e:
            print(f"Error generating mini ID cards: {str(e)}")
            return {}

    def _generate_old_id_cards(self, data: Dict, remove_white: bool = False, remove_black: bool = False, city_option: str = 'default', use_onnx_bg: bool = False) -> Dict[str, str]:
        """Render old ID cards using old template (both front and reverse)."""
        try:
            name = (data.get('name_en') or 'ID').replace(' ', '_')
            
            # Load old template configurations
            if os.path.exists(self.config.OLD_TEMPLATE_JSON):
                with open(self.config.OLD_TEMPLATE_JSON, encoding='utf-8') as f:
                    old_front_layout = json.load(f)
            else:
                print("Old front template JSON not found, using default layout")
                old_front_layout = {
                    'fields': [],
                    'photo': {'main': {'position': [128, 250], 'size': [550, 700]}},
                    'qr': {'position': [2875, 90], 'size': [934, 937]},
                    'barcode': {'position': [857, 930], 'size': [487, 87]}
                }

            if os.path.exists(self.config.OLD_REVERSE_TEMPLATE_JSON):
                with open(self.config.OLD_REVERSE_TEMPLATE_JSON, encoding='utf-8') as f:
                    old_reverse_layout = json.load(f)
            else:
                print("Old reverse template JSON not found, using default layout")
                old_reverse_layout = {
                    'fields': [],
                    'photo': {'main': {'position': [128, 324], 'size': [550, 735]}},
                    'qr': {'position': [2875, 90], 'size': [934, 937]}
                }

            # Get template images
            front_template = self.config.OLD_TEMPLATE_IMG if os.path.exists(self.config.OLD_TEMPLATE_IMG) else self.config.TEMPLATE_IMG
            reverse_template = self.config.OLD_REVERSE_TEMPLATE_IMG if os.path.exists(self.config.OLD_REVERSE_TEMPLATE_IMG) else self.config.REVERSE_TEMPLATE_IMG

            # Preprocess photo
            photo_path = os.path.join(self.config.STATIC_FOLDER, 'photo_temp.png')
            qr_path = os.path.join(self.config.STATIC_FOLDER, 'qr_temp.png')
            
            # Photo configurations - use actual positions from JSON files
            front_photo_conf = old_front_layout.get('photo', {}).get('main', {})
            front_photo_size = tuple(front_photo_conf.get('size', [550, 700]))
            front_photo_pos = tuple(front_photo_conf.get('position', [128, 250]))
            
            reverse_photo_conf = old_reverse_layout.get('photo', {}).get('main', {})
            # Use same positions and sizes as default reverse ID
            reverse_photo_size = tuple(reverse_photo_conf.get('size', [255, 330]))  # Same as default reverse_large
            # Position for large photo to appear on RIGHT after flip (mirror of default reverse)
            reverse_photo_pos = (148, 130)  # Mirrored position for right side after flip
            
            # QR configurations - use actual positions from JSON files
            front_qr_conf = old_front_layout.get('qr', {})
            front_qr_size = tuple(front_qr_conf.get('size', [934, 937]))
            front_qr_pos = tuple(front_qr_conf.get('position', [2875, 90]))
            
            # Use same QR position and size as default reverse
            reverse_qr_conf = old_reverse_layout.get('qr', {})
            reverse_qr_size = (380, 390)  # Same as default reverse
            # Position for QR to appear on LEFT after flip (mirror of default reverse)
            reverse_qr_pos = (1290, 50)   # Mirrored position for left side after flip
            
            # Barcode configuration (front only) - use actual position from JSON file
            barcode_conf = old_front_layout.get('barcode', {})
            barcode_size = tuple(barcode_conf.get('size', [487, 87]))
            barcode_pos = tuple(barcode_conf.get('position', [857, 930]))

            # Address positions for old template based on selected city (separate map for old)
            old_address_positions = self.config.OLD_ADDRESS_POSITIONS.get(city_option, self.config.OLD_ADDRESS_POSITIONS['default'])

            def render_old_front(color: bool) -> Image.Image:
                canvas = Image.open(front_template).convert('RGBA')
                draw = ImageDraw.Draw(canvas)
                
                # Draw text fields from old front template
                for field in old_front_layout.get('fields', []):
                    key = field.get('key')
                    if not key or key.startswith('label_'):
                        continue
                    # Avoid duplicate address: skip if handled by city address positions
                    if key in old_address_positions['front']:
                        continue
                    
                    content = data.get(key, field.get('label', ''))
                    if not content:
                        continue
                        
                    pos = tuple(field.get('position', [0, 0]))
                    color_val = tuple(field.get('color', [0, 0, 0]))
                    align = field.get('align', 'left')
                    font_size = field.get('font', {}).get('size', 32)
                    
                    # Select appropriate font
                    if key.endswith('_am'):
                        font = ImageFont.truetype(self.config.AMHARIC_FONT_PATH, font_size)
                    else:
                        font = ImageFont.truetype(self.config.ENGLISH_FONT_PATH, font_size)
                    
                    # Bold Amharic date fields
                    is_amharic_date = key in ["issue_date_am", "expiry_date_am", "dob_am"]

                    # Handle rotated text for issue date
                    if key in ["issue_date_am", "issue_date_en"]:
                        rotated_img, pos2 = draw_rotated_text(draw, content, pos, font, color_val, 90, bold=is_amharic_date)
                        canvas.paste(rotated_img, pos2, rotated_img)
                    else:
                        max_width = field.get('wrap_width')
                        draw_text_with_alignment(draw, content, pos, font, color_val, align, max_width, bold=is_amharic_date)
                
                # Draw address fields using selected city positions
                fs_old_front = getattr(self.config, 'OLD_ADDRESS_FONT_SIZES', {}).get('front', {'am': 48, 'en': 50})
                font_am = ImageFont.truetype(self.config.AMHARIC_FONT_PATH, fs_old_front.get('am', 48))
                font_en = ImageFont.truetype(self.config.ENGLISH_FONT_PATH, fs_old_front.get('en', 50))
                for key, pos in old_address_positions['front'].items():
                    content = data.get(key, '')
                    font = font_am if key.endswith('_am') else font_en
                    max_width = getattr(self.config, 'OLD_TEXT_MAX_WIDTH', {}).get('front', {}).get(key, None) or self.config.TEXT_MAX_WIDTH['front'].get(key, None)
                    draw_text_with_alignment(draw, content, tuple(pos), font, (0, 0, 0), 'left', max_width)
                
                # Large Photo
                if os.path.exists(photo_path):
                    src_photo = process_photo(photo_path, front_photo_size, remove_white, remove_black, use_onnx_bg)
                    if src_photo:
                        img = src_photo if color else src_photo.convert('LA').convert('RGBA')
                        canvas.paste(img, front_photo_pos, img)
                
                # Small Photo (for old ID front)
                if os.path.exists(photo_path):
                    small_photo_size = (199, 205)  # Small photo size
                    small_photo_pos = (1493, 860)  # Small photo position
                    src_photo_small = process_photo(photo_path, small_photo_size, remove_white, remove_black, use_onnx_bg)
                    if src_photo_small:
                        img_small = src_photo_small if color else src_photo_small.convert('LA').convert('RGBA')
                        canvas.paste(img_small, small_photo_pos, img_small)
                
                # QR Code
                if os.path.exists(qr_path):
                    qr_img = Image.open(qr_path).resize(front_qr_size)
                    canvas.paste(qr_img, front_qr_pos)
                
                # Barcode
                barcode_path = data.get('fcn_barcode')
                if barcode_path:
                    barcode_full_path = os.path.join(self.config.STATIC_FOLDER, barcode_path)
                    if os.path.exists(barcode_full_path):
                        barcode_img = Image.open(barcode_full_path)
                        barcode_img = barcode_img.resize(barcode_size)
                        canvas.paste(barcode_img, barcode_pos)
                        
                        # Add FCN text above barcode
                        fcn_text = data.get('fcn_formatted', '')
                        if fcn_text:
                            # If JSON provides barcode_text configuration, use it; otherwise fallback to centered above barcode
                            bt_conf = old_front_layout.get('barcode_text') or {}
                            bt_font_conf = bt_conf.get('font', {})
                            bt_font_size = bt_font_conf.get('size', 24)
                            font = ImageFont.truetype(self.config.ENGLISH_FONT_PATH, bt_font_size)
                            text_width = draw.textlength(fcn_text, font=font)
                            if bt_conf.get('position'):
                                base_x, base_y = tuple(bt_conf.get('position', [barcode_pos[0], barcode_pos[1] - 30]))
                                align = bt_conf.get('align', 'center')
                                if align == 'center':
                                    x = base_x - text_width // 2
                                elif align == 'right':
                                    x = base_x - text_width
                                else:
                                    x = base_x
                                y = base_y
                            else:
                                # fallback: centered above barcode image
                                x = barcode_pos[0] + (barcode_size[0] - text_width) // 2
                                y = barcode_pos[1] - 30
                            draw.text((x, y), fcn_text, font=font, fill=(0, 0, 0))
                
                return canvas

            def render_old_reverse(color: bool) -> Image.Image:
                canvas = Image.open(reverse_template).convert('RGBA')
                data_layer = Image.new("RGBA", canvas.size, (255, 255, 255, 0))
                draw = ImageDraw.Draw(data_layer)
                
                # Draw text fields from old reverse template
                for field in old_reverse_layout.get('fields', []):
                    key = field.get('key')
                    if not key or key.startswith('label_'):
                        continue
                    # Avoid duplicate address: skip if handled by city address positions
                    if key in old_address_positions['reverse']:
                        continue
                    
                    content = data.get(key, field.get('label', ''))
                    if not content:
                        continue
                        
                    pos = tuple(field.get('position', [0, 0]))
                    color_val = tuple(field.get('color', [0, 0, 0]))
                    align = field.get('align', 'left')
                    font_size = field.get('font', {}).get('size', 32)
                    
                    # Select appropriate font
                    if key.endswith('_am'):
                        font = ImageFont.truetype(self.config.AMHARIC_FONT_PATH, font_size)
                    else:
                        font = ImageFont.truetype(self.config.ENGLISH_FONT_PATH, font_size)
                    
                    # Bold Amharic date fields on reverse too
                    is_amharic_date = key in ["issue_date_am", "expiry_date_am", "dob_am"]

                    # Rotate issue date text vertically if applicable
                    if key in ["issue_date_am", "issue_date_en"]:
                        rotated_img, pos2 = draw_rotated_text(draw, content, pos, font, color_val, 90, bold=is_amharic_date)
                        data_layer.paste(rotated_img, pos2, rotated_img)
                    else:
                        max_width = field.get('wrap_width')
                        draw_text_with_alignment(draw, content, pos, font, color_val, align, max_width, bold=is_amharic_date)
                
                # Large Photo
                if os.path.exists(photo_path):
                    src_photo = process_photo(photo_path, reverse_photo_size, remove_white, remove_black, use_onnx_bg)
                    if src_photo:
                        img = src_photo if color else src_photo.convert('LA').convert('RGBA')
                        data_layer.paste(img, reverse_photo_pos, img)
                
                # Small Photo (same as default reverse)
                if os.path.exists(photo_path):
                    small_photo_size = (105, 115)  # Same as default reverse_small
                    # Position for small photo to appear on RIGHT after flip (mirror of default reverse)
                    small_photo_pos = (710, 360)  # Mirrored position for right side after flip
                    src_photo_small = process_photo(photo_path, small_photo_size, remove_white, remove_black, use_onnx_bg)
                    if src_photo_small:
                        img_small = src_photo_small if color else src_photo_small.convert('LA').convert('RGBA')
                        data_layer.paste(img_small, small_photo_pos, img_small)
                
                # QR Code
                if os.path.exists(qr_path):
                    qr_img = Image.open(qr_path).resize(reverse_qr_size)
                    data_layer.paste(qr_img, reverse_qr_pos)
                
                # Barcode (same as default reverse)
                barcode_path = data.get('fcn_barcode')
                if barcode_path:
                    barcode_full_path = os.path.join(self.config.STATIC_FOLDER, barcode_path)
                    if os.path.exists(barcode_full_path):
                        barcode_img = Image.open(barcode_full_path)
                        gray = barcode_img.convert('L')
                        bbox = gray.point(lambda x: 0 if x > 250 else 255, '1').getbbox()
                        if bbox:
                            barcode_img = barcode_img.crop(bbox)
                        barcode_img = barcode_img.resize((206, 40))
                        # Position for barcode to appear on RIGHT after flip (mirror of default reverse)
                        data_layer.paste(barcode_img, (460, 425))  # Mirrored position for right side after flip
                        
                        # Add FCN text above barcode (same as default reverse)
                        fcn_text = data.get('fcn_formatted', '')
                        if fcn_text:
                            font = ImageFont.truetype(self.config.ENGLISH_FONT_PATH, 18)
                            text_width = draw.textlength(fcn_text, font=font)
                            # Position for FCN text to appear on RIGHT after flip
                            center_x = 423 + (287 - text_width) // 2
                            draw.text((center_x, 399), fcn_text, font=font, fill=(0, 0, 0))
                
                # Draw address fields on reverse using selected city positions
                fs_old_rev = getattr(self.config, 'OLD_ADDRESS_FONT_SIZES', {}).get('reverse', {'am': 34, 'en': 34})
                font_am = ImageFont.truetype(self.config.AMHARIC_FONT_PATH, fs_old_rev.get('am', 34))
                font_en = ImageFont.truetype(self.config.ENGLISH_FONT_PATH, fs_old_rev.get('en', 34))
                for key, pos in old_address_positions['reverse'].items():
                    content = data.get(key, '')
                    font = font_am if key.endswith('_am') else font_en
                    max_width = getattr(self.config, 'OLD_TEXT_MAX_WIDTH', {}).get('reverse', {}).get(key, None) or self.config.TEXT_MAX_WIDTH['reverse'].get(key, None)
                    draw_text_with_alignment(draw, content, tuple(pos), font, (0, 0, 0), 'left', max_width)

                # Flip the data layer horizontally like the default reverse ID
                flipped_data = data_layer.transpose(Image.FLIP_LEFT_RIGHT)
                canvas.alpha_composite(flipped_data)
                
                return canvas

            # Generate both front and reverse, color and grayscale versions
            front_color = render_old_front(True)
            front_bw = render_old_front(False)
            reverse_color = render_old_reverse(True)
            reverse_bw = render_old_reverse(False)
            
            # Save files
            old_front_color_filename = f"{name}_Old_Front_Color.png"
            old_front_bw_filename = f"{name}_Old_Front_Grayscale.png"
            old_reverse_color_filename = f"{name}_Old_Reverse_Color.png"
            old_reverse_bw_filename = f"{name}_Old_Reverse_Grayscale.png"
            
            front_color.save(os.path.join(self.config.STATIC_FOLDER, old_front_color_filename))
            front_bw.save(os.path.join(self.config.STATIC_FOLDER, old_front_bw_filename))
            reverse_color.save(os.path.join(self.config.STATIC_FOLDER, old_reverse_color_filename))
            reverse_bw.save(os.path.join(self.config.STATIC_FOLDER, old_reverse_bw_filename))
            
            # Clean up old images after successful generation
            current_files = [
                old_front_color_filename,
                old_front_bw_filename,
                old_reverse_color_filename,
                old_reverse_bw_filename
            ]
            self.cleanup_old_images(keep_current_files=current_files)
            
            return {
                'old_front_color': old_front_color_filename,
                'old_front_bw': old_front_bw_filename,
                'old_reverse_color': old_reverse_color_filename,
                'old_reverse_bw': old_reverse_bw_filename
            }
            
        except Exception as e:
            print(f"Error generating old ID cards: {str(e)}")
            return {}