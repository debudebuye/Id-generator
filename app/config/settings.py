import os
from pathlib import Path

class Config:
    # Base directory
    BASE_DIR = Path(__file__).parent.parent
    
    # Flask configuration
    SECRET_KEY = os.environ.get('SECRET_KEY', 'your-secret-key-here')
    
    # File paths
    STATIC_FOLDER = os.path.join(BASE_DIR, 'static')
    UPLOAD_FOLDER = os.path.join(BASE_DIR.parent, 'uploads')
    AMHARIC_FONT_PATH = os.path.join(BASE_DIR.parent, 'fonts', 'AbyssinicaSIL-2.300', 'AbyssinicaSIL-Regular.ttf')
    ENGLISH_FONT_PATH = os.path.join(BASE_DIR.parent, 'fonts', 'Inter', 'static', 'Inter_24pt-Bold.ttf')
    TEMPLATE_IMG = os.path.join(BASE_DIR.parent, 'normal_template.png')
    REVERSE_TEMPLATE_IMG = os.path.join(BASE_DIR.parent, 'reverse-template.png')
    TEMPLATE_JSON = os.path.join(BASE_DIR.parent, 'template.json')
    REVERSE_TEMPLATE_JSON = os.path.join(BASE_DIR.parent, 'reverse_template.json')
    # Mini template paths
    MINI_TEMPLATE_IMG = os.path.join(BASE_DIR.parent, 'mini_normal_template.png')
    MINI_TEMPLATE_JSON = os.path.join(BASE_DIR.parent, 'mini_template.json')
    
    # Old template paths
    OLD_TEMPLATE_IMG = os.path.join(BASE_DIR.parent, 'old_template.png')
    OLD_TEMPLATE_JSON = os.path.join(BASE_DIR.parent, 'old_template.json')
    OLD_REVERSE_TEMPLATE_IMG = os.path.join(BASE_DIR.parent, 'old_reverse_template.png')
    OLD_REVERSE_TEMPLATE_JSON = os.path.join(BASE_DIR.parent, 'old_reverse_template.json')
    
    # Allowed file extensions
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'pdf'}
    
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
            'region_am': 460,
            'region_en': 460,
            'subcity_am': 460,
            'subcity_en': 460,
            'woreda_am': 460,
            'woreda_en': 460,
            'address_am': 460,
            'address_en': 460
        }
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
                'region_en': [1340, 300],
                'subcity_am': [1340, 340],
                'subcity_en': [1340, 370],
                'woreda_am': [1340, 420],
                'woreda_en': [1340, 470]
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
                'region_am': [1340, 260],
                'region_en': [1340, 290],
                'subcity_am': [1340, 320],
                'subcity_en': [1340, 390],
                'woreda_am': [1340, 495],
                'woreda_en': [1340, 525]
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
                'region_am': [2120, 450],
                'region_en': [2120, 510],
                'subcity_am': [2120, 610],
                'subcity_en': [2120, 660],
                'woreda_am': [2120, 760],
                'woreda_en': [2120, 810]
            },
            'reverse': {
                'region_am': [1340, 270],
                'region_en': [1340, 300],
                'subcity_am': [1340, 340],
                'subcity_en': [1340, 370],
                'woreda_am': [1340, 420],
                'woreda_en': [1340, 470]
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
                'region_am': [1340, 260],
                'region_en': [1340, 290],
                'subcity_am': [1340, 320],
                'subcity_en': [1340, 390],
                'woreda_am': [1340, 495],
                'woreda_en': [1340, 525]
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
                'region_am': [1720, 150],
                'region_en': [1720, 210],
                'subcity_am': [1720, 280],
                'subcity_en': [1720, 390],
                'woreda_am': [1720, 510],
                'woreda_en': [1720, 550]
            },
            'reverse': {
                'region_am': [1340, 260],
                'region_en': [1340, 290],
                'subcity_am': [1340, 320],
                'subcity_en': [1340, 390],
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