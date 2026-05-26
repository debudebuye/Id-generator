from flask import Flask, make_response, request
from .config.settings import Config
from .config.production import ProductionConfig
import os
from dotenv import load_dotenv

def create_app(config_name=None):
    """Application factory pattern"""
    # Load environment variables from telegram_bot/.env
    telegram_bot_env_path = os.path.join(os.path.dirname(__file__), '..', 'telegram_bot', '.env')
    if os.path.exists(telegram_bot_env_path):
        load_dotenv(telegram_bot_env_path)
        print(f"Loaded environment variables from {telegram_bot_env_path}")
    
    app = Flask(__name__,
                template_folder='templates',
                static_folder='static')
    
    # Configure app based on environment
    if config_name == 'production' or os.environ.get('FLASK_ENV') == 'production':
        app.config.from_object(ProductionConfig)
        print("Using production configuration")
    else:
        app.config.from_object(Config)
        print("Using development configuration")
    
    # Ensure required directories exist
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
    os.makedirs(app.config['STATIC_FOLDER'], exist_ok=True)
    
    # Configure Tesseract OCR path for Windows
    try:
        import pytesseract
        import platform
        if platform.system() == 'Windows':
            # Set the path to tesseract executable
            pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'
            print("✅ Tesseract OCR configured for Windows")
    except ImportError:
        print("⚠️ pytesseract not available")
    
    # Initialize Swagger
    from flasgger import Swagger
    Swagger(app)
    
    # Import routes after app initialization
    from .routes import bp
    app.register_blueprint(bp)
    
    # Basic CORS support for admin_panel (Vite dev server and deployed origins)
    allowed_origins = os.environ.get('CORS_ORIGINS', 'http://localhost:5173').split(',')
    allowed_origins = [o.strip() for o in allowed_origins if o.strip()]

    @app.after_request
    def add_cors_headers(response):
        origin = os.environ.get('REQUEST_ORIGIN_OVERRIDE') or ''
        # If a specific origin is configured, use it; otherwise default to first allowed or '*'
        cors_origin = origin or (allowed_origins[0] if allowed_origins else '*')
        response.headers['Access-Control-Allow-Origin'] = cors_origin
        response.headers['Access-Control-Allow-Credentials'] = 'true'
        response.headers['Access-Control-Allow-Headers'] = 'Content-Type, Authorization, X-Requested-With'
        response.headers['Access-Control-Allow-Methods'] = 'GET, POST, PUT, PATCH, DELETE, OPTIONS'
        response.headers['Access-Control-Max-Age'] = '86400'
        return response
    
    @app.before_request
    def handle_preflight():
        if request.method == "OPTIONS":
            response = make_response()
            response.headers.add("Access-Control-Allow-Origin", "*")
            response.headers.add('Access-Control-Allow-Headers', "Content-Type, Authorization, X-Requested-With")
            response.headers.add('Access-Control-Allow-Methods', "GET, POST, PUT, PATCH, DELETE, OPTIONS")
            return response
    
    return app

# Create the Flask application instance
app = create_app()

# Export the app instance
__all__ = ['app', 'create_app'] 