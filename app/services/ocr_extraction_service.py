"""
OCR Extraction Service for Ethiopian Digital ID Cards
Extracts data from front and back ID card images
"""

import cv2
import numpy as np
from PIL import Image
import pytesseract
import re
from typing import Dict, Optional, Tuple
import os

class OCRExtractionService:
    def __init__(self):
        """Initialize OCR service"""
        # Configure Tesseract for Amharic and English
        self.tesseract_config = '--oem 3 --psm 6'
        
    def preprocess_image(self, image_path: str) -> np.ndarray:
        """Preprocess image for better OCR results"""
        # Read image
        img = cv2.imread(image_path)
        
        # Convert to grayscale
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        
        # Apply thresholding
        _, thresh = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
        
        # Denoise
        denoised = cv2.fastNlMeansDenoising(thresh, None, 10, 7, 21)
        
        return denoised
    
    def extract_photo_from_front(self, image_path: str, output_path: str) -> Optional[str]:
        """Extract profile photo from front ID card"""
        try:
            img = cv2.imread(image_path)
            height, width = img.shape[:2]
            
            # Photo is typically in the center-left area
            # Adjust these coordinates based on your ID card layout
            photo_x = int(width * 0.15)
            photo_y = int(height * 0.15)
            photo_w = int(width * 0.35)
            photo_h = int(height * 0.45)
            
            # Extract photo region
            photo = img[photo_y:photo_y+photo_h, photo_x:photo_x+photo_w]
            
            # Save extracted photo
            cv2.imwrite(output_path, photo)
            return output_path
        except Exception as e:
            print(f"Error extracting photo: {e}")
            return None
    
    def extract_text_regions(self, image_path: str) -> Dict:
        """Extract text from specific regions of Ethiopian Digital ID Card"""
        try:
            img = cv2.imread(image_path)
            if img is None:
                print(f"❌ Could not read image: {image_path}")
                return {}
            
            height, width = img.shape[:2]
            print(f"📐 Image dimensions: {width}x{height}")
            
            # Define regions based on EXACT pixel coordinates from Ethiopian Digital ID Card
            # Coordinates based on 591x1280px reference image from Adobe
            # NAME_AM: X:107, Y:660, W:379, H:28 → (107,660)-(486,688)
            # NAME_EN: X:103, Y:683, W:379, H:26 → (103,683)-(482,709)
            # DOB_ETHIOPIAN: X:105, Y:734, W:104, H:23 → (105,734)-(209,757)
            # DOB_GREGORIAN: X:213, Y:734, W:147, H:22 → (213,734)-(360,756)
            # SEX_AM: X:108, Y:773, W:45, H:20 → (108,773)-(153,793)
            # SEX_EN: X:162, Y:769, W:91, H:24 → (162,769)-(253,793)
            # EXPIRY_ETHIOPIAN: X:105, Y:820, W:101, H:18 → (105,820)-(206,838)
            # EXPIRY_GREGORIAN: X:210, Y:819, W:155, H:23 → (210,819)-(365,842)
            # FAN_NUMBER: X:180, Y:862, W:212, H:17 → (180,862)-(392,879)
            
            # Reference dimensions (from Adobe measurements)
            ref_width = 591
            ref_height = 1280
            
            # Calculate percentage-based regions (will scale to actual image size)
            # EXACT coordinates from Adobe measurements
            regions = {
                'full_name_am': (85/ref_width, 664/ref_height, 490/ref_width, 686/ref_height),                    # Full name Amharic (85,664)-(490,686) - Extended left and right
                'full_name_en': (103/ref_width, 683/ref_height, 482/ref_width, 709/ref_height),                    # Full name English (103,683)-(482,709)
                'dob_ethiopian': (105/ref_width, 734/ref_height, 209/ref_width, 757/ref_height),                   # DOB Ethiopian (105,734)-(209,757)
                'dob_gregorian': (213/ref_width, 734/ref_height, 360/ref_width, 756/ref_height),                   # DOB Gregorian (213,734)-(360,756)
                'sex_am': (108/ref_width, 773/ref_height, 153/ref_width, 793/ref_height),                          # Sex Amharic (108,773)-(153,793)
                'sex_en': (162/ref_width, 769/ref_height, 253/ref_width, 793/ref_height),                          # Sex English (162,769)-(253,793)
                'expiry_ethiopian': (105/ref_width, 820/ref_height, 206/ref_width, 838/ref_height),                # Expiry Ethiopian (105,820)-(206,838)
                'expiry_gregorian': (210/ref_width, 819/ref_height, 365/ref_width, 842/ref_height),                # Expiry Gregorian (210,819)-(365,842)
                'fan_number': (180/ref_width, 862/ref_height, 392/ref_width, 879/ref_height),                      # FAN Number (180,862)-(392,879)
                'issue_gregorian': (892/900, 576/1650, (892+45)/900, (576+278)/1650),                              # Issue date Gregorian VERTICAL - TODO: get exact coordinates
                'issue_ethiopian': (895/900, 861/1650, (895+45)/900, (861+231)/1650),                              # Issue date Ethiopian VERTICAL - TODO: get exact coordinates
            }
            
            print(f"📏 Using reference dimensions: {ref_width}x{ref_height}, actual: {width}x{height}")
            
            extracted_regions = {}
            
            for region_name, (x1, y1, x2, y2) in regions.items():
                # Convert percentages to pixels
                x1_px = int(x1 * width)
                y1_px = int(y1 * height)
                x2_px = int(x2 * width)
                y2_px = int(y2 * height)
                
                # Add padding for name fields to avoid cutting off text
                if 'full_name' in region_name:
                    padding_x = 5  # Add 5 pixels padding on left and right
                    padding_y = 2  # Add 2 pixels padding on top and bottom
                    x1_px = max(0, x1_px - padding_x)
                    y1_px = max(0, y1_px - padding_y)
                    x2_px = min(width, x2_px + padding_x)
                    y2_px = min(height, y2_px + padding_y)
                
                # Extract region
                region_img = img[y1_px:y2_px, x1_px:x2_px]
                
                # Convert to grayscale
                gray = cv2.cvtColor(region_img, cv2.COLOR_BGR2GRAY)
                
                # Resize for better OCR - use higher scale for small text
                scale = 3.0  # Increased scale for better OCR accuracy
                gray = cv2.resize(gray, None, fx=scale, fy=scale, interpolation=cv2.INTER_CUBIC)
                
                # Apply preprocessing based on region type
                if 'fan_number' in region_name:
                    # For FAN number, use aggressive preprocessing
                    clahe = cv2.createCLAHE(clipLimit=3.0, tileGridSize=(8,8))
                    enhanced = clahe.apply(gray)
                    _, thresh = cv2.threshold(enhanced, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
                    config = '--oem 3 --psm 7 -c tessedit_char_whitelist=0123456789'
                    text = pytesseract.image_to_string(thresh, lang='eng', config=config)
                elif 'issue_' in region_name:
                    # For vertical text - rotate 90 degrees counterclockwise
                    rotated = cv2.rotate(gray, cv2.ROTATE_90_COUNTERCLOCKWISE)
                    clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8,8))
                    enhanced = clahe.apply(rotated)
                    _, thresh = cv2.threshold(enhanced, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
                    config = '--oem 3 --psm 6'
                    text = pytesseract.image_to_string(thresh, lang='eng+amh', config=config)
                elif 'dob_' in region_name or 'expiry_' in region_name:
                    # For date fields - use more aggressive preprocessing
                    clahe = cv2.createCLAHE(clipLimit=3.0, tileGridSize=(8,8))
                    enhanced = clahe.apply(gray)
                    _, thresh = cv2.threshold(enhanced, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
                    config = '--oem 3 --psm 7'  # Single line
                    # Try both with and without Amharic
                    if 'ethiopian' in region_name or '_am' in region_name:
                        text = pytesseract.image_to_string(thresh, lang='amh+eng', config=config)
                    else:
                        text = pytesseract.image_to_string(thresh, lang='eng', config=config)
                elif 'sex_' in region_name:
                    # For sex field - very short text
                    clahe = cv2.createCLAHE(clipLimit=3.0, tileGridSize=(8,8))
                    enhanced = clahe.apply(gray)
                    _, thresh = cv2.threshold(enhanced, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
                    config = '--oem 3 --psm 8'  # Single word
                    if '_am' in region_name:
                        text = pytesseract.image_to_string(thresh, lang='amh', config=config)
                    else:
                        text = pytesseract.image_to_string(thresh, lang='eng', config=config)
                    text = pytesseract.image_to_string(thresh, lang='eng+amh', config=config)
                else:
                    # For text fields (names)
                    bilateral = cv2.bilateralFilter(gray, 9, 75, 75)
                    _, thresh = cv2.threshold(bilateral, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
                    
                    # Use different config for Amharic vs English names
                    if '_am' in region_name or 'full_name_am' in region_name:
                        # Amharic names - prioritize Amharic language
                        config = '--oem 3 --psm 7'  # Single line
                        text = pytesseract.image_to_string(thresh, lang='amh+eng', config=config)
                    else:
                        # English names
                        config = '--oem 3 --psm 7'  # Single line
                        text = pytesseract.image_to_string(thresh, lang='eng+amh', config=config)
                
                extracted_regions[region_name] = text.strip()
                print(f"✓ {region_name}: {text.strip()[:80]}")
            
            return extracted_regions
            
        except Exception as e:
            print(f"❌ Error extracting regions: {e}")
            import traceback
            traceback.print_exc()
            return {}
    
    def extract_text_from_image(self, image_path: str, lang: str = 'eng+amh') -> str:
        """Extract text from image using OCR with improved preprocessing for ID cards"""
        try:
            # Read image
            img = cv2.imread(image_path)
            if img is None:
                print(f"❌ Could not read image: {image_path}")
                return ""
            
            # Convert to grayscale
            gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
            
            # Resize image for better OCR (2x is optimal for most ID cards)
            scale_factor = 2.0
            width = int(gray.shape[1] * scale_factor)
            height = int(gray.shape[0] * scale_factor)
            gray = cv2.resize(gray, (width, height), interpolation=cv2.INTER_CUBIC)
            
            # Apply multiple preprocessing techniques and try OCR on each
            texts = []
            
            # Method 1: Bilateral filter + OTSU (good for noisy images)
            bilateral = cv2.bilateralFilter(gray, 9, 75, 75)
            _, thresh1 = cv2.threshold(bilateral, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
            # Try with different PSM modes
            text1a = pytesseract.image_to_string(thresh1, lang=lang, config='--oem 3 --psm 3')  # Fully automatic
            text1b = pytesseract.image_to_string(thresh1, lang=lang, config='--oem 3 --psm 6')  # Uniform block
            text1c = pytesseract.image_to_string(thresh1, lang=lang, config='--oem 3 --psm 11') # Sparse text
            texts.extend([text1a, text1b, text1c])
            print(f"📝 Method 1 (Bilateral+OTSU): PSM3={len(text1a)}, PSM6={len(text1b)}, PSM11={len(text1c)} chars")
            
            # Method 2: Contrast enhancement + threshold
            clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8,8))
            enhanced = clahe.apply(gray)
            _, thresh2 = cv2.threshold(enhanced, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
            text2 = pytesseract.image_to_string(thresh2, lang=lang, config='--oem 3 --psm 6')
            texts.append(text2)
            print(f"📝 Method 2 (CLAHE): {len(text2)} chars")
            
            # Method 3: Denoise + threshold (good for scanned documents)
            denoised = cv2.fastNlMeansDenoising(gray, None, h=10, templateWindowSize=7, searchWindowSize=21)
            _, thresh3 = cv2.threshold(denoised, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
            text3 = pytesseract.image_to_string(thresh3, lang=lang, config='--oem 3 --psm 6')
            texts.append(text3)
            print(f"📝 Method 3 (Denoise): {len(text3)} chars")
            
            # Method 4: Simple threshold with different values
            _, thresh4a = cv2.threshold(gray, 127, 255, cv2.THRESH_BINARY)
            _, thresh4b = cv2.threshold(gray, 150, 255, cv2.THRESH_BINARY)
            text4a = pytesseract.image_to_string(thresh4a, lang=lang, config='--oem 3 --psm 6')
            text4b = pytesseract.image_to_string(thresh4b, lang=lang, config='--oem 3 --psm 6')
            texts.extend([text4a, text4b])
            print(f"📝 Method 4 (Fixed thresh): 127={len(text4a)}, 150={len(text4b)} chars")
            
            # Filter out texts that are mostly garbage (high ratio of special chars)
            def is_valid_text(text):
                if len(text) < 20:
                    return False
                # Count alphanumeric vs special characters
                alnum_count = sum(c.isalnum() or c.isspace() for c in text)
                total_count = len(text)
                ratio = alnum_count / total_count if total_count > 0 else 0
                return ratio > 0.3  # At least 30% should be alphanumeric or spaces
            
            valid_texts = [t for t in texts if is_valid_text(t)]
            
            if not valid_texts:
                print("⚠️ No valid text extracted from any method")
                # Return the longest text anyway
                combined_text = max(texts, key=len) if texts else ""
            else:
                # Use the longest valid text
                combined_text = max(valid_texts, key=len)
            
            print(f"✓ Best extraction: {len(combined_text)} characters from {image_path}")
            if len(combined_text) < 50:
                print(f"⚠️ Warning: Very little text extracted. Sample: {combined_text[:200]}")
            else:
                # Show first 300 chars to see actual content
                print(f"📄 Sample text: {combined_text[:300]}...")
            
            return combined_text.strip()
            
        except Exception as e:
            print(f"❌ Error extracting text: {e}")
            import traceback
            traceback.print_exc()
            return ""

    
    def parse_front_card_data(self, text: str, image_path: str = None) -> Dict:
        """Parse extracted text from front ID card with improved pattern matching"""
        data = {
            'full_name_en': '',
            'full_name_am': '',
            'date_of_birth': '',
            'sex': '',
            'date_of_expiry': '',
            'date_of_issue': '',
            'fan': '',  # FAN not FIN
            'barcode': ''  # Will be generated from FAN, not extracted from image
        }
        
        # Try region-based extraction first if image path provided
        if image_path:
            print("🎯 Attempting region-based extraction...")
            regions = self.extract_text_regions(image_path)
            
            if regions:
                # Extract full names from separate Amharic and English regions
                if 'full_name_am' in regions and regions['full_name_am']:
                    name_am = regions['full_name_am'].strip()
                    # Clean Amharic name - remove non-Amharic characters
                    name_am_clean = ''.join(c for c in name_am if '\u1200' <= c <= '\u137F' or c.isspace())
                    name_am_clean = ' '.join(name_am_clean.split())  # Normalize spaces
                    if len(name_am_clean) >= 3:
                        data['full_name_am'] = name_am_clean
                        print(f"✓ Extracted name (AM): {name_am_clean}")
                
                if 'full_name_en' in regions and regions['full_name_en']:
                    name_en = regions['full_name_en'].strip()
                    # Clean English name - remove non-ASCII characters
                    name_en_clean = ''.join(c for c in name_en if c.isascii() and (c.isalpha() or c.isspace()))
                    name_en_clean = ' '.join(name_en_clean.split())  # Normalize spaces
                    if len(name_en_clean) >= 3:
                        data['full_name_en'] = name_en_clean
                        print(f"✓ Extracted name (EN): {name_en_clean}")
                
                # Legacy fallback for old 'full_name' region
                if 'full_name' in regions and regions['full_name']:
                    name_text = regions['full_name']
                    lines = [l.strip() for l in name_text.split('\n') if l.strip()]
                    
                    # In Ethiopian ID, Amharic name comes first, then English
                    # DOB may also be in this region
                    for i, line in enumerate(lines):
                        # Skip labels - be more aggressive
                        if 'full name' in line.lower() or 'ሙሉ ስም' in line.lower():
                            continue
                        if 'date of birth' in line.lower() or 'የትውልድ' in line:
                            continue
                        
                        # Check if line contains a date (DOB might be in this region)
                        if re.search(r'\d{2}/\d{2}/\d{4}', line):
                            # Extract DOB if not already found
                            if not data['date_of_birth']:
                                gregorian_match = re.search(r'(\d{2}/\d{2}/\d{4})', line)
                                ethiopian_match = re.search(r'(\d{4}/[A-Za-z]{3}/\d{2})', line)
                                if gregorian_match:
                                    data['date_of_birth_en'] = gregorian_match.group(1)
                                    data['date_of_birth'] = gregorian_match.group(1)
                                    print(f"✓ Extracted DOB (Gregorian) from name region: {data['date_of_birth_en']}")
                                if ethiopian_match:
                                    data['date_of_birth_am'] = ethiopian_match.group(1)
                                    print(f"✓ Extracted DOB (Ethiopian) from name region: {data['date_of_birth_am']}")
                            continue
                        
                        # Skip lines that look like garbled labels (lots of special chars)
                        special_char_count = sum(1 for c in line if not c.isalnum() and not c.isspace())
                        if special_char_count > len(line) * 0.3:  # More than 30% special chars
                            continue
                        
                        # Skip very short lines
                        if len(line) < 5:
                            continue
                        
                        # Check if line contains Amharic characters
                        has_amharic = any('\u1200' <= c <= '\u137F' for c in line)
                        has_english = any(c.isascii() and c.isalpha() for c in line)
                        
                        # Count Amharic vs English characters
                        amharic_count = sum(1 for c in line if '\u1200' <= c <= '\u137F')
                        english_count = sum(1 for c in line if c.isascii() and c.isalpha())
                        
                        if has_amharic and amharic_count >= 3 and not data['full_name_am']:
                            # This is Amharic name - clean it up
                            # Remove any English/Latin characters mixed in
                            cleaned = ''.join(c for c in line if '\u1200' <= c <= '\u137F' or c.isspace())
                            cleaned = ' '.join(cleaned.split())  # Normalize spaces
                            if len(cleaned) >= 5:
                                data['full_name_am'] = cleaned
                                print(f"✓ Extracted name (AM): {cleaned}")
                        elif has_english and english_count >= 5 and not has_amharic and not data['full_name_en']:
                            # This is English name - clean it up
                            # Remove any non-ASCII characters
                            cleaned = ''.join(c for c in line if c.isascii() and (c.isalpha() or c.isspace()))
                            cleaned = ' '.join(cleaned.split())  # Normalize spaces
                            if len(cleaned) >= 5:
                                data['full_name_en'] = cleaned
                                print(f"✓ Extracted name (EN): {cleaned}")
                
                # Extract DOB from separate Gregorian and Ethiopian regions
                if 'dob_gregorian' in regions and regions['dob_gregorian']:
                    dob_greg = regions['dob_gregorian'].strip()
                    # Look for date patterns - YYYY/Mon/DD format
                    gregorian_match = re.search(r'(\d{4}/[A-Za-z]{3}/\d{2})', dob_greg)
                    if gregorian_match:
                        data['date_of_birth_en'] = gregorian_match.group(1)
                        if not data['date_of_birth']:
                            data['date_of_birth'] = gregorian_match.group(1)
                        print(f"✓ Extracted DOB (Gregorian): {data['date_of_birth_en']}")
                    # Try DD/MM/YYYY format
                    if not gregorian_match:
                        dd_match = re.search(r'(\d{2}/\d{2}/\d{4})', dob_greg)
                        if dd_match:
                            data['date_of_birth_en'] = dd_match.group(1)
                            if not data['date_of_birth']:
                                data['date_of_birth'] = dd_match.group(1)
                            print(f"✓ Extracted DOB (DD/MM/YYYY): {data['date_of_birth_en']}")
                
                if 'dob_ethiopian' in regions and regions['dob_ethiopian']:
                    dob_eth = regions['dob_ethiopian'].strip()
                    # Look for Ethiopian date pattern - DD/MM/YYYY format
                    ethiopian_match = re.search(r'(\d{2}/\d{2}/\d{4})', dob_eth)
                    if ethiopian_match:
                        data['date_of_birth_am'] = ethiopian_match.group(1)
                        print(f"✓ Extracted DOB (Ethiopian): {data['date_of_birth_am']}")
                
                # Legacy fallback for old 'date_of_birth' region
                if 'date_of_birth' in regions and regions['date_of_birth']:
                    dob_text = regions['date_of_birth']
                    
                    # Check for sex in this region
                    if not data['sex']:
                        if 'female' in dob_text.lower() or 'ሴት' in dob_text:
                            data['sex'] = 'Female'
                            data['sex_en'] = 'Female'
                            data['sex_am'] = 'ሴት'
                            print(f"✓ Extracted sex from DOB region: Female")
                        elif 'male' in dob_text.lower() or 'ወንድ' in dob_text:
                            data['sex'] = 'Male'
                            data['sex_en'] = 'Male'
                            data['sex_am'] = 'ወንድ'
                            print(f"✓ Extracted sex from DOB region: Male")
                    
                    # Check for expiry date in this region
                    if not data['date_of_expiry']:
                        if 'expiry' in dob_text.lower() or 'የሚያበቃበት' in dob_text:
                            # Look for dates after the expiry label
                            gregorian_matches = re.findall(r'(\d{4}/\d{2}/\d{2})', dob_text)
                            ethiopian_matches = re.findall(r'(\d{4}/[A-Za-z]{3}/\d{2})', dob_text)
                            if gregorian_matches:
                                data['date_of_expiry_en'] = gregorian_matches[0]
                                data['date_of_expiry'] = gregorian_matches[0]
                                print(f"✓ Extracted expiry (Gregorian) from DOB region: {data['date_of_expiry_en']}")
                            if ethiopian_matches:
                                data['date_of_expiry_am'] = ethiopian_matches[0]
                                print(f"✓ Extracted expiry (Ethiopian) from DOB region: {data['date_of_expiry_am']}")
                    
                    # Look for date patterns - both formats may be present
                    if not data['date_of_birth']:
                        gregorian_matches = re.findall(r'(\d{2}/\d{2}/\d{4})', dob_text)  # DD/MM/YYYY
                        ethiopian_matches = re.findall(r'(\d{4}/[A-Za-z]{3}/\d{2})', dob_text)  # YYYY/Mon/DD

                        if gregorian_matches:
                            data['date_of_birth_en'] = gregorian_matches[0]
                            if not data['date_of_birth']:
                                data['date_of_birth'] = gregorian_matches[0]
                            print(f"✓ Extracted DOB (Gregorian): {data['date_of_birth_en']}")

                        if ethiopian_matches:
                            data['date_of_birth_am'] = ethiopian_matches[0]
                            print(f"✓ Extracted DOB (Ethiopian): {data['date_of_birth_am']}")
                
                # Extract sex from separate Amharic and English regions
                if 'sex_am' in regions and regions['sex_am']:
                    sex_am = regions['sex_am'].strip()
                    if 'ወንድ' in sex_am or 'ወ/ድ' in sex_am:
                        data['sex'] = 'Male'
                        data['sex_am'] = 'ወንድ'
                        print(f"✓ Extracted sex (AM): ወንድ")
                    elif 'ሴት' in sex_am:
                        data['sex'] = 'Female'
                        data['sex_am'] = 'ሴት'
                        print(f"✓ Extracted sex (AM): ሴት")
                
                if 'sex_en' in regions and regions['sex_en']:
                    sex_en = regions['sex_en'].strip().lower()
                    if 'male' in sex_en and 'female' not in sex_en:
                        data['sex'] = 'Male'
                        data['sex_en'] = 'Male'
                        print(f"✓ Extracted sex (EN): Male")
                    elif 'female' in sex_en:
                        data['sex'] = 'Female'
                        data['sex_en'] = 'Female'
                        print(f"✓ Extracted sex (EN): Female")
                
                # Legacy fallback for old 'sex' region
                if 'sex' in regions and regions['sex']:
                    sex_text = regions['sex']
                    
                    # Check for FAN number in sex region
                    if not data['fan']:
                        fan_match = re.search(r'(\d{15,17})', sex_text.replace(' ', ''))
                        if fan_match:
                            fan_num = fan_match.group(1)
                            if len(fan_num) >= 15:
                                data['fan'] = fan_num[:16] if len(fan_num) >= 16 else fan_num[:15]
                                print(f"✓ Extracted FAN from sex region: {data['fan']}")
                    
                    # Clean up the text - handle bilingual format "ወንድ | Male"
                    sex_text_clean = sex_text.replace('|', ' ').replace('Ove', 'Male').replace('Oryx', '').strip().lower()
                    
                    # Check for male indicators
                    if not data['sex']:
                        if 'male' in sex_text_clean and 'female' not in sex_text_clean:
                            data['sex'] = 'Male'
                            data['sex_en'] = 'Male'
                            print(f"✓ Extracted sex (EN): Male")
                        elif 'female' in sex_text_clean:
                            data['sex'] = 'Female'
                            data['sex_en'] = 'Female'
                            print(f"✓ Extracted sex (EN): Female")
                        # Check Amharic
                        elif 'ወንድ' in sex_text or 'ወ/ድ' in sex_text:
                            data['sex'] = 'Male'
                            data['sex_en'] = data.get('sex_en') or 'Male'
                            data['sex_am'] = 'ወንድ'
                            print(f"✓ Extracted sex (AM): ወንድ")
                        elif 'ሴት' in sex_text:
                            data['sex'] = 'Female'
                            data['sex_en'] = data.get('sex_en') or 'Female'
                            data['sex_am'] = 'ሴት'
                            print(f"✓ Extracted sex (AM): ሴት")
                
                # Extract expiry date from separate Gregorian and Ethiopian regions
                if 'expiry_gregorian' in regions and regions['expiry_gregorian']:
                    expiry_greg = regions['expiry_gregorian'].strip()
                    # Look for date patterns - YYYY/Mon/DD format
                    gregorian_match = re.search(r'(\d{4}/[A-Za-z]{3}/\d{2})', expiry_greg)
                    if gregorian_match:
                        data['date_of_expiry_en'] = gregorian_match.group(1)
                        if not data['date_of_expiry']:
                            data['date_of_expiry'] = gregorian_match.group(1)
                        print(f"✓ Extracted expiry (Gregorian): {data['date_of_expiry_en']}")
                    # Try YYYY/MM/DD format
                    if not gregorian_match:
                        yyyy_match = re.search(r'(\d{4}/\d{2}/\d{2})', expiry_greg)
                        if yyyy_match:
                            data['date_of_expiry_en'] = yyyy_match.group(1)
                            if not data['date_of_expiry']:
                                data['date_of_expiry'] = yyyy_match.group(1)
                            print(f"✓ Extracted expiry (YYYY/MM/DD): {data['date_of_expiry_en']}")
                
                if 'expiry_ethiopian' in regions and regions['expiry_ethiopian']:
                    expiry_eth = regions['expiry_ethiopian'].strip()
                    # Look for Ethiopian date pattern - YYYY/MM/DD format
                    ethiopian_match = re.search(r'(\d{4}/\d{2}/\d{2})', expiry_eth)
                    if ethiopian_match:
                        data['date_of_expiry_am'] = ethiopian_match.group(1)
                        print(f"✓ Extracted expiry (Ethiopian): {data['date_of_expiry_am']}")
                
                # Legacy fallback for old 'date_of_expiry' region
                if 'date_of_expiry' in regions and regions['date_of_expiry']:
                    expiry_text = regions['date_of_expiry']
                    
                    # Check for FAN number in expiry region
                    if not data['fan']:
                        fan_match = re.search(r'(\d{15,17})', expiry_text.replace(' ', '').replace('|', '').replace('[', '').replace(']', ''))
                        if fan_match:
                            fan_num = fan_match.group(1)
                            if len(fan_num) >= 15:
                                data['fan'] = fan_num[:16] if len(fan_num) >= 16 else fan_num[:15]
                                print(f"✓ Extracted FAN from expiry region: {data['fan']}")
                    
                    # Example from card: "2026/06/01 | 2034/Feb/08"
                    gregorian_matches = re.findall(r'(\d{4}/\d{2}/\d{2})', expiry_text)  # YYYY/MM/DD
                    ethiopian_matches = re.findall(r'(\d{4}/[A-Za-z]{3}/\d{2})', expiry_text)  # YYYY/Mon/DD

                    if gregorian_matches and not data['date_of_expiry']:
                        data['date_of_expiry_en'] = gregorian_matches[0]
                        if not data['date_of_expiry']:
                            data['date_of_expiry'] = gregorian_matches[0]
                        print(f"✓ Extracted expiry (Gregorian): {data['date_of_expiry_en']}")

                    # Handle 2‑digit year variants as Gregorian as well
                    if not gregorian_matches and not data['date_of_expiry']:
                        yy_matches = re.findall(r'(\d{2}/\d{2}/\d{2})', expiry_text)
                        if yy_matches:
                            data['date_of_expiry_en'] = yy_matches[0]
                            if not data['date_of_expiry']:
                                data['date_of_expiry'] = yy_matches[0]
                            print(f"✓ Extracted expiry (YY/MM/DD): {data['date_of_expiry_en']}")

                    if ethiopian_matches and not data['date_of_expiry_am']:
                        data['date_of_expiry_am'] = ethiopian_matches[0]
                        print(f"✓ Extracted expiry (Ethiopian): {data['date_of_expiry_am']}")
                
                # Extract FAN from region
                if 'fan_number' in regions and regions['fan_number']:
                    fan_text = regions['fan_number'].replace(' ', '').replace('-', '')
                    # Look for 15-17 digit number (FAN can be 15-16 digits)
                    fan_match = re.search(r'(\d{15,17})', fan_text)
                    if fan_match:
                        fan_num = fan_match.group(1)
                        # Take first 15-16 digits
                        if len(fan_num) >= 15 and not data['fan']:
                            data['fan'] = fan_num[:16] if len(fan_num) >= 16 else fan_num[:15]
                            data['barcode'] = data['fan']
                            print(f"✓ Extracted FAN: {data['fan']}")
                
                # Extract date of issue from separate Gregorian and Ethiopian regions (vertical text)
                if 'issue_gregorian' in regions and regions['issue_gregorian']:
                    issue_greg = regions['issue_gregorian'].strip()
                    print(f"🔍 Raw issue date (Gregorian): {issue_greg}")
                    
                    # Clean up OCR errors
                    issue_greg = issue_greg.replace('O', '0').replace('o', '0')
                    issue_greg = issue_greg.replace('l', '1').replace('I', '1')
                    issue_greg = issue_greg.replace('S', '5').replace('s', '5')
                    issue_greg = issue_greg.replace('B', '8')
                    
                    # Try multiple date patterns
                    date_patterns = [
                        r'(\d{4}[/\-]\d{2}[/\-]\d{2})',
                        r'(\d{2}[/\-]\d{2}[/\-]\d{4})',
                        r'(\d{4}[/\-][A-Za-z]{3}[/\-]\d{2})',
                        r'(\d{4}\s*/\s*\d{2}\s*/\s*\d{2})',
                    ]
                    
                    for pattern in date_patterns:
                        match = re.search(pattern, issue_greg)
                        if match:
                            extracted_date = re.sub(r'\s+', '', match.group(1)).replace('-', '/')
                            data['date_of_issue_en'] = extracted_date
                            if not data['date_of_issue']:
                                data['date_of_issue'] = extracted_date
                            print(f"✓ Extracted issue date (Gregorian): {data['date_of_issue_en']}")
                            break
                
                if 'issue_ethiopian' in regions and regions['issue_ethiopian']:
                    issue_eth = regions['issue_ethiopian'].strip()
                    print(f"🔍 Raw issue date (Ethiopian): {issue_eth}")
                    
                    # Look for Ethiopian date pattern
                    ethiopian_match = re.search(r'(\d{4}[/\-][A-Za-z]{3}[/\-]\d{2})', issue_eth)
                    if ethiopian_match:
                        extracted_eth = re.sub(r'\s+', '', ethiopian_match.group(1)).replace('-', '/')
                        data['date_of_issue_am'] = extracted_eth
                        print(f"✓ Extracted issue date (Ethiopian): {data['date_of_issue_am']}")
                
                # Legacy fallback for old 'date_of_issue' region
                if 'date_of_issue' in regions and regions['date_of_issue']:
                    issue_text = regions['date_of_issue']
                    print(f"🔍 Raw issue date text: {issue_text}")
                    
                    # Clean up the text - remove common OCR errors
                    issue_text = issue_text.replace('O', '0').replace('o', '0')  # O to 0
                    issue_text = issue_text.replace('l', '1').replace('I', '1')  # l/I to 1
                    issue_text = issue_text.replace('S', '5').replace('s', '5')  # S to 5
                    issue_text = issue_text.replace('B', '8')  # B to 8
                    
                    # Try multiple date patterns with more flexibility
                    date_patterns = [
                        r'(\d{4}[/\-]\d{2}[/\-]\d{2})',          # YYYY/MM/DD or YYYY-MM-DD
                        r'(\d{2}[/\-]\d{2}[/\-]\d{4})',          # DD/MM/YYYY or DD-MM-YYYY
                        r'(\d{4}[/\-][A-Za-z]{3}[/\-]\d{2})',    # YYYY/Mon/DD
                        r'(\d{2}[/\-][A-Za-z]{3}[/\-]\d{4})',    # DD/Mon/YYYY
                        r'(\d{4}\s*/\s*\d{2}\s*/\s*\d{2})',      # YYYY / MM / DD (with spaces)
                    ]
                    
                    # Find all dates in the text
                    all_dates = []
                    for pattern in date_patterns:
                        matches = re.findall(pattern, issue_text)
                        all_dates.extend(matches)
                    
                    if all_dates:
                        # Separate numeric Gregorian vs Ethiopian (month-name) forms
                        gregorian_candidates = [d for d in all_dates if re.search(r'\d{4}[/\-]\d{2}[/\-]\d{2}', d) or re.search(r'\d{2}[/\-]\d{2}[/\-]\d{4}', d)]
                        ethiopian_candidates = [d for d in all_dates if re.search(r'[A-Za-z]{3}', d)]

                        if gregorian_candidates:
                            extracted_date = re.sub(r'\s+', '', gregorian_candidates[0]).replace('-', '/')
                            data['date_of_issue_en'] = extracted_date
                            if not data['date_of_issue']:
                                data['date_of_issue'] = extracted_date
                            print(f"✓ Extracted issue date (Gregorian): {data['date_of_issue_en']}")

                        if ethiopian_candidates:
                            extracted_eth = re.sub(r'\s+', '', ethiopian_candidates[0]).replace('-', '/')
                            data['date_of_issue_am'] = extracted_eth
                            print(f"✓ Extracted issue date (Ethiopian): {data['date_of_issue_am']}")
                    else:
                        print(f"⚠️ No date pattern found in issue text: {issue_text}")
                
                # If we got good data from regions, return it
                extracted_count = sum(1 for v in data.values() if v)
                if extracted_count >= 3:
                    print(f"✅ Region-based extraction successful: {extracted_count}/{len(data)} fields")
                    return data
                else:
                    print(f"⚠️ Region-based extraction incomplete: {extracted_count}/{len(data)} fields")
                    print("   Falling back to full-page OCR...")
        
        # Fall back to full-page text parsing
        print(f"🔍 Parsing full text ({len(text)} chars)")
        print(f"📄 Full text:\n{text}\n{'='*60}")
        
        lines = text.split('\n')
        
        # Extract FAN (not FIN) - try multiple patterns
        if not data['fan']:
            fan_patterns = [
                r'FAN[:\s]*(\d{15,17})',  # FAN: 5164983502379087
                r'ካርድ[:\s]*(\d{15,17})',  # Amharic label
                r'(?:^|\s)(\d{15,17})(?:\s|$)',  # Just 15-17 digits with word boundaries
            ]
            
            for pattern in fan_patterns:
                fan_match = re.search(pattern, text, re.IGNORECASE | re.MULTILINE)
                if fan_match:
                    fan_num = fan_match.group(1)
                    # FAN can be 15 or 16 digits
                    if len(fan_num) >= 15:
                        data['fan'] = fan_num[:16] if len(fan_num) >= 16 else fan_num
                        print(f"✓ Found FAN: {data['fan']}")
                        break
            
            # If no FAN found, look for any 15-17 digit number
            if not data['fan']:
                all_numbers = re.findall(r'\d{15,17}', text.replace(' ', ''))
                if all_numbers:
                    fan_num = all_numbers[0]
                    data['fan'] = fan_num[:16] if len(fan_num) >= 16 else fan_num
                    print(f"✓ Found FAN (fallback): {data['fan']}")
        
        # Don't extract barcode - it will be generated from FAN
        # Leave barcode field empty
        data['barcode'] = ''
        
        # Extract dates - try multiple formats
        date_patterns = [
            r'(\d{1,2}/\d{1,2}/\d{2,4})',  # DD/MM/YYYY or DD-MM-YYYY
            r'(\d{4}/\d{1,2}/\d{1,2})',  # YYYY/MM/DD or YYYY-MM-DD
            r'(\d{1,2}\s+[A-Za-z]+\s+\d{4})',  # DD Month YYYY
        ]
        
        # Try to extract names directly from concatenated text
        # Pattern: Amharic name followed by English name before "Date of Birth" or "Oate of Beth"
        # Example: "።ፊራኦል ወርቅነህ ቡሰሪ 3Firaol Workineh Buseri a።ት >ል ቆ ፣ ! Oate of Beth"
        if not data['full_name_en'] or not data['full_name_am']:
            # Look for pattern: Amharic text followed by English capitalized words before date/birth keywords
            name_pattern = r'([ሀ-፼\s]{10,})\s*\d*\s*([A-Z][a-z]+(?:\s+[A-Z][a-z]+){1,3})\s*[a-z\s]*(?:Oate of Beth|Date of Birth|የትውልድ|birth)'
            name_match = re.search(name_pattern, text, re.IGNORECASE)
            if name_match:
                amharic_name = name_match.group(1).strip()
                english_name = name_match.group(2).strip()
                
                # Clean Amharic name
                amharic_name = ' '.join(amharic_name.split())  # Normalize spaces
                # Remove leading punctuation
                amharic_name = re.sub(r'^[።፣፤፥፦፧፨]+\s*', '', amharic_name)
                
                # Clean English name
                english_name = ' '.join(english_name.split())  # Normalize spaces
                
                if len(amharic_name) >= 5 and not data['full_name_am']:
                    data['full_name_am'] = amharic_name
                    print(f"✓ Found name (AM, pattern): {amharic_name}")
                
                if len(english_name) >= 5 and not data['full_name_en']:
                    data['full_name_en'] = english_name
                    print(f"✓ Found name (EN, pattern): {english_name}")
        
        # Extract names - look for patterns
        if not data['full_name_en']:
            for i, line in enumerate(lines):
                line_clean = line.strip()
                
                # Skip empty lines
                if not line_clean or len(line_clean) < 3:
                    continue
                
                # Look for Full Name section
                if 'full name' in line_clean.lower() or 'ሙሉ ስም' in line_clean or 'name' in line_clean.lower():
                    # Next 1-2 lines are likely names
                    # In Ethiopian ID: Amharic comes first, then English
                    # Skip lines that are too short or contain special characters
                    for j in range(i + 1, min(i + 4, len(lines))):
                        potential_name = lines[j].strip()
                        
                        # Skip if too short, has too many special chars, or is a label
                        if len(potential_name) < 5:
                            continue
                        if potential_name.count('=') > 0 or potential_name.count('|') > 1:
                            continue
                        if any(label in potential_name.lower() for label in ['date', 'sex', 'birth', 'expiry']):
                            continue
                        
                        # Clean up the name
                        potential_name = potential_name.replace("'", "").replace("=", "").strip()
                        # Remove trailing numbers/special chars
                        potential_name = re.sub(r'[0-9°]+$', '', potential_name).strip()
                        
                        if len(potential_name) > 5:
                            # Check if it's Amharic or English
                            has_amharic = any('\u1200' <= c <= '\u137F' for c in potential_name)
                            if has_amharic and not data['full_name_am']:
                                data['full_name_am'] = potential_name
                                print(f"✓ Found name (AM): {potential_name}")
                            elif not has_amharic and not data['full_name_en']:
                                data['full_name_en'] = potential_name
                                print(f"✓ Found name (EN): {potential_name}")
                
                # Look for Date of Birth
                if not data['date_of_birth'] and ('date of birth' in line_clean.lower() or 'የትውልድ' in line_clean or 'birth' in line_clean.lower() or 'dob' in line_clean.lower() or '2+OAL' in line_clean):
                    # Check current line and next line for date
                    for check_line in [line_clean, lines[i + 1].strip() if i + 1 < len(lines) else '']:
                        for pattern in date_patterns:
                            date_match = re.search(pattern, check_line)
                            if date_match:
                                data['date_of_birth'] = date_match.group(1)
                                print(f"✓ Found DOB: {data['date_of_birth']}")
                                break
                        if data['date_of_birth']:
                            break
                
                # Also check if line contains a date pattern directly (for compact formats)
                if not data['date_of_birth'] and re.search(r'\d{2}/\d{2}/\d{4}', line_clean):
                    # Check if this line has "birth" context nearby
                    context = ' '.join(lines[max(0, i-1):min(len(lines), i+2)])
                    if 'birth' in context.lower() or 'የትውልድ' in context or 'Beth' in context:
                        date_match = re.search(r'(\d{2}/\d{2}/\d{4})', line_clean)
                        if date_match:
                            data['date_of_birth'] = date_match.group(1)
                            print(f"✓ Found DOB (inline): {data['date_of_birth']}")
        
        # Extract DOB from concatenated text if not found
        # Pattern: "Oate of Beth" or "Date of Birth" followed by date
        if not data['date_of_birth']:
            dob_pattern = r'(?:Oate of Beth|Date of Birth|የትውልድ)["\s]*(\d{2}/\d{2}/\d{4})'
            dob_match = re.search(dob_pattern, text, re.IGNORECASE)
            if dob_match:
                data['date_of_birth'] = dob_match.group(1)
                print(f"✓ Found DOB (concatenated): {data['date_of_birth']}")
        
        # Extract expiry date from concatenated text
        # Pattern: "Dare of Expory" or "Date of Expiry" followed by date
        if not data['date_of_expiry']:
            expiry_pattern = r'(?:Dare of Expory|Date of Expiry|የማብቂያ)["\s]*(\d{4}/\d{2}/\d{2})'
            expiry_match = re.search(expiry_pattern, text, re.IGNORECASE)
            if expiry_match:
                data['date_of_expiry'] = expiry_match.group(1)
                print(f"✓ Found expiry (concatenated): {data['date_of_expiry']}")
        
        # Continue with line-by-line parsing for remaining fields
        for i, line in enumerate(lines):
            line_clean = line.strip()
            
            # Skip empty lines
            if not line_clean or len(line_clean) < 3:
                continue
            
            # Look for Sex/Gender
            if not data['sex'] and ('sex' in line_clean.lower() or 'ጾታ' in line_clean or 'gender' in line_clean.lower() or '|' in line_clean or '.Pt' in line_clean):
                # Check current line and next line
                for check_line in [line_clean, lines[i + 1].strip() if i + 1 < len(lines) else '']:
                    # Clean up the line
                    check_clean = check_line.replace('|', ' ').replace('Ove', 'Male').replace('Oryx', '').replace('t+]', '').strip()
                    if 'female' in check_clean.lower():
                        data['sex'] = 'Female'
                        print(f"✓ Found sex: Female")
                        break
                    elif 'male' in check_clean.lower() and 'female' not in check_clean.lower():
                        data['sex'] = 'Male'
                        print(f"✓ Found sex: Male")
                        break
                    elif 'ወንድ' in check_line or 'ወ/ድ' in check_line or 'm' == check_clean.lower().strip():
                        data['sex'] = 'Male'
                        print(f"✓ Found sex: Male")
                        break
                    elif 'ሴት' in check_line or 'f' == check_clean.lower().strip():
                        data['sex'] = 'Female'
                        print(f"✓ Found sex: Female")
                        break
            
            # Look for Date of Issue
            if not data['date_of_issue'] and ('date of issue' in line_clean.lower() or 'issue date' in line_clean.lower() or 'የመስጫ' in line_clean or 'issued' in line_clean.lower()):
                for check_line in [line_clean, lines[i + 1].strip() if i + 1 < len(lines) else '']:
                    for pattern in date_patterns:
                        date_match = re.search(pattern, check_line)
                        if date_match:
                            data['date_of_issue'] = date_match.group(1)
                            print(f"✓ Found issue date: {data['date_of_issue']}")
                            break
                    if data['date_of_issue']:
                        break
        
        # Look for issue date in vertical text (appears anywhere in document)
        # Issue date is often written vertically on the right side
        if not data['date_of_issue']:
            # Look for date patterns that might be issue dates
            # Format: "Date Issued - 2018/06/02 | 2026/Feb/09"
            all_dates = re.findall(r'(\d{4}/\d{2}/\d{2})', text)
            all_dates.extend(re.findall(r'(\d{4}/[A-Za-z]{3}/\d{2})', text))
            
            # Look for "Date Issued" or "የመስጫ ቀን" followed by a date
            issue_pattern = r'(?:Date Issued|የመስጫ\s*ቀን|Issued)[:\s\-]*(\d{4}/\d{2}/\d{2})'
            issue_match = re.search(issue_pattern, text, re.IGNORECASE)
            if issue_match:
                data['date_of_issue'] = issue_match.group(1)
                print(f"✓ Found issue date (with label): {data['date_of_issue']}")
            elif all_dates and data['date_of_birth'] and data['date_of_expiry']:
                # Issue date should be after DOB and before expiry
                for date_str in all_dates:
                    if date_str not in [data['date_of_birth'], data['date_of_expiry']]:
                        data['date_of_issue'] = date_str
                        print(f"✓ Found issue date (vertical/inline): {data['date_of_issue']}")
                        break
                
                # Look for Expiry Date
                if not data['date_of_expiry'] and ('expiry' in line_clean.lower() or 'የማብቂያ' in line_clean or 'expires' in line_clean.lower() or 'valid until' in line_clean.lower() or 'POLPNSNY' in line_clean):
                    for check_line in [line_clean, lines[i + 1].strip() if i + 1 < len(lines) else '']:
                        for pattern in date_patterns:
                            date_match = re.search(pattern, check_line)
                            if date_match:
                                expiry_date = date_match.group(1)
                                # Fix 2-digit year to 4-digit year if needed
                                if re.match(r'\d{2}/\d{2}/\d{2}$', expiry_date):
                                    # Convert YY/MM/DD to YYYY/MM/DD
                                    parts = expiry_date.split('/')
                                    if len(parts) == 3:
                                        year = int(parts[0])
                                        # Assume 20xx for years 00-99
                                        full_year = 2000 + year if year < 100 else year
                                        expiry_date = f"{full_year}/{parts[1]}/{parts[2]}"
                                data['date_of_expiry'] = expiry_date
                                print(f"✓ Found expiry: {data['date_of_expiry']}")
                                break
                        if data['date_of_expiry']:
                            break
                
                # Also check if line contains a date pattern with "expiry" context
                if not data['date_of_expiry'] and re.search(r'\d{4}/\d{2}/\d{2}', line_clean):
                    context = ' '.join(lines[max(0, i-1):min(len(lines), i+2)])
                    if 'expiry' in context.lower() or 'የማብቂያ' in context or 'POLPNSNY' in context:
                        date_match = re.search(r'(\d{4}/\d{2}/\d{2})', line_clean)
                        if date_match:
                            data['date_of_expiry'] = date_match.group(1)
                            print(f"✓ Found expiry (inline): {data['date_of_expiry']}")
        
        # If no names found, try to find capitalized text (likely names)
        if not data['full_name_en']:
            for line in lines:
                line_clean = line.strip().replace("'", "").replace("=", "").strip()
                
                # Skip if too short
                if len(line_clean) < 8:
                    continue
                
                # Skip lines with pipe character (bilingual format like "ወንድ | Male")
                if '|' in line_clean:
                    continue
                
                # Skip lines that look like sex field
                if any(sex_word in line_clean.lower() for sex_word in ['male', 'female', 'ወንድ', 'ሴት']):
                    continue
                
                # Skip lines with too many special characters
                special_count = sum(1 for c in line_clean if not c.isalnum() and not c.isspace())
                if special_count > 3:
                    continue
                
                # Look for lines with mostly letters and spaces (names)
                alpha_count = sum(1 for c in line_clean if c.isalpha() or c.isspace())
                if alpha_count / len(line_clean) > 0.7:  # At least 70% letters/spaces
                    # Skip common labels
                    if not any(label in line_clean.lower() for label in ['full name', 'date', 'sex', 'nationality', 'address', 'digital', 'card', 'copy', 'ethiopian', 'expiry', 'birth']):
                        # Check if it looks like a name (has spaces, title case or all caps)
                        if ' ' in line_clean and (line_clean.istitle() or line_clean.isupper()):
                            data['full_name_en'] = line_clean
                            print(f"✓ Found name (pattern match): {line_clean}")
                            break
        
        print(f"📊 Extraction summary: {sum(1 for v in data.values() if v)} / {len(data)} fields extracted")
        return data
        """Parse extracted text from front ID card with improved pattern matching"""
        data = {
            'full_name_en': '',
            'full_name_am': '',
            'date_of_birth': '',
            'sex': '',
            'date_of_expiry': '',
            'date_of_issue': '',
            'fan': '',  # FAN not FIN
            'barcode': ''
        }
        
        print(f"🔍 Parsing front card text ({len(text)} chars)")
        print(f"📄 Full text:\n{text}\n{'='*60}")
        
        lines = text.split('\n')
        
        # Extract FAN (not FIN) - try multiple patterns
        if not data['fan']:
            fan_patterns = [
                r'FAN[:\s]*(\d{15,17})',  # FAN: 5164983502379087
                r'ካርድ[:\s]*(\d{15,17})',  # Amharic label
                r'(?:^|\s)(\d{15,17})(?:\s|$)',  # Just 15-17 digits with word boundaries
            ]
            
            for pattern in fan_patterns:
                fan_match = re.search(pattern, text, re.IGNORECASE | re.MULTILINE)
                if fan_match:
                    fan_num = fan_match.group(1)
                    # FAN can be 15 or 16 digits
                    if len(fan_num) >= 15:
                        data['fan'] = fan_num[:16] if len(fan_num) >= 16 else fan_num
                        print(f"✓ Found FAN: {data['fan']}")
                        break
            
            # If no FAN found, look for any 15-17 digit number
            if not data['fan']:
                all_numbers = re.findall(r'\d{15,17}', text.replace(' ', ''))
                if all_numbers:
                    fan_num = all_numbers[0]
                    data['fan'] = fan_num[:16] if len(fan_num) >= 16 else fan_num
                    print(f"✓ Found FAN (fallback): {data['fan']}")
        if not data['fan']:
            all_numbers = re.findall(r'\d{15}', text)
            if all_numbers:
                data['fan'] = all_numbers[0]
                print(f"✓ Found FAN (fallback): {data['fan']}")
        
        # Extract barcode number (same as FAN usually)
        if data['fan']:
            data['barcode'] = data['fan']
            print(f"✓ Barcode: {data['barcode']}")
        
        # Extract dates - try multiple formats
        date_patterns = [
            r'(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})',  # DD/MM/YYYY or DD-MM-YYYY
            r'(\d{4}[/-]\d{1,2}[/-]\d{1,2})',  # YYYY/MM/DD or YYYY-MM-DD
            r'(\d{1,2}\s+[A-Za-z]+\s+\d{4})',  # DD Month YYYY
        ]
        
        # Extract names - look for patterns
        for i, line in enumerate(lines):
            line_clean = line.strip()
            
            # Skip empty lines
            if not line_clean or len(line_clean) < 3:
                continue
            
            # Look for Full Name section
            if 'full name' in line_clean.lower() or 'ሙሉ ስም' in line_clean or 'name' in line_clean.lower():
                # Next 1-2 lines are likely names
                if i + 1 < len(lines):
                    potential_name = lines[i + 1].strip()
                    if len(potential_name) > 3 and not any(char.isdigit() for char in potential_name):
                        data['full_name_en'] = potential_name
                        print(f"✓ Found name (EN): {potential_name}")
                if i + 2 < len(lines):
                    potential_name_am = lines[i + 2].strip()
                    if len(potential_name_am) > 3:
                        data['full_name_am'] = potential_name_am
                        print(f"✓ Found name (AM): {potential_name_am}")
            
            # Look for Date of Birth
            if 'date of birth' in line_clean.lower() or 'የትውልድ' in line_clean or 'birth' in line_clean.lower() or 'dob' in line_clean.lower():
                # Check current line and next line for date
                for check_line in [line_clean, lines[i + 1].strip() if i + 1 < len(lines) else '']:
                    for pattern in date_patterns:
                        date_match = re.search(pattern, check_line)
                        if date_match:
                            data['date_of_birth'] = date_match.group(1)
                            print(f"✓ Found DOB: {data['date_of_birth']}")
                            break
                    if data['date_of_birth']:
                        break
            
            # Look for Sex/Gender
            if 'sex' in line_clean.lower() or 'ጾታ' in line_clean or 'gender' in line_clean.lower():
                # Check current line and next line
                for check_line in [line_clean, lines[i + 1].strip() if i + 1 < len(lines) else '']:
                    if 'male' in check_line.lower() or 'ወንድ' in check_line or 'ወ/ድ' in check_line or 'm' == check_line.lower().strip():
                        data['sex'] = 'Male'
                        print(f"✓ Found sex: Male")
                        break
                    elif 'female' in check_line.lower() or 'ሴት' in check_line or 'f' == check_line.lower().strip():
                        data['sex'] = 'Female'
                        print(f"✓ Found sex: Female")
                        break
            
            # Look for Date of Issue
            if 'date of issue' in line_clean.lower() or 'issue date' in line_clean.lower() or 'የመስጫ' in line_clean or 'issued' in line_clean.lower():
                for check_line in [line_clean, lines[i + 1].strip() if i + 1 < len(lines) else '']:
                    for pattern in date_patterns:
                        date_match = re.search(pattern, check_line)
                        if date_match:
                            data['date_of_issue'] = date_match.group(1)
                            print(f"✓ Found issue date: {data['date_of_issue']}")
                            break
                    if data['date_of_issue']:
                        break
            
            # Look for Expiry Date
            if 'expiry' in line_clean.lower() or 'የማብቂያ' in line_clean or 'expires' in line_clean.lower() or 'valid until' in line_clean.lower():
                for check_line in [line_clean, lines[i + 1].strip() if i + 1 < len(lines) else '']:
                    for pattern in date_patterns:
                        date_match = re.search(pattern, check_line)
                        if date_match:
                            data['date_of_expiry'] = date_match.group(1)
                            print(f"✓ Found expiry: {data['date_of_expiry']}")
                            break
                    if data['date_of_expiry']:
                        break
        
        # If no names found, try to find capitalized text (likely names)
        if not data['full_name_en']:
            for line in lines:
                line_clean = line.strip()
                # Look for lines with mostly uppercase letters and spaces
                if len(line_clean) > 10 and line_clean.isupper() and ' ' in line_clean:
                    if not any(char.isdigit() for char in line_clean):
                        # Skip common labels
                        if not any(label in line_clean.lower() for label in ['full name', 'date', 'sex', 'nationality', 'address']):
                            data['full_name_en'] = line_clean
                            print(f"✓ Found name (uppercase): {line_clean}")
                            break
        
        print(f"📊 Extraction summary: {sum(1 for v in data.values() if v)} / {len(data)} fields extracted")
        return data
    
    def extract_qr_code_region(self, image_path: str, output_path: str) -> Optional[str]:
        """Extract QR code region from back ID card image with improved detection"""
        try:
            img = cv2.imread(image_path)
            if img is None:
                print(f"❌ Could not read image: {image_path}")
                return None
            
            height, width = img.shape[:2]
            print(f"📐 Image dimensions for QR extraction: {width}x{height}")
            
            # Try to detect QR code using OpenCV's QRCodeDetector
            qr_detector = cv2.QRCodeDetector()
            data, bbox, straight_qrcode = qr_detector.detectAndDecode(img)
            
            if bbox is not None and len(bbox) > 0:
                # QR code detected! Extract the bounding box region
                print("✓ QR code detected using OpenCV detector")
                
                # Get bounding box coordinates
                bbox = bbox[0]  # Get first QR code
                x_coords = [int(point[0]) for point in bbox]
                y_coords = [int(point[1]) for point in bbox]
                
                x_min, x_max = min(x_coords), max(x_coords)
                y_min, y_max = min(y_coords), max(y_coords)
                
                # Add some padding (10%)
                padding_x = int((x_max - x_min) * 0.1)
                padding_y = int((y_max - y_min) * 0.1)
                
                x_min = max(0, x_min - padding_x)
                y_min = max(0, y_min - padding_y)
                x_max = min(width, x_max + padding_x)
                y_max = min(height, y_max + padding_y)
                
                # Extract QR region
                qr_region = img[y_min:y_max, x_min:x_max]
                
                print(f"   Detected region: Y({y_min}-{y_max}), X({x_min}-{x_max})")
                print(f"   Size: {x_max-x_min}x{y_max-y_min} pixels")
                
                if data:
                    print(f"   QR data: {data[:100]}...")
            else:
                # Fallback to predefined region if detection fails
                print("⚠️ QR code not detected, using predefined region")
                
                # QR code takes up most of the top portion (based on sample image)
                # Adjusted to capture the large QR code
                qr_y1 = int(height * 0.08)   # Start at 8%
                qr_y2 = int(height * 0.62)   # End at 62% (QR is very large)
                qr_x1 = int(width * 0.10)    # Start at 10%
                qr_x2 = int(width * 0.90)    # End at 90%
                
                # Extract QR region
                qr_region = img[qr_y1:qr_y2, qr_x1:qr_x2]
                
                print(f"   Region: Y({qr_y1}-{qr_y2}), X({qr_x1}-{qr_x2})")
                print(f"   Size: {qr_x2-qr_x1}x{qr_y2-qr_y1} pixels")
            
            # Save the QR code region
            cv2.imwrite(output_path, qr_region)
            print(f"✓ QR code region extracted and saved to: {output_path}")
            
            return output_path
            
        except Exception as e:
            print(f"❌ Error extracting QR code region: {e}")
            import traceback
            traceback.print_exc()
            return None
    
    def decode_qr_code(self, image_path: str) -> Optional[str]:
        """Decode QR code from image using pyzbar"""
        try:
            # Try to import pyzbar
            try:
                from pyzbar import pyzbar
            except ImportError:
                print("⚠️ pyzbar not installed. QR code decoding skipped.")
                print("   Install with: pip install pyzbar")
                return None
            
            # Read image
            img = cv2.imread(image_path)
            if img is None:
                print(f"❌ Could not read image: {image_path}")
                return None
            
            # Decode QR codes
            decoded_objects = pyzbar.decode(img)
            
            if decoded_objects:
                for obj in decoded_objects:
                    qr_data = obj.data.decode('utf-8')
                    print(f"✓ QR Code decoded: {qr_data[:100]}...")
                    return qr_data
            else:
                print("⚠️ No QR code found in image")
                return None
                
        except Exception as e:
            print(f"❌ Error decoding QR code: {e}")
            import traceback
            traceback.print_exc()
            return None
    
    def extract_back_card_regions(self, image_path: str) -> Dict:
        """Extract text from specific regions of Ethiopian Digital ID Card (Back)"""
        try:
            img = cv2.imread(image_path)
            if img is None:
                print(f"❌ Could not read image: {image_path}")
                return {}
            
            height, width = img.shape[:2]
            print(f"📐 Image dimensions: {width}x{height}")
            
            # Define regions for back card based on EXACT pixel coordinates
            # IMPORTANT: Coordinates are for reference card size ~900x1600
            # We calculate percentages and apply to actual image dimensions
            # Coordinates based on 591x1280px reference image from Adobe
            # PHONE: X:94, Y:729, W:143, H:25 → (94,729)-(237,754)
            # FIN: X:362, Y:713, W:144, H:29 → (362,713)-(506,742)
            # NATIONALITY_AM: X:89, Y:782, W:72, H:29 → (89,782)-(161,811)
            # NATIONALITY_EN: X:167, Y:785, W:127, H:27 → (167,785)-(294,812)
            # REGION_AM: X:95, Y:829, W:370, H:25 → (95,829)-(465,854)
            # REGION_EN: X:94, Y:850, W:416, H:25 → (94,850)-(510,875)
            # SUBCITY_AM: X:93, Y:872, W:398, H:26 → (93,872)-(491,898)
            # SUBCITY_EN: X:94, Y:893, W:382, H:26 → (94,893)-(476,919)
            # WOREDA_AM: X:92, Y:916, W:427, H:30 → (92,916)-(519,946)
            # WOREDA_EN: X:89, Y:938, W:411, H:28 → (89,938)-(500,966)
            
            # Reference dimensions (from Adobe measurements)
            ref_width = 591
            ref_height = 1280
            
            # Calculate percentage-based regions (will scale to actual image size)
            regions = {
                'phone_number': (94/ref_width, 729/ref_height, 237/ref_width, 754/ref_height),           # Phone number (94,729)-(237,754)
                'fin_number': (362/ref_width, 713/ref_height, 506/ref_width, 742/ref_height),            # FIN number (362,713)-(506,742)
                'nationality_am': (89/ref_width, 782/ref_height, 161/ref_width, 811/ref_height),         # Nationality Amharic (89,782)-(161,811)
                'nationality_en': (167/ref_width, 785/ref_height, 294/ref_width, 812/ref_height),        # Nationality English (167,785)-(294,812)
                'region_am': (95/ref_width, 829/ref_height, 465/ref_width, 854/ref_height),              # Address Region Amharic (95,829)-(465,854)
                'region_en': (94/ref_width, 850/ref_height, 510/ref_width, 875/ref_height),              # Address Region English (94,850)-(510,875)
                'subcity_am': (93/ref_width, 872/ref_height, 491/ref_width, 898/ref_height),             # Sub City/Zone Amharic (93,872)-(491,898)
                'subcity_en': (94/ref_width, 893/ref_height, 476/ref_width, 919/ref_height),             # Sub City/Zone English (94,893)-(476,919)
                'woreda_am': (92/ref_width, 916/ref_height, 519/ref_width, 946/ref_height),              # Woreda Amharic (92,916)-(519,946)
                'woreda_en': (89/ref_width, 938/ref_height, 500/ref_width, 966/ref_height),              # Woreda English (89,938)-(500,966)
            }
            
            print(f"📏 Using reference dimensions: {ref_width}x{ref_height}, actual: {width}x{height}")
            
            extracted_regions = {}
            
            for region_name, (x1, y1, x2, y2) in regions.items():
                # Convert percentages to pixels
                x1_px = int(x1 * width)
                y1_px = int(y1 * height)
                x2_px = int(x2 * width)
                y2_px = int(y2 * height)
                
                # Extract region
                region_img = img[y1_px:y2_px, x1_px:x2_px]
                
                # Convert to grayscale
                gray = cv2.cvtColor(region_img, cv2.COLOR_BGR2GRAY)
                
                # Resize for better OCR (reduced scale for speed)
                scale = 2.0  # Reduced from 3.0 to 2.0 for faster processing
                gray = cv2.resize(gray, None, fx=scale, fy=scale, interpolation=cv2.INTER_CUBIC)
                
                # Apply preprocessing
                if region_name in ['phone_number', 'fin_number']:
                    # For numbers, use aggressive preprocessing
                    clahe = cv2.createCLAHE(clipLimit=3.0, tileGridSize=(8,8))
                    enhanced = clahe.apply(gray)
                    _, thresh = cv2.threshold(enhanced, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
                    
                    # Extract only numbers
                    config = '--oem 3 --psm 7 -c tessedit_char_whitelist=0123456789'
                    text = pytesseract.image_to_string(thresh, lang='eng', config=config)
                else:
                    # For text fields
                    bilateral = cv2.bilateralFilter(gray, 9, 75, 75)
                    _, thresh = cv2.threshold(bilateral, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
                    
                    if region_name == 'address':
                        config = '--oem 3 --psm 6'  # Block of text
                    else:
                        config = '--oem 3 --psm 7'  # Single line
                    
                    text = pytesseract.image_to_string(thresh, lang='eng+amh', config=config)
                
                extracted_regions[region_name] = text.strip()
                print(f"✓ {region_name}: {text.strip()[:80]}")
            
            return extracted_regions
            
        except Exception as e:
            print(f"❌ Error extracting back card regions: {e}")
            import traceback
            traceback.print_exc()
            return {}
    
    def parse_back_card_data(self, text: str, image_path: str = None) -> Dict:
        """Parse extracted text from back ID card with improved pattern matching"""
        data = {
            'phone_number': '',
            'nationality_en': '',
            'nationality_am': '',
            'address_en': '',
            'address_am': '',
            'region_en': '',
            'region_am': '',
            'subcity_en': '',
            'subcity_am': '',
            'woreda_en': '',
            'woreda_am': '',
            'fin': ''  # FIN also on back card
        }
        
        # Try region-based extraction first if image path provided
        if image_path:
            print("🎯 Attempting region-based extraction for back card...")
            regions = self.extract_back_card_regions(image_path)
            
            if regions:
                # Extract phone number
                if 'phone_number' in regions and regions['phone_number']:
                    phone_text = regions['phone_number'].replace(' ', '').replace('-', '').replace('|', '')
                    # Remove labels
                    phone_text = phone_text.replace('Phone', '').replace('Number', '').replace('ስልክ', '').strip()
                    # Look for 10-digit number
                    phone_match = re.search(r'(0\d{9})', phone_text)
                    if phone_match:
                        data['phone_number'] = phone_match.group(1)
                        print(f"✓ Extracted phone: {data['phone_number']}")
                
                # Extract FIN number from back card
                if 'fin_number' in regions and regions['fin_number']:
                    fin_text = regions['fin_number'].replace(' ', '').replace('-', '').replace('|', '')
                    # Remove labels
                    fin_text = fin_text.replace('FIN', '').replace('ሀረፍ', '').strip()
                    # Look for 12-digit number (FIN format: 9124 0871 5809)
                    fin_match = re.search(r'(\d{12,15})', fin_text)
                    if fin_match:
                        data['fin'] = fin_match.group(1)[:12]  # Take first 12 digits
                        print(f"✓ Extracted FIN: {data['fin']}")
                
                # Extract nationality (now separate Amharic and English regions)
                if 'nationality_am' in regions and regions['nationality_am']:
                    nat_am_text = regions['nationality_am'].strip()
                    # Clean up and extract Amharic nationality
                    nat_am_text = nat_am_text.replace('ዜግነት', '').replace('|', '').strip()
                    if 'ኢትዮጵያ' in nat_am_text or 'አትዮጵያ' in nat_am_text:
                        data['nationality_am'] = 'ኢትዮጵያዊ'
                        print(f"✓ Extracted nationality (AM): {data['nationality_am']}")
                
                if 'nationality_en' in regions and regions['nationality_en']:
                    nat_en_text = regions['nationality_en'].strip()
                    # Clean up and extract English nationality
                    nat_en_text = nat_en_text.replace('Nationality', '').replace('|', '').strip()
                    if 'ethiopian' in nat_en_text.lower() or 'ethio' in nat_en_text.lower():
                        data['nationality_en'] = 'Ethiopian'
                        print(f"✓ Extracted nationality (EN): {data['nationality_en']}")
                
                # Extract address region (separate Amharic and English)
                if 'region_am' in regions and regions['region_am']:
                    region_am_text = regions['region_am'].strip()
                    # Clean Amharic text
                    region_am_text = ''.join(c for c in region_am_text if '\u1200' <= c <= '\u137F' or c.isspace())
                    region_am_text = ' '.join(region_am_text.split())
                    if len(region_am_text) >= 2:
                        data['region_am'] = region_am_text
                        print(f"✓ Extracted region (AM): {data['region_am']}")
                
                if 'region_en' in regions and regions['region_en']:
                    region_en_text = regions['region_en'].strip()
                    # Clean English text
                    region_en_text = ''.join(c for c in region_en_text if c.isascii() and (c.isalpha() or c.isspace()))
                    region_en_text = ' '.join(region_en_text.split())
                    if len(region_en_text) >= 3:
                        data['region_en'] = region_en_text
                        print(f"✓ Extracted region (EN): {data['region_en']}")
                
                # Extract subcity/zone (separate Amharic and English)
                if 'subcity_am' in regions and regions['subcity_am']:
                    subcity_am_text = regions['subcity_am'].strip()
                    # Clean Amharic text
                    subcity_am_text = ''.join(c for c in subcity_am_text if '\u1200' <= c <= '\u137F' or c.isspace())
                    subcity_am_text = ' '.join(subcity_am_text.split())
                    if len(subcity_am_text) >= 2:
                        data['subcity_am'] = subcity_am_text
                        print(f"✓ Extracted subcity (AM): {data['subcity_am']}")
                
                if 'subcity_en' in regions and regions['subcity_en']:
                    subcity_en_text = regions['subcity_en'].strip()
                    # Clean English text
                    subcity_en_text = ''.join(c for c in subcity_en_text if c.isascii() and (c.isalpha() or c.isspace() or c.isdigit()))
                    subcity_en_text = ' '.join(subcity_en_text.split())
                    if len(subcity_en_text) >= 3:
                        data['subcity_en'] = subcity_en_text
                        print(f"✓ Extracted subcity (EN): {data['subcity_en']}")
                
                # Extract woreda (separate Amharic and English)
                if 'woreda_am' in regions and regions['woreda_am']:
                    woreda_am_text = regions['woreda_am'].strip()
                    # Clean Amharic text
                    woreda_am_text = ''.join(c for c in woreda_am_text if '\u1200' <= c <= '\u137F' or c.isspace() or c.isdigit())
                    woreda_am_text = ' '.join(woreda_am_text.split())
                    if len(woreda_am_text) >= 2:
                        data['woreda_am'] = woreda_am_text
                        print(f"✓ Extracted woreda (AM): {data['woreda_am']}")
                
                if 'woreda_en' in regions and regions['woreda_en']:
                    woreda_en_text = regions['woreda_en'].strip()
                    # Clean English text
                    woreda_en_text = ''.join(c for c in woreda_en_text if c.isascii() and (c.isalpha() or c.isspace() or c.isdigit()))
                    woreda_en_text = ' '.join(woreda_en_text.split())
                    if len(woreda_en_text) >= 3:
                        data['woreda_en'] = woreda_en_text
                        print(f"✓ Extracted woreda (EN): {data['woreda_en']}")
                
                # Build complete address strings from components
                if data['region_am'] or data['subcity_am'] or data['woreda_am']:
                    address_parts_am = [p for p in [data['region_am'], data['subcity_am'], data['woreda_am']] if p]
                    data['address_am'] = ', '.join(address_parts_am)
                    print(f"✓ Built Amharic address: {data['address_am']}")
                
                if data['region_en'] or data['subcity_en'] or data['woreda_en']:
                    address_parts_en = [p for p in [data['region_en'], data['subcity_en'], data['woreda_en']] if p]
                    data['address_en'] = ', '.join(address_parts_en)
                    print(f"✓ Built English address: {data['address_en']}")
                
                # If we got good data from regions, return it
                extracted_count = sum(1 for k, v in data.items() if v and k not in ['address_am', 'address_en'])
                if extracted_count >= 3:
                    print(f"✅ Region-based extraction successful: {extracted_count}/8 fields")
                    return data
                else:
                    print(f"⚠️ Region-based extraction incomplete: {extracted_count}/8 fields")
                    print("   Falling back to full-page OCR...")
        
        # Fall back to full-page text parsing
        print(f"🔍 Parsing back card full text ({len(text)} chars)")
        print(f"📄 Full text:\n{text}\n{'='*60}")
        
        lines = text.split('\n')
        address_lines = []
        
        # Extract Phone Number - try multiple patterns
        if not data['phone_number']:
            phone_patterns = [
                r'(?:phone|ስልክ|tel|mobile)[:\s]*(\d{10})',  # With label
                r'(?:^|\s)(09\d{8})(?:\s|$)',  # Ethiopian mobile format with word boundaries
                r'(?:^|\s)(\+251\d{9})(?:\s|$)',  # International format
                r'(?:^|\s)(0\d{9})(?:\s|$)',  # Any 10 digits starting with 0
            ]
            
            for pattern in phone_patterns:
                phone_match = re.search(pattern, text, re.IGNORECASE | re.MULTILINE)
                if phone_match and not data['phone_number']:
                    data['phone_number'] = phone_match.group(1)
                    print(f"✓ Found phone: {data['phone_number']}")
                    break
            
            # If no phone found, look for any 10-digit number starting with 0
            if not data['phone_number']:
                all_phones = re.findall(r'0\d{9}', text)
                if all_phones:
                    data['phone_number'] = all_phones[0]
                    print(f"✓ Found phone (fallback): {data['phone_number']}")
        
        # Extract FIN from back card
        if not data['fin']:
            fin_patterns = [
                r'FIN[:\s]*(\d{12,15})',
                r'(?:^|\s)(\d{12})(?:\s|$)',
            ]
            for pattern in fin_patterns:
                fin_match = re.search(pattern, text, re.IGNORECASE | re.MULTILINE)
                if fin_match:
                    data['fin'] = fin_match.group(1)[:12]
                    print(f"✓ Found FIN: {data['fin']}")
                    break
        
        for i, line in enumerate(lines):
            line_clean = line.strip()
            
            # Skip empty lines
            if not line_clean or len(line_clean) < 2:
                continue
            
            # Extract Nationality
            if not data['nationality_en'] and ('nationality' in line_clean.lower() or 'ዜግነት' in line_clean):
                if i + 1 < len(lines):
                    nat_en = lines[i + 1].strip()
                    if nat_en and len(nat_en) > 2:
                        data['nationality_en'] = nat_en
                        print(f"✓ Found nationality (EN): {data['nationality_en']}")
                if i + 2 < len(lines):
                    nat_am = lines[i + 2].strip()
                    if nat_am and len(nat_am) > 2:
                        data['nationality_am'] = nat_am
                        print(f"✓ Found nationality (AM): {data['nationality_am']}")
            
            # Extract Address (multiple lines)
            if 'address' in line_clean.lower() or 'አድራሻ' in line_clean:
                # Collect next several lines as address
                for j in range(i + 1, min(i + 10, len(lines))):
                    addr_line = lines[j].strip()
                    if addr_line and len(addr_line) > 2:
                        # Stop if we hit another label
                        if any(label in addr_line.lower() for label in ['phone', 'nationality', 'date', 'sex', 'name']):
                            break
                        address_lines.append(addr_line)
                        print(f"✓ Found address line: {addr_line}")
        
        # Parse address lines if not already done
        if not data['region_en'] and len(address_lines) >= 1:
            # Try to identify region, subcity, woreda
            for line in address_lines:
                line_upper = line.upper()
                # Common Ethiopian regions
                if any(region in line_upper for region in ['OROMIA', 'AMHARA', 'TIGRAY', 'ADDIS', 'DIRE', 'SOMALI', 'AFAR', 'BENISHANGUL', 'GAMBELA', 'HARARI', 'SIDAMA', 'SOUTHERN']):
                    if not data['region_en']:
                        data['region_en'] = line
                        print(f"✓ Identified region: {line}")
                # Common subcities/zones
                elif any(sub in line_upper for sub in ['WEST', 'EAST', 'NORTH', 'SOUTH', 'TOWN', 'CITY', 'ZONE', 'KIFLE', 'ክፍለ', 'ARSI', 'BALE']):
                    if not data['subcity_en']:
                        data['subcity_en'] = line
                        print(f"✓ Identified subcity: {line}")
                # Woreda indicators
                elif 'WOREDA' in line_upper or 'KEBELE' in line_upper or 'ወረዳ' in line or 'TOWN' in line_upper:
                    if not data['woreda_en']:
                        data['woreda_en'] = line
                        print(f"✓ Identified woreda: {line}")
            
            # If not identified, use first lines
            if not data['region_en'] and len(address_lines) > 0:
                data['region_en'] = address_lines[0]
                print(f"✓ Using first line as region: {address_lines[0]}")
            if not data['subcity_en'] and len(address_lines) > 2:
                data['subcity_en'] = address_lines[2]
                print(f"✓ Using third line as subcity: {address_lines[2]}")
            if not data['woreda_en'] and len(address_lines) > 4:
                data['woreda_en'] = address_lines[4]
                print(f"✓ Using fifth line as woreda: {address_lines[4]}")
            
            # Combine for full address
            address_parts = [p for p in [data['region_en'], data['subcity_en'], data['woreda_en']] if p]
            data['address_en'] = ', '.join(address_parts)
            if len(address_lines) > 1:
                data['address_am'] = address_lines[1]
        
        print(f"📊 Extraction summary: {sum(1 for v in data.values() if v)} / {len(data)} fields extracted")
        return data
        """Parse extracted text from back ID card with improved pattern matching"""
        data = {
            'phone_number': '',
            'nationality_en': '',
            'nationality_am': '',
            'address_en': '',
            'address_am': '',
            'region': '',
            'subcity': '',
            'woreda': ''
        }
        
        print(f"🔍 Parsing back card text ({len(text)} chars)")
        print(f"📄 Full text:\n{text}\n{'='*60}")
        
        lines = text.split('\n')
        address_lines = []
        
        # Extract Phone Number - try multiple patterns
        phone_patterns = [
            r'(?:phone|ስልክ|tel|mobile)[:\s]*(\d{10})',  # With label
            r'(?:^|\s)(09\d{8})(?:\s|$)',  # Ethiopian mobile format with word boundaries
            r'(?:^|\s)(\+251\d{9})(?:\s|$)',  # International format
            r'(?:^|\s)(0\d{9})(?:\s|$)',  # Any 10 digits starting with 0
        ]
        
        for pattern in phone_patterns:
            phone_match = re.search(pattern, text, re.IGNORECASE | re.MULTILINE)
            if phone_match and not data['phone_number']:
                data['phone_number'] = phone_match.group(1)
                print(f"✓ Found phone: {data['phone_number']}")
                break
        
        # If no phone found, look for any 10-digit number starting with 0
        if not data['phone_number']:
            all_phones = re.findall(r'0\d{9}', text)
            if all_phones:
                data['phone_number'] = all_phones[0]
                print(f"✓ Found phone (fallback): {data['phone_number']}")
        
        for i, line in enumerate(lines):
            line_clean = line.strip()
            
            # Skip empty lines
            if not line_clean or len(line_clean) < 2:
                continue
            
            # Extract Nationality
            if 'nationality' in line_clean.lower() or 'ዜግነት' in line_clean:
                if i + 1 < len(lines):
                    nat_en = lines[i + 1].strip()
                    if nat_en and len(nat_en) > 2:
                        data['nationality_en'] = nat_en
                        print(f"✓ Found nationality (EN): {data['nationality_en']}")
                if i + 2 < len(lines):
                    nat_am = lines[i + 2].strip()
                    if nat_am and len(nat_am) > 2:
                        data['nationality_am'] = nat_am
                        print(f"✓ Found nationality (AM): {data['nationality_am']}")
            
            # Extract Address (multiple lines)
            if 'address' in line_clean.lower() or 'አድራሻ' in line_clean:
                # Collect next several lines as address
                for j in range(i + 1, min(i + 10, len(lines))):
                    addr_line = lines[j].strip()
                    if addr_line and len(addr_line) > 2:
                        # Stop if we hit another label
                        if any(label in addr_line.lower() for label in ['phone', 'nationality', 'date', 'sex', 'name']):
                            break
                        address_lines.append(addr_line)
                        print(f"✓ Found address line: {addr_line}")
        
        # Parse address lines
        if len(address_lines) >= 1:
            # Try to identify region, subcity, woreda
            for line in address_lines:
                line_upper = line.upper()
                # Common Ethiopian regions
                if any(region in line_upper for region in ['OROMIA', 'AMHARA', 'TIGRAY', 'ADDIS', 'DIRE', 'SOMALI', 'AFAR', 'BENISHANGUL', 'GAMBELA', 'HARARI', 'SIDAMA', 'SOUTHERN']):
                    if not data['region']:
                        data['region'] = line
                        print(f"✓ Identified region: {line}")
                # Common subcities/zones
                elif any(sub in line_upper for sub in ['WEST', 'EAST', 'NORTH', 'SOUTH', 'TOWN', 'CITY', 'ZONE', 'KIFLE', 'ክፍለ']):
                    if not data['subcity']:
                        data['subcity'] = line
                        print(f"✓ Identified subcity: {line}")
                # Woreda indicators
                elif 'WOREDA' in line_upper or 'KEBELE' in line_upper or 'ወረዳ' in line:
                    if not data['woreda']:
                        data['woreda'] = line
                        print(f"✓ Identified woreda: {line}")
            
            # If not identified, use first lines
            if not data['region'] and len(address_lines) > 0:
                data['region'] = address_lines[0]
                print(f"✓ Using first line as region: {address_lines[0]}")
            if not data['subcity'] and len(address_lines) > 2:
                data['subcity'] = address_lines[2]
                print(f"✓ Using third line as subcity: {address_lines[2]}")
            if not data['woreda'] and len(address_lines) > 4:
                data['woreda'] = address_lines[4]
                print(f"✓ Using fifth line as woreda: {address_lines[4]}")
            
            # Combine for full address
            address_parts = [p for p in [data['region'], data['subcity'], data['woreda']] if p]
            data['address_en'] = ', '.join(address_parts)
            if len(address_lines) > 1:
                data['address_am'] = address_lines[1]
        
        print(f"📊 Extraction summary: {sum(1 for v in data.values() if v)} / {len(data)} fields extracted")
        return data
    
    def extract_all_data(self, front_image_path: str, back_image_path: str, 
                        photo_output_path: str) -> Dict:
        """Extract all data from front and back ID cards using region-based extraction only"""
        result = {
            'photo_path': None,
            'front_data': {},
            'back_data': {},
            'combined_data': {}
        }
        
        # Extract photo from front
        if front_image_path and os.path.exists(front_image_path):
            photo_path = self.extract_photo_from_front(front_image_path, photo_output_path)
            result['photo_path'] = photo_path
            
            # Use region-based extraction only (faster and more accurate)
            print("🎯 Using region-based extraction for front card...")
            result['front_data'] = self.parse_front_card_data("", image_path=front_image_path)
        
        # Extract text from back using region-based extraction
        if back_image_path and os.path.exists(back_image_path):
            print("🎯 Using region-based extraction for back card...")
            result['back_data'] = self.parse_back_card_data("", image_path=back_image_path)
        
        # Combine all data
        result['combined_data'] = {
            **result['front_data'],
            **result['back_data']
        }
        
        return result
