"""
Test barcode generation from FAN number
"""
import os
import sys

# Add app directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'app'))

from services.id_card_service import IDCardService

def test_barcode_generation():
    """Test barcode generation with different FAN formats"""
    print("=" * 60)
    print("Testing Barcode Generation from FAN")
    print("=" * 60)
    
    # Initialize ID card service
    id_service = IDCardService()
    
    # Test cases
    test_cases = [
        ("5164983502379087", "16-digit FAN (valid)"),
        ("516498350237908", "15-digit FAN (needs padding)"),
        ("51649835023790871", "17-digit FAN (needs truncation)"),
        ("453109604193018", "15-digit FAN from image"),
        ("4531096041930180", "16-digit FAN from image"),
    ]
    
    for fan_number, description in test_cases:
        print(f"\n{'='*60}")
        print(f"Test: {description}")
        print(f"Input FAN: {fan_number} ({len(fan_number)} digits)")
        
        # Normalize to 16 digits
        normalized_fan = fan_number
        if len(fan_number) == 15:
            normalized_fan = fan_number + '0'
            print(f"Padded to: {normalized_fan}")
        elif len(fan_number) > 16:
            normalized_fan = fan_number[:16]
            print(f"Truncated to: {normalized_fan}")
        
        # Generate barcode
        barcode_filename, formatted_fcn = id_service.generate_barcode(normalized_fan)
        
        if barcode_filename:
            print(f"✅ SUCCESS")
            print(f"   Barcode file: {barcode_filename}")
            print(f"   Formatted FCN: {formatted_fcn}")
            
            # Check if file exists
            barcode_path = os.path.join('app', 'static', barcode_filename)
            if os.path.exists(barcode_path):
                file_size = os.path.getsize(barcode_path)
                print(f"   File exists: Yes ({file_size} bytes)")
            else:
                print(f"   File exists: No (ERROR)")
        else:
            print(f"❌ FAILED")
            print(f"   Barcode generation returned None")
    
    print(f"\n{'='*60}")
    print("Testing Complete")
    print("=" * 60)

if __name__ == "__main__":
    test_barcode_generation()
