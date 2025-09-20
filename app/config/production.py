import os
from .settings import Config

class ProductionConfig(Config):
    """Production configuration for PythonAnywhere deployment"""
    
    # Security settings
    DEBUG = False
    TESTING = False
    
    # Use environment variables for sensitive data
    SECRET_KEY = os.environ.get('SECRET_KEY', 'dev-secret-key-change-in-production')
    
    # Database settings (if you add a database later)
    # SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL')
    
    # File upload settings
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB max file size
    
    # Logging
    LOG_LEVEL = 'INFO'
    
    # CORS settings (if needed)
    CORS_ORIGINS = os.environ.get('CORS_ORIGINS', '').split(',') if os.environ.get('CORS_ORIGINS') else []
    
    # Cache settings
    CACHE_TYPE = 'simple'
    CACHE_DEFAULT_TIMEOUT = 300
    
    # Session settings
    SESSION_COOKIE_SECURE = True
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'
    
    # Static file serving
    SEND_FILE_MAX_AGE_DEFAULT = 31536000  # 1 year
    
    # Error handling
    PROPAGATE_EXCEPTIONS = True
