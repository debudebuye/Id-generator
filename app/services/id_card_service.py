from PIL import Image, ImageDraw, ImageFont, ImageStat, ImageFilter
import json
import os
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

from ..config.settings import Config
from ..utils.image_utils import process_photo, draw_text_with_alignment, draw_rotated_text
from ..utils.date_utils import get_id_dates, gregorian_to_ethiopian # Added gregorian_to_ethiopian

class IDCardService:
    # PDF_FORMAT_MAPPING defines line indices for default and image indices for all.
    # Residential Addis and Sheger now explicitly define image indices.
    # For residential formats, line numbers in mapping are illustrative as pattern-based parsing is used.
    PDF_FORMAT_MAPPING = {
        'default': {
            'fcn': 0,
            'name': 1,
            'dob': 2,
            'gender': 3,
            'nationality': 4,
            'phone': 5,
            'region': 6,
            'subcity': 7,
            'woreda': 8,
            'photo_img_index': 1, # Index in images list for photo
            'qr_img_index': 2 # Index in images list for QR
        },

        'residential_sheger': {
            'photo_img_index': 0, # Based on user's snippet for residential
            'qr_img_index': 1 # Based on user's snippet for residential
        },
        
        'demographic_format': {
            'photo_img_index': 0, # Same as residential for now
            'qr_img_index': 1 # Same as residential for now
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
            
            print(f"    No separator found, returning same for both: '{line}' | '{line}'")
            return line, line # Return same for both if no pipe
        except IndexError as e:
            print(f"    IndexError in _parse_line: {str(e)}")
            return "", ""
        except Exception as e:
            print(f"    Unexpected error in _parse_line: {str(e)}")
            return "", ""

    def _extract_address_components(self, lines: List[str], region_index: int) -> Tuple[str, str, str, str]:
        """Extract subcity and woreda information with improved logic."""
        subcity_am, subcity_en = "", ""
        woreda_am, woreda_en = ""
        
        print(f"Address extraction - Region index: {region_index}")
        print(f"Available lines around region:")
        for i in range(max(0, region_index - 1), min(len(lines), region_index + 4)):
            print(f"  Line {i}: '{lines[i]}'")
        
        # Try to find subcity and woreda in the expected positions first
        if region_index + 1 < len(lines):
            subcity_am, subcity_en = self._parse_line(lines, region_index + 1)
        if region_index + 2 < len(lines):
            woreda_am, woreda_en = self._parse_line(lines, region_index + 2)
            
        # Special handling for the case where line 8 is malformed (no separator)
        if region_index + 2 < len(lines):
            line_8 = lines[region_index + 2].strip()
            if line_8 and '|' not in line_8:
                print(f"  Line 8 is malformed (no separator): '{line_8}'")
                # Skip this line and try to find woreda in the next line
                if region_index + 3 < len(lines):
                    woreda_am, woreda_en = self._parse_line(lines, region_index + 3)
                    print(f"  Found woreda in line {region_index + 3}: '{woreda_am}' | '{woreda_en}'")
        
        print(f"Initial extraction from expected positions:")
        print(f"  Subcity (line {region_index + 1}): '{subcity_am}' | '{subcity_en}'")
        print(f"  Woreda (line {region_index + 2}): '{woreda_am}' | '{woreda_en}'")
        
        # Check if we have the same content for both subcity and woreda (indicates extraction error)
        if subcity_am == woreda_am and subcity_am and woreda_am:
            print(f"WARNING: Subcity and woreda have identical content: '{subcity_am}'")
            # This suggests we're getting the same line twice, need to look for actual woreda
            woreda_am, woreda_en = "", ""
        
        # If we don't have complete data, search more intelligently
        if not subcity_am or not subcity_en or not woreda_am or not woreda_en:
            # Search for address-related keywords in nearby lines
            search_start = max(0, region_index - 2)
            search_end = min(len(lines), region_index + 5)
            
            for i in range(search_start, search_end):
                line = lines[i].strip()
                if not line or i == region_index:  # Skip empty lines and region line
                    continue
                    
                print(f"Analyzing line {i}: '{line}'")
                
                # Look for subcity indicators
                if any(keyword in line.lower() for keyword in ['ክፍለ ከተማ', 'sub-city', 'subcity', 'ከተማ አስተዳደር', 'administration']):
                    if '|' in line:
                        parts = line.split('|', 1)
                        if len(parts) == 2:
                            amharic, english = parts[0].strip(), parts[1].strip()
                            if not subcity_am:
                                subcity_am = amharic
                                subcity_en = english
                                print(f"  Found subcity by keyword: '{subcity_am}' | '{subcity_en}'")
                
                # Look for woreda indicators
                elif any(keyword in line.lower() for keyword in ['ወረዳ', 'woreda', 'kebele', 'ቀበሌ']):
                    if '|' in line:
                        parts = line.split('|', 1)
                        if len(parts) == 2:
                            amharic, english = parts[0].strip(), parts[1].strip()
                            if not woreda_am:
                                woreda_am = amharic
                                woreda_en = english
                                print(f"  Found woreda by keyword: '{woreda_am}' | '{woreda_en}'")
                
                # If no keywords found, try to identify by content patterns
                elif '|' in line:
                    parts = line.split('|', 1)
                    if len(parts) == 2:
                        amharic, english = parts[0].strip(), parts[1].strip()
                    else:
                        amharic, english = parts[0].strip(), parts[0].strip()
                    
                    # Skip if this line is already used for region
                    if i == region_index:
                        continue
                    
                    # Check if this looks like a subcity (usually longer names, administrative terms)
                    if (len(amharic) > 3 and 
                        not any(char.isdigit() for char in amharic) and
                        not subcity_am and
                        not any(keyword in amharic.lower() for keyword in ['ወረዳ', 'woreda', 'kebele']) and
                        ('ከተማ' in amharic or 'administration' in english.lower())):
                        subcity_am = amharic
                        subcity_en = english
                        print(f"  Identified as subcity by pattern: '{subcity_am}' | '{subcity_en}'")
                    
                    # Check if this looks like a woreda (usually shorter, more specific)
                    elif (len(amharic) > 2 and 
                          not any(char.isdigit() for char in amharic) and
                          not woreda_am and
                          not any(keyword in amharic.lower() for keyword in ['ክፍለ ከተማ', 'sub-city', 'subcity', 'administration']) and
                          not ('ከተማ' in amharic or 'administration' in english.lower())):
                        woreda_am = amharic
                        woreda_en = english
                        print(f"  Identified as woreda by pattern: '{woreda_am}' | '{woreda_en}'")
                
                # Handle lines without separator (like line 8 in your case)
                elif line and not any(char.isdigit() for char in line) and len(line) > 2:
                    print(f"  Found line without separator: '{line}' - skipping as it's likely malformed")
                    continue
        
        # Fallback: if we still don't have data, try the original line indices
        if not subcity_am and not subcity_en:
            try:
                if region_index + 1 < len(lines):
                    subcity_am, subcity_en = self._parse_line(lines, region_index + 1)
                    print(f"  Fallback subcity from line {region_index + 1}: '{subcity_am}' | '{subcity_en}'")
            except:
                pass
                
        if not woreda_am and not woreda_en:
            try:
                if region_index + 2 < len(lines):
                    woreda_am, woreda_en = self._parse_line(lines, region_index + 2)
                    print(f"  Fallback woreda from line {region_index + 2}: '{woreda_am}' | '{woreda_en}'")
            except:
                pass
        
        # Ensure we have at least some data
        if not subcity_am:
            subcity_am = subcity_en if subcity_en else ""
        if not subcity_en:
            subcity_en = subcity_am if subcity_am else ""
        if not woreda_am:
            woreda_am = woreda_en if woreda_en else ""
        if not woreda_en:
            woreda_en = woreda_am if woreda_am else ""
        
        # Try to detect if we have mixed up subcity and woreda
        # Sometimes the order might be different in the PDF
        if (subcity_am and woreda_am and 
            len(subcity_am) < len(woreda_am) and 
            not any(keyword in subcity_am.lower() for keyword in ['ክፍለ ከተማ', 'sub-city', 'subcity', 'administration']) and
            any(keyword in woreda_am.lower() for keyword in ['ከተማ', 'administration'])):
            # Swap them if subcity looks more like a woreda and woreda looks more like a subcity
            print(f"Swapping subcity and woreda due to content mismatch")
            subcity_am, woreda_am = woreda_am, subcity_am
            subcity_en, woreda_en = woreda_en, subcity_en
        
        # Final validation: ensure we don't have identical content
        if subcity_am == woreda_am and subcity_am:
            print(f"ERROR: Subcity and woreda still have identical content after processing: '{subcity_am}'")
            # Clear woreda if they're identical
            woreda_am, woreda_en = "", ""
        
        # Debug logging
        print(f"Final address extraction result:")
        print(f"  Subcity: '{subcity_am}' | '{subcity_en}'")
        print(f"  Woreda: '{woreda_am}' | '{woreda_en}'")
        
        return subcity_am, subcity_en, woreda_am, woreda_en

    def get_photo_data(self, data: Dict, remove_white: bool = False, remove_black: bool = False) -> bytes:
        """Return photo image bytes from provided data or create a placeholder.
        
        Supports:
        - data['photo_bytes']: raw bytes
        - data['photo_b64']: base64-encoded string
        - data['photo']: file path relative or absolute
        Falls back to a transparent placeholder if nothing available.
        """
        try:
            # 1) Raw bytes
            if data.get('photo_bytes'):
                if isinstance(data['photo_bytes'], bytes):
                    return data['photo_bytes']
                else:
                    return data['photo_bytes'].encode('utf-8')
            
            # 2) Base64 encoded
            if data.get('photo_b64'):
                import base64
                return base64.b64decode(data['photo_b64'])
            
            # 3) File path
            if data.get('photo'):
                photo_path = data['photo']
                if not os.path.isabs(photo_path):
                    photo_path = os.path.join(self.config.STATIC_FOLDER, photo_path)
                if os.path.exists(photo_path):
                    with open(photo_path, 'rb') as f:
                        return f.read()
            
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
        """Validate and clean address data to ensure consistency."""
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
                    if not pattern_subcity_en and any(x in ln.lower() for x in ["zone", "subcity", "sub city", "city admin", "city administration"]):
                        l, r = split_pair(ln)
                        pattern_subcity_am, pattern_subcity_en = l, r
                        continue
                    if not pattern_woreda_en and any(x in ln.lower() for x in ["woreda", "administration", "admin", "kebele"]):
                        l, r = split_pair(ln)
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
                # Nationality bilingual
                if '|' in ln and not pattern_nat_en and any(x in ln for x in ["ኢትዮጵያ", "ኢትዮጵያዊ", "Ethiopian"]):
                    l, r = split_pair(ln)
                    if (l in ["ኢትዮጵያ", "ኢትዮጵያዊ"]) and r.lower().startswith("ethiop"):
                        pattern_nat_am, pattern_nat_en = l, "Ethiopian"
                        continue
                # Phone (10 digits typical)
                digits = ln.replace(" ", "")
                if not pattern_phone and digits.isdigit() and 9 <= len(digits) <= 13:
                    pattern_phone = ln.strip()

            # Apply pattern overrides when found
            if pattern_name_en and pattern_name_am:
                name_en, name_am = pattern_name_en, pattern_name_am
            if pattern_dob_en and pattern_dob_am:
                dob_en_raw, dob_am = pattern_dob_en, pattern_dob_am
            if pattern_gender_en and pattern_gender_am:
                gender_en, gender_am = pattern_gender_en, pattern_gender_am
            if pattern_nat_en and pattern_nat_am:
                nationality_en, nationality_am = pattern_nat_en, pattern_nat_am
            if pattern_phone:
                phone = self.format_phone_number(pattern_phone)
            if pattern_region_en and pattern_region_am:
                region_en, region_am = pattern_region_en, pattern_region_am
            if pattern_subcity_en and pattern_subcity_am:
                subcity_en, subcity_am = pattern_subcity_en, pattern_subcity_am
            if pattern_woreda_en and pattern_woreda_am:
                woreda_en, woreda_am = pattern_woreda_en, pattern_woreda_am
        except Exception as _:
            pass
        # Debug: Log the PDF structure around address fields
        print(f"PDF structure debug - Lines around address fields:")
        for i in range(max(0, line_indices['region'] - 2), min(len(lines), line_indices['region'] + 5)):
            print(f"  Line {i}: '{lines[i]}'")
        
        # Extract address components with improved logic
        try:
            if not region_am or not region_en:
                region_am, region_en = self._parse_line(lines, line_indices['region'])
            # Only derive structured address if any part missing from pattern scan
            if (not subcity_am or not subcity_en) or (not woreda_am or not woreda_en):
                subcity_am, subcity_en, woreda_am, woreda_en = self._extract_address_components(lines, line_indices['region'])
            
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
                print(f"  Woreda extracted: '{woreda_am}' | '{woreda_en}'")
                
                # Check if woreda looks like it's actually subcity data (malformed line)
                if woreda_am == woreda_en and 'administration' in woreda_en.lower():
                    print(f"  Woreda appears to be malformed subcity data, trying next line...")
                    # Try the next line for woreda
                    if line_indices['woreda'] + 1 < len(lines):
                        woreda_am, woreda_en = self._parse_line(lines, line_indices['woreda'] + 1)
                        print(f"  Woreda from next line: '{woreda_am}' | '{woreda_en}'")
                    else:
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
        """Extract data from Residential Sheger PDF format using pattern matching."""
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
            elif line.strip() in ["ኢትዮጵያዊ", "ኢትዮጵያ"]:  # Fix: Added "ኢትዮጵያ" as possible Amharic value
                extracted["nationality_am"] = line.strip()
                print(f"Found nationality AM: '{line.strip()}'")
                # Look for English nationality in next few lines
                for j in range(i+1, min(i+4, len(lines))):
                    if lines[j].strip() in ["Ethiopian", "Ethiopia"]:  # Fix: Added "Ethiopia" as possible English value
                        extracted["nationality_en"] = "Ethiopian"  # Fix: Always set to "Ethiopian"
                        print(f"Found nationality EN: '{lines[j].strip()}'")
                continue
            elif line.replace(" ", "").isdigit() and len(line.replace(" ", "")) == 10:
                extracted["phone"] = line.strip()
                print(f"Found phone: '{line.strip()}'")
        
                # Extract names with more targeted approach
        # Try to detect bilingual name line like "የስም | Name" with no digits
        if not extracted["name_en"] and not extracted["name_am"]:
            for i, line in enumerate(lines):
                if "|" in line and not any(ch.isdigit() for ch in line):
                    left, right = [part.strip() for part in line.split("|", 1)]
                    # Exclude obvious labels/addresses
                    excluded_en = ["region", "zone", "sub city", "city", "admin", "administration", "woreda", "kebele", "sex", "nationality", "phone", "date", "demographic", "disclaimer"]
                    if (any(ord(c) > 127 for c in left) and right.replace(" ", "").replace("-", "").replace(".", "").isalpha() and
                        not any(word in right.lower() for word in excluded_en)):
                        extracted["name_am"] = left
                        extracted["name_en"] = right
                        break

        # First, try to find names near the FCN number (most reliable location)
        if extracted["fcn"] and (not extracted["name_en"] or not extracted["name_am"]):
            print(f"Looking for names near FCN: {extracted['fcn']}")
            for i, line in enumerate(lines):
                if extracted["fcn"] in line:  # Found the FCN line
                    print(f"Found FCN at line {i}: '{line}'")
                    # Look for names in the next few lines after FCN
                    for j in range(i+1, min(i+8, len(lines))):
                        check_line = lines[j].strip()
                        if not check_line or len(check_line) < 3:
                            continue
                            
                        print(f"  Checking line {j}: '{check_line}'")
                        
                        # Skip lines that are clearly not names
                        if any(word.lower() in check_line.lower() for word in [
                            "subcity", "woreda", "region", "address", "phone", "date",
                            "ethiopian", "ethiopia", "digital", "id", "card", "program",
                            "national", "identity", "valid", "forms", "legal", "sex",
                            "nationality", "demographic", "disclaimer",
                            "የኢትዮጵያ", "ብሔራዊ", "መታወቂያ", "ፕሮግራም"
                        ]):
                            print(f"    Skipping (contains excluded words): '{check_line}'")
                            continue
                            
                        # Check if it's an English name (only letters, spaces, dots, hyphens)
                        if (check_line.replace(" ", "").replace(".", "").replace("-", "").isalpha() and 
                            len(check_line.split()) >= 2 and len(check_line.split()) <= 5 and
                            len(check_line) < 60):
                            
                            # Additional validation: should not contain common non-name words
                            if not any(word.lower() in check_line.lower() for word in ["subcity", "woreda", "region", "address", "phone", "date", "ethiopian", "ethiopia", "digital", "id", "card", "program", "national", "identity", "valid", "forms", "legal", "የኢትዮጵያ", "ብሔራዊ", "መታወቂያ", "ፕሮግራም"]):
                                extracted["name_en"] = check_line
                                print(f"    Found English name: '{check_line}'")
                                break
                        
                        # Check if it's an Amharic name (contains Amharic characters)
                        elif any(ord(char) > 127 for char in check_line):
                            if (len(check_line.split()) >= 2 and len(check_line.split()) <= 5 and
                                len(check_line) < 60 and
                                not any(word in check_line for word in ["ወረዳ", "Woreda", "ለሚ", "Lemi", "አራዳ", "Arada", "ፆታ", "የኢትዮጵያ", "ብሔራዊ", "መታወቂያ", "ፕሮግራም"])):
                                
                                extracted["name_am"] = check_line
                                print(f"    Found Amharic name: '{check_line}'")
                                break
                    break
        else:
            print("No FCN found, will try pattern-based name search...")
        
        # If still no names, try looking for names in specific patterns
        if not extracted["name_en"] and not extracted["name_am"]:
            print("Trying pattern-based name search...")
            for i, line in enumerate(lines):
                line_clean = line.strip()
                
                # Skip empty lines, numbers, and very short lines
                if not line_clean or len(line_clean) < 3 or line_clean.isdigit():
                    continue
                
                # Look for English names with strict validation
                if (line_clean.replace(" ", "").replace(".", "").replace("-", "").isalpha() and 
                    len(line_clean.split()) >= 2 and len(line_clean.split()) <= 5 and
                    len(line_clean) < 60):
                    
                    # Must NOT contain any of these words
                    excluded_words = [
                        "subcity", "woreda", "region", "address", "phone", "date",
                        "ethiopian", "ethiopia", "digital", "id", "card", "program",
                        "national", "identity", "valid", "forms", "legal", "sex",
                        "demographic", "disclaimer", "ethiopian digital id card", "nationality",
                        "የኢትዮጵያ", "ብሔራዊ", "መታወቂያ", "ፕሮግራም"
                    ]
                    if not any(word.lower() in line_clean.lower() for word in excluded_words):
                        extracted["name_en"] = line_clean
                        print(f"Found English name with pattern search: '{line_clean}'")
                        break
                
                # Look for Amharic names with strict validation
                elif any(ord(char) > 127 for char in line_clean):
                    if (len(line_clean.split()) >= 2 and len(line_clean.split()) <= 5 and
                        len(line_clean) < 60):
                        
                        excluded_words = [
                            "ወረዳ", "Woreda", "ለሚ", "Lemi", "አራዳ", "Arada", "ፆታ",
                            "ማሳሰቢያ", "የስነ ሕዝብ መረጃ", "ዜግነት",
                            "የኢትዮጵያ", "ብሔራዊ", "መታወቂያ", "ፕሮግራም"
                        ]
                        if not any(word in line_clean for word in excluded_words):
                            extracted["name_am"] = line_clean
                            print(f"Found Amharic name with pattern search: '{line_clean}'")
                            break

        # If nationality is still not set but we found Amharic, set default English
        if extracted["nationality_am"] and not extracted["nationality_en"]:
            extracted["nationality_en"] = "Ethiopian"
        # If we found neither, but we know this is an Ethiopian ID
        if not extracted["nationality_am"] and not extracted["nationality_en"]:
            extracted["nationality_am"] = "ኢትዮጵያዊ"
            extracted["nationality_en"] = "Ethiopian"
        
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

        return processed_data

    def _extract_demographic_format_pdf_data(self, doc: fitz.Document, lines: List[str], images: List[Tuple], fin_number: str) -> Dict:
        """Extract data from demographic format PDF using pattern matching."""
        # Extract data using demographic format
        
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
        
        # Extract nationality
        for line in lines:
            if line.strip() in ["ኢትዮጵያዊ", "ኢትዮጵያ"]:
                extracted["nationality_am"] = line.strip()
                extracted["nationality_en"] = "Ethiopian"
                break
        
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

    def extract_pdf_data(self, pdf_input, fin_number: str, pdf_format: str = 'auto') -> Dict:
        """Extract data from PDF file or stream with automatic format detection and fallback."""
        # Handle both file path and BytesIO input
        if isinstance(pdf_input, str):
            doc = fitz.open(pdf_input)
        else:
            doc = fitz.open(stream=pdf_input, filetype="pdf")
            
        try:
            page = doc[0]
            text = page.get_text()
            images = page.get_images(full=True)
            lines = [line.strip() for line in text.strip().split('\n') if line.strip()]

            extracted_data = {}
            used_format = None
            
            # Try formats in order: default first (fits official layout), then residential_sheger, then demographic
            formats_to_try = ['default', 'residential_sheger', 'demographic_format']
            
            for format_type in formats_to_try:
                try:
                    if format_type == 'default':
                        extracted_data = self._extract_default_pdf_data(doc, lines, images, fin_number)
                    elif format_type == 'residential_sheger':
                        extracted_data = self._extract_residential_sheger_pdf_data(doc, lines, images, fin_number)
                    elif format_type == 'demographic_format':
                        extracted_data = self._extract_demographic_format_pdf_data(doc, lines, images, fin_number)
                    
                    # Check if extraction was successful by validating key fields
                    # For residential_sheger, accept FCN with at least one name present (EN or AM)
                    if format_type == 'residential_sheger':
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
            if used_format == 'residential_sheger':
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

    def generate_id_card(self, data: Dict, city_option: str = 'default', remove_white: bool = False, remove_black: bool = False, generate_mini_id: bool = False, generate_old_id: bool = False) -> Dict[str, str]:
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
                address_positions = self.config.ADDRESS_POSITIONS.get(city_option, self.config.ADDRESS_POSITIONS['default'])
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
            
            if data.get('qr_path') and os.path.exists(os.path.join(self.config.STATIC_FOLDER, data['qr_path'].replace('static/', ''))):
                # Use the extracted QR from PDF
                qr_path = os.path.join(self.config.STATIC_FOLDER, data['qr_path'].replace('static/', ''))
                print(f"Using extracted QR from PDF: {qr_path}")
            else:
                # Generate QR data if not available
                qr_bytes = self.generate_qr_code(data, include_nationality=False)
                qr_img = Image.open(BytesIO(qr_bytes)).convert("RGBA")
                qr_img.save(qr_path)
                print(f"Generated QR data and saved to: {qr_path}")
            
            # Preload and process photo once per size (optimized)
            photo_large = process_photo(photo_path, self.config.PHOTO_SIZES['large'], remove_white, remove_black) if os.path.exists(photo_path) else None
            photo_small = process_photo(photo_path, self.config.PHOTO_SIZES['small'], remove_white, remove_black) if os.path.exists(photo_path) else None
            photo_reverse_large = process_photo(photo_path, self.config.PHOTO_SIZES['reverse_large'], remove_white, remove_black) if os.path.exists(photo_path) else None
            photo_reverse_small = process_photo(photo_path, self.config.PHOTO_SIZES['reverse_small'], remove_white, remove_black) if os.path.exists(photo_path) else None

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
                        if any(c.isdigit() for c in content):
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
                font_am = ImageFont.truetype(self.config.AMHARIC_FONT_PATH, 48)
                font_en = ImageFont.truetype(self.config.ENGLISH_FONT_PATH, 50)
                for key, pos in used_address_positions_front.items():
                    content = data.get(key, '')
                    font = font_am if key.endswith('_am') else font_en
                    max_width = self.config.TEXT_MAX_WIDTH['front'].get(key, None)
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
                        if any(c.isdigit() for c in content):
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
                font_am = ImageFont.truetype(self.config.AMHARIC_FONT_PATH, 34)
                font_en = ImageFont.truetype(self.config.ENGLISH_FONT_PATH, 34)
                for key, pos in address_positions['reverse'].items():
                    content = data.get(key, '')
                    font = font_am if key.endswith('_am') else font_en
                    max_width = self.config.TEXT_MAX_WIDTH['reverse'].get(key, None)
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
            if generate_old_id:
                # Only generate old ID cards (4 cards)
                print("Generating ONLY old ID cards...")
                old_files = self._generate_old_id_cards(data, remove_white, remove_black)
                old_files['city_option'] = city_option
                return old_files
            elif generate_mini_id:
                # Only generate mini ID cards with default reverse (4 cards)
                print("Generating ONLY mini ID cards with default reverse...")
                
                # Generate mini front cards
                mini_files = self._generate_mini_id_cards(data, remove_white, remove_black)
                
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

                return all_files
        except Exception as e:
            print(f"Error generating ID card: {str(e)}")
            raise 

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
                
                # Extract address positions from JSON fields
                address_front = {}
                for field in mini_json.get('fields', []):
                    key = field.get('key')
                    if key in ['region_am', 'region_en', 'subcity_am', 'subcity_en', 'woreda_am', 'woreda_en']:
                        address_front[key] = field.get('position', [0, 0])
                
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

    def _generate_mini_id_cards(self, data: Dict, remove_white: bool = False, remove_black: bool = False) -> Dict[str, str]:
        """Render mini front cards using mini template but export at normal size."""
        try:
            name = (data.get('name_en') or 'ID').replace(' ', '_')
            normal_w, normal_h = Image.open(self.config.TEMPLATE_IMG).size
            # Prepare mini layout scaled up to normal canvas
            base_positions = self.config.ADDRESS_POSITIONS.get('default', {})
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
            src_photo = process_photo(photo_path, tuple(photo_conf['size']), remove_white, remove_black) if os.path.exists(photo_path) else None
            src_photo_small = process_photo(photo_path, self.config.PHOTO_SIZES['small'], remove_white, remove_black) if os.path.exists(photo_path) else None
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
                font_am = ImageFont.truetype(self.config.AMHARIC_FONT_PATH, 48)
                font_en = ImageFont.truetype(self.config.ENGLISH_FONT_PATH, 50)
                for key, pos in used_address_positions_front.items():
                    content = data.get(key, '')
                    font = font_am if key.endswith('_am') else font_en
                    max_width = self.config.TEXT_MAX_WIDTH['front'].get(key, None)
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
                    barcode_img = barcode_img.resize((487, 87))
                    canvas.paste(barcode_img, (857, 930))
                    font = ImageFont.truetype(self.config.ENGLISH_FONT_PATH, 42)
                    text_width = draw.textlength(data['fcn_formatted'], font=font)
                    center_x = 850 + (500 - text_width) // 2
                    draw.text((center_x, 878), data['fcn_formatted'], font=font, fill=(0, 0, 0))
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

    def _generate_old_id_cards(self, data: Dict, remove_white: bool = False, remove_black: bool = False) -> Dict[str, str]:
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

            def render_old_front(color: bool) -> Image.Image:
                canvas = Image.open(front_template).convert('RGBA')
                draw = ImageDraw.Draw(canvas)
                
                # Draw text fields from old front template
                for field in old_front_layout.get('fields', []):
                    key = field.get('key')
                    if not key or key.startswith('label_'):
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
                
                # Draw address fields from template configuration
                font_am = ImageFont.truetype(self.config.AMHARIC_FONT_PATH, 32)
                font_en = ImageFont.truetype(self.config.ENGLISH_FONT_PATH, 28)
                
                # Add address information if available and defined in template
                address_fields = ['region_am', 'region_en', 'subcity_am', 'subcity_en', 'woreda_am', 'woreda_en']
                for field in old_front_layout.get('fields', []):
                    key = field.get('key')
                    if key in address_fields and key in data:
                        content = data.get(key, '')
                        if content:
                            pos = tuple(field.get('position', [0, 0]))
                            font = font_am if key.endswith('_am') else font_en
                            draw.text(pos, content, font=font, fill=(0, 0, 0))
                
                # Large Photo
                if os.path.exists(photo_path):
                    src_photo = process_photo(photo_path, front_photo_size, remove_white, remove_black)
                    if src_photo:
                        img = src_photo if color else src_photo.convert('LA').convert('RGBA')
                        canvas.paste(img, front_photo_pos, img)
                
                # Small Photo (for old ID front)
                if os.path.exists(photo_path):
                    small_photo_size = (199, 205)  # Small photo size
                    small_photo_pos = (1493, 860)  # Small photo position
                    src_photo_small = process_photo(photo_path, small_photo_size, remove_white, remove_black)
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
                            font = ImageFont.truetype(self.config.ENGLISH_FONT_PATH, 24)
                            text_width = draw.textlength(fcn_text, font=font)
                            center_x = barcode_pos[0] + (barcode_size[0] - text_width) // 2
                            draw.text((center_x, barcode_pos[1] - 30), fcn_text, font=font, fill=(0, 0, 0))
                
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
                    src_photo = process_photo(photo_path, reverse_photo_size, remove_white, remove_black)
                    if src_photo:
                        img = src_photo if color else src_photo.convert('LA').convert('RGBA')
                        data_layer.paste(img, reverse_photo_pos, img)
                
                # Small Photo (same as default reverse)
                if os.path.exists(photo_path):
                    small_photo_size = (105, 115)  # Same as default reverse_small
                    # Position for small photo to appear on RIGHT after flip (mirror of default reverse)
                    small_photo_pos = (710, 360)  # Mirrored position for right side after flip
                    src_photo_small = process_photo(photo_path, small_photo_size, remove_white, remove_black)
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
                        data_layer.paste(barcode_img, (465, 425))  # Mirrored position for right side after flip
                        
                        # Add FCN text above barcode (same as default reverse)
                        fcn_text = data.get('fcn_formatted', '')
                        if fcn_text:
                            font = ImageFont.truetype(self.config.ENGLISH_FONT_PATH, 18)
                            text_width = draw.textlength(fcn_text, font=font)
                            # Position for FCN text to appear on RIGHT after flip
                            center_x = 428 + (287 - text_width) // 2
                            draw.text((center_x, 399), fcn_text, font=font, fill=(0, 0, 0))
                
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