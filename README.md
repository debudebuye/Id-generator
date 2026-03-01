# ID Card Processing System

## Project Structure

```
.
├── admin_panel/          # React-based admin dashboard
├── app/                  # Main Flask application
│   ├── config/          # Application configuration
│   ├── routes/          # API routes
│   ├── services/        # Business logic services
│   ├── static/          # Static assets
│   ├── templates/       # HTML templates
│   └── utils/           # Utility functions
├── config/              # Setup and configuration scripts
├── data/                # Application data files
├── deployment/          # Production deployment files
├── docs/                # Documentation
│   └── images/         # Documentation images
├── fonts/               # Font files
├── logs/                # Application logs
├── scripts/             # Utility scripts
│   ├── debug/          # Debugging scripts
│   ├── test/           # Test scripts
│   └── visualization/  # Visualization scripts
├── telegram_bot/        # Telegram bot integration
├── temp/                # Temporary files
├── templates/           # Additional templates
├── tests/               # Test files
├── uploads/             # User uploads
├── app.py              # Main application entry point
├── Dockerfile          # Docker configuration
└── requirements.txt    # Python dependencies
```

## Quick Start

1. Install dependencies: `pip install -r requirements.txt`
2. Configure environment: Copy `.env.example` to `.env`
3. Run application: `python app.py`

## Documentation

See the `docs/` directory for detailed documentation.
