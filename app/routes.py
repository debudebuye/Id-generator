from flask import Blueprint, request, render_template, redirect, url_for, session, jsonify, current_app
from werkzeug.utils import secure_filename
import os
import json
from typing import Dict, Optional, List
from io import BytesIO
from datetime import datetime

from .config.settings import Config
from .services.id_card_service import IDCardService
from .services.firebase_service import firebase_service
from .services.daily_report_service import DailyReportService

# Create blueprint
bp = Blueprint('main', __name__)
config = Config()
id_service = IDCardService()

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
    ---
    post:
      summary: Generate ID from document
      consumes:
        - multipart/form-data
      parameters:
        - in: formData
          name: document
          type: file
          required: true
          description: Document (PDF, DOC, DOCX) to extract data from
        - in: formData
          name: fin
          type: string
          required: true
          description: 12-digit FIN number
        - in: formData
          name: document_format
          type: string
          required: false
          enum: [default, residential_sheger]
          description: Document format type (only applies to PDF files)
        - in: formData
          name: skip_preview
          type: string
          required: false
          description: Skip data preview and generate ID directly
      responses:
        302:
          description: Redirects to preview page or results page
        400:
          description: Invalid input
    """
    if 'document' not in request.files:
        return redirect(request.url)

    document = request.files['document']
    raw_fin = request.form.get('fin', '').strip()
    document_format = request.form.get('document_format', 'auto')
    skip_preview = request.form.get('skip_preview') == 'on'
    
    # Check if file type is allowed
    if not allowed_file(document.filename):
        return "Invalid file type. Please upload a PDF, DOC, or DOCX file."

    # Validate FIN number
    clean_fin = raw_fin.replace('-', '')
    if len(clean_fin) != 12 or not clean_fin.isdigit():
        return "Invalid FIN number. Please enter exactly 12 digits."
    fin_number = f"{clean_fin[:4]}-{clean_fin[4:8]}-{clean_fin[8:12]}"

    try:
        # Read document into memory
        document_bytes = document.read()
        document_stream = BytesIO(document_bytes)
        document_stream.name = document.filename  # attach filename for format detection
        
        # Check if it's a PDF for data extraction
        if document.filename.lower().endswith('.pdf'):
            # Extract data from PDF in memory
            extracted = id_service.extract_pdf_data(document_stream, fin_number, document_format)
        else:
            # For DOC/DOCX files, create basic extracted data structure
            extracted = {
                'fin': fin_number,
                'name_en': '',
                'name_am': '',
                'nationality_en': 'Ethiopian',
                'nationality_am': 'ኢትዮጵያዊ',
                'region_en': '',
                'region_am': '',
                'subcity_en': '',
                'subcity_am': '',
                'woreda_en': '',
                'woreda_am': '',
                'address_en': '',
                'address_am': '',
                'birth_date': '',
                'sex': '',
                'issue_date': '',
                'expiry_date': '',
                'document_type': document.filename.split('.')[-1].upper()
            }
        
        # Store in session
        session['extracted'] = extracted
        
        # Check if user wants to skip preview
        if skip_preview:
            # Generate ID directly with optimized default settings
            try:
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
                
                # Add user tracking information for direct generation
                extracted['user_id'] = session.get('user_id', 0)
                extracted['username'] = session.get('username', extracted.get('name_en', 'Unknown User'))
                extracted['telegram_user_id'] = session.get('telegram_user_id', 0)
                
                # Generate ID card with optimized default settings
                generated_files = id_service.generate_id_card(
                    data=extracted,
                    city_option='default',
                    remove_white=True,  # Enable white background removal
                    remove_black=True,  # Enable black background removal
                    generate_mini_id=False,
                    generate_old_id=False,
                    use_onnx_bg=True    # Enable AI background removal for better results
                )
                
                # Store results in session
                session['generated_files'] = generated_files
                session['extracted'] = extracted  # Ensure data is still in session
                
                return redirect(url_for('main.result'))
                
            except Exception as e:
                # If direct generation fails, fall back to preview
                session['generation_error'] = f"Direct generation failed: {str(e)}"
                return redirect(url_for('main.preview'))
        else:
            # Normal flow - show preview
            return redirect(url_for('main.preview'))

    except Exception as e:
        return f"Failed to extract data: {str(e)}"

@bp.route('/preview')
def preview():
    """
    ---
    get:
      summary: Show preview of extracted data
      responses:
        200:
          description: Preview page
    """
    data = session.get('extracted', {})
    photo_path = 'static/photo_temp.png' if os.path.exists(os.path.join(config.STATIC_FOLDER, 'photo_temp.png')) else None
    qr_path = 'static/qr_temp.png' if os.path.exists(os.path.join(config.STATIC_FOLDER, 'qr_temp.png')) else None
    return render_template('preview.html', data=data, photo=photo_path, qr=qr_path)

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