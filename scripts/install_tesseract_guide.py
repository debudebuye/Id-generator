#!/usr/bin/env python3
"""
Quick Tesseract OCR Installation Guide for Windows
"""

import os
import sys
import subprocess
import platform

def main():
    print("Tesseract OCR Installation Guide")
    print("=" * 40)
    print("Your FIN extraction is failing because Tesseract OCR is not installed.")
    print("Here's how to fix it:")
    print()
    
    if platform.system().lower() == 'windows':
        print("WINDOWS INSTALLATION:")
        print("1. Download Tesseract from:")
        print("   https://github.com/UB-Mannheim/tesseract/wiki")
        print()
        print("2. Download the latest installer:")
        print("   tesseract-ocr-w64-setup-5.3.3.20231005.exe")
        print()
        print("3. Run the installer and:")
        print("   ✅ Check 'Add to PATH' during installation")
        print("   ✅ Install to default location (C:\\Program Files\\Tesseract-OCR)")
        print()
        print("4. Restart your terminal/IDE after installation")
        print()
        print("5. Test installation by running:")
        print("   tesseract --version")
        print()
        print("ALTERNATIVE METHODS:")
        print("Method 1 - Chocolatey:")
        print("   choco install tesseract")
        print()
        print("Method 2 - Scoop:")
        print("   scoop install tesseract")
        print()
        print("Method 3 - Manual PATH setup:")
        print("   Add C:\\Program Files\\Tesseract-OCR to your system PATH")
        print()
    else:
        print("For other operating systems:")
        print("macOS: brew install tesseract")
        print("Ubuntu/Debian: sudo apt-get install tesseract-ocr")
        print("CentOS/RHEL: sudo yum install tesseract")
    
    print()
    print("CURRENT WORKAROUND:")
    print("The system is using text-based extraction as fallback.")
    print("This works but may not be as accurate as OCR.")
    print("Installing Tesseract will significantly improve accuracy.")
    print()
    print("After installation, your FIN extraction should work correctly!")

if __name__ == "__main__":
    main()








