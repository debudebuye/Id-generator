#!/usr/bin/env python3
"""
Tesseract OCR Installation Guide and Verification Script
This script provides step-by-step instructions for installing Tesseract OCR on Windows.
"""

import os
import sys
import subprocess
import platform
import webbrowser

def check_tesseract():
    """Check if Tesseract is already installed."""
    try:
        result = subprocess.run(['tesseract', '--version'], 
                              capture_output=True, text=True, timeout=10)
        if result.returncode == 0:
            print("✅ Tesseract OCR is already installed!")
            print(f"Version: {result.stdout.split()[1]}")
            return True
    except (subprocess.TimeoutExpired, FileNotFoundError):
        pass
    
    print("❌ Tesseract OCR is not installed")
    return False

def install_tesseract_manual():
    """Provide manual installation instructions."""
    print("\n" + "="*60)
    print("TESSERACT OCR MANUAL INSTALLATION")
    print("="*60)
    
    print("\n📥 STEP 1: Download Tesseract OCR")
    print("-" * 40)
    print("1. Open your web browser")
    print("2. Go to: https://github.com/UB-Mannheim/tesseract/wiki")
    print("3. Click on the latest Windows installer link")
    print("4. Download: tesseract-ocr-w64-setup-5.3.3.20231005.exe")
    
    # Open the download page
    try:
        webbrowser.open("https://github.com/UB-Mannheim/tesseract/wiki")
        print("✅ Download page opened in your browser")
    except:
        print("⚠️ Could not open browser automatically")
    
    print("\n📦 STEP 2: Install Tesseract OCR")
    print("-" * 40)
    print("1. Run the downloaded installer (tesseract-ocr-w64-setup-5.3.3.20231005.exe)")
    print("2. Follow the installation wizard")
    print("3. ⚠️ IMPORTANT: Check 'Add to PATH' during installation")
    print("4. Install to default location: C:\\Program Files\\Tesseract-OCR")
    print("5. Complete the installation")
    
    print("\n🔄 STEP 3: Restart Terminal/IDE")
    print("-" * 40)
    print("1. Close this terminal/IDE completely")
    print("2. Reopen your terminal/IDE")
    print("3. Navigate back to your project directory")
    
    print("\n✅ STEP 4: Verify Installation")
    print("-" * 40)
    print("Run this command to verify:")
    print("   tesseract --version")
    print("\nYou should see Tesseract version information if installed correctly.")

def test_installation():
    """Test if Tesseract is working after installation."""
    print("\n" + "="*60)
    print("TESTING TESSERACT INSTALLATION")
    print("="*60)
    
    if check_tesseract():
        print("\n🎉 SUCCESS! Tesseract OCR is working!")
        print("Your FIN extraction should now work automatically.")
        
        # Test pytesseract
        try:
            import pytesseract
            from PIL import Image, ImageDraw, ImageFont
            
            # Create a test image
            img = Image.new('RGB', (200, 50), color='white')
            draw = ImageDraw.Draw(img)
            
            try:
                font = ImageFont.truetype("arial.ttf", 20)
            except:
                font = ImageFont.load_default()
            
            # Draw test FIN
            test_fin = "679571631281"
            draw.text((10, 15), test_fin, fill='black', font=font)
            
            # Test OCR
            text = pytesseract.image_to_string(img, config='--oem 3 --psm 8 -c tessedit_char_whitelist=0123456789')
            text = text.strip()
            
            if test_fin in text:
                print("✅ pytesseract is working correctly!")
                print(f"✅ OCR test successful: '{text}'")
            else:
                print("⚠️ pytesseract installed but OCR quality needs improvement")
                print(f"OCR result: '{text}'")
                
        except ImportError:
            print("❌ pytesseract not installed")
            print("Install with: pip install pytesseract")
        except Exception as e:
            print(f"❌ OCR test failed: {str(e)}")
            
        return True
    else:
        print("❌ Tesseract OCR is still not installed or not in PATH")
        return False

def main():
    """Main installation guide."""
    print("Tesseract OCR Installation Guide")
    print("="*50)
    print("This will help you install Tesseract OCR for automatic FIN extraction.")
    print("Expected FIN: 679571631281")
    print("="*50)
    
    # Check current status
    if check_tesseract():
        print("\n🎉 Tesseract is already installed!")
        test_installation()
        return True
    
    print("\n❌ Tesseract OCR needs to be installed")
    
    # Provide installation instructions
    install_tesseract_manual()
    
    print("\n" + "="*60)
    print("NEXT STEPS")
    print("="*60)
    print("1. Follow the installation steps above")
    print("2. Restart your terminal/IDE")
    print("3. Run this script again to verify installation")
    print("4. Test FIN extraction with your PDF")
    print("\nAfter installation, your FIN extraction should work automatically!")
    
    return False

if __name__ == "__main__":
    success = main()
    if success:
        print("\n🎉 Installation complete! FIN extraction should work now.")
    else:
        print("\n📋 Please follow the installation steps above.")
    
    input("\nPress Enter to continue...")








