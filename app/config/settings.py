import os
from pathlib import Path

class Config:
    # Base directory
    BASE_DIR = Path(__file__).parent.parent
    
    # Flask configuration
    SECRET_KEY = os.environ.get('SECRET_KEY', 'your-secret-key-here')
    
    # File paths - Updated for new folder structure
    STATIC_FOLDER = os.path.join(BASE_DIR, 'static')
    UPLOAD_FOLDER = os.path.join(BASE_DIR.parent, 'uploads')
    AMHARIC_FONT_PATH = os.path.join(BASE_DIR.parent, 'fonts', 'AbyssinicaSIL-2.300', 'AbyssinicaSIL-Regular.ttf')
    ENGLISH_FONT_PATH = os.path.join(BASE_DIR.parent, 'fonts', 'Inter', 'static', 'Inter_24pt-Bold.ttf')
    
    # Template paths - Updated to use templates folder
    TEMPLATE_IMG = os.path.join(BASE_DIR.parent, 'templates', 'normal_template.png')
    REVERSE_TEMPLATE_IMG = os.path.join(BASE_DIR.parent, 'templates', 'reverse-template.png')
    TEMPLATE_JSON = os.path.join(BASE_DIR.parent, 'templates', 'template.json')
    REVERSE_TEMPLATE_JSON = os.path.join(BASE_DIR.parent, 'templates', 'reverse_template.json')
    
    # Mini template paths - Updated to use templates folder
    MINI_TEMPLATE_IMG = os.path.join(BASE_DIR.parent, 'templates', 'mini_normal_template.png')
    MINI_TEMPLATE_JSON = os.path.join(BASE_DIR.parent, 'templates', 'mini_template.json')
    
    # Old template paths - Updated to use templates folder
    OLD_TEMPLATE_IMG = os.path.join(BASE_DIR.parent, 'templates', 'old_template.png')
    OLD_TEMPLATE_JSON = os.path.join(BASE_DIR.parent, 'templates', 'old_template.json')
    OLD_REVERSE_TEMPLATE_IMG = os.path.join(BASE_DIR.parent, 'templates', 'old_reverse_template.png')
    OLD_REVERSE_TEMPLATE_JSON = os.path.join(BASE_DIR.parent, 'templates', 'old_reverse_template.json')
    
    # Allowed file extensions
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'pdf', 'doc', 'docx'}
    
    # Image processing settings
    PHOTO_SIZES = {
        'large': (550, 700),
        'small': (199, 205),
        'reverse_large': (288, 421),
        'reverse_small': (127, 131)
    }
    
    # Text settings
    TEXT_MAX_WIDTH = {
        'front': {
            'region_am': 700,
            'region_en': 700,
            'subcity_am': 700,
            'subcity_en': 700,
            'woreda_am': 700,
            'woreda_en': 700,
            'address_am': 700,
            'address_en': 700
        },
        'reverse': {
            'region_am': 440,
            'region_en': 440,
            'subcity_am': 440,
            'subcity_en': 440,
            'woreda_am': 440,
            'woreda_en': 440,
            'address_am': 440,
            'address_en': 440
        }
    }

    # Default (normal) ID address font sizes
    ADDRESS_FONT_SIZES = {
        'front': {'am': 48, 'en': 50},
        'reverse': {'am': 30, 'en': 30}
    }

    # Old ID specific text max widths (can be tuned independently)
    OLD_TEXT_MAX_WIDTH = {
        'front': {
            'region_am': 700,
            'region_en': 700,
            'subcity_am': 700,
            'subcity_en': 700,
            'woreda_am': 700,
            'woreda_en': 700,
            'address_am': 700,
            'address_en': 700
        },
        'reverse': {
            'region_am': 330,
            'region_en': 330,
            'subcity_am': 330,
            'subcity_en': 330,
            'woreda_am': 330,
            'woreda_en': 330,
            'address_am': 330,
            'address_en': 330
        }
    }

    # Old ID specific address font sizes
    OLD_ADDRESS_FONT_SIZES = {
        'front': {'am': 46, 'en': 50},
        'reverse': {'am': 21, 'en': 21}
    }
    
    # Barcode settings
    BARCODE_OPTIONS = {
        'module_width': 1,  # Increased from 0.2 for wider bars
        'module_height': 40,  # Increased from 10 for taller barcode
        'font_size': 10,
        'quiet_zone': 5,
        'text_distance': 2,
        'write_text': False
    }
    
    # FCN Length
    FCN_LENGTH = 16
    
    # Address positions for different city types
    ADDRESS_POSITIONS = {
        'default': {
            'front': {
                'region_am': [2120, 450],
                'region_en': [2120, 510],
                'subcity_am': [2120, 610],
                'subcity_en': [2120, 660],
                'woreda_am': [2120, 760],
                'woreda_en': [2120, 810]
            },
            'reverse': {
                'region_am': [1340, 270],
                'region_en': [1340, 305],
                'subcity_am': [1340, 345],
                'subcity_en': [1340, 380],
                'woreda_am': [1340, 425],
                'woreda_en': [1340, 465]
            }
        },
        'shger': {
            'front': {
                'region_am': [2120, 450],
                'region_en': [2120, 510],
                'subcity_am': [2120, 580],
                'subcity_en': [2120, 690],
                'woreda_am': [2120, 810],
                'woreda_en': [2120, 850]
            },
            'reverse': {
                'region_am': [1341, 270],
                'region_en': [1341, 300],
                'subcity_am': [1341, 340],
                'subcity_en': [1341, 415],
                'woreda_am': [1341, 490],
                'woreda_en': [1341, 520]
            }
        },
        'koye': {
            'front': {
                'region_am': [2120, 450],
                'region_en': [2120, 510],
                'subcity_am': [2120, 550],
                'subcity_en': [2120, 600],
                'woreda_am': [2120, 650],
                'woreda_en': [2120, 700]
            },
            'reverse': {
                'region_am': [1340, 270],
                'region_en': [1340, 270],
                'subcity_am': [1340, 270],
                'subcity_en': [1340, 270],
                'woreda_am': [1340, 270],
                'woreda_en': [1340, 270]
            }
        },
        'tafo': {
            'front': {
                'region_am': [2120, 450],
                'region_en': [2120, 510],
                'subcity_am': [2120, 570],
                'subcity_en': [2120, 670],
                'woreda_am': [2120, 830],
                'woreda_en': [2120, 870]
            },
            'reverse': {
                'region_am': [1340, 260],
                'region_en': [1340, 290],
                'subcity_am': [1340, 320],
                'subcity_en': [1340, 390],
                'woreda_am': [1340, 495],
                'woreda_en': [1340, 525]
            }
        }
    } 
    
    # Old ID specific address positions (using the old template layout)
    OLD_ADDRESS_POSITIONS = {
        'default': {
            'front': {
                'region_am': [2050, 450],
                'region_en': [2050, 510],
                'subcity_am': [2050, 610],
                'subcity_en': [2050, 660],
                'woreda_am': [2050, 760],
                'woreda_en': [2050, 810]
            },
            'reverse': {
                'region_am': [970, 200],
                'region_en': [970, 230],
                'subcity_am': [970, 270],
                'subcity_en': [970, 300],
                'woreda_am': [970, 340],
                'woreda_en': [970, 365]
            }
        },
        'shger': {
            'front': {
                'region_am': [2035, 450],
                'region_en': [2035, 510],
                'subcity_am': [2035, 580],
                'subcity_en': [2035, 690],
                'woreda_am': [2035, 810],
                'woreda_en': [2035, 850]
            },
            'reverse': {
                'region_am': [970, 190],
                'region_en': [970, 220],
                'subcity_am': [970, 250],
                'subcity_en': [970, 300],
                'woreda_am': [970, 350],
                'woreda_en': [970, 380]
            }
        },
        'koye': {
            'front': {
                'region_am': [2120, 450],
                'region_en': [2120, 510],
                'subcity_am': [2120, 550],
                'subcity_en': [2120, 600],
                'woreda_am': [2120, 650],
                'woreda_en': [2120, 700]
            },
            'reverse': {
                'region_am': [1340, 270],
                'region_en': [1340, 270],
                'subcity_am': [1340, 270],
                'subcity_en': [1340, 270],
                'woreda_am': [1340, 270],
                'woreda_en': [1340, 270]
            }
        },
        'tafo': {
            'front': {
                'region_am': [2120, 450],
                'region_en': [2120, 510],
                'subcity_am': [2120, 570],
                'subcity_en': [2120, 670],
                'woreda_am': [2120, 830],
                'woreda_en': [2120, 870]
            },
            'reverse': {
                'region_am': [1340, 260],
                'region_en': [1340, 290],
                'subcity_am': [1340, 320],
                'subcity_en': [1340, 390],
                'woreda_am': [1340, 495],
                'woreda_en': [1340, 525]
            }
        }
    }
    
    # Mini ID specific address positions (currently same as default, but can be adjusted independently)
    MINI_ADDRESS_POSITIONS = {
        'default': {
            'front': {
                'region_am': [1410, 270],
                'region_en': [1410, 310],
                'subcity_am': [1410, 350],
                'subcity_en': [1410, 390],
                'woreda_am': [1410, 430],
                'woreda_en': [1410, 470]
            },
            'reverse': {
                 'region_am': [1340, 265],
                'region_en': [1340, 305],
                'subcity_am': [1340, 345],
                'subcity_en': [1340, 385],
                'woreda_am': [1340, 425],
                'woreda_en': [1340, 470]
            }
        },
        'shger': {
            'front': {
                'region_am': [1410, 280],
                'region_en': [1410, 310],
                'subcity_am': [1410, 350],
                'subcity_en': [1410, 405],
                'woreda_am': [1410, 470],
                'woreda_en': [1410, 500]
            },
            'reverse': {
                'region_am': [1340, 270],
                'region_en': [1340, 300],
                'subcity_am': [1340, 340],
                'subcity_en': [1340, 415],
                'woreda_am': [1340, 495],
                'woreda_en': [1340, 525]
            }
        },
        'koye': {
            'front': {
                'region_am': [1720, 150],
                'region_en': [1720, 210],
                'subcity_am': [1720, 250],
                'subcity_en': [1720, 300],
                'woreda_am': [1720, 350],
                'woreda_en': [1720, 400]
            },
            'reverse': {
                'region_am': [1340, 270],
                'region_en': [1340, 270],
                'subcity_am': [1340, 270],
                'subcity_en': [1340, 270],
                'woreda_am': [1340, 270],
                'woreda_en': [1340, 270]
            }
        },
        'tafo': {
            'front': {
                'region_am': [1720, 150],
                'region_en': [1720, 210],
                'subcity_am': [1720, 270],
                'subcity_en': [1720, 370],
                'woreda_am': [1720, 530],
                'woreda_en': [1720, 570]
            },
            'reverse': {
                'region_am': [1340, 260],
                'region_en': [1340, 290],
                'subcity_am': [1340, 320],
                'subcity_en': [1340, 390],
                'woreda_am': [1340, 495],
                'woreda_en': [1340, 525]
            }
        }
    } 

    # Mini ID text max widths
    MINI_TEXT_MAX_WIDTH = {
        'front': {
            'region_am': 650,
            'region_en': 650,
            'subcity_am': 650,
            'subcity_en': 650,
            'woreda_am': 650,
            'woreda_en': 650,
            'address_am': 650,
            'address_en': 650
        },
        'reverse': {
            'region_am': 450,
            'region_en': 450,
            'subcity_am': 450,
            'subcity_en': 450,
            'woreda_am': 450,
            'woreda_en': 450,
            'address_am': 450,
            'address_en': 450
        }
    }

    # Mini ID address font sizes
    MINI_ADDRESS_FONT_SIZES = {
        'front': {'am': 45, 'en': 45},
        'reverse': {'am': 34, 'en': 34}
    }