"""
OCR Extraction Service for Ethiopian Digital ID Cards - OPTIMIZED VERSION
Extracts data from front and back ID card images with parallel processing and caching
"""

import cv2
import numpy as np
from PIL import Image
import pytesseract
import re
from typing import Dict, Optional, Tuple, List
import os
from functools import lru_cache
from concurrent.futures import ThreadPoolExecutor, as_completed
import hashlib
import time

class OCRExtractionServiceOptimized:
    def __init__(self, enable_debug=False, max_workers=4):
        """Initialize OCR service with optimization settings
        
        Args:
            enable_debug: Enable debug image saving (disable in production)
            max_workers: Number of parallel workers for region extraction
        """
        self.tesseract_config = '--oem 3 --psm 6'
        self.enable_debug = enable_debug
        self.max_workers = max_workers
        self._image_cache = {}
        
    def _get_image_hash(self, image_path: str) -> str:
        """Generate hash for image caching"""
        with open(image_path, 'rb') as f:
            return hashlib.md5(f.read()).hexdigest()
    
    @lru_cache(maxsize=32)
    def _load_and_preprocess_image(self, image_path: str, image_hash: str) -> Tuple[np.ndarray, int, int]:
        """Load image once and cache it
        
        Returns: (image, width, height)
        """
        img = cv2.imread(image_path)
        if img is None:
            raise ValueError(f"Could not read image: {image_path}")
        height, width = img.shape[:2]
        return img, width, height
    
    def _extract_single_region(self, args: Tuple) -> Tuple[str, str]:
        """Extract text from a single region (for parallel processing)
        
        Args:
            args: Tuple of (region_name, img, x1_px, y1_px, x2_px, y2_px, region_type)
        
        Returns: (region_name, extracted_text)
        """
        region_name, img, x1_px, y1_px, x2_px, y2_px, region_type = args
        
        try:
            # Extract region
            region_img = img[y1_px:y2_px, x1_px:x2_px]
            
            # Convert to grayscale
            gray = cv2.cvtColor(region_img, cv2.COLOR_BGR2GRAY)
            
            # Adaptive scaling based on region type
            if region_type == 'number':
                scale = 2.5
            elif region_type == 'amharic':
                scale = 3.0
            elif region_type == 'date':
                scale = 2.5
            else:  # text
                scale = 2.0
            
            gray = cv2.resize(gray, None, fx=scale, fy=scale, interpolation=cv2.INTER_CUBIC)
            
            # Optimized preprocessing based on region type
            if region_type == 'number':
                # Fast preprocessing for numbers
                clahe = cv2.createCLAHE(clipLimit=3.0, tileGridSize=(8,8))
                enhanced = clahe.apply(gray)
                _, thresh = cv2.threshold(enhanced, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
                config = '--oem 3 --psm 7 -c tessedit_char_whitelist=0123456789'
                text = pytesseract.image_to_string(thresh, lang='eng', config=config)
            
            elif region_type == 'date':
                clahe = cv2.createCLAHE(clipLimit=3.0, tileGridSize=(8,8))
                enhanced = clahe.apply(gray)
                _, thresh = cv2.threshold(enhanced, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
                config = '--oem 3 --psm 7'
                
                if 'ethiopian' in region_name or '_am' in region_name:
                    text = pytesseract.image_to_string(thresh, lang='amh+eng', config=config)
                else:
                    text = pytesseract.image_to_string(thresh, lang='eng', config=config)
            
            elif region_type == 'sex':
                clahe = cv2.createCLAHE(clipLimit=3.0, tileGridSize=(8,8))
                enhanced = clahe.apply(gray)
                _, thresh = cv2.threshold(enhanced, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
                config = '--oem 3 --psm 8'
                
                if '_am' in region_name:
                    text = pytesseract.image_to_string(thresh, lang='amh', config=config)
                else:
                    text = pytesseract.image_to_string(thresh, lang='eng+amh', config=config)
            
            elif region_type == 'amharic':
                bilateral = cv2.bilateralFilter(gray, 9, 75, 75)
                _, thresh = cv2.threshold(bilateral, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
                
                # Save debug image only if enabled
                if self.enable_debug:
                    debug_path = f'app/static/debug_regions/{region_name}.png'
                    os.makedirs(os.path.dirname(debug_path), exist_ok=True)
                    cv2.imwrite(debug_path, thresh)
                
                if region_name in ['region_am', 'subcity_am', 'woreda_am']:
                    config = '--oem 3 --psm 6'
                else:
                    config = '--oem 3 --psm 7'
                
                text = pytesseract.image_to_string(thresh, lang='eng+amh', config=config)
            
            else:  # text (English)
                bilateral = cv2.bilateralFilter(gray, 9, 75, 75)
                _, thresh = cv2.threshold(bilateral, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
                
                if region_name in ['region_en', 'subcity_en', 'woreda_en']:
                    config = '--oem 3 --psm 6'
                else:
                    config = '--oem 3 --psm 7'
                
                if '_am' in region_name or 'full_name_am' in region_name:
                    text = pytesseract.image_to_string(thresh, lang='amh+eng', config=config)
                else:
                    text = pytesseract.image_to_string(thresh, lang='eng+amh', config=config)
            
            return (region_name, text.strip())
        
        except Exception as e:
            print(f"❌ Error extracting {region_name}: {e}")
            return (region_name, "")

    
    def extract_text_regions_parallel(self, image_path: str, card_side: str = 'front') -> Dict:
        """Extract text from specific regions using parallel processing
        
        Args:
            image_path: Path to the ID card image
            card_side: 'front' or 'back'
        
        Returns: Dictionary of extracted text by region name
        """
        start_time = time.time()
        
        try:
            # Load and cache image
            image_hash = self._get_image_hash(image_path)
            img, width, height = self._load_and_preprocess_image(image_path, image_hash)
            
            print(f"📐 Image dimensions: {width}x{height}")
            
            # Reference dimensions
            ref_width = 900
            ref_height = 1441
            
            # Define regions based on card side
            if card_side == 'front':
                regions_config = {
                    'full_name_am': ((89/ref_width, 834/ref_height, 792/ref_width, 885/ref_height), 'text', 5, 2),
                    'full_name_en': ((95/ref_width, 882/ref_height, 792/ref_width, 927/ref_height), 'text', 5, 2),
                    'dob_ethiopian': ((93/ref_width, 964/ref_height, 292/ref_width, 1017/ref_height), 'date', 0, 0),
                    'sex_am': ((103/ref_width, 1034/ref_height, 190/ref_width, 1075/ref_height), 'sex', 0, 0),
                    'expiry_ethiopian': ((99/ref_width, 1118/ref_height, 288/ref_width, 1169/ref_height), 'date', 0, 0),
                    'fan_number': ((225/ref_width, 1198/ref_height, 648/ref_width, 1237/ref_height), 'number', 0, 0),
                }
            else:  # back
                regions_config = {
                    'phone_number': ((69/ref_width, 960/ref_height, 354/ref_width, 1005/ref_height), 'number', 0, 0),
                    'fin_number': ((567/ref_width, 934/ref_height, 846/ref_width, 989/ref_height), 'number', 0, 0),
                    'nationality_am': ((69/ref_width, 1060/ref_height, 206/ref_width, 1107/ref_height), 'amharic', 0, 0),
                    'nationality_en': ((217/ref_width, 1060/ref_height, 498/ref_width, 1113/ref_height), 'text', 0, 0),
                    'region_am': ((63/ref_width, 1144/ref_height, 810/ref_width, 1185/ref_height), 'amharic', 0, 0),
                    'region_en': ((63/ref_width, 1186/ref_height, 810/ref_width, 1227/ref_height), 'text', 0, 0),
                    'subcity_am': ((63/ref_width, 1228/ref_height, 810/ref_width, 1269/ref_height), 'amharic', 0, 0),
                    'subcity_en': ((63/ref_width, 1266/ref_height, 810/ref_width, 1307/ref_height), 'text', 0, 0),
                    'woreda_am': ((63/ref_width, 1310/ref_height, 810/ref_width, 1351/ref_height), 'amharic', 0, 0),
                    'woreda_en': ((63/ref_width, 1350/ref_height, 810/ref_width, 1391/ref_height), 'text', 0, 0),
                }
            
            # Prepare extraction tasks
            tasks = []
            for region_name, (coords, region_type, padding_x, padding_y) in regions_config.items():
                x1, y1, x2, y2 = coords
                
                # Convert percentages to pixels
                x1_px = int(x1 * width)
                y1_px = int(y1 * height)
                x2_px = int(x2 * width)
                y2_px = int(y2 * height)
                
                # Apply padding
                if padding_x > 0 or padding_y > 0:
                    x1_px = max(0, x1_px - padding_x)
                    y1_px = max(0, y1_px - padding_y)
                    x2_px = min(width, x2_px + padding_x)
                    y2_px = min(height, y2_px + padding_y)
                
                tasks.append((region_name, img, x1_px, y1_px, x2_px, y2_px, region_type))
            
            # Extract regions in parallel
            extracted_regions = {}
            with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
                futures = {executor.submit(self._extract_single_region, task): task[0] for task in tasks}
                
                for future in as_completed(futures):
                    region_name, text = future.result()
                    extracted_regions[region_name] = text
                    if text:
                        print(f"✓ {region_name}: {text[:80]}")
            
            elapsed = time.time() - start_time
            print(f"⚡ Parallel extraction completed in {elapsed:.2f}s ({len(extracted_regions)} regions)")
            
            return extracted_regions
            
        except Exception as e:
            print(f"❌ Error in parallel extraction: {e}")
            import traceback
            traceback.print_exc()
            return {}
    
    def extract_photo_from_front(self, image_path: str, output_path: str) -> Optional[str]:
        """Extract profile photo from front ID card"""
        try:
            img = cv2.imread(image_path)
            height, width = img.shape[:2]
            
            # Photo region coordinates
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
    
    def parse_front_card_data(self, image_path: str) -> Dict:
        """Parse front card data using optimized region extraction"""
        data = {
            'full_name_en': '',
            'full_name_am': '',
            'date_of_birth': '',
            'date_of_birth_am': '',
            'date_of_birth_en': '',
            'sex': '',
            'sex_am': '',
            'sex_en': '',
            'date_of_expiry': '',
            'date_of_expiry_am': '',
            'date_of_expiry_en': '',
            'date_of_issue': '',
            'date_of_issue_am': '',
            'date_of_issue_en': '',
            'fan': '',
            'barcode': ''
        }
        
        print("🎯 Using optimized parallel region extraction for front card...")
        regions = self.extract_text_regions_parallel(image_path, card_side='front')
        
        if not regions:
            print("⚠️ No regions extracted")
            return data
        
        # Extract and clean names
        if 'full_name_am' in regions and regions['full_name_am']:
            name_am = regions['full_name_am'].strip()
            name_am_clean = ''.join(c for c in name_am if '\u1200' <= c <= '\u137F' or c.isspace())
            name_am_clean = ' '.join(name_am_clean.split())
            if len(name_am_clean) >= 3:
                data['full_name_am'] = name_am_clean
        
        if 'full_name_en' in regions and regions['full_name_en']:
            name_en = regions['full_name_en'].strip()
            name_en_clean = ''.join(c for c in name_en if c.isascii() and (c.isalpha() or c.isspace()))
            name_en_clean = ' '.join(name_en_clean.split())
            if len(name_en_clean) >= 3:
                data['full_name_en'] = name_en_clean
        
        # Extract DOB (Ethiopian only, calculate Gregorian if needed)
        if 'dob_ethiopian' in regions and regions['dob_ethiopian']:
            dob_eth = regions['dob_ethiopian'].strip()
            ethiopian_match = re.search(r'(\d{2}/\d{2}/\d{4})', dob_eth)
            if ethiopian_match:
                data['date_of_birth_am'] = ethiopian_match.group(1)
                data['date_of_birth'] = ethiopian_match.group(1)
        
        # Extract sex (Amharic only, translate to English)
        if 'sex_am' in regions and regions['sex_am']:
            sex_am = regions['sex_am'].strip()
            
            # OCR corrections
            sex_ocr_corrections = {
                '"ATE': 'ሴት', 'ATE': 'ሴት', 'SET': 'ሴት', 'SEET': 'ሴት',
                'WND': 'ወንድ', 'WEND': 'ወንድ',
            }
            
            for wrong, correct in sex_ocr_corrections.items():
                if wrong in sex_am:
                    sex_am = sex_am.replace(wrong, correct)
            
            if 'ወንድ' in sex_am or 'ወ/ድ' in sex_am:
                data['sex'] = 'Male'
                data['sex_am'] = 'ወንድ'
                data['sex_en'] = 'Male'
            elif 'ሴት' in sex_am:
                data['sex'] = 'Female'
                data['sex_am'] = 'ሴት'
                data['sex_en'] = 'Female'
        
        # Extract expiry (Ethiopian only)
        if 'expiry_ethiopian' in regions and regions['expiry_ethiopian']:
            expiry_eth = regions['expiry_ethiopian'].strip()
            ethiopian_match = re.search(r'(\d{2}/\d{2}/\d{4})', expiry_eth)
            if ethiopian_match:
                data['date_of_expiry_am'] = ethiopian_match.group(1)
                data['date_of_expiry'] = ethiopian_match.group(1)
        
        # Extract FAN number
        if 'fan_number' in regions and regions['fan_number']:
            fan_text = regions['fan_number'].replace(' ', '').replace('-', '')
            fan_match = re.search(r'(\d{15,17})', fan_text)
            if fan_match:
                fan_num = fan_match.group(1)
                data['fan'] = fan_num[:16] if len(fan_num) >= 16 else fan_num[:15]
                data['barcode'] = data['fan']
        
        # Use today's date for issue date (optimization: no extraction needed)
        from datetime import datetime
        today = datetime.now()
        data['date_of_issue'] = today.strftime('%Y/%m/%d')
        data['date_of_issue_en'] = data['date_of_issue']
        
        print(f"📊 Extracted {sum(1 for v in data.values() if v)}/{len(data)} fields")
        return data
    
    def parse_back_card_data(self, image_path: str) -> Dict:
        """Parse back card data using optimized region extraction"""
        data = {
            'phone_number': '',
            'nationality_en': '',
            'nationality_am': '',
            'region_en': '',
            'region_am': '',
            'subcity_en': '',
            'subcity_am': '',
            'woreda_en': '',
            'woreda_am': '',
            'fin': ''
        }
        
        print("🎯 Using optimized parallel region extraction for back card...")
        regions = self.extract_text_regions_parallel(image_path, card_side='back')
        
        if not regions:
            print("⚠️ No regions extracted")
            return data
        
        # Extract phone number
        if 'phone_number' in regions and regions['phone_number']:
            phone_text = regions['phone_number'].replace(' ', '').replace('-', '').replace('|', '')
            phone_text = phone_text.replace('Phone', '').replace('Number', '').replace('ስልክ', '').strip()
            phone_match = re.search(r'(0\d{9})', phone_text)
            if phone_match:
                data['phone_number'] = phone_match.group(1)
        
        # Extract FIN number
        if 'fin_number' in regions and regions['fin_number']:
            fin_text = regions['fin_number'].replace(' ', '').replace('-', '').replace('|', '')
            fin_text = fin_text.replace('FIN', '').replace('ሀረፍ', '').strip()
            fin_match = re.search(r'(\d{12,15})', fin_text)
            if fin_match:
                data['fin'] = fin_match.group(1)[:12]
        
        # Extract nationality
        if 'nationality_am' in regions and regions['nationality_am']:
            nat_am_text = regions['nationality_am'].strip()
            ocr_corrections = {
                'ATP RE': 'ኢትዮጵያ', 'ATPRE': 'ኢትዮጵያ', 'ETHIOP': 'ኢትዮጵያ',
            }
            for wrong, correct in ocr_corrections.items():
                if wrong in nat_am_text:
                    nat_am_text = nat_am_text.replace(wrong, correct)
            
            nat_am_text = nat_am_text.replace('ዜግነት', '').replace('|', '').strip()
            if 'ኢትዮጵያ' in nat_am_text or 'አትዮጵያ' in nat_am_text:
                data['nationality_am'] = 'ኢትዮጵያዊ'
        
        if 'nationality_en' in regions and regions['nationality_en']:
            nat_en_text = regions['nationality_en'].strip()
            nat_en_text = nat_en_text.replace('Nationality', '').replace('|', '').strip()
            if 'ethiopian' in nat_en_text.lower() or 'ethio' in nat_en_text.lower():
                data['nationality_en'] = 'Ethiopian'
        
        # Extract address components with OCR corrections
        if 'region_am' in regions and regions['region_am']:
            region_am_text = regions['region_am'].strip()
            ocr_corrections = {
                'አዲስ ANA': 'አዲስ አበባ', 'አዲስ ANN': 'አዲስ አበባ', 'አዲስ ABA': 'አዲስ አበባ',
                'አዲስ ABABA': 'አዲስ አበባ', 'አዲስ Ababa': 'አዲስ አበባ',
                ' HAA': ' ክልል', ' KAA': ' ክልል', ' KLIL': ' ክልል', ' Klil': ' ክልል',
            }
            for wrong, correct in ocr_corrections.items():
                if wrong in region_am_text:
                    region_am_text = region_am_text.replace(wrong, correct)
            
            region_am_clean = ''.join(c for c in region_am_text if '\u1200' <= c <= '\u137F' or c.isspace())
            region_am_clean = ' '.join(region_am_clean.split())
            if len(region_am_clean) >= 2:
                data['region_am'] = region_am_clean
        
        if 'region_en' in regions and regions['region_en']:
            region_en_text = regions['region_en'].strip()
            region_en_text = ''.join(c for c in region_en_text if c.isascii() and (c.isalpha() or c.isspace()))
            region_en_text = ' '.join(region_en_text.split())
            if len(region_en_text) >= 3:
                data['region_en'] = region_en_text
        
        # Extract subcity
        if 'subcity_am' in regions and regions['subcity_am']:
            subcity_am_text = regions['subcity_am'].strip()
            subcity_am_clean = ''.join(c for c in subcity_am_text if '\u1200' <= c <= '\u137F' or c.isspace())
            subcity_am_clean = ' '.join(subcity_am_clean.split())
            if len(subcity_am_clean) >= 2:
                data['subcity_am'] = subcity_am_clean
        
        if 'subcity_en' in regions and regions['subcity_en']:
            subcity_en_text = regions['subcity_en'].strip()
            subcity_en_text = ''.join(c for c in subcity_en_text if c.isascii() and (c.isalpha() or c.isspace()))
            subcity_en_text = ' '.join(subcity_en_text.split())
            if len(subcity_en_text) >= 2:
                data['subcity_en'] = subcity_en_text
        
        # Extract woreda
        if 'woreda_am' in regions and regions['woreda_am']:
            woreda_am_text = regions['woreda_am'].strip()
            woreda_am_clean = ''.join(c for c in woreda_am_text if '\u1200' <= c <= '\u137F' or c.isspace() or c.isdigit())
            woreda_am_clean = ' '.join(woreda_am_clean.split())
            if len(woreda_am_clean) >= 1:
                data['woreda_am'] = woreda_am_clean
        
        if 'woreda_en' in regions and regions['woreda_en']:
            woreda_en_text = regions['woreda_en'].strip()
            woreda_en_text = ''.join(c for c in woreda_en_text if c.isascii() and (c.isalnum() or c.isspace()))
            woreda_en_text = ' '.join(woreda_en_text.split())
            if len(woreda_en_text) >= 1:
                data['woreda_en'] = woreda_en_text
        
        print(f"📊 Extracted {sum(1 for v in data.values() if v)}/{len(data)} fields")
        return data
    
    def extract_all_data(self, front_image_path: str, back_image_path: str, 
                        photo_output_path: str) -> Dict:
        """Extract all data from front and back ID cards using optimized parallel extraction
        
        Returns: Dictionary with photo_path, front_data, back_data, and combined_data
        """
        start_time = time.time()
        
        result = {
            'photo_path': None,
            'front_data': {},
            'back_data': {},
            'combined_data': {}
        }
        
        # Extract photo from front (fast operation, no parallelization needed)
        if front_image_path and os.path.exists(front_image_path):
            photo_path = self.extract_photo_from_front(front_image_path, photo_output_path)
            result['photo_path'] = photo_path
            
            # Extract front card data
            result['front_data'] = self.parse_front_card_data(front_image_path)
        
        # Extract back card data
        if back_image_path and os.path.exists(back_image_path):
            result['back_data'] = self.parse_back_card_data(back_image_path)
        
        # Combine all data
        result['combined_data'] = {
            **result['front_data'],
            **result['back_data']
        }
        
        elapsed = time.time() - start_time
        print(f"⚡ Total extraction completed in {elapsed:.2f}s")
        
        return result
    
    def clear_cache(self):
        """Clear image cache to free memory"""
        self._load_and_preprocess_image.cache_clear()
        self._image_cache.clear()
        print("🧹 Cache cleared")
