# Quick Deployment Reference

## Files Created for Deployment

- `deployment/wsgi.py` - WSGI entry point for PythonAnywhere
- `deployment/gunicorn.conf.py` - Gunicorn configuration for production
- `deployment/requirements-prod.txt` - Production dependencies with pinned versions
- `app/config/production.py` - Production configuration
- `deployment/env.example` - Environment variables template for production
- `deployment/env.dev` - Environment variables template for development
- `deployment/deploy.py` - Deployment automation script
- `docs/PYTHONANYWHERE_DEPLOYMENT.md` - Comprehensive deployment guide

## Quick Start

### For Development (Local)
1. **Set up development environment:**
   ```bash
   python deployment/deploy.py dev
   ```

2. **Start development server:**
   ```bash
   python app.py
   ```

3. **Your app will be available at:** http://localhost:5000

### For Production (PythonAnywhere)
1. **Install production dependencies:**
   ```bash
   pip install -r deployment/requirements-prod.txt
   ```

2. **Set up production environment:**
   ```bash
   python deployment/deploy.py
   ```

3. **Edit .env file with your production values**

## Environment Setup

### Development Environment
- **File**: `deployment/env.dev` → `.env`
- **Purpose**: Local development with debug mode
- **Features**: Debug enabled, simple SECRET_KEY, localhost CORS

### Production Environment
- **File**: `deployment/env.example` → `.env`
- **Purpose**: Production deployment on PythonAnywhere
- **Features**: Debug disabled, secure SECRET_KEY, production CORS

## PythonAnywhere Configuration

- **WSGI file**: Use `deployment/wsgi.py`
- **Working directory**: Your project folder
- **Static files**: `/static/` → `app/static/`
- **Python version**: 3.9

## Environment Variables Required

### Development
```env
FLASK_ENV=development
FLASK_APP=app.py
SECRET_KEY=dev-secret-key-change-in-production
CORS_ORIGINS=http://localhost:5000,http://127.0.0.1:5000
```

### Production
```env
FLASK_ENV=production
FLASK_APP=deployment/wsgi.py
SECRET_KEY=your-secure-key-here
CORS_ORIGINS=https://yourdomain.com
```

## Key Changes Made

1. **Application Factory Pattern** - Added `create_app()` function
2. **Production Configuration** - Separate production settings
3. **Development Configuration** - Easy local development setup
4. **WSGI Entry Point** - `deployment/wsgi.py` for PythonAnywhere
5. **Security Hardening** - Production-ready security settings
6. **Dependency Management** - Pinned versions for stability
7. **Environment Detection** - Automatic config selection
8. **Organized Structure** - All deployment files in `deployment/` folder

## Testing Deployment

### Local Development
1. Run with development config:
   ```bash
   python deployment/deploy.py dev
   python app.py
   ```

2. Check logs and error handling
3. Verify static file serving
4. Test all application routes

### Production Testing
1. Test locally with production config:
   ```bash
   export FLASK_ENV=production
   python deployment/wsgi.py
   ```

2. Check production security settings
3. Verify error handling without debug mode

## Troubleshooting

### Development Issues
- Check that `.env` file exists and has correct values
- Verify Flask environment is set to development
- Check console output for configuration messages

### Production Issues
- Check PythonAnywhere error logs
- Verify virtual environment activation
- Ensure all dependencies are installed
- Check file permissions and paths
- Verify environment variables are set

## Commands Summary

```bash
# Development setup
python deployment/deploy.py dev

# Production setup
python deployment/deploy.py

# Start development server
python app.py

# Test production locally
export FLASK_ENV=production
python deployment/wsgi.py
```

## New Folder Structure

```
Fyda/
├── deployment/              # All deployment files
│   ├── wsgi.py             # WSGI entry point
│   ├── gunicorn.conf.py    # Gunicorn configuration
│   ├── requirements-prod.txt # Production dependencies
│   ├── env.example         # Production environment
│   ├── env.dev             # Development environment
│   └── deploy.py           # Deployment script
├── docs/                    # Documentation
├── templates/               # ID card templates
├── app/                     # Flask application
└── ...                     # Other project files
```

For detailed instructions, see `docs/PYTHONANYWHERE_DEPLOYMENT.md`.
