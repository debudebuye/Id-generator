"""
Image handling routes for cropped images
Add these routes to your main routes.py file
"""

import base64
import os
from io import BytesIO
from PIL import Image
from flask import request, session
from werkzeug.utils import secure_filename

def save_cropped_image(base64_data, image_type, config):
    """
    Save a base64 encoded cropped image to the static folder
    
    Args:
        base64_data: Base64 encoded image data
        image_type: Type of image ('photo', 'front', 'back')
        config: Config object with STATIC_FOLDER path
    
    Returns:
        str: Path to saved image file
    """
    if not base64_data:
        return None
    
    try:
        # Remove data URL prefix if present
        if ',' in base64_data:
            base64_data = base64_data.split(',')[1]
        
        # Decode base64 image
        image_data = base64.b64decode(base64_data)
        image = Image.open(BytesIO(image_data))
        
        # Generate filename
        filename = f'{image_type}_cropped.png'
        filepath = os.path.join(config.STATIC_FOLDER, filename)
        
        # Save image
        image.save(filepath, 'PNG', quality=95)
        
        return filepath
    except Exception as e:
        print(f"Error saving cropped image: {e}")
        return None


def handle_cropped_images_in_generate_id():
    """
    Add this code to your generate_id() function to handle cropped images
    Place it after validating the FIN number and before extracting PDF data
    """
    # Get cropped images from form
    cropped_photo_qr = request.form.get('cropped_photo_qr', '')  # Combined photo + QR
    cropped_front = request.form.get('cropped_front', '')
    cropped_back = request.form.get('cropped_back', '')
    
    # Save cropped images if provided
    from .config.settings import Config
    config = Config()
    
    photo_path = None
    qr_path = None
    front_path = None
    back_path = None
    
    # Handle combined photo + QR image
    if cropped_photo_qr:
        print("📸 Processing combined photo + QR image...")
        combined_path = save_cropped_image(cropped_photo_qr, 'photo_qr_combined', config)
        if combined_path:
            # Extract photo and QR from the combined image
            from .utils.image_utils import detect_and_extract_photo_qr
            photo_path, qr_path = detect_and_extract_photo_qr(combined_path, config.STATIC_FOLDER)
            
            if photo_path:
                session['uploaded_photo'] = photo_path
                print(f"✓ Extracted profile photo: {photo_path}")
            
            if qr_path:
                session['uploaded_qr'] = qr_path
                print(f"✓ Extracted QR code: {qr_path}")
    
    if cropped_front:
        front_path = save_cropped_image(cropped_front, 'front', config)
        if front_path:
            session['uploaded_front'] = front_path
            print(f"✓ Saved front ID card: {front_path}")
    
    if cropped_back:
        back_path = save_cropped_image(cropped_back, 'back', config)
        if back_path:
            session['uploaded_back'] = back_path
            print(f"✓ Saved back ID card: {back_path}")
    
    return {
        'photo': photo_path,
        'qr': qr_path,
        'front': front_path,
        'back': back_path
    }
