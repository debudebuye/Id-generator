# Project Structure

This document describes the organization of the Ethiopian Digital ID Card Generator project.

## Root Directory

```
.
├── app/                    # Main Flask application
├── admin_panel/            # React admin dashboard
├── config/                 # Configuration files
├── data/                   # Data files (allowed users, etc.)
├── docs/                   # Documentation
├── scripts/                # Utility scripts
├── templates/              # ID card templates
├── tests/                  # Test files and debug tools
├── telegram_bot/           # Telegram bot integration
├── app.py                  # Main application entry point
├── requirements.txt        # Python dependencies
└── Dockerfile             # Docker configuration
```

## Detailed Structure

### `/app` - Main Application
```
app/
├── config/                 # Application configuration
├── models/                 # Data models
├── routes/                 # Route handlers
├── services/               # Business logic services
│   ├── ocr_extraction_service.py    # OCR text extraction
│   ├── id_card_service.py           # ID card generation
│   ├── firebase_service.py          # Firebase integration
│   └── ...
├── static/                 # Static files (images, CSS, JS)
├── templates/              # HTML templates
├── utils/                  # Utility functions
└── __init__.py
```

### `/docs` - Documentation
```
docs/
├── guides/                 # User guides and tutorials
│   ├── OCR_EXTRACTION_GUIDE.md
│   ├── QR_EXTRACTION_QUICK_START.md
│   ├── NAME_EXTRACTION_FIX.md
│   └── ...
├── analysis/               # Technical analysis documents
└── ...
```

### `/tests` - Tests and Debug Tools
```
tests/
├── debug/                  # Debug scripts
│   ├── images/            # Debug output images
│   ├── debug_*.py         # Debug scripts
│   ├── diagnose_*.py      # Diagnostic scripts
│   ├── analyze_*.py       # Analysis scripts
│   └── visualize_*.py     # Visualization scripts
├── test_*.py              # Test scripts
└── test_*.html            # HTML test pages
```

### `/scripts` - Utility Scripts
```
scripts/
├── utilities/              # General utilities
│   ├── check_*.py         # Verification scripts
│   ├── fix_*.py           # Fix/repair scripts
│   ├── install_*.py       # Installation scripts
│   └── update_*.py        # Update scripts
├── setup_*.py             # Setup scripts
└── ...
```

### `/templates` - ID Card Templates
```
templates/
├── template.json           # Standard template
├── old_template.json       # Old format template
├── reverse_template.json   # Reverse side template
└── ...
```

## Key Files

- **app.py** - Main Flask application entry point
- **requirements.txt** - Python package dependencies
- **Dockerfile** - Docker container configuration
- **.env** - Environment variables (not in git)
- **.gitignore** - Git ignore rules

## Development Workflow

1. **Main application code** → `/app`
2. **Documentation** → `/docs/guides`
3. **Tests** → `/tests`
4. **Debug tools** → `/tests/debug`
5. **Utility scripts** → `/scripts/utilities`

## Recent Improvements

### OCR Extraction Optimization
- Removed slow full-image OCR (8 calls per image)
- Using only region-based extraction (faster and more accurate)
- Extended Amharic name region to capture full names
- Added padding to prevent text cutoff
- Prioritized Amharic language for Amharic fields

### File Organization
- Moved 50+ markdown files to `/docs/guides`
- Organized debug scripts into `/tests/debug`
- Moved test files to `/tests`
- Moved utility scripts to `/scripts/utilities`
- Cleaned up root directory

## Notes

- All debug images are stored in `/tests/debug/images`
- Documentation is organized by topic in `/docs/guides`
- Test scripts follow naming convention: `test_*.py`
- Debug scripts follow naming convention: `debug_*.py`
