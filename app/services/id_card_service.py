from PIL import Image, ImageDraw, ImageFont
import json
import os
import barcode
from barcode.writer import ImageWriter
from typing import Dict, Optional, Tuple, List
import random
import fitz # PyMuPDF
from datetime import datetime, date # Needed for dob parsing in new logic
from dateutil.relativedelta import relativedelta # Added for date calculations

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
        'residential_addis': {
            'photo_img_index': 0, # Based on user's snippet for residential
            'qr_img_index': 1 # Based on user's snippet for residential
        },
        'residential_sheger': {
            'photo_img_index': 0, # Based on user's snippet for residential
            'qr_img_index': 1 # Based on user's snippet for residential
        }
    }

    def __init__(self):
        self.config = Config()
        
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
            line = lines[index].strip()
            if '|' in line:
                amharic, english = line.split('|', 1)
                return amharic.strip(), english.strip()
            return line, line # Return same for both if no pipe
        except IndexError:
            return "", ""

    def _extract_default_pdf_data(self, doc: fitz.Document, lines: List[str], images: List[Tuple], fin_number: str) -> Dict:
        """Extract data from default PDF format."""
        line_indices = self.PDF_FORMAT_MAPPING['default']
        
        # Ensure lines are padded for safe access
        max_index = max(line_indices.values())
        if len(lines) <= max_index:
            lines += [""] * (max_index + 1 - len(lines))

        # Extract FCN and validate
        fcn_raw = lines[line_indices['fcn']].strip()
        fcn = ''.join(filter(str.isdigit, fcn_raw))
        if len(fcn) != self.config.FCN_LENGTH:
            raise ValueError(f"Invalid FCN number. Must be {self.config.FCN_LENGTH} digits. Extracted: '{fcn_raw}' -> '{fcn}' (Length: {len(fcn)})")

        # Extract other fields
        name_am, name_en = self._parse_line(lines, line_indices['name'])
        dob_am, dob_en_raw = self._parse_line(lines, line_indices['dob'])
        gender_am, gender_en = self._parse_line(lines, line_indices['gender'])
        nationality_am, nationality_en = self._parse_line(lines, line_indices['nationality'])
        phone_raw, _ = self._parse_line(lines, line_indices['phone'])
        phone = self.format_phone_number(phone_raw)
        region_am, region_en = self._parse_line(lines, line_indices['region'])
        subcity_am, subcity_en = self._parse_line(lines, line_indices['subcity'])
        woreda_am, woreda_en = self._parse_line(lines, line_indices['woreda'])

        # Parse DOB to desired format
        dob_en = ""
        try:
            dob_en = datetime.strptime(dob_en_raw, "%Y/%m/%d").strftime("%Y/%b/%d")
        except ValueError:
            dob_en = dob_en_raw # Fallback if parsing fails

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

        if len(images) > photo_idx:
            photo_bytes = doc.extract_image(images[photo_idx][0])['image']
            with open(os.path.join(self.config.STATIC_FOLDER, 'photo_temp.png'), 'wb') as f:
                f.write(photo_bytes)
            extracted_data["photo"] = 'static/photo_temp.png' 
                
        if len(images) > qr_idx:
            qr_bytes = doc.extract_image(images[qr_idx][0])['image']
            with open(os.path.join(self.config.STATIC_FOLDER, 'qr_temp.png'), 'wb') as f:
                f.write(qr_bytes)
            extracted_data["qr_path"] = 'static/qr_temp.png' 

        return extracted_data

    def _extract_residential_addis_pdf_data(self, doc: fitz.Document, lines: List[str], images: List[Tuple], fin_number: str) -> Dict:
        """Extract data from Residential Addis PDF format using pattern matching."""
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
            if line_cleaned.isdigit() and len(line_cleaned) == self.config.FCN_LENGTH:
                extracted["fcn"] = ' '.join([line_cleaned[j:j+4] for j in range(0, len(line_cleaned), 4)])
            elif "/" in line and any(char.isdigit() for char in line):  # Date detection
                if extracted["dob_greg"] == "":
                    extracted["dob_greg"] = line
                else:
                    extracted["dob_eth"] = line
            elif line.strip() in ["ሴት", "ወንድ", "Female", "Male"]:
                if any('\u1200' <= c <= '\u137F' for c in line):
                    extracted["gender_am"] = line.strip()
                    if i+1 < len(lines) and lines[i+1].lower() in ["male", "female"]:
                        extracted["gender_en"] = lines[i+1].strip()
                else:
                    extracted["gender_en"] = line.strip()
                    if i > 0 and lines[i-1].strip() in ["ሴት", "ወንድ"]:
                        extracted["gender_am"] = lines[i-1].strip()
            elif line.strip() in ["ኢትዮጵያ", "ኢትዮጵያዊ", "Ethiopia", "Ethiopian"]:
                if any('\u1200' <= c <= '\u137F' for c in line):
                    extracted["nationality_am"] = line.strip()
                    if i+1 < len(lines) and lines[i+1].strip() in ["Ethiopia", "Ethiopian"]:
                        extracted["nationality_en"] = lines[i+1].strip()
                else:
                    extracted["nationality_en"] = line.strip()
                    if i > 0 and any('\u1200' <= c <= '\u137F' for c in lines[i-1]):
                        extracted["nationality_am"] = lines[i-1].strip()
            elif line_cleaned.isdigit() and len(line_cleaned) == 10 and line_cleaned.startswith('0'):
                extracted["phone"] = line.strip()
            elif line.strip() in ["አዲስ አበባ", "Addis Ababa"]:
                extracted["region_am"] = line.strip()
                extracted["region_en"] = lines[i+1].strip() if i+1 < len(lines) else ""
            elif "ወረዳ" in line or "Woreda" in line:
                if "ወረዳ" in line:
                    extracted["woreda_am"] = line.strip()
                    if i+1 < len(lines) and "Woreda" in lines[i+1]:
                        extracted["woreda_en"] = lines[i+1].strip()
                elif "Woreda" in line:
                    extracted["woreda_en"] = line.strip()
                    if i > 0 and "ወረዳ" in lines[i-1]:
                        extracted["woreda_am"] = lines[i-1].strip()

        # Special handling for subcity (after the main loop)
        region_index = -1
        for i, line in enumerate(lines):
            if line.strip() in ["አዲስ አበባ", "Addis Ababa"]:
                region_index = i
                break

        if region_index != -1:
            if region_index + 2 < len(lines):
                extracted["subcity_am"] = lines[region_index + 2].strip()
            if region_index + 3 < len(lines):
                extracted["subcity_en"] = lines[region_index + 3].strip()

        # Fallback for nationality if not found
        if not extracted["nationality_am"] and extracted["nationality_en"]:
            extracted["nationality_am"] = "ኢትዮጵያ"
        elif not extracted["nationality_en"] and extracted["nationality_am"]:
            extracted["nationality_en"] = "Ethiopia"

        # Find name - usually appears near the end
        for i in range(len(lines)-1, -1, -1):
            if " " in lines[i] and not any(c.isdigit() for c in lines[i]) and "/" not in lines[i]:
                extracted["name_en"] = lines[i].strip()
                if i > 0:
                    extracted["name_am"] = lines[i-1].strip()
                break

        # Parse dates
        dob_greg = extracted["dob_greg"]
        if extracted["dob_greg"] and not extracted["dob_greg"].startswith("000"):
            try:
                dob_greg_obj = datetime.strptime(extracted["dob_greg"], "%d/%m/%Y")
                dob_greg = dob_greg_obj.strftime("%Y/%b/%d")
            except ValueError:
                try:
                    dob_greg_obj = datetime.strptime(extracted["dob_greg"], "%Y/%m/%d")
                    dob_greg = dob_greg_obj.strftime("%Y/%b/%d")
                except ValueError:
                    pass

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
            "fin": fin_number,
            "serial_number": self.generate_serial_number(),
        }

        # Extract images
        photo_idx = self.PDF_FORMAT_MAPPING['residential_addis']['photo_img_index']
        qr_idx = self.PDF_FORMAT_MAPPING['residential_addis']['qr_img_index']

        if len(images) > photo_idx:
            photo_bytes = doc.extract_image(images[photo_idx][0])['image']
            with open(os.path.join(self.config.STATIC_FOLDER, 'photo_temp.png'), 'wb') as f:
                f.write(photo_bytes)
            processed_data["photo"] = 'static/photo_temp.png'

        if len(images) > qr_idx:
            qr_bytes = doc.extract_image(images[qr_idx][0])['image']
            with open(os.path.join(self.config.STATIC_FOLDER, 'qr_temp.png'), 'wb') as f:
                f.write(qr_bytes)
            processed_data["qr_path"] = 'static/qr_temp.png'

        return processed_data

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
            if line_cleaned.isdigit() and len(line_cleaned) == self.config.FCN_LENGTH:
                extracted["fcn"] = ' '.join([line_cleaned[j:j+4] for j in range(0, len(line_cleaned), 4)])
            elif "/" in line and any(char.isdigit() for char in line):  # Date detection
                if extracted["dob_greg"] == "":
                    extracted["dob_greg"] = line
                else:
                    extracted["dob_eth"] = line
            elif line.strip() in ["ሴት", "ወንድ"]:
                extracted["gender_am"] = line.strip()
                if i+1 < len(lines) and lines[i+1].strip() in ["Female", "Male"]:
                    extracted["gender_en"] = lines[i+1].strip()
            elif line.strip() in ["ኢትዮጵያዊ", "ኢትዮጵያ"]:  # Fix: Added "ኢትዮጵያ" as possible Amharic value
                extracted["nationality_am"] = line.strip()
                # Look for English nationality in next few lines
                for j in range(i+1, min(i+4, len(lines))):
                    if lines[j].strip() in ["Ethiopian", "Ethiopia"]:  # Fix: Added "Ethiopia" as possible English value
                        extracted["nationality_en"] = "Ethiopian"  # Fix: Always set to "Ethiopian"
                        break
            elif line.replace(" ", "").isdigit() and len(line.replace(" ", "")) == 10:
                extracted["phone"] = line.strip()

        # If nationality is still not set but we found Amharic, set default English
        if extracted["nationality_am"] and not extracted["nationality_en"]:
            extracted["nationality_en"] = "Ethiopian"
        # If we found neither, but we know this is an Ethiopian ID
        if not extracted["nationality_am"] and not extracted["nationality_en"]:
            extracted["nationality_am"] = "ኢትዮጵያዊ"
            extracted["nationality_en"] = "Ethiopian"

        # Improved address field extraction
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

        # Process collected address fields
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

        # Find name - usually appears near the end
        for i in range(len(lines)-1, -1, -1):
            if " " in lines[i] and not any(c.isdigit() for c in lines[i]) and "/" not in lines[i]:
                extracted["name_en"] = lines[i].strip()
                if i > 0:
                    extracted["name_am"] = lines[i-1].strip()
                break

        # Parse dates
        dob_greg = extracted["dob_greg"]
        if extracted["dob_greg"] and not extracted["dob_greg"].startswith("000"):
            try:
                dob_greg_obj = datetime.strptime(extracted["dob_greg"], "%d/%m/%Y")
                dob_greg = dob_greg_obj.strftime("%Y/%b/%d")
            except ValueError:
                try:
                    dob_greg_obj = datetime.strptime(extracted["dob_greg"], "%Y/%m/%d")
                    dob_greg = dob_greg_obj.strftime("%Y/%b/%d")
                except ValueError:
                    pass

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
            "fin": fin_number,
            "serial_number": self.generate_serial_number(),
        }

        # Extract images
        photo_idx = self.PDF_FORMAT_MAPPING['residential_sheger']['photo_img_index']
        qr_idx = self.PDF_FORMAT_MAPPING['residential_sheger']['qr_img_index']

        if len(images) > photo_idx:
            photo_bytes = doc.extract_image(images[photo_idx][0])['image']
            with open(os.path.join(self.config.STATIC_FOLDER, 'photo_temp.png'), 'wb') as f:
                f.write(photo_bytes)
            processed_data["photo"] = 'static/photo_temp.png'

        if len(images) > qr_idx:
            qr_bytes = doc.extract_image(images[qr_idx][0])['image']
            with open(os.path.join(self.config.STATIC_FOLDER, 'qr_temp.png'), 'wb') as f:
                f.write(qr_bytes)
            processed_data["qr_path"] = 'static/qr_temp.png'

        return processed_data

    def extract_pdf_data(self, pdf_input, fin_number: str, pdf_format: str = 'default') -> Dict:
        """Extract data from PDF file or stream based on format."""
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
            if pdf_format == 'default':
                extracted_data = self._extract_default_pdf_data(doc, lines, images, fin_number)
            elif pdf_format == 'residential_addis':
                extracted_data = self._extract_residential_addis_pdf_data(doc, lines, images, fin_number)
            elif pdf_format == 'residential_sheger':
                extracted_data = self._extract_residential_sheger_pdf_data(doc, lines, images, fin_number)
            else:
                raise ValueError(f"Unknown PDF format: {pdf_format}")

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

    def generate_id_card(self, data: Dict, city_option: str = 'default', remove_white: bool = False, remove_black: bool = False) -> Dict[str, str]:
        """Generate ID card images."""
        try:
            # Get address positions for selected city type
            address_positions = self.config.ADDRESS_POSITIONS.get(city_option, self.config.ADDRESS_POSITIONS['default'])
            
            # Get the person's name for filenames
            name = data.get('name_en', '').replace(' ', '_')
            
            # === Generate Front Side ===
            template = Image.open(self.config.TEMPLATE_IMG).convert("RGBA")
            draw = ImageDraw.Draw(template)
            
            # Load template configuration
            with open(self.config.TEMPLATE_JSON, encoding='utf-8') as f:
                template_json = json.load(f)
            
            # Process non-address fields
            for field in template_json['fields']:
                key = field.get("key")
                if key in address_positions['front']:
                    continue
                    
                content = data.get(key, field.get("label", ""))
                pos = tuple(field["position"])
                color = tuple(field.get("color", (0, 0, 0)))
                align = field.get("align", "left")
                font_spec = field["font"]
                
                # Choose font based on language
                if key.endswith('_am'):
                    font = ImageFont.truetype(self.config.AMHARIC_FONT_PATH, font_spec["size"])
                else:
                    font = ImageFont.truetype(self.config.ENGLISH_FONT_PATH, font_spec["size"])
                
                if key in ["issue_date_am", "issue_date_en"]:
                    rotated_img, pos = draw_rotated_text(draw, content, pos, font, color)
                    template.paste(rotated_img, pos, rotated_img)
                else:
                    max_width = field.get("wrap_width")
                    draw_text_with_alignment(draw, content, pos, font, color, align, max_width)
            
            # Handle address fields
            font_am = ImageFont.truetype(self.config.AMHARIC_FONT_PATH, 48)
            font_en = ImageFont.truetype(self.config.ENGLISH_FONT_PATH, 50)
            
            for key, pos in address_positions['front'].items():
                content = data.get(key, '')
                font = font_am if key.endswith('_am') else font_en
                max_width = self.config.TEXT_MAX_WIDTH['front'].get(key, None)
                draw_text_with_alignment(draw, content, tuple(pos), font, (0, 0, 0), "left", max_width)
            
            # Process photos
            photo_path = os.path.join(self.config.STATIC_FOLDER, 'photo_temp.png')
            if os.path.exists(photo_path):
                # Large photo
                large_photo = process_photo(photo_path, self.config.PHOTO_SIZES['large'], remove_white, remove_black)
                template.paste(large_photo, (128, 250), large_photo)
                
                # Small photo
                small_photo = process_photo(photo_path, self.config.PHOTO_SIZES['small'], remove_white, remove_black)
                template.paste(small_photo, (1493, 860), small_photo)
            
            # Process QR code
            qr_path = os.path.join(self.config.STATIC_FOLDER, 'qr_temp.png')
            if os.path.exists(qr_path):
                qr_img = Image.open(qr_path).resize((934, 937))
                template.paste(qr_img, (2875, 90))
            
            # Process barcode
            barcode_path = data.get('fcn_barcode')
            if barcode_path:
                barcode_full_path = os.path.join(self.config.STATIC_FOLDER, barcode_path)
                if os.path.exists(barcode_full_path):
                    barcode_img = Image.open(barcode_full_path).resize((487, 87))
                    template.paste(barcode_img, (857, 930))
                    
                    # Draw FCN text
                    font = ImageFont.truetype(self.config.ENGLISH_FONT_PATH, 28)
                    text_width = draw.textlength(data['fcn_formatted'], font=font)
                    center_x = 830 + (500 - text_width) // 2
                    draw.text((center_x, 888), data['fcn_formatted'], font=font, fill=(0, 0, 0))
            
            # Save color output with person's name
            color_filename = f"{name}_Front_Color.png"
            color_path = os.path.join(self.config.STATIC_FOLDER, color_filename)
            template.save(color_path)
            
            # Generate B&W version
            bw_template = template.copy()
            if os.path.exists(photo_path):
                try:
                    processed_photo_large = process_photo(photo_path, self.config.PHOTO_SIZES['large'], remove_white, remove_black)
                    processed_photo_small = process_photo(photo_path, self.config.PHOTO_SIZES['small'], remove_white, remove_black)
                    bw_large = processed_photo_large.convert('LA').convert('RGBA')
                    bw_small = processed_photo_small.convert('LA').convert('RGBA')
                    bw_template.paste(bw_large, (128, 225), bw_large)
                    bw_template.paste(bw_small, (1493, 860), bw_small)
                except Exception as e:
                    print(f"B&W photo processing failed: {e}")
                    bw_large_photo = Image.open(photo_path).convert('L').resize(self.config.PHOTO_SIZES['large'])
                    bw_template.paste(bw_large_photo, (128, 225))
                    
                    bw_small_photo = Image.open(photo_path).convert('L').resize(self.config.PHOTO_SIZES['small'])
                    bw_template.paste(bw_small_photo, (1493, 860))
            
            # Save B&W version with person's name
            bw_filename = f"{name}_Front_Grayscale.png"
            bw_path = os.path.join(self.config.STATIC_FOLDER, bw_filename)
            bw_template.save(bw_path)
            
            # === Generate Reverse Side ===
            reverse_template = Image.open(self.config.REVERSE_TEMPLATE_IMG).convert("RGBA")
            data_layer = Image.new("RGBA", reverse_template.size, (255, 255, 255, 0))
            draw_data = ImageDraw.Draw(data_layer)
            
            # Load reverse template configuration
            with open(self.config.REVERSE_TEMPLATE_JSON, encoding='utf-8') as f:
                reverse_json = json.load(f)
            
            # Process non-address fields
            for field in reverse_json['fields']:
                key = field.get("key")
                if key in address_positions['reverse']:
                    continue
                    
                content = data.get(key, field.get("label", ""))
                pos = tuple(field["position"])
                color = tuple(field.get("color", (0, 0, 0)))
                align = field.get("align", "left")
                font_spec = field["font"]
                
                # Choose font based on language
                if key.endswith('_am'):
                    font = ImageFont.truetype(self.config.AMHARIC_FONT_PATH, font_spec["size"])
                else:
                    font = ImageFont.truetype(self.config.ENGLISH_FONT_PATH, font_spec["size"])
                
                if key in ["issue_date_am", "issue_date_en"]:
                    rotated_img, pos = draw_rotated_text(draw_data, content, pos, font, color)
                    data_layer.paste(rotated_img, pos, rotated_img)
                else:
                    max_width = field.get("wrap_width")
                    draw_text_with_alignment(draw_data, content, pos, font, color, align, max_width)
            
            # Handle address fields
            font_am = ImageFont.truetype(self.config.AMHARIC_FONT_PATH, 34)
            font_en = ImageFont.truetype(self.config.ENGLISH_FONT_PATH, 34)
            
            for key, pos in address_positions['reverse'].items():
                content = data.get(key, '')
                font = font_am if key.endswith('_am') else font_en
                max_width = self.config.TEXT_MAX_WIDTH['reverse'].get(key, None)
                draw_text_with_alignment(draw_data, content, tuple(pos), font, (0, 0, 0), "left", max_width)
            
            # Process photos
            if os.path.exists(photo_path):
                reverse_photo_lg = process_photo(photo_path, self.config.PHOTO_SIZES['reverse_large'], remove_white, remove_black)
                reverse_template.paste(reverse_photo_lg, (1978, 170), reverse_photo_lg)
                
                reverse_photo_sm = process_photo(photo_path, self.config.PHOTO_SIZES['reverse_small'], remove_white, remove_black)
                reverse_template.paste(reverse_photo_sm, (1398, 510), reverse_photo_sm)
            
            # Process QR code
            if os.path.exists(qr_path):
                qr_img = Image.open(qr_path).resize((530, 530))
                reverse_template.paste(qr_img, (180, 70))
            
            # Process barcode
            if barcode_path:
                barcode_full_path = os.path.join(self.config.STATIC_FOLDER, barcode_path)
                if os.path.exists(barcode_full_path):
                    barcode_img = Image.open(barcode_full_path).resize((287, 62))
                    reverse_template.paste(barcode_img, (1578, 536))
                    
                    # Draw FCN text
                    font = ImageFont.truetype(self.config.ENGLISH_FONT_PATH, 16)
                    text_width = draw_data.textlength(data['fcn_formatted'], font=font)
                    center_x = 700 + (120 - text_width) // 2
                    draw_data.text((center_x, 517), data['fcn_formatted'], font=font, fill=(0, 0, 0))
            
            # Mirror the data layer
            flipped_data = data_layer.transpose(Image.FLIP_LEFT_RIGHT)
            reverse_template.alpha_composite(flipped_data)
            
            # Save reverse output with person's name
            reverse_filename = f"{name}_Reverse_Color.png"
            reverse_path = os.path.join(self.config.STATIC_FOLDER, reverse_filename)
            reverse_template.save(reverse_path)
            
            # Generate reverse B&W version
            bw_template_reverse = reverse_template.copy()
            if os.path.exists(photo_path):
                try:
                    processed_photo = process_photo(photo_path, self.config.PHOTO_SIZES['reverse_large'], remove_white, remove_black)
                    bw_reverse_large = processed_photo.convert('LA').convert('RGBA')
                    bw_template_reverse.paste(bw_reverse_large, (1978, 170), bw_reverse_large)
                    
                    processed_photo_small = process_photo(photo_path, self.config.PHOTO_SIZES['reverse_small'], remove_white, remove_black)
                    bw_reverse_small = processed_photo_small.convert('LA').convert('RGBA')
                    bw_template_reverse.paste(bw_reverse_small, (1398, 510), bw_reverse_small)
                except Exception as e:
                    print(f"Reverse B&W photo processing failed: {e}")
                    bw_reverse_large = Image.open(photo_path).convert('L').resize(self.config.PHOTO_SIZES['reverse_large'])
                    bw_template_reverse.paste(bw_reverse_large, (1978, 170))
                    
                    bw_reverse_small = Image.open(photo_path).convert('L').resize(self.config.PHOTO_SIZES['reverse_small'])
                    bw_template_reverse.paste(bw_reverse_small, (1398, 510))
            
            # Save reverse B&W version with person's name
            bw_filename_reverse = f"{name}_Reverse_Grayscale.png"
            bw_path_reverse = os.path.join(self.config.STATIC_FOLDER, bw_filename_reverse)
            bw_template_reverse.save(bw_path_reverse)
            
            return {
                'front_color': color_filename,
                'front_bw': bw_filename,
                'reverse': reverse_filename,
                'reverse_bw': bw_filename_reverse,
                'city_option': city_option
            }
            
        except Exception as e:
            print(f"Error generating ID card: {str(e)}")
            raise 