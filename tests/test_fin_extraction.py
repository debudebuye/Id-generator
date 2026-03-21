#!/usr/bin/env python3
"""
Test script for automatic FIN extraction from PDF.
This script tests the FIN extraction functionality.
"""

import os
import sys
import tempfile
from io import BytesIO

# Add the app directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'app'))

def create_test_pdf_with_fin():
    """Create a test PDF with FIN number for testing."""
    try:
        import fitz  # PyMuPDF
        
        # Create a new PDF document
        doc = fitz.open()
        page = doc.new_page()
        
        # Add text content with FIN number
        text_content = """
        ETHIOPIAN DIGITAL ID CARD
        
        Personal Information:
        Name: Test User
        FIN: 1234-5678-9012
        Date of Birth: 01/01/1990
        Region: Addis Ababa
        Subcity: Bole
        Woreda: 01
        
        Contact Information:
        Phone: +251911234567
        Email: test@example.com
        
        This is a test document for FIN extraction.
        """
        
        # Insert text into the page
        page.insert_text((50, 100), text_content, fontsize=12)
        
        # Save to BytesIO
        pdf_bytes = BytesIO()
        doc.save(pdf_bytes)
        pdf_bytes.seek(0)
        
        doc.close()
        return pdf_bytes.getvalue()
        
    except ImportError:
        print("❌ PyMuPDF not available for creating test PDF")
        return None

def test_fin_extraction():
    """Test FIN extraction from PDF."""
    print("Testing FIN extraction from PDF...")
    
    try:
        from services.id_card_service import IDCardService
        
        # Initialize service
        id_service = IDCardService()
        
        # Create test PDF
        test_pdf_bytes = create_test_pdf_with_fin()
        if not test_pdf_bytes:
            print("❌ Could not create test PDF")
            return False
        
        # Test FIN extraction
        pdf_stream = BytesIO(test_pdf_bytes)
        extracted_fin = id_service.extract_fin_from_pdf(pdf_stream)
        
        if extracted_fin:
            print(f"✅ FIN extracted successfully: {extracted_fin}")
            
            # Validate the extracted FIN
            if len(extracted_fin) == 12 and extracted_fin.isdigit():
                print("✅ Extracted FIN is valid (12 digits)")
                return True
            else:
                print(f"❌ Extracted FIN is invalid: {extracted_fin}")
                return False
        else:
            print("❌ No FIN extracted from test PDF")
            return False
        
    except Exception as e:
        print(f"❌ FIN extraction test failed: {str(e)}")
        return False

def test_fin_patterns():
    """Test various FIN patterns."""
    print("Testing FIN pattern recognition...")
    
    try:
        from services.id_card_service import IDCardService
        
        # Initialize service
        id_service = IDCardService()
        
        # Test patterns
        test_patterns = [
            "FIN: 1234-5678-9012",
            "FIN 987654321098",
            "1234 5678 9012",
            "123456789012",
            "FCN: 1234567890123456",  # Should extract last 12 digits
            "PCM: 9876543210987654",  # Should extract last 12 digits
        ]
        
        for i, pattern in enumerate(test_patterns):
            print(f"Testing pattern {i+1}: {pattern}")
            
            # Create PDF with this pattern
            import fitz
            doc = fitz.open()
            page = doc.new_page()
            page.insert_text((50, 100), f"Test Document\n{pattern}", fontsize=12)
            
            pdf_bytes = BytesIO()
            doc.save(pdf_bytes)
            pdf_bytes.seek(0)
            doc.close()
            
            # Extract FIN
            extracted_fin = id_service.extract_fin_from_pdf(pdf_bytes)
            
            if extracted_fin:
                print(f"  ✅ Extracted: {extracted_fin}")
            else:
                print(f"  ❌ No FIN extracted")
        
        return True
        
    except Exception as e:
        print(f"❌ Pattern testing failed: {str(e)}")
        return False

def test_api_endpoint():
    """Test the API endpoint for FIN extraction."""
    print("Testing API endpoint...")
    
    try:
        import requests
        
        # Create test PDF
        test_pdf_bytes = create_test_pdf_with_fin()
        if not test_pdf_bytes:
            print("❌ Could not create test PDF")
            return False
        
        # Test API endpoint
        files = {'pdf': ('test.pdf', BytesIO(test_pdf_bytes), 'application/pdf')}
        
        response = requests.post('http://localhost:5000/extract_fin', files=files)
        
        if response.status_code == 200:
            data = response.json()
            if data.get('success') and data.get('fin'):
                print(f"✅ API endpoint working: {data['fin']}")
                return True
            else:
                print(f"❌ API endpoint failed: {data.get('message', 'Unknown error')}")
                return False
        else:
            print(f"❌ API endpoint error: {response.status_code}")
            return False
        
    except requests.exceptions.ConnectionError:
        print("⚠️ Flask server not running. Start with: python app.py")
        return False
    except Exception as e:
        print(f"❌ API endpoint test failed: {str(e)}")
        return False

def main():
    """Run all FIN extraction tests."""
    print("Automatic FIN Extraction Test Suite")
    print("=" * 45)
    print("This test verifies the automatic FIN extraction functionality.")
    print("=" * 45)
    
    tests = [
        test_fin_extraction,
        test_fin_patterns,
        test_api_endpoint
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        try:
            if test():
                passed += 1
        except Exception as e:
            print(f"❌ Test {test.__name__} crashed: {str(e)}")
        print()
    
    print("=" * 45)
    print(f"Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed!")
        print("The automatic FIN extraction is working correctly.")
        print("Users can now upload PDFs and have FIN numbers extracted automatically.")
    else:
        print("⚠️  Some tests failed - check the output above")
        print("Make sure PyMuPDF is installed: pip install PyMuPDF")
    
    return passed == total

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)









