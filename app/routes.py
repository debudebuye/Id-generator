from flask import Blueprint, request, render_template, redirect, url_for, session, jsonify
from werkzeug.utils import secure_filename
import os
from typing import Dict, Optional
from io import BytesIO

from .config.settings import Config
from .services.id_card_service import IDCardService

# Create blueprint
bp = Blueprint('main', __name__)
config = Config()
id_service = IDCardService()

def allowed_file(filename: str) -> bool:
    """Check if file extension is allowed."""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in config.ALLOWED_EXTENSIONS

@bp.route('/')
def index():
    """Render the index page."""
    return render_template('index.html')

@bp.route('/health')
def health_check():
    return jsonify({"status": "healthy"})

@bp.route('/upload_photo', methods=['POST'])
def upload_photo():
    """Handle photo upload."""
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
    """Handle ID generation request."""
    if 'pdf' not in request.files:
        return redirect(request.url)

    pdf = request.files['pdf']
    raw_fin = request.form.get('fin', '').strip()
    pdf_format = request.form.get('pdf_format', 'default')

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
    """Show preview of extracted data."""
    data = session.get('extracted', {})
    photo_path = 'static/photo_temp.png' if os.path.exists(os.path.join(config.STATIC_FOLDER, 'photo_temp.png')) else None
    qr_path = 'static/qr_temp.png' if os.path.exists(os.path.join(config.STATIC_FOLDER, 'qr_temp.png')) else None
    return render_template('preview.html', data=data, photo=photo_path, qr=qr_path)

@bp.route('/confirm_generate', methods=['POST'])
def confirm_generate():
    """Handle ID card generation confirmation."""
    try:
        extracted = session.get('extracted', {})
        if not extracted:
            return "Session expired. Please upload the PDF again."
        
        # Get form values
        remove_white = request.form.get('remove_white_bg') == '1'
        remove_black = request.form.get('remove_black_bg') == '1'
        city_option = request.form.get('city_type', 'default')
        
        # Update nationality from session if available
        if 'nationality_am' in session and 'nationality_en' in session:
            extracted['nationality_am'] = session['nationality_am']
            extracted['nationality_en'] = session['nationality_en']
        
        # Generate ID card
        generated_files = id_service.generate_id_card(
            data=extracted,
            city_option=city_option,
            remove_white=remove_white,
            remove_black=remove_black
        )
        
        # Store in session
        session['generated_files'] = generated_files
        return redirect(url_for('main.result'))

    except Exception as e:
        return f"Failed to generate ID: {str(e)}"

@bp.route('/result')
def result():
    """Show generated ID card results."""
    files = session.get('generated_files', {})

    def verify_file(filename: Optional[str]) -> Optional[str]:
        if not filename or filename == 'default.png':
            return None
        path = os.path.join(config.STATIC_FOLDER, filename)
        return filename if os.path.exists(path) else None

    return render_template('result.html',
                         front_color=verify_file(files.get('front_color')),
                         front_bw=verify_file(files.get('front_bw')),
                         reverse=verify_file(files.get('reverse')),
                         reverse_bw=verify_file(files.get('reverse_bw')))

@bp.route('/update_address', methods=['POST'])
def update_address():
    """Update address information."""
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
    try:
        nationality_am = request.form.get('nationality_am')
        nationality_en = request.form.get('nationality_en')
        
        # Update the session data
        session['nationality_am'] = nationality_am
        session['nationality_en'] = nationality_en
        
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}) 