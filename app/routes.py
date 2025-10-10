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

# Create blueprint
bp = Blueprint('main', __name__)
config = Config()
id_service = IDCardService()

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
                        f"🎉 **Access Granted!**\n\n"
                        f"Hello {user_name}!\n\n"
                        f"Your access request has been **approved** by the administrator.\n"
                        f"You can now use the bot to generate your digital ID card.\n\n"
                        f"🔄 **To start:** Send /start or any message to the bot\n\n"
                        f"Thank you for your patience!"
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
                    "🚫 **Access Revoked**\n\n"
                    "Your access to the bot has been revoked by the administrator.\n"
                    "You can no longer use the bot to generate ID cards.\n\n"
                    "If you believe this is an error, please contact the administrator.\n"
                    "Contact Administrator:\n\n"
                    "@fayda\\_software\n\n"
                    "Thank you for your understanding."
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
        if os.path.exists(new_users_path):
            with open(new_users_path, 'r', encoding='utf-8') as f:
                items = json.load(f)
        for item in items:
            if str(item.get('id')) == str(user_id) or str(item.get('telegramId')) == str(user_id):
                item['status'] = 'rejected'
        with open(new_users_path, 'w', encoding='utf-8') as f:
            json.dump(items, f, ensure_ascii=False, indent=2)
        return jsonify({"status": "rejected", "message": f"User {user_id} rejected"})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

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

@bp.route('/generate_id', methods=['POST'])
def generate_id():
    """
    ---
    post:
      summary: Generate ID from PDF
      consumes:
        - multipart/form-data
      parameters:
        - in: formData
          name: pdf
          type: file
          required: true
          description: PDF document to extract data from
        - in: formData
          name: fin
          type: string
          required: true
          description: 12-digit FIN number
        - in: formData
          name: pdf_format
          type: string
          required: false
          enum: [default, residential_sheger]
          description: PDF format type
      responses:
        302:
          description: Redirects to preview page
        400:
          description: Invalid input
    """
    if 'pdf' not in request.files:
        return redirect(request.url)

    pdf = request.files['pdf']
    raw_fin = request.form.get('fin', '').strip()
    pdf_format = request.form.get('pdf_format', 'auto')

    # Validate FIN number
    clean_fin = raw_fin.replace('-', '')
    if len(clean_fin) != 12 or not clean_fin.isdigit():
        return "Invalid FIN number. Please enter exactly 12 digits."
    fin_number = f"{clean_fin[:4]}-{clean_fin[4:8]}-{clean_fin[8:12]}"

    try:
        # Read PDF into memory
        pdf_bytes = pdf.read()
        pdf_stream = BytesIO(pdf_bytes)
        
        # Extract data from PDF in memory
        extracted = id_service.extract_pdf_data(pdf_stream, fin_number, pdf_format)
        
        # Add address fields
        extracted["address_am"] = f"{extracted['region_am']}, {extracted['subcity_am']}, {extracted['woreda_am']}"
        extracted["address_en"] = f"{extracted['region_en']}, {extracted['subcity_en']}, {extracted['woreda_en']}"

        # Store in session
        session['extracted'] = extracted
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
        city_option = request.form.get('city_type', 'default')
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
        
        # Ensure address fields are properly formatted
        if all(key in extracted for key in ['region_am', 'subcity_am', 'woreda_am']):
            extracted["address_am"] = f"{extracted['region_am']}, {extracted['subcity_am']}, {extracted['woreda_am']}"
        if all(key in extracted for key in ['region_en', 'subcity_en', 'woreda_en']):
            extracted["address_en"] = f"{extracted['region_en']}, {extracted['subcity_en']}, {extracted['woreda_en']}"
        
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
            generate_mini_id=generate_mini_id,
            generate_old_id=generate_old_id
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