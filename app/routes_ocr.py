"""
New OCR-based route for image-only ID generation
Add this to your routes.py or use as reference
"""

from flask import request, session, redirect, url_for, render_template
import os
from .routes_image_handler import handle_cropped_images_in_generate_id
from .services.ocr_extraction_service import OCRExtractionService
from .config.settings import Config

def generate_id_from_images():
    """
    Generate ID from uploaded images only (no PDF/DOC required)
    Extracts data using OCR from front and back ID images
    """
    config = Config()
    ocr_service = OCRExtractionService()
    
    try:
        # Handle cropped images from form
        uploaded_images = handle_cropped_images_in_generate_id()
        print(f"✓ Processed uploaded images: {uploaded_images}")
        
        # Check if we have at least front and back images
        if not uploaded_images['front'] or not uploaded_images['back']:
            return "Please upload both Front and Back ID images for data extraction.", 400
        
        # Prepare paths
        front_path = uploaded_images['front']
        back_path = uploaded_images['back']
        photo_path = uploaded_images['photo']  # User uploaded photo (optional)
        
        # Extract photo from front ID if user didn't upload separate photo
        if not photo_path:
            photo_output = os.path.join(config.STATIC_FOLDER, 'extracted_photo.png')
        else:
            photo_output = photo_path
        
        # Extract all data using OCR
        print("🔍 Starting OCR extraction...")
        extraction_result = ocr_service.extract_all_data(
            front_image_path=front_path,
            back_image_path=back_path,
            photo_output_path=photo_output
        )
        
        print(f"✓ OCR Extraction complete")
        print(f"  - Photo: {extraction_result['photo_path']}")
        print(f"  - Front data: {extraction_result['front_data']}")
        print(f"  - Back data: {extraction_result['back_data']}")
        
        # Prepare extracted data for preview
        combined_data = extraction_result['combined_data']
        
        # Format the data for the preview page
        extracted = {
            'fin': combined_data.get('fin', ''),
            'name_en': combined_data.get('full_name_en', ''),
            'name_am': combined_data.get('full_name_am', ''),
            'nationality_en': combined_data.get('nationality_en', 'Ethiopian'),
            'nationality_am': combined_data.get('nationality_am', 'ኢትዮጵያዊ'),
            'region_en': combined_data.get('region', ''),
            'region_am': '',
            'subcity_en': combined_data.get('subcity', ''),
            'subcity_am': '',
            'woreda_en': combined_data.get('woreda', ''),
            'woreda_am': '',
            'address_en': combined_data.get('address_en', ''),
            'address_am': combined_data.get('address_am', ''),
            'birth_date': combined_data.get('date_of_birth', ''),
            'sex': combined_data.get('sex', ''),
            'issue_date': '',
            'expiry_date': combined_data.get('date_of_expiry', ''),
            'phone_number': combined_data.get('phone_number', ''),
            'photo_path': extraction_result['photo_path'] or photo_path,
            'extraction_method': 'OCR'
        }
        
        # Store in session
        session['extracted'] = extracted
        session['uploaded_images'] = uploaded_images
        
        print("✓ Data stored in session, redirecting to preview")
        
        # Redirect to preview page
        return redirect(url_for('main.preview'))
        
    except Exception as e:
        print(f"✗ Error in OCR extraction: {e}")
        import traceback
        traceback.print_exc()
        return f"Failed to extract data from images: {str(e)}", 500
