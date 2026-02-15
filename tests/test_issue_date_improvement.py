"""
Test script to verify improved issue date extraction
"""
import sys
import os

# Add app directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'app'))

from services.ocr_extraction_service import OCRExtractionService

def test_issue_date_extraction():
    """Test issue date extraction with actual ID card images"""
    
    print("=" * 60)
    print("Testing Issue Date Extraction Improvements")
    print("=" * 60)
    
    # Initialize OCR service
    ocr_service = OCRExtractionService()
    
    # Check if test images exist
    front_image = 'app/static/front_cropped.png'
    back_image = 'app/static/back_cropped.png'
    
    if not os.path.exists(front_image):
        print(f"❌ Front image not found: {front_image}")
        print("Please upload images through the web interface first")
        return
    
    if not os.path.exists(back_image):
        print(f"❌ Back image not found: {back_image}")
        print("Please upload images through the web interface first")
        return
    
    print(f"\n✓ Found front image: {front_image}")
    print(f"✓ Found back image: {back_image}")
    
    # Extract data
    print("\n" + "=" * 60)
    print("Extracting data from ID card...")
    print("=" * 60 + "\n")
    
    try:
        result = ocr_service.extract_all_data(front_image, back_image)
        
        print("\n" + "=" * 60)
        print("Extraction Results")
        print("=" * 60)
        
        # Check issue date
        issue_date = result.get('date_of_issue', '')
        if issue_date:
            print(f"\n✅ Issue Date Extracted: {issue_date}")
        else:
            print(f"\n⚠️ Issue Date Not Extracted")
        
        # Show all extracted fields
        print("\n" + "-" * 60)
        print("All Extracted Fields:")
        print("-" * 60)
        
        fields = [
            ('FAN Number', 'fan'),
            ('Full Name (EN)', 'full_name_en'),
            ('Full Name (AM)', 'full_name_am'),
            ('Date of Birth', 'date_of_birth'),
            ('Sex', 'sex'),
            ('Date of Issue', 'date_of_issue'),
            ('Date of Expiry', 'date_of_expiry'),
            ('Phone Number', 'phone_number'),
            ('FIN Number', 'fin'),
            ('Nationality (EN)', 'nationality_en'),
            ('Nationality (AM)', 'nationality_am'),
            ('Region (EN)', 'region_en'),
            ('Region (AM)', 'region_am'),
            ('Sub City (EN)', 'subcity_en'),
            ('Sub City (AM)', 'subcity_am'),
            ('Woreda (EN)', 'woreda_en'),
            ('Woreda (AM)', 'woreda_am'),
        ]
        
        extracted_count = 0
        for label, key in fields:
            value = result.get(key, '')
            if value:
                print(f"✓ {label:20s}: {value}")
                extracted_count += 1
            else:
                print(f"✗ {label:20s}: (not extracted)")
        
        print("\n" + "=" * 60)
        print(f"Extraction Rate: {extracted_count}/{len(fields)} fields ({extracted_count*100//len(fields)}%)")
        print("=" * 60)
        
        # Specific focus on issue date
        if issue_date:
            print("\n✅ SUCCESS: Issue date extraction is working!")
            print(f"   Extracted: {issue_date}")
        else:
            print("\n⚠️ Issue date not extracted - this is expected for some cards")
            print("   The vertical text on the right side can be challenging")
            print("   Users can manually enter this field in the preview page")
        
    except Exception as e:
        print(f"\n❌ Error during extraction: {e}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    test_issue_date_extraction()
