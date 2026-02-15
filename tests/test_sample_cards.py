"""
Test extraction on the sample front card images provided
"""
from app.services.ocr_extraction_service import OCRExtractionService
import cv2
import os

def test_sample_card(image_data, card_name):
    """Test extraction on a sample card"""
    print(f"\n{'='*60}")
    print(f"Testing: {card_name}")
    print('='*60)
    
    # Save the image temporarily
    temp_path = f'temp_test_{card_name.replace(" ", "_")}.png'
    with open(temp_path, 'wb') as f:
        f.write(image_data)
    
    try:
        ocr_service = OCRExtractionService()
        
        # Extract regions
        print("\n1. Extracting regions...")
        regions = ocr_service.extract_text_regions(temp_path)
        
        print(f"\n2. Region extraction results:")
        for region_name, text in regions.items():
            print(f"   {region_name}: {text[:100]}")
        
        # Parse the data
        print(f"\n3. Parsing data...")
        full_text = ocr_service.extract_text_from_image(temp_path)
        data = ocr_service.parse_front_card_data(full_text, image_path=temp_path)
        
        # Display results
        print(f"\n4. Extracted Data:")
        print(f"   ✓ Full Name (EN): {data.get('full_name_en', 'NOT FOUND')}")
        print(f"   ✓ Full Name (AM): {data.get('full_name_am', 'NOT FOUND')}")
        print(f"   ✓ Date of Birth: {data.get('date_of_birth', 'NOT FOUND')}")
        print(f"   ✓ Sex: {data.get('sex', 'NOT FOUND')}")
        print(f"   ✓ Date of Expiry: {data.get('date_of_expiry', 'NOT FOUND')}")
        print(f"   ✓ Date of Issue: {data.get('date_of_issue', 'NOT FOUND')}")
        print(f"   ✓ FAN: {data.get('fan', 'NOT FOUND')}")
        
        # Check if issue date was extracted
        if data.get('date_of_issue'):
            print(f"\n   ✅ Issue date successfully extracted!")
        else:
            print(f"\n   ⚠️  Issue date NOT extracted - needs debugging")
        
        return data
        
    finally:
        # Clean up temp file
        if os.path.exists(temp_path):
            os.remove(temp_path)

def main():
    """Main test function"""
    print("="*60)
    print("Sample Front Card Extraction Test")
    print("="*60)
    print("\nExpected issue dates from images:")
    print("  - Card 1 (Mabele): 2018/06/02")
    print("  - Card 2 (Dejay): 2018/06/03")
    print("  - Card 3 (Wudinesh): 2018/06/03")
    
    # Note: This script expects you to save the sample images
    # and update the paths below
    
    sample_cards = [
        # Add your sample card paths here
        # Example: ('path/to/card1.png', 'Mabele Mihretab Solomon'),
    ]
    
    if not sample_cards:
        print("\n⚠️  No sample cards configured")
        print("   Please save the sample images and update the script")
        print("\n   Or upload cards through the web interface and run:")
        print("   python debug_issue_date_phone.py")
        return
    
    results = []
    for image_path, card_name in sample_cards:
        if os.path.exists(image_path):
            with open(image_path, 'rb') as f:
                image_data = f.read()
            result = test_sample_card(image_data, card_name)
            results.append((card_name, result))
        else:
            print(f"\n⚠️  Image not found: {image_path}")
    
    # Summary
    print("\n" + "="*60)
    print("Summary")
    print("="*60)
    
    success_count = sum(1 for _, data in results if data.get('date_of_issue'))
    total_count = len(results)
    
    print(f"\nIssue Date Extraction: {success_count}/{total_count} successful")
    
    if success_count == total_count:
        print("✅ All cards extracted successfully!")
    else:
        print("⚠️  Some cards failed - check the output above")

if __name__ == '__main__':
    main()
