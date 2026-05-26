from flask import Blueprint, request, render_template, redirect, url_for, session, jsonify, current_app
from werkzeug.utils import secure_filename
import os
import json
from typing import Dict, Optional, List
from io import BytesIO
from datetime import datetime

from .config.settings import Config
from .services.id_card_service import IDCardService
from .routes_image_handler import handle_cropped_images_in_generate_id, save_cropped_image
from .services.ocr_extraction_service import OCRExtractionService
from .utils.date_utils import get_id_dates

from .services.firebase_service import firebase_service
from .services.daily_report_service import DailyReportService

# Create blueprint
bp = Blueprint('main', __name__)
config = Config()
id_service = IDCardService()
ocr_service = OCRExtractionService()

def format_address_smart(region, subcity, woreda, language='en'):
    """Format address based on subcity name length and content with improved logic"""
    # Clean up empty or invalid values
    region = region.strip() if region else ""
    subcity = subcity.strip() if subcity else ""
    woreda = woreda.strip() if woreda else ""
    
    # Remove generic labels that shouldn't be in the final address
    generic_labels_en = ['region', 'subcity', 'sub-city', 'woreda', 'city admin', 'administration', 'zone', 'sub city']
    generic_labels_am = ['ክልል', 'ክፍለ ከተማ', 'ወረዳ', 'ከተማ አስተዳደር', 'ዞን', 'አስተዳደር']
    
    # Clean subcity field if it contains generic labels
    if language == 'en':
        if any(label in subcity.lower() for label in generic_labels_en) and len(subcity) < 25:
            print(f"Removing generic subcity label: '{subcity}'")
            subcity = ""
    else:
        if any(label in subcity for label in generic_labels_am) and len(subcity) < 25:
            print(f"Removing generic subcity label: '{subcity}'")
            subcity = ""
    
    # Clean woreda field if it contains generic labels
    if language == 'en':
        if any(label in woreda.lower() for label in generic_labels_en) and len(woreda) < 20:
            print(f"Removing generic woreda label: '{woreda}'")
            woreda = ""
    else:
        if any(label in woreda for label in generic_labels_am) and len(woreda) < 20:
            print(f"Removing generic woreda label: '{woreda}'")
            woreda = ""
    
    # Build address components list
    address_parts = []
    if region:
        address_parts.append(region)
    if subcity:
        address_parts.append(subcity)
    if woreda:
        address_parts.append(woreda)
    
    # Return formatted address
    if address_parts:
        formatted_address = ", ".join(address_parts)
        print(f"Formatted address ({language}): '{formatted_address}'")
        return formatted_address
    else:
        # Fallback if all parts are empty
        fallback = f"{region or ''}, {subcity or ''}, {woreda or ''}"
        print(f"Fallback address ({language}): '{fallback}'")
        return fallback

def sync_firebase_to_local_allowlist():
    """Sync Firebase approved users to local allowlist for bot access"""
    try:
        # Get approved users from Firebase
        approved_users = firebase_service.get_approved_users()
        
        # Extract telegram IDs
        telegram_ids = []
        for user in approved_users:
            try:
                telegram_id = int(user.get('telegramId', user.get('id')))
                telegram_ids.append(telegram_id)
            except (ValueError, TypeError):
                continue
        
        # Update local allowlist
        allowlist_path = os.path.join(os.path.dirname(__file__), '..', 'telegram_bot', 'data', 'allowed_users.json')
        with open(allowlist_path, 'w', encoding='utf-8') as f:
            json.dump(telegram_ids, f, ensure_ascii=False, indent=2)
        
        print(f"✅ Synced {len(telegram_ids)} approved users to local allowlist")
        
    except Exception as e:
        print(f"⚠️ Error syncing Firebase to local allowlist: {e}")

def allowed_file(filename: str) -> bool:
    """Check if file extension is allowed."""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in config.ALLOWED_EXTENSIONS

@bp.route('/')
def index():
    """
    ---
    get:
      summary: Render the index page
      responses:
        200:
          description: Index page
    """
    print("🔄 User returned to index page - clearing all cached and session data")
    
    # Clear session data when loading index page for fresh start
    session.clear()
    print("✓ Session data cleared")
    
    # Clear OCR service preprocessing cache
    try:
        ocr_service.clear_cache()
        print("✓ OCR preprocessing cache cleared")
    except Exception as e:
        print(f"⚠️ Could not clear OCR cache: {e}")
    
    # Clear ID card service cache if it exists
    try:
        if hasattr(id_service, 'clear_cache'):
            id_service.clear_cache()
            print("✓ ID card service cache cleared")
    except Exception as e:
        print(f"⚠️ Could not clear ID service cache: {e}")
    
    # Clean up temporary files from previous sessions
    temp_files = [
        'photo_temp.png',
        'qr_temp.png',
        'photo_cropped.png',
        'qr_cropped.png',
        'front_cropped.png',
        'back_cropped.png',
        'fcn_barcode.png',
        'photo_extracted.png',
        'qr_extracted.png',
        'photo_qr_combined_cropped.png',
        'barcode_temp.png'
    ]
    
    cleaned_count = 0
    for temp_file in temp_files:
        temp_path = os.path.join(config.STATIC_FOLDER, temp_file)
        if os.path.exists(temp_path):
            try:
                os.remove(temp_path)
                cleaned_count += 1
                print(f"  🗑️ Deleted: {temp_file}")
            except Exception as e:
                print(f"  ⚠️ Could not delete {temp_file}: {e}")
    
    if cleaned_count > 0:
        print(f"✓ Cleaned up {cleaned_count} temporary files")
    else:
        print("ℹ️ No temporary files to clean up")
    
    # Clean up debug regions folder
    debug_regions_path = os.path.join(config.STATIC_FOLDER, 'debug_regions')
    if os.path.exists(debug_regions_path):
        try:
            import glob
            debug_files = glob.glob(os.path.join(debug_regions_path, '*.png'))
            debug_cleaned = 0
            for debug_file in debug_files:
                try:
                    os.remove(debug_file)
                    debug_cleaned += 1
                except Exception as e:
                    print(f"  ⚠️ Could not delete debug file: {e}")
            
            if debug_cleaned > 0:
                print(f"✓ Cleaned up {debug_cleaned} debug region files")
        except Exception as e:
            print(f"⚠️ Could not clean debug regions: {e}")
    
    print("✅ Index page ready - all caches and session data cleared")
    
    return render_template('index.html')

@bp.route('/health')
def health_check():
    """
    ---
    get:
      summary: Health check endpoint
      responses:
        200:
          description: Healthy status
    """
    return jsonify({"status": "healthy"})

@bp.route('/api/new-users', methods=['GET'])
def get_new_users():
    """
    ---
    get:
      summary: Get new users for admin panel
      responses:
        200:
          description: List of new users
    """
    try:
        # Persisted new user events emitted by the bot
        new_users_path = os.path.join(os.path.dirname(__file__), '..', 'telegram_bot', 'data', 'new_users.json')
        if os.path.exists(new_users_path):
            with open(new_users_path, 'r', encoding='utf-8') as f:
                new_users = json.load(f)
        else:
            new_users = []
        # Sort by timestamp desc
        new_users_sorted = sorted(new_users, key=lambda x: x.get('timestamp', ''), reverse=True)
        return jsonify(new_users_sorted)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@bp.route('/api/new-users', methods=['POST'])
def add_new_user():
    """
    Receive a new user event from the Telegram bot and persist it.
    Body JSON: { id, username, telegramId, firstName, lastName, timestamp }
    """
    try:
        payload = request.get_json(force=True, silent=True) or {}
        required = ['id', 'telegramId', 'firstName', 'timestamp']
        for key in required:
            if key not in payload:
                return jsonify({"error": f"Missing field: {key}"}), 400

        new_users_path = os.path.join(os.path.dirname(__file__), '..', 'telegram_bot', 'data', 'new_users.json')
        os.makedirs(os.path.dirname(new_users_path), exist_ok=True)
        if os.path.exists(new_users_path):
            with open(new_users_path, 'r', encoding='utf-8') as f:
                items = json.load(f)
        else:
            items = []

        # Upsert by telegramId if already exists
        found = False
        for item in items:
            if str(item.get('telegramId')) == str(payload['telegramId']):
                item.update(payload)
                found = True
                break
        if not found:
            payload.setdefault('status', 'pending')
            items.append(payload)

        with open(new_users_path, 'w', encoding='utf-8') as f:
            json.dump(items, f, ensure_ascii=False, indent=2)
        return jsonify({"ok": True}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@bp.route('/api/users/<user_id>/approve', methods=['POST'])
def approve_user(user_id):
    """
    ---
    post:
      summary: Approve a user and add to allowlist
      parameters:
        - name: user_id
          in: path
          type: string
          required: true
      responses:
        200:
          description: User approved and added to allowlist
    """
    try:
        new_users_path = os.path.join(os.path.dirname(__file__), '..', 'telegram_bot', 'data', 'new_users.json')
        allowlist_path = os.path.join(os.path.dirname(__file__), '..', 'telegram_bot', 'data', 'allowed_users.json')
        
        # Update new_users.json status
        items = []
        if os.path.exists(new_users_path):
            with open(new_users_path, 'r', encoding='utf-8') as f:
                items = json.load(f)
        
        user_data = None
        for item in items:
            if str(item.get('id')) == str(user_id) or str(item.get('telegramId')) == str(user_id):
                item['status'] = 'approved'
                user_data = item
                break
        
        with open(new_users_path, 'w', encoding='utf-8') as f:
            json.dump(items, f, ensure_ascii=False, indent=2)
        
        # Add user to allowlist and Firebase
        if user_data:
            telegram_id = int(user_data.get('telegramId', user_id))
            
            # Add to Firebase (approved users collection)
            firebase_service.add_approved_user(user_data)
            
            # Update the user's access_status in the users collection
            firebase_service.update_user_access_status(str(telegram_id), 'approved')
            
            # Sync Firebase approved users to local allowlist
            sync_firebase_to_local_allowlist()
            
            print(f"✅ Added user {telegram_id} ({user_data.get('firstName', 'Unknown')}) to allowlist")
        
        # Notify the user via Telegram bot
        if user_data:
            try:
                import requests
                bot_token = os.getenv('TELEGRAM_BOT_TOKEN')
                if bot_token:
                    telegram_id = int(user_data.get('telegramId', user_id))
                    user_name = user_data.get('firstName', 'User')
                    
                    # Send approval notification to user
                    message = (
                        f"🎉 **መዳረሻ ተፈቅዷል!**\n\n"
                        f"ሰላም {user_name}!\n\n"
                        f"የመዳረሻ ጥያቄዎ በአስተዳዳሪ **ተፈቅዷል**።\n"
                        f"አሁን ዲጂታል መለያ ለመፍጠር ቦቱን መጠቀም ይችላሉ።\n\n"
                        f"🔄 **ለመጀመር:** /start ወይም ማንኛውንም መልዕክት ወደ ቦቱ ይላኩ\n\n"
                        f"ለትዕግስትዎ እናመሰግናለን!"
                    )
                    
                    url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
                    payload = {
                        'chat_id': telegram_id,
                        'text': message,
                        'parse_mode': 'Markdown'
                    }
                    
                    response = requests.post(url, json=payload, timeout=10)
                    if response.status_code == 200:
                        print(f"✅ Sent approval notification to user {telegram_id}")
                    else:
                        response_data = response.json() if response.headers.get('content-type', '').startswith('application/json') else response.text
                        if 'chat not found' in str(response_data):
                            print(f"ℹ️ User {telegram_id} not found in Telegram (test user or user hasn't started bot)")
                        else:
                            print(f"⚠️ Failed to send notification to user {telegram_id}: {response_data}")
                else:
                    print("⚠️ TELEGRAM_BOT_TOKEN not found, skipping user notification")
            except Exception as notify_error:
                print(f"⚠️ Error sending notification: {notify_error}")
        
        return jsonify({"status": "approved", "message": f"User {user_id} approved and added to allowlist"})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@bp.route('/api/approved-users', methods=['GET'])
def get_approved_users():
    """
    ---
    get:
      summary: Get all approved users
      responses:
        200:
          description: List of approved users
    """
    try:
        approved_users = firebase_service.get_approved_users()
        return jsonify(approved_users)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@bp.route('/api/sync-firebase-to-local', methods=['POST'])
def sync_firebase_endpoint():
    """
    ---
    post:
      summary: Manually sync Firebase approved users to local allowlist
      responses:
        200:
          description: Sync completed
    """
    try:
        sync_firebase_to_local_allowlist()
        return jsonify({"status": "success", "message": "Firebase synced to local allowlist"})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@bp.route('/api/sync-approved-users', methods=['POST'])
def sync_approved_users():
    """Sync approved users from Firebase to local storage."""
    try:
        # Get users from Firebase
        users = firebase_service.get_approved_users()
        
        # Update local approved_users.json
        local_file = 'telegram_bot/data/approved_users.json'
        with open(local_file, 'w', encoding='utf-8') as f:
            json.dump(users, f, ensure_ascii=False, indent=2)
        
        # Also update allowed_users.json
        allowed_file = 'telegram_bot/data/allowed_users.json'
        allowed_ids = [int(user.get('telegramId', user.get('id'))) for user in users]
        
        with open(allowed_file, 'w', encoding='utf-8') as f:
            json.dump(allowed_ids, f, indent=2)
        
        return jsonify({
            "success": True, 
            "message": f"Synced {len(users)} approved users from Firebase",
            "count": len(users)
        })
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@bp.route('/api/users/<user_id>/revoke', methods=['POST'])
def revoke_user_access(user_id):
    """
    ---
    post:
      summary: Revoke user access and remove from approved users
      parameters:
        - name: user_id
          in: path
          type: string
          required: true
      responses:
        200:
          description: User access revoked
    """
    try:
        allowlist_path = os.path.join(os.path.dirname(__file__), '..', 'telegram_bot', 'data', 'allowed_users.json')
        
        # Remove user from Firebase/local storage
        success = firebase_service.remove_approved_user(user_id)
        
        # Sync Firebase approved users to local allowlist (this will remove the user)
        sync_firebase_to_local_allowlist()
        
        telegram_id = int(user_id)
        print(f"✅ Removed user {telegram_id} from allowlist")
        
        # Notify the user via Telegram bot
        try:
            import requests
            bot_token = os.getenv('TELEGRAM_BOT_TOKEN')
            print(f"🔍 Bot token found: {bool(bot_token)}")
            if bot_token:
                message = (
                    "🚫 **መዳረሻ ተመለሰ**\n\n"
                    "የቦቱ መዳረሻዎ በአስተዳዳሪ ተመለሰ።\n"
                    "ከአሁን በኋላ መለያ ለመፍጠር ቦቱን መጠቀም አይችሉም።\n\n"
                    "ይህ ስህተት ነው ብለው ካሰቡ፣ እባክዎ ከአስተዳዳሪ ጋር ይገናኙ።\n"
                    "ከአስተዳዳሪ ጋር ይገናኙ፡\n\n"
                    "@fayda\\_software\n\n"
                    "ለመረዳትዎ እናመሰግናለን።"
                )
                
                url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
                payload = {
                    'chat_id': telegram_id,
                    'text': message,
                    'parse_mode': 'Markdown'
                }
                
                response = requests.post(url, json=payload, timeout=10)
                print(f"🔍 Telegram API response status: {response.status_code}")
                if response.status_code == 200:
                    print(f"✅ Sent revocation notification to user {telegram_id}")
                else:
                    response_data = response.json() if response.headers.get('content-type', '').startswith('application/json') else response.text
                    print(f"🔍 Telegram API response: {response_data}")
                    if 'chat not found' in str(response_data):
                        print(f"ℹ️ User {telegram_id} not found in Telegram (user hasn't started bot)")
                    else:
                        print(f"⚠️ Failed to send revocation notification to user {telegram_id}: {response_data}")
            else:
                print("⚠️ TELEGRAM_BOT_TOKEN not found, skipping user notification")
        except Exception as notify_error:
            print(f"⚠️ Error sending revocation notification: {notify_error}")
        
        return jsonify({"status": "revoked", "message": f"User {user_id} access revoked"})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@bp.route('/api/users/<user_id>/reject', methods=['POST'])
def reject_user(user_id):
    """
    ---
    post:
      summary: Reject a user
      parameters:
        - name: user_id
          in: path
          type: string
          required: true
      responses:
        200:
          description: User rejected
    """
    try:
        new_users_path = os.path.join(os.path.dirname(__file__), '..', 'telegram_bot', 'data', 'new_users.json')
        items = []
        user_data = None
        if os.path.exists(new_users_path):
            with open(new_users_path, 'r', encoding='utf-8') as f:
                items = json.load(f)
        for item in items:
            if str(item.get('id')) == str(user_id) or str(item.get('telegramId')) == str(user_id):
                item['status'] = 'rejected'
                user_data = item
                break
        with open(new_users_path, 'w', encoding='utf-8') as f:
            json.dump(items, f, ensure_ascii=False, indent=2)
        
        # Update Firebase users collection
        if user_data:
            telegram_id = str(user_data.get('telegramId', user_id))
            firebase_service.update_user_access_status(telegram_id, 'rejected')
        
        return jsonify({"status": "rejected", "message": f"User {user_id} rejected"})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@bp.route('/decode_qr', methods=['POST'])
def decode_qr():
    """Decode QR code from a base64 image and return FCN/FAN number"""
    try:
        data = request.get_json()
        if not data or 'image' not in data:
            return jsonify({'error': 'No image data provided'}), 400

        import base64
        from io import BytesIO
        import numpy as np
        from PIL import Image as PILImage
        from pyzbar.pyzbar import decode as pyzbar_decode

        # Strip data URL prefix if present
        img_data = data['image']
        if ',' in img_data:
            img_data = img_data.split(',')[1]

        image_bytes = base64.b64decode(img_data)
        pil_img = PILImage.open(BytesIO(image_bytes)).convert('RGB')
        img_np = np.array(pil_img)

        # Try pyzbar first (most reliable)
        decoded_objects = pyzbar_decode(pil_img)

        if not decoded_objects:
            # Fallback: try cv2 QR detector
            import cv2
            gray = cv2.cvtColor(img_np, cv2.COLOR_RGB2GRAY)
            detector = cv2.QRCodeDetector()
            val, _, _ = detector.detectAndDecode(gray)
            if val:
                decoded_objects = [type('obj', (), {'data': val.encode()})()]

        if not decoded_objects:
            return jsonify({'success': False, 'message': 'No QR code found in image'}), 200

        # Extract FCN/FAN — look for a 15-17 digit number in QR content
        import re
        for obj in decoded_objects:
            qr_text = obj.data.decode('utf-8') if isinstance(obj.data, bytes) else obj.data
            print(f"QR decoded text: {qr_text}")

            # Try to find a 15-17 digit number (FCN/FAN format)
            match = re.search(r'\b(\d{15,17})\b', qr_text)
            if match:
                fan = match.group(1)
                # Trim to 16 digits if longer
                if len(fan) > 16:
                    fan = fan[:16]
                return jsonify({'success': True, 'fan': fan, 'raw': qr_text})

            # If QR text itself is mostly digits, use it directly
            digits_only = re.sub(r'\D', '', qr_text)
            if 15 <= len(digits_only) <= 17:
                fan = digits_only[:16]
                return jsonify({'success': True, 'fan': fan, 'raw': qr_text})

        return jsonify({'success': False, 'message': 'QR found but no FCN/FAN number detected', 'raw': decoded_objects[0].data.decode('utf-8', errors='replace')}), 200

    except Exception as e:
        print(f"QR decode error: {e}")
        return jsonify({'error': str(e)}), 500


@bp.route('/extract_fin', methods=['POST'])
def extract_fin():
    """
    ---
    post:
      summary: Extract FIN number from document
      consumes:
        - multipart/form-data
      parameters:
        - in: formData
          name: document
          type: file
          required: true
          description: Document (PDF, DOC, DOCX) to extract FIN from
      responses:
        200:
          description: FIN extracted successfully
        400:
          description: Invalid file or extraction failed
    """
    if 'document' not in request.files:
        return jsonify({'error': 'No document uploaded'}), 400
    
    document = request.files['document']
    if document.filename == '':
        return jsonify({'error': 'No selected file'}), 400
    
    # Check if file type is allowed
    if not allowed_file(document.filename):
        return jsonify({'error': 'Invalid file type. Please upload a PDF, DOC, or DOCX file.'}), 400
    
    # Only PDFs support automatic FIN extraction
    if not document.filename.lower().endswith('.pdf'):
        return jsonify({
            'success': False,
            'message': 'Automatic FIN extraction is only supported for PDF files. Please enter FIN manually.'
        })
    
    try:
        # Read PDF into memory
        pdf_bytes = document.read()
        pdf_stream = BytesIO(pdf_bytes)
        
        # Extract FIN from PDF
        extracted_fin = id_service.extract_fin_from_pdf(pdf_stream)
        
        if extracted_fin:
            return jsonify({
                'success': True,
                'fin': extracted_fin,
                'message': 'FIN number extracted successfully from PDF'
            })
        else:
            return jsonify({
                'success': False,
                'message': 'Could not find a valid FIN number in the PDF. Please enter it manually.'
            })
            
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'Failed to extract FIN: {str(e)}'
        }), 500

@bp.route('/upload_photo', methods=['POST'])
def upload_photo():
    """
    ---
    post:
      summary: Upload a photo for the ID
      consumes:
        - multipart/form-data
      parameters:
        - in: formData
          name: photo
          type: file
          required: true
          description: Photo to upload
      responses:
        200:
          description: Photo uploaded successfully
        400:
          description: Invalid file or no photo uploaded
    """
    if 'photo' not in request.files:
        return jsonify({'error': 'No photo uploaded'}), 400
    
    photo = request.files['photo']
    if photo.filename == '':
        return jsonify({'error': 'No selected file'}), 400
    
    if photo and allowed_file(photo.filename):
        filename = 'photo_temp.png'
        filepath = os.path.join(config.STATIC_FOLDER, filename)
        photo.save(filepath)
        return jsonify({'success': True, 'photo_url': url_for('static', filename=filename)})
    
    return jsonify({'error': 'Invalid file type'}), 400

@bp.route('/upload_qr', methods=['POST'])
def upload_qr():
    """
    ---
    post:
      summary: Upload a QR code image for the ID
      consumes:
        - multipart/form-data
      parameters:
        - in: formData
          name: qr
          type: file
          required: true
          description: QR code image to upload
      responses:
        200:
          description: QR code uploaded successfully
        400:
          description: Invalid file or no QR code uploaded
    """
    if 'qr' not in request.files:
        return jsonify({'error': 'No QR code uploaded'}), 400
    
    qr = request.files['qr']
    if qr.filename == '':
        return jsonify({'error': 'No selected file'}), 400
    
    if qr and allowed_file(qr.filename):
        filename = 'qr_temp.png'
        filepath = os.path.join(config.STATIC_FOLDER, filename)
        qr.save(filepath)
        return jsonify({'success': True, 'qr_url': url_for('static', filename=filename)})
    
    return jsonify({'error': 'Invalid file type'}), 400

@bp.route('/upload_barcode', methods=['POST'])
def upload_barcode():
    """
    ---
    post:
      summary: Upload a barcode image for the ID
      consumes:
        - multipart/form-data
      parameters:
        - in: formData
          name: barcode
          type: file
          required: true
          description: Barcode image to upload
      responses:
        200:
          description: Barcode uploaded successfully
        400:
          description: Invalid file or no barcode uploaded
    """
    if 'barcode' not in request.files:
        return jsonify({'error': 'No barcode uploaded'}), 400
    
    barcode = request.files['barcode']
    if barcode.filename == '':
        return jsonify({'error': 'No selected file'}), 400
    
    if barcode and allowed_file(barcode.filename):
        filename = 'barcode_temp.png'
        filepath = os.path.join(config.STATIC_FOLDER, filename)
        barcode.save(filepath)
        return jsonify({'success': True, 'barcode_url': url_for('static', filename=filename)})
    
    return jsonify({'error': 'Invalid file type'}), 400

@bp.route('/generate_id', methods=['POST'])
def generate_id():
    """
    Generate ID from uploaded images using OCR extraction
    No PDF/DOC required - extracts data from front and back ID images
    Can also accept JSON data directly to skip OCR
    """
    import time
    
    # Start timing
    extraction_start_time = time.time()
    print(f"⏱️  Extraction started at {extraction_start_time}")
    
    try:
        # Handle cropped images from form
        uploaded_images = handle_cropped_images_in_generate_id()
        print(f"✓ Processed uploaded images: {uploaded_images}")
        
        # Get manual FAN from form
        manual_fan = request.form.get('manual_fan', '').strip()
        if manual_fan:
            print(f"📝 Manual FAN provided: {manual_fan}")
        
        # Check for unified JSON data from form
        card_json_str = request.form.get('card_json_data', '').strip()
        
        card_json_data = None
        
        # Parse JSON data if provided
        if card_json_str:
            try:
                import json
                card_json_data = json.loads(card_json_str)
                print(f"✓ Unified card JSON data received: {card_json_data}")
            except json.JSONDecodeError as e:
                print(f"⚠️ Invalid card JSON data: {e}")
                return render_template('error.html', 
                                     message=f"Invalid card JSON data: {str(e)}"), 400
        
        # Check if we have at least one image or JSON data
        if not uploaded_images['front'] and not uploaded_images['back'] and not uploaded_images['photo'] and not card_json_data:
            return render_template('error.html', 
                                 message="Please upload at least one image or provide JSON data."), 400
        
        # Prepare paths
        front_path = uploaded_images['front']
        back_path = uploaded_images['back']
        photo_path = uploaded_images['photo']  # Use uploaded profile photo
        qr_path = uploaded_images.get('qr')  # Get uploaded QR code if available
        
        # Initialize extracted data with empty defaults (no hard-coded fallbacks)
        extracted = {
            'fan': '',  # FAN not FIN
            'fin': '',  # Keep for compatibility
            'fcn_full': '',  # For preview page display
            'fcn_barcode': '',  # For preview page barcode display
            'barcode': '',
            'serial_number': '',  # Serial number field
            # Name fields - both formats for compatibility
            'name_en': '',
            'name_am': '',
            'full_name_en': '',
            'full_name_am': '',
            'nationality_en': '',
            'nationality_am': '',
            'region_en': '',
            'region_am': '',
            'subcity_en': '',
            'subcity_am': '',
            'woreda_en': '',
            'woreda_am': '',
            'address_en': '',
            'address_am': '',
            # Date of birth - multiple formats for compatibility
            'birth_date': '',
            'birth_date_am': '',
            'birth_date_en': '',
            'date_of_birth': '',
            'dob_am': '',
            'dob_en': '',
            # Gender/Sex - multiple formats for compatibility
            'sex': '',
            'sex_am': '',
            'sex_en': '',
            'gender_am': '',
            'gender_en': '',
            # Issue date - multiple formats
            'issue_date': '',
            'issue_date_am': '',
            'issue_date_en': '',
            'date_of_issue': '',
            # Expiry date - multiple formats
            'expiry_date': '',
            'expiry_date_am': '',
            'expiry_date_en': '',
            'date_of_expiry': '',
            # Phone - both formats
            'phone': '',
            'phone_number': '',
            'photo_path': photo_path,  # Always use uploaded profile photo
            'qr_path': qr_path if qr_path else None,  # Use uploaded QR code if available
            'extraction_method': 'Manual',
            'front_image': front_path,
            'back_image': back_path
        }
        
        # Try OCR extraction if we have at least one ID side
        if front_path or back_path:
            try:
                print("🔍 Starting OCR extraction from ID card images...")
                print("📸 Using uploaded profile photo (not extracting from front ID)")

                front_data = {}
                back_data = {}

                # Extract text from front ID using region-based extraction only (faster)
                if front_path:
                    print(f"   → Extracting data from FRONT image: {front_path}")
                    front_data = ocr_service.parse_front_card_data("", image_path=front_path)
                else:
                    print("   → No FRONT image uploaded")

                # Extract text from back ID using region-based extraction only (faster)
                if back_path:
                    print(f"   → Extracting data from BACK image: {back_path}")
                    back_data = ocr_service.parse_back_card_data("", image_path=back_path)
                else:
                    print("   → No BACK image uploaded")

                # Use uploaded QR code if available, otherwise extract from back ID (when back exists)
                qr_extracted_path = None
                if qr_path:
                    print(f"✓ Using uploaded QR code from index page: {qr_path}")
                    qr_extracted_path = qr_path
                elif back_path:
                    print("ℹ️ No QR uploaded, extracting from back ID card...")
                    # Extract QR code from back ID
                    qr_output_path = os.path.join(config.STATIC_FOLDER, 'qr_extracted.png')
                    qr_extracted_path = ocr_service.extract_qr_code_region(back_path, qr_output_path)
                
                if qr_extracted_path:
                    if qr_path:
                        print(f"✓ QR code ready (uploaded from index page)")
                    else:
                        print(f"✓ QR code extracted from back card: {qr_extracted_path}")
                    # Optionally decode QR code data
                    qr_data = ocr_service.decode_qr_code(qr_extracted_path)
                    if qr_data:
                        print(f"✓ QR code data: {qr_data[:100]}...")
                else:
                    print("⚠️ QR code extraction failed")
                
                print(f"✓ OCR Extraction complete")
                print(f"  - Front data keys: {list(front_data.keys())}")
                print(f"  - Front data: {front_data}")
                print(f"  - Back data keys: {list(back_data.keys())}")
                print(f"  - Back data: {back_data}")
                
                # Combine data
                combined_data = {**front_data, **back_data}
                
                print(f"✓ Combined OCR data:")
                print(f"  - date_of_birth: {combined_data.get('date_of_birth', 'NOT SET')}")
                print(f"  - date_of_birth_am: {combined_data.get('date_of_birth_am', 'NOT SET')}")
                print(f"  - date_of_birth_en: {combined_data.get('date_of_birth_en', 'NOT SET')}")
                print(f"  - date_of_expiry: {combined_data.get('date_of_expiry', 'NOT SET')}")
                print(f"  - date_of_expiry_am: {combined_data.get('date_of_expiry_am', 'NOT SET')}")
                print(f"  - date_of_expiry_en: {combined_data.get('date_of_expiry_en', 'NOT SET')}")
                
                # Ensure DOB fields are properly mapped
                if combined_data.get('date_of_birth_en') and not combined_data.get('dob_en'):
                    combined_data['dob_en'] = combined_data['date_of_birth_en']
                    combined_data['birth_date_en'] = combined_data['date_of_birth_en']
                    print(f"  - Copied date_of_birth_en to dob_en: {combined_data['dob_en']}")
                
                if combined_data.get('date_of_birth_am') and not combined_data.get('dob_am'):
                    combined_data['dob_am'] = combined_data['date_of_birth_am']
                    combined_data['birth_date_am'] = combined_data['date_of_birth_am']
                    print(f"  - Copied date_of_birth_am to dob_am: {combined_data['dob_am']}")
                
                # Ensure expiry_date_en is set if date_of_expiry_en is available
                if combined_data.get('date_of_expiry_en') and not combined_data.get('expiry_date_en'):
                    combined_data['expiry_date_en'] = combined_data['date_of_expiry_en']
                    print(f"  - Copied date_of_expiry_en to expiry_date_en: {combined_data['expiry_date_en']}")
                
                # Ensure expiry_date_am is set if date_of_expiry_am is available
                if combined_data.get('date_of_expiry_am') and not combined_data.get('expiry_date_am'):
                    combined_data['expiry_date_am'] = combined_data['date_of_expiry_am']
                    print(f"  - Copied date_of_expiry_am to expiry_date_am: {combined_data['expiry_date_am']}")
                
                print(f"✓ Combined data keys: {list(combined_data.keys())}")
                print(f"✓ Combined data values:")
                for key, value in combined_data.items():
                    if value:  # Only print non-empty values
                        print(f"    {key}: {value}")
                
                # Update extracted data with OCR results
                fan_number = combined_data.get('fan', '')
                fin_number = combined_data.get('fin', '')  # FIN from back card
                
                # Prioritize manual FAN input, then extracted FAN, then FIN from back card
                extraction_method = 'OCR'
                if manual_fan:
                    fan_number = manual_fan
                    extraction_method = 'Manual'  # Mark as manual when using manual FAN
                    print(f"✓ Using manual FAN (priority): {manual_fan}")
                elif fan_number:
                    print(f"✓ Using extracted FAN from OCR: {fan_number}")
                elif fin_number:
                    fan_number = fin_number
                    print(f"ℹ️ Using FIN from back card as FAN fallback: {fin_number}")
                else:
                    print("⚠️ No FAN found in OCR extraction and no manual FAN provided")
                
                # Generate serial number (7-8 digit number)
                serial_number = id_service.generate_serial_number()
                print(f"🔢 Generated serial number: {serial_number}")
                
                # Don't extract barcode from image - it will be generated from FAN
                # The barcode field should be empty, system will generate it
                extracted.update({
                    'fan': fan_number,
                    'fin': fin_number,  # Keep FIN separate
                    'fcn_full': fan_number,  # For preview page display
                    'fcn_barcode': '',  # Don't use extracted barcode - will be generated
                    'barcode': '',  # Don't use extracted barcode - will be generated
                    'serial_number': serial_number,  # Generated serial number
                    # Map full_name_* to name_* for template compatibility
                    'name_en': combined_data.get('full_name_en', ''),
                    'name_am': combined_data.get('full_name_am', ''),
                    'full_name_en': combined_data.get('full_name_en', ''),  # Keep for compatibility
                    'full_name_am': combined_data.get('full_name_am', ''),  # Keep for compatibility
                    # Nationality (leave empty if not extracted)
                    'nationality_en': combined_data.get('nationality_en', ''),
                    'nationality_am': combined_data.get('nationality_am', ''),
                    'region_en': combined_data.get('region_en', ''),
                    'region_am': combined_data.get('region_am', ''),
                    'subcity_en': combined_data.get('subcity_en', ''),
                    'subcity_am': combined_data.get('subcity_am', ''),
                    'woreda_en': combined_data.get('woreda_en', ''),
                    'woreda_am': combined_data.get('woreda_am', ''),
                    'address_en': combined_data.get('address_en', ''),
                    'address_am': combined_data.get('address_am', ''),
                    # Map DOB (separate calendars when available)
                    'dob_am': combined_data.get('date_of_birth_am', combined_data.get('dob_am', '')),
                    'dob_en': combined_data.get('date_of_birth_en', combined_data.get('dob_en', combined_data.get('date_of_birth', ''))),
                    'birth_date': combined_data.get('date_of_birth', ''),  # Legacy
                    'birth_date_am': combined_data.get('date_of_birth_am', combined_data.get('birth_date_am', '')),
                    'birth_date_en': combined_data.get('date_of_birth_en', combined_data.get('birth_date_en', '')),
                    'date_of_birth': combined_data.get('date_of_birth', ''),  # Legacy single field
                    'date_of_birth_en': combined_data.get('date_of_birth_en', combined_data.get('dob_en', '')),  # Ensure this is set
                    'date_of_birth_am': combined_data.get('date_of_birth_am', combined_data.get('dob_am', '')),  # Ensure this is set
                    # Map sex/gender (both languages when available)
                    'gender_am': combined_data.get('sex_am', combined_data.get('gender_am', '')),
                    'gender_en': combined_data.get('sex_en', combined_data.get('gender_en', combined_data.get('sex', ''))),
                    'sex': combined_data.get('sex', ''),  # Legacy
                    'sex_am': combined_data.get('sex_am', ''),
                    'sex_en': combined_data.get('sex_en', ''),
                    # Issue date (separate calendars when available)
                    'issue_date': combined_data.get('date_of_issue', ''),
                    'issue_date_am': combined_data.get('date_of_issue_am', combined_data.get('issue_date_am', '')),
                    'issue_date_en': combined_data.get('date_of_issue_en', combined_data.get('issue_date_en', combined_data.get('date_of_issue', ''))),
                    'date_of_issue': combined_data.get('date_of_issue', ''),  # Legacy
                    # Expiry date (separate calendars when available)
                    'expiry_date': combined_data.get('date_of_expiry', ''),
                    'expiry_date_am': combined_data.get('date_of_expiry_am', combined_data.get('expiry_date_am', '')),
                    'expiry_date_en': combined_data.get('date_of_expiry_en', combined_data.get('expiry_date_en', combined_data.get('date_of_expiry', ''))),
                    'date_of_expiry': combined_data.get('date_of_expiry', ''),  # Legacy
                    'date_of_expiry_en': combined_data.get('date_of_expiry_en', combined_data.get('expiry_date_en', '')),  # Ensure this is set
                    'date_of_expiry_am': combined_data.get('date_of_expiry_am', combined_data.get('expiry_date_am', '')),  # Ensure this is set
                    # Map phone_number to phone for template compatibility
                    'phone': combined_data.get('phone_number', ''),  # Template uses phone
                    'phone_number': combined_data.get('phone_number', ''),  # Keep for compatibility
                    'photo_path': photo_path,  # Keep using uploaded profile photo
                    'qr_path': qr_extracted_path if qr_extracted_path else (qr_path if qr_path else None),  # Use uploaded QR or extracted QR
                    'extraction_method': extraction_method
                })
                
            except Exception as ocr_error:
                print(f"⚠️ OCR extraction failed: {ocr_error}")
                print("   Continuing with manual data entry...")
                import traceback
                traceback.print_exc()
        else:
            print("ℹ️ Not enough images for OCR extraction (need front and back)")
            print("   User will need to enter data manually in preview page")
            
            # Use manual FAN if provided even without OCR
            if manual_fan:
                extracted['fan'] = manual_fan
                extracted['fcn_full'] = manual_fan
                extracted['extraction_method'] = 'Manual'
                print(f"ℹ️ Using manual FAN without OCR: {manual_fan}")
        
        # Always generate serial number if not already set
        if not extracted.get('serial_number'):
            serial_number = id_service.generate_serial_number()
            extracted['serial_number'] = serial_number
            print(f"🔢 Generated serial number: {serial_number}")
        
        # Always use today's date as issue date (ignore JSON input)
        id_dates = get_id_dates()
        extracted['issue_date'] = id_dates['issue_date_greg']
        extracted['issue_date_en'] = id_dates['issue_date_greg']
        extracted['issue_date_am'] = id_dates['issue_date_eth']
        extracted['date_of_issue'] = id_dates['issue_date_greg']
        print(f"📅 Issue Date (English/Gregorian): {id_dates['issue_date_greg']}")
        print(f"📅 Issue Date (Amharic/Ethiopian): {id_dates['issue_date_eth']}")
        
        # Override with unified JSON data if provided
        if card_json_data:
            print("📝 Merging unified card JSON data into extracted data...")
            print(f"   Card JSON structure: {card_json_data}")
            
            # Extract personal_information section
            if 'personal_information' in card_json_data:
                personal_info = card_json_data['personal_information']
                
                # Full name
                if 'full_name' in personal_info:
                    if isinstance(personal_info['full_name'], dict):
                        extracted['full_name_en'] = personal_info['full_name'].get('english', '')
                        extracted['full_name_am'] = personal_info['full_name'].get('amharic', '')
                        extracted['name_en'] = personal_info['full_name'].get('english', '')
                        extracted['name_am'] = personal_info['full_name'].get('amharic', '')
                    else:
                        extracted['name_en'] = personal_info['full_name']
                        extracted['full_name_en'] = personal_info['full_name']
                
                # Date of birth
                if 'date_of_birth' in personal_info:
                    if isinstance(personal_info['date_of_birth'], dict):
                        extracted['dob_en'] = personal_info['date_of_birth'].get('english', '')
                        extracted['dob_am'] = personal_info['date_of_birth'].get('amharic', '')
                        extracted['birth_date_en'] = extracted['dob_en']
                        extracted['birth_date_am'] = extracted['dob_am']
                        extracted['date_of_birth'] = extracted['dob_en']
                    else:
                        extracted['dob_en'] = personal_info['date_of_birth']
                        extracted['birth_date'] = personal_info['date_of_birth']
                        extracted['date_of_birth'] = personal_info['date_of_birth']
                
                # Sex/Gender
                if 'sex' in personal_info:
                    if isinstance(personal_info['sex'], dict):
                        extracted['sex_en'] = personal_info['sex'].get('english', '')
                        extracted['sex_am'] = personal_info['sex'].get('amharic', '')
                        extracted['gender_en'] = personal_info['sex'].get('english', '')
                        extracted['gender_am'] = personal_info['sex'].get('amharic', '')
                    else:
                        extracted['sex'] = personal_info['sex']
                        extracted['gender_en'] = personal_info['sex']
                
                # Nationality
                if 'nationality' in personal_info:
                    if isinstance(personal_info['nationality'], dict):
                        extracted['nationality_en'] = personal_info['nationality'].get('english', '')
                        extracted['nationality_am'] = personal_info['nationality'].get('amharic', '')
                    else:
                        extracted['nationality_en'] = personal_info['nationality']
            
            # Extract card_information section
            if 'card_information' in card_json_data:
                card_info = card_json_data['card_information']
                
                # FAN number
                if 'fan' in card_info:
                    extracted['fan'] = card_info['fan']
                    extracted['fcn_full'] = card_info['fan']
                
                # FIN number
                if 'fin' in card_info:
                    extracted['fin'] = card_info['fin']
                    # Use FIN as FAN if FAN is not set
                    if not extracted.get('fan'):
                        extracted['fan'] = card_info['fin']
                        extracted['fcn_full'] = card_info['fin']
                
                # Note: issue_date is ignored from JSON - we always use today's date (set above)
                
                # Expiry date
                if 'expiry_date' in card_info:
                    if isinstance(card_info['expiry_date'], dict):
                        extracted['expiry_date_en'] = card_info['expiry_date'].get('english', '')
                        extracted['expiry_date_am'] = card_info['expiry_date'].get('amharic', '')
                        extracted['expiry_date'] = extracted['expiry_date_en']
                        extracted['date_of_expiry'] = extracted['expiry_date_en']
                    else:
                        extracted['expiry_date'] = card_info['expiry_date']
                        extracted['expiry_date_en'] = card_info['expiry_date']
                        extracted['date_of_expiry'] = card_info['expiry_date']
            
            # Extract contact_information section
            if 'contact_information' in card_json_data:
                contact_info = card_json_data['contact_information']
                
                # Phone number
                if 'phone_number' in contact_info:
                    extracted['phone'] = contact_info['phone_number']
                    extracted['phone_number'] = contact_info['phone_number']
                
                # Address
                if 'address' in contact_info:
                    addr = contact_info['address']
                    
                    # Region
                    if 'region' in addr:
                        if isinstance(addr['region'], dict):
                            extracted['region_en'] = addr['region'].get('english', '')
                            extracted['region_am'] = addr['region'].get('amharic', '')
                        else:
                            extracted['region_en'] = addr['region']
                    
                    # Sub city or zone
                    if 'sub_city_or_zone' in addr:
                        subcity = addr['sub_city_or_zone']
                        if isinstance(subcity, dict):
                            extracted['subcity_en'] = subcity.get('english', '')
                            extracted['subcity_am'] = subcity.get('amharic', '')
                        else:
                            extracted['subcity_en'] = subcity
                    
                    # Woreda or city
                    if 'woreda_or_city' in addr:
                        woreda = addr['woreda_or_city']
                        if isinstance(woreda, dict):
                            extracted['woreda_en'] = woreda.get('english', '')
                            extracted['woreda_am'] = woreda.get('amharic', '')
                        else:
                            extracted['woreda_en'] = woreda
            
            print(f"✓ Unified JSON data merged - extracted fields: {[k for k, v in extracted.items() if v and k not in ['photo_path', 'qr_path', 'front_image', 'back_image']]}")
        
        # Store in session
        session['extracted'] = extracted
        session['uploaded_images'] = uploaded_images
        
        # Calculate and store extraction time
        extraction_end_time = time.time()
        extraction_time = extraction_end_time - extraction_start_time
        session['extraction_time'] = round(extraction_time, 2)
        
        print("=" * 80)
        print(f"⏱️  EXTRACTION COMPLETED IN {extraction_time:.2f} SECONDS")
        print("=" * 80)
        print("✓ Data stored in session, redirecting to preview")
        print(f"   Photo path: {photo_path}")
        print(f"   Extracted data keys: {list(extracted.keys())}")
        print(f"   Non-empty extracted fields:")
        for key, value in extracted.items():
            if value and key not in ['photo_path', 'qr_path', 'front_image', 'back_image']:
                print(f"     {key}: {value}")
        print("=" * 80)
        
        # Redirect to preview page
        return redirect(url_for('main.preview'))
        
    except Exception as e:
        print(f"✗ Error in generate_id: {e}")
        import traceback
        traceback.print_exc()
        return render_template('error.html', 
                             message=f"Failed to process images: {str(e)}"), 500

@bp.route('/preview')
def preview():
    """
    Show preview of extracted data from OCR
    """
    data = session.get('extracted', {})
    uploaded_images = session.get('uploaded_images', {})
    
    # Debug: Print what data we have
    print("=" * 60)
    print("PREVIEW PAGE - Data received:")
    print(f"Extracted data keys: {list(data.keys())}")
    print(f"Extracted data: {data}")
    print(f"Uploaded images: {uploaded_images}")
    print("=" * 60)
    
    # Generate barcode from FAN number if available
    fan_number = data.get('fan') or data.get('fcn_full') or data.get('fin')
    if fan_number:
        # Clean the FAN number (remove any spaces or non-digits)
        clean_fan = ''.join(c for c in str(fan_number) if c.isdigit())
        
        if len(clean_fan) == 16:
            print(f"🔢 Generating barcode from valid 16-digit FAN: {clean_fan}")
            barcode_filename, formatted_fcn = id_service.generate_barcode(clean_fan)
            
            if barcode_filename:
                data['fcn_barcode'] = barcode_filename
                data['fcn_formatted'] = formatted_fcn
                data['fcn_full'] = clean_fan
                print(f"✓ Barcode generated: {barcode_filename}")
                print(f"✓ Formatted FCN: {formatted_fcn}")
            else:
                print("⚠️ Barcode generation failed")
                data['fcn_barcode'] = None
                data['fcn_formatted'] = clean_fan
        elif len(clean_fan) == 15:
            # Pad to 16 digits
            padded_fan = clean_fan + '0'
            print(f"🔢 Padding 15-digit FAN to 16 digits: {clean_fan} → {padded_fan}")
            barcode_filename, formatted_fcn = id_service.generate_barcode(padded_fan)
            
            if barcode_filename:
                data['fcn_barcode'] = barcode_filename
                data['fcn_formatted'] = formatted_fcn
                data['fcn_full'] = padded_fan
                print(f"✓ Barcode generated: {barcode_filename}")
                print(f"✓ Formatted FCN: {formatted_fcn}")
            else:
                print("⚠️ Barcode generation failed")
                data['fcn_barcode'] = None
                data['fcn_formatted'] = padded_fan
        else:
            print(f"⚠️ Invalid FAN length for barcode generation: {len(clean_fan)} digits (need 15-16). FAN: {clean_fan}")
            print("💡 Please manually enter a valid 16-digit FAN number in the preview page")
            data['fcn_barcode'] = None
            data['fcn_formatted'] = clean_fan
    else:
        print("⚠️ No FAN number available for barcode generation")
        data['fcn_barcode'] = None
        data['fcn_barcode'] = None
        data['fan_validation_error'] = f"FAN must be 15-16 digits (current: {len(fan_number) if fan_number else 0} digits)"
    
    # Update session with barcode info
    session['extracted'] = data
    
    # Get photo path from extracted data or uploaded images
    photo_path = data.get('photo_path')
    if not photo_path:
        photo_path = uploaded_images.get('photo')
    
    # Convert absolute path to relative path for template
    if photo_path:
        # Extract just the filename from the full path
        photo_filename = os.path.basename(photo_path)
        print(f"📸 Photo filename: {photo_filename}")
    else:
        photo_filename = None
    
    # Get front and back images
    front_image = data.get('front_image') or uploaded_images.get('front')
    back_image = data.get('back_image') or uploaded_images.get('back')
    
    # Convert to filenames
    front_filename = os.path.basename(front_image) if front_image else None
    back_filename = os.path.basename(back_image) if back_image else None
    
    # Get QR code path from extracted data
    qr_path = data.get('qr_path')
    qr_filename = None
    if qr_path and os.path.exists(qr_path):
        qr_filename = os.path.basename(qr_path)
        print(f"📱 QR code filename: {qr_filename}")
    else:
        print("ℹ️ No QR code extracted yet")
    
    # Get extraction time from session
    extraction_time = session.get('extraction_time', 0)
    
    return render_template('preview.html', 
                         data=data, 
                         photo=photo_filename,
                         qr=qr_filename,
                         front_image=front_filename,
                         back_image=back_filename,
                         extraction_time=extraction_time,
                         timestamp=datetime.now().timestamp())

@bp.route('/confirm_generate', methods=['POST'])
def confirm_generate():
    """
    ---
    post:
      summary: Confirm and generate ID card images
      consumes:
        - application/x-www-form-urlencoded
      parameters:
        - in: formData
          name: remove_white_bg
          type: boolean
          required: false
        - in: formData
          name: remove_black_bg
          type: boolean
          required: false
        - in: formData
          name: use_onnx_bg
          type: boolean
          required: false
        - in: formData
          name: city_type
          type: string
          required: false
      responses:
        302:
          description: Redirects to result page
        400:
          description: Invalid input
    """
    try:
        extracted = session.get('extracted', {})
        if not extracted:
            return "Session expired. Please upload the PDF again."
        
        # Get form values
        remove_white = request.form.get('remove_white_bg') == '1'
        remove_black = request.form.get('remove_black_bg') == '1'
        use_onnx_bg = request.form.get('use_onnx_bg') == '1'
        city_option = request.form.get('city_type', 'default')
        generate_front_only = request.form.get('generate_front_only') == '1'
        generate_reverse_only = request.form.get('generate_reverse_only') == '1'
        generate_mini_id = request.form.get('generate_mini_id') == '1'
        generate_old_id = request.form.get('generate_old_id') == '1'
        
        # Debug print before generation
        print("DEBUG: Session keys:", list(session.keys()))
        print("DEBUG: Extracted data keys:", list(extracted.keys()))
        print("DEBUG: Data before generation:", extracted)
        
        # Check if photo was updated via upload_photo endpoint
        photo_temp_path = os.path.join(config.STATIC_FOLDER, 'photo_temp.png')
        if os.path.exists(photo_temp_path):
            # Update photo_path to use the newly uploaded photo
            extracted['photo_path'] = photo_temp_path
            extracted['photo'] = photo_temp_path
            print(f"DEBUG: Updated photo_path to newly uploaded photo: {photo_temp_path}")
        
        # Check if QR was updated via upload_qr endpoint
        qr_temp_path = os.path.join(config.STATIC_FOLDER, 'qr_temp.png')
        if os.path.exists(qr_temp_path):
            # Update qr_path to use the newly uploaded QR
            extracted['qr_path'] = qr_temp_path
            print(f"DEBUG: Updated qr_path to newly uploaded QR: {qr_temp_path}")
        
        # Ensure we have the latest data from individual field updates
        # The extracted data should already contain all the updated fields
        # since update_field() updates session['extracted'] directly
        
        # Update nationality from session if available (legacy support)
        if 'nationality_am' in session and 'nationality_en' in session:
            extracted['nationality_am'] = session['nationality_am']
            extracted['nationality_en'] = session['nationality_en']
            print("DEBUG: Updated nationality from legacy session fields")
        
        # Apply smart formatting to address fields
        if all(key in extracted for key in ['region_am', 'subcity_am', 'woreda_am']):
            extracted["address_am"] = format_address_smart(
                extracted['region_am'], 
                extracted['subcity_am'], 
                extracted['woreda_am'], 
                'am'
            )
        
        if all(key in extracted for key in ['region_en', 'subcity_en', 'woreda_en']):
            extracted["address_en"] = format_address_smart(
                extracted['region_en'], 
                extracted['subcity_en'], 
                extracted['woreda_en'], 
                'en'
            )
        
        # Add user tracking information
        extracted['user_id'] = session.get('user_id', 0)  # Default to 0 if no user ID
        extracted['username'] = session.get('username', extracted.get('name_en', 'Unknown User'))
        extracted['telegram_user_id'] = session.get('telegram_user_id', 0)
        
        # Explicitly save the updated data back to session to ensure it's current
        session['extracted'] = extracted
        session.modified = True  # Force session to be saved
        
        print("DEBUG: Final data for generation:", extracted)
        print("DEBUG: Session data after update:", session.get('extracted'))
        
        # Generate ID card
        generated_files = id_service.generate_id_card(
            data=extracted,
            city_option=city_option,
            remove_white=remove_white,
            remove_black=remove_black,
            generate_front_only=generate_front_only,
            generate_reverse_only=generate_reverse_only,
            generate_mini_id=generate_mini_id,
            generate_old_id=generate_old_id,
            use_onnx_bg=use_onnx_bg
        )
        
        # Store in session
        session['generated_files'] = generated_files
        session['extracted'] = extracted  # Ensure data is still in session
        
        # Debug print after storing in session
        print("Generated files:", generated_files)
        print("Stored data:", session.get('extracted'))
        
        return redirect(url_for('main.result'))

    except Exception as e:
        print("Error in confirm_generate:", str(e))  # Debug print for errors
        return f"Failed to generate ID: {str(e)}"

@bp.route('/results')
def results():
    """
    ---
    get:
      summary: Show generated ID card results (alternative route)
      responses:
        200:
          description: Result page with generated ID cards
    """
    return result()

@bp.route('/result')
def result():
    """
    ---
    get:
      summary: Show generated ID card results
      responses:
        200:
          description: Result page with generated ID cards
    """
    files = session.get('generated_files', {})
    data = session.get('extracted', {})  # Get the extracted data from session
    
    # Debug print
    print("Session data:", data)
    print("Files:", files)

    def verify_file(filename: Optional[str]) -> Optional[str]:
        if not filename or filename == 'default.png':
            return None
        path = os.path.join(config.STATIC_FOLDER, filename)
        return filename if os.path.exists(path) else None

    # Ensure we have the name
    if not data.get('name_en'):
        print("Warning: name_en not found in session data")
    else:
        print("Found name_en:", data['name_en'])
    
    # Debug print for files being passed to template
    # Check if we have normal ID cards, mini ID cards, or old ID cards
    has_normal_ids = any(files.get(key) for key in ['front_color', 'front_bw', 'reverse', 'reverse_bw'])
    has_mini_ids = any(files.get(key) for key in ['mini_front_color', 'mini_front_bw'])
    has_old_ids = any(files.get(key) for key in ['old_front_color', 'old_front_bw', 'old_reverse_color', 'old_reverse_bw'])
    
    if has_old_ids and not has_normal_ids and not has_mini_ids:
        # Only old ID cards were generated
        front_color = None
        front_bw = None
        reverse = None
        reverse_bw = None
        mini_front_color = None
        mini_front_bw = None
        old_front_color = verify_file(files.get('old_front_color'))
        old_front_bw = verify_file(files.get('old_front_bw'))
        old_reverse_color = verify_file(files.get('old_reverse_color'))
        old_reverse_bw = verify_file(files.get('old_reverse_bw'))
    elif has_mini_ids and not has_normal_ids and not has_old_ids:
        # Only mini ID cards were generated (with default reverse)
        front_color = None
        front_bw = None
        reverse = verify_file(files.get('reverse'))
        reverse_bw = verify_file(files.get('reverse_bw'))
        mini_front_color = verify_file(files.get('mini_front_color'))
        mini_front_bw = verify_file(files.get('mini_front_bw'))
        old_front_color = None
        old_front_bw = None
        old_reverse_color = None
        old_reverse_bw = None
    else:
        # Normal ID cards were generated (with optional mini/old)
        front_color = verify_file(files.get('front_color'))
        front_bw = verify_file(files.get('front_bw'))
        reverse = verify_file(files.get('reverse'))
        reverse_bw = verify_file(files.get('reverse_bw'))
        mini_front_color = verify_file(files.get('mini_front_color'))
        mini_front_bw = verify_file(files.get('mini_front_bw'))
        old_front_color = verify_file(files.get('old_front_color'))
        old_front_bw = verify_file(files.get('old_front_bw'))
        old_reverse_color = verify_file(files.get('old_reverse_color'))
        old_reverse_bw = verify_file(files.get('old_reverse_bw'))
    
    print("Files being passed to template:")
    print("front_color:", front_color)
    print("front_bw:", front_bw)
    print("reverse:", reverse)
    print("reverse_bw:", reverse_bw)
    print("mini_front_color:", mini_front_color)
    print("mini_front_bw:", mini_front_bw)
    print("old_front_color:", old_front_color)
    print("old_front_bw:", old_front_bw)
    print("old_reverse_color:", old_reverse_color)
    print("old_reverse_bw:", old_reverse_bw)
        
    return render_template('result.html',
                         data=data,  # Pass the data to the template
                         front_color=front_color,
                         front_bw=front_bw,
                         reverse=reverse,
                         reverse_bw=reverse_bw,
                         mini_front_color=mini_front_color,
                         mini_front_bw=mini_front_bw,
                         old_front_color=old_front_color,
                         old_front_bw=old_front_bw,
                         old_reverse_color=old_reverse_color,
                         old_reverse_bw=old_reverse_bw)

@bp.route('/update_address', methods=['POST'])
def update_address():
    """
    ---
    post:
      summary: Update address information
      consumes:
        - application/x-www-form-urlencoded
      parameters:
        - in: formData
          name: region_am
          type: string
          required: false
        - in: formData
          name: region_en
          type: string
          required: false
        - in: formData
          name: subcity_am
          type: string
          required: false
        - in: formData
          name: subcity_en
          type: string
          required: false
        - in: formData
          name: woreda_am
          type: string
          required: false
        - in: formData
          name: woreda_en
          type: string
          required: false
      responses:
        200:
          description: Address updated
        400:
          description: Error updating address
    """
    try:
        # Get the current data from session
        extracted = session.get('extracted', {})
        
        # Update with new values
        extracted['region_am'] = request.form.get('region_am', '')
        extracted['region_en'] = request.form.get('region_en', '')
        extracted['subcity_am'] = request.form.get('subcity_am', '')
        extracted['subcity_en'] = request.form.get('subcity_en', '')
        extracted['woreda_am'] = request.form.get('woreda_am', '')
        extracted['woreda_en'] = request.form.get('woreda_en', '')
        
        # Update combined address fields
        extracted["address_am"] = f"{extracted['region_am']}, {extracted['subcity_am']}, {extracted['woreda_am']}"
        extracted["address_en"] = f"{extracted['region_en']}, {extracted['subcity_en']}, {extracted['woreda_en']}"
        
        # Save back to session
        session['extracted'] = extracted
        
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@bp.route('/update_nationality', methods=['POST'])
def update_nationality():
    """
    ---
    post:
      summary: Update nationality information
      consumes:
        - application/x-www-form-urlencoded
      parameters:
        - in: formData
          name: nationality_am
          type: string
          required: false
        - in: formData
          name: nationality_en
          type: string
          required: false
      responses:
        200:
          description: Nationality updated
        400:
          description: Error updating nationality
    """
    try:
        nationality_am = request.form.get('nationality_am')
        nationality_en = request.form.get('nationality_en')
        
        # Update the session data
        session['nationality_am'] = nationality_am
        session['nationality_en'] = nationality_en
        
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}) 

@bp.route('/update_field', methods=['POST'])
def update_field():
    """
    ---
    post:
      summary: Update individual field in session data
      consumes:
        - application/x-www-form-urlencoded
      parameters:
        - in: formData
          name: field_name
          type: string
          required: true
          description: Name of the field to update (e.g., name_am, name_en, phone)
        - in: formData
          name: value
          type: string
          required: true
          description: New value for the field
      responses:
        200:
          description: Field updated successfully
        400:
          description: Error updating field
    """
    try:
        field_name = request.form.get('field_name')
        value = request.form.get('value')
        
        print(f"DEBUG: Received field_name='{field_name}', value='{value}'")
        print(f"DEBUG: Form data: {dict(request.form)}")
        
        if not field_name:
            print("DEBUG: Field name is missing")
            return jsonify({'success': False, 'error': 'Field name is required'})
        
        # Get the current data from session
        extracted = session.get('extracted', {})
        print(f"DEBUG: Current session data keys: {list(extracted.keys())}")
        
        # Update the specific field
        extracted[field_name] = value
        print(f"DEBUG: Updated {field_name} to '{value}'")
        
        # Special handling for FAN field - also update related fields and regenerate barcode
        if field_name == 'fan':
            # Clean the FAN value (remove non-digits)
            clean_fan = ''.join(c for c in str(value) if c.isdigit())
            extracted['fan'] = clean_fan
            extracted['fcn_full'] = clean_fan
            print(f"DEBUG: Cleaned FAN to '{clean_fan}'")
            
            # Regenerate barcode if FAN is valid (16 digits)
            if len(clean_fan) == 16:
                try:
                    from app.services.id_card_service import IDCardService
                    id_service = IDCardService()
                    barcode_filename, formatted_fcn = id_service.generate_barcode(clean_fan)
                    
                    if barcode_filename:
                        extracted['fcn_barcode'] = barcode_filename
                        extracted['fcn_formatted'] = formatted_fcn
                        print(f"DEBUG: Regenerated barcode: {barcode_filename}")
                    else:
                        print("DEBUG: Barcode generation failed")
                        extracted['fcn_barcode'] = None
                except Exception as barcode_error:
                    print(f"DEBUG: Barcode generation error: {barcode_error}")
                    extracted['fcn_barcode'] = None
            else:
                print(f"DEBUG: FAN length invalid for barcode: {len(clean_fan)} digits")
                extracted['fcn_barcode'] = None
        
        # Update combined address fields if address components were changed
        if field_name in ['region_am', 'region_en', 'subcity_am', 'subcity_en', 'woreda_am', 'woreda_en']:
            if all(key in extracted for key in ['region_am', 'subcity_am', 'woreda_am']):
                extracted["address_am"] = f"{extracted['region_am']}, {extracted['subcity_am']}, {extracted['woreda_am']}"
                print(f"DEBUG: Updated address_am to '{extracted['address_am']}'")
            if all(key in extracted for key in ['region_en', 'subcity_en', 'woreda_en']):
                extracted["address_en"] = f"{extracted['region_en']}, {extracted['subcity_en']}, {extracted['woreda_en']}"
                print(f"DEBUG: Updated address_en to '{extracted['address_en']}'")
        
        # Save back to session
        session['extracted'] = extracted
        print(f"DEBUG: Session saved successfully")
        
        # Return barcode info if FAN was updated
        if field_name == 'fan' and extracted.get('fcn_barcode'):
            return jsonify({
                'success': True,
                'barcode_filename': extracted['fcn_barcode'],
                'fcn_formatted': extracted.get('fcn_formatted', '')
            })
        
        return jsonify({'success': True})
    except Exception as e:
        print(f"DEBUG: Error in update_field: {str(e)}")
        return jsonify({'success': False, 'error': str(e)})

@bp.route('/api/latest_images')
def latest_images():
    """
    ---
    get:
      summary: Get latest generated ID images
      responses:
        200:
          description: List of latest image filenames
    """
    import os
    from flask import current_app, jsonify
    static_folder = current_app.static_folder
    patterns = ['Front_Color', 'Front_Grayscale', 'Reverse_Color', 'Reverse_Grayscale']
    files = []
    for fname in os.listdir(static_folder):
        if fname.endswith('.png') and any(p in fname for p in patterns):
            files.append(fname)
    # Sort by modification time, newest first
    files = sorted(files, key=lambda x: os.path.getmtime(os.path.join(static_folder, x)), reverse=True)
    return jsonify(files[:4]) 

@bp.route('/reset_session', methods=['POST'])
def reset_session():
    """
    ---
    post:
      summary: Reset the session and delete generated ID images for the previous person
      responses:
        204:
          description: Session reset successfully
    """
    # Delete generated images for the previous person
    extracted = session.get('extracted', {})
    name_en = extracted.get('name_en', '').replace(' ', '_') if extracted else ''
    if name_en:
        static_folder = current_app.static_folder
        patterns = [
            f"{name_en}_Front_Color.png",
            f"{name_en}_Front_Grayscale.png",
            f"{name_en}_Reverse_Color.png",
            f"{name_en}_Reverse_Grayscale.png",
            f"{name_en}_Mini_Front_Color.png",
            f"{name_en}_Mini_Front_Grayscale.png"
        ]
        for fname in patterns:
            fpath = os.path.join(static_folder, fname)
            if os.path.exists(fpath):
                try:
                    os.remove(fpath)
                except Exception as e:
                    print(f"Failed to delete {fpath}: {e}")
    session.clear()
    return ('', 204) 

@bp.route('/check_session')
def check_session():
    """
    ---
    get:
      summary: Check if user session is valid
      responses:
        200:
          description: Session status
    """
    return jsonify({"session_valid": True})


@bp.route('/api/daily-reports', methods=['GET'])
def get_daily_reports():
    """Get all daily reports."""
    try:
        daily_service = DailyReportService()
        reports = daily_service.get_all_daily_reports()
        return jsonify({"success": True, "reports": reports})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@bp.route('/api/daily-reports/<date>', methods=['GET'])
def get_daily_report(date):
    """Get daily report for a specific date."""
    try:
        daily_service = DailyReportService()
        report = daily_service.get_daily_report(date)
        return jsonify({"success": True, "report": report})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@bp.route('/api/user-stats/<int:user_id>', methods=['GET'])
def get_user_stats(user_id):
    """Get stats for a specific user."""
    try:
        daily_service = DailyReportService()
        stats = daily_service.get_user_stats(user_id)
        return jsonify({"success": True, "stats": stats})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@bp.route('/api/generate-daily-report', methods=['POST'])
def generate_daily_report():
    """Generate daily report for today or specified date."""
    try:
        data = request.get_json() or {}
        date = data.get('date')  # Optional date parameter
        
        daily_service = DailyReportService()
        report = daily_service.generate_daily_report(date)
        return jsonify({"success": True, "report": report})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@bp.route('/api/users/<int:user_id>/pause', methods=['POST'])
def pause_user(user_id):
    """Pause a user."""
    try:
        data = request.get_json() or {}
        paused_by = data.get('paused_by', 'admin')
        
        daily_service = DailyReportService()
        success = daily_service.pause_user(user_id, paused_by)
        
        if success:
            return jsonify({"success": True, "message": f"User {user_id} paused successfully"})
        else:
            return jsonify({"success": False, "error": "Failed to pause user"}), 500
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@bp.route('/api/users/<int:user_id>/resume', methods=['POST'])
def resume_user(user_id):
    """Resume a user."""
    try:
        data = request.get_json() or {}
        resumed_by = data.get('resumed_by', 'admin')
        
        daily_service = DailyReportService()
        success = daily_service.resume_user(user_id, resumed_by)
        
        if success:
            return jsonify({"success": True, "message": f"User {user_id} resumed successfully"})
        else:
            return jsonify({"success": False, "error": "Failed to resume user"}), 500
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@bp.route('/api/users/<user_id>/status', methods=['GET'])
def get_user_status(user_id):
    """Get user status."""
    try:
        daily_service = DailyReportService()
        status = daily_service.get_user_status(int(user_id))
        return jsonify({"success": True, "status": status})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@bp.route('/api/users/<user_id>/status', methods=['PUT', 'PATCH'])
def update_user_status(user_id):
    """Update user access status in Firebase."""
    try:
        data = request.get_json()
        status = data.get('status')
        
        if not status:
            return jsonify({"success": False, "error": "Status is required"}), 400
        
        # Validate status
        valid_statuses = ['approved', 'not approved', 'pending', 'paused', 'rejected']
        if status not in valid_statuses:
            return jsonify({"success": False, "error": f"Invalid status. Must be one of: {', '.join(valid_statuses)}"}), 400
        
        # Update Firebase users collection
        telegram_id = str(user_id)
        success = firebase_service.update_user_access_status(telegram_id, status)
        
        if success:
            return jsonify({"success": True, "message": f"User {user_id} status updated to {status}"})
        else:
            return jsonify({"success": False, "error": "Failed to update user status"}), 500
            
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@bp.route('/api/user-statuses', methods=['GET'])
def get_all_user_statuses():
    """Get all user statuses."""
    try:
        daily_service = DailyReportService()
        statuses = daily_service.get_all_user_statuses()
        return jsonify({"success": True, "statuses": statuses})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@bp.route('/api/bot/pause', methods=['POST'])
def pause_bot():
    """Pause the bot."""
    try:
        data = request.get_json() or {}
        paused_by = data.get('paused_by', 'admin')
        
        daily_service = DailyReportService()
        success = daily_service.pause_bot(paused_by)
        
        if success:
            return jsonify({"success": True, "message": "Bot paused successfully"})
        else:
            return jsonify({"success": False, "error": "Failed to pause bot"}), 500
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@bp.route('/api/bot/resume', methods=['POST'])
def resume_bot():
    """Resume the bot."""
    try:
        data = request.get_json() or {}
        resumed_by = data.get('resumed_by', 'admin')
        
        daily_service = DailyReportService()
        success = daily_service.resume_bot(resumed_by)
        
        if success:
            return jsonify({"success": True, "message": "Bot resumed successfully"})
        else:
            return jsonify({"success": False, "error": "Failed to resume bot"}), 500
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@bp.route('/api/bot/status', methods=['GET'])
def get_bot_status():
    """Get bot status."""
    try:
        daily_service = DailyReportService()
        status = daily_service.get_bot_status()
        return jsonify({"success": True, "status": status})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500 