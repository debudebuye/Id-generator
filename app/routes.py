from flask import Blueprint, request, render_template, redirect, url_for, session, jsonify, current_app
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
          enum: [default, residential_addis, residential_sheger]
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
        
        # Update nationality from session if available
        if 'nationality_am' in session and 'nationality_en' in session:
            extracted['nationality_am'] = session['nationality_am']
            extracted['nationality_en'] = session['nationality_en']
        
        # Debug print before generation
        print("Data before generation:", extracted)
        
        # Generate ID card
        generated_files = id_service.generate_id_card(
            data=extracted,
            city_option=city_option,
            remove_white=remove_white,
            remove_black=remove_black
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
    front_color = verify_file(files.get('front_color'))
    front_bw = verify_file(files.get('front_bw'))
    reverse = verify_file(files.get('reverse'))
    reverse_bw = verify_file(files.get('reverse_bw'))
    
    print("Files being passed to template:")
    print("front_color:", front_color)
    print("front_bw:", front_bw)
    print("reverse:", reverse)
    print("reverse_bw:", reverse_bw)
        
    return render_template('result.html',
                         data=data,  # Pass the data to the template
                         front_color=front_color,
                         front_bw=front_bw,
                         reverse=reverse,
                         reverse_bw=reverse_bw)

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
            f"{name_en}_Reverse_Grayscale.png"
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