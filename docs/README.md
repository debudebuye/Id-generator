# Fyda ID Card Generator

A Flask-based web application for generating Ethiopian ID cards with support for multiple templates and languages.

## 🗂️ Project Structure

```
Fyda/
├── app/                    # Main Flask application
│   ├── config/            # Configuration files
│   ├── routes/            # Route definitions
│   ├── services/          # Business logic services
│   ├── static/            # Static files (CSS, JS, images)
│   ├── templates/         # HTML templates
│   └── utils/             # Utility functions
├── deployment/             # Deployment configuration
│   ├── wsgi.py            # WSGI entry point for PythonAnywhere
│   ├── gunicorn.conf.py   # Gunicorn configuration
│   ├── requirements-prod.txt # Production dependencies
│   ├── env.example        # Production environment template
│   ├── env.dev            # Development environment template
│   └── deploy.py          # Deployment automation script
├── docs/                   # Documentation
│   ├── PYTHONANYWHERE_DEPLOYMENT.md
│   ├── README_DEPLOYMENT.md
│   ├── ERROR_HANDLING_IMPROVEMENTS.md
│   ├── ACCESS_CONTROL_EXAMPLE.md
│   └── TELEGRAM_BOT_SETUP.md
├── templates/              # ID card templates
│   ├── *.png              # Template images
│   └── *.json             # Template configurations
├── fonts/                  # Font files
├── scripts/                # Utility scripts
│   ├── get_telegram_user_id.py
│   └── run_telegram_bot.py
├── tests/                  # Test files
├── config/                 # Configuration files
├── uploads/                # User uploads
└── telegram_bot/           # Telegram bot implementation
```

## 🚀 Quick Start

### Development
```bash
# Set up development environment
python deployment/deploy.py dev

# Start development server
python app.py
```

### Production (PythonAnywhere)
```bash
# Set up production environment
python deployment/deploy.py

# Follow deployment guide in docs/
```

## 📚 Documentation

- **Deployment Guide**: `docs/PYTHONANYWHERE_DEPLOYMENT.md`
- **Quick Reference**: `docs/README_DEPLOYMENT.md`
- **Error Handling**: `docs/ERROR_HANDLING_IMPROVEMENTS.md`
- **Access Control**: `docs/ACCESS_CONTROL_EXAMPLE.md`
- **Telegram Bot**: `docs/TELEGRAM_BOT_SETUP.md`

## 🔧 Configuration

### Environment Variables
- **Development**: Copy `deployment/env.dev` to `.env`
- **Production**: Copy `deployment/env.example` to `.env`

### Templates
All ID card templates are stored in the `templates/` folder:
- PNG images for visual templates
- JSON files for configuration data

## 🧪 Testing

Run tests from the `tests/` directory:
```bash
cd tests
python test_extraction.py
python test_mini_id_generation.py
python test_cleanup.py
```

## 📱 Telegram Bot

The Telegram bot is located in `telegram_bot/` and can be run independently:
```bash
cd telegram_bot
python run_bot.py
```

## 🚀 Deployment

### PythonAnywhere
1. Use `deployment/wsgi.py` as your WSGI file
2. Set working directory to project root
3. Configure static files: `/static/` → `app/static/`
4. Follow detailed guide in `docs/PYTHONANYWHERE_DEPLOYMENT.md`

### Local Production Testing
```bash
export FLASK_ENV=production
python deployment/wsgi.py
```

## 📁 Key Directories Explained

- **`app/`**: Core Flask application code
- **`deployment/`**: All deployment-related files and configurations
- **`docs/`**: Comprehensive documentation and guides
- **`templates/`**: ID card template files (images and configs)
- **`scripts/`**: Utility scripts for maintenance and setup
- **`tests/`**: Test files for application functionality
- **`config/`**: Project configuration and TODO files

## 🔒 Security

- Environment variables for sensitive configuration
- Production-ready security settings
- Separate development and production configurations
- Secure file handling and validation

## 📈 Performance

- Optimized static file serving
- Production-ready Gunicorn configuration
- Efficient image processing
- Caching strategies for production

## 🤝 Contributing

1. Follow the established folder structure
2. Add tests for new functionality
3. Update documentation as needed
4. Use appropriate configuration files

## 📞 Support

For deployment issues, check:
1. PythonAnywhere error logs
2. Application configuration
3. Environment variable setup
4. Documentation in `docs/` folder

---

**Note**: This project is organized for better maintainability and deployment. All deployment files are in the `deployment/` folder, documentation in `docs/`, and templates in `templates/`.

