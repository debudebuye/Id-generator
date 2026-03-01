#!/usr/bin/env python3
"""
Setup script for Tesseract OCR installation.
This script helps install Tesseract OCR for FIN extraction from PDFs.
"""

import os
import sys
import subprocess
import platform

def check_tesseract():
    """Check if Tesseract is installed and accessible."""
    try:
        result = subprocess.run(['tesseract', '--version'], 
                              capture_output=True, text=True, timeout=10)
        if result.returncode == 0:
            print("OK Tesseract OCR is already installed")
            print(f"Version: {result.stdout.split()[1]}")
            return True
    except (subprocess.TimeoutExpired, FileNotFoundError):
        pass
    
    print("X Tesseract OCR is not installed or not in PATH")
    return False

def install_tesseract_windows():
    """Install Tesseract on Windows."""
    print("Installing Tesseract OCR on Windows...")
    print("Please follow these steps:")
    print()
    print("1. Download Tesseract from: https://github.com/UB-Mannheim/tesseract/wiki")
    print("2. Run the installer (tesseract-ocr-w64-setup-5.3.3.20231005.exe)")
    print("3. During installation, make sure to check 'Add to PATH'")
    print("4. Restart your terminal/IDE after installation")
    print()
    print("Alternative: Install via Chocolatey:")
    print("  choco install tesseract")
    print()
    print("Alternative: Install via Scoop:")
    print("  scoop install tesseract")

def install_tesseract_macos():
    """Install Tesseract on macOS."""
    print("Installing Tesseract OCR on macOS...")
    try:
        # Try Homebrew first
        subprocess.run(['brew', 'install', 'tesseract'], check=True)
        print("OK Tesseract installed via Homebrew")
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("Homebrew not found. Please install Homebrew first:")
        print("  /bin/bash -c \"$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)\"")
        print("Then run: brew install tesseract")
        return False

def install_tesseract_linux():
    """Install Tesseract on Linux."""
    print("Installing Tesseract OCR on Linux...")
    
    # Detect package manager
    if os.path.exists('/usr/bin/apt-get'):
        # Debian/Ubuntu
        try:
            subprocess.run(['sudo', 'apt-get', 'update'], check=True)
            subprocess.run(['sudo', 'apt-get', 'install', '-y', 'tesseract-ocr'], check=True)
            print("OK Tesseract installed via apt-get")
            return True
        except subprocess.CalledProcessError:
            print("X Failed to install via apt-get")
            return False
    
    elif os.path.exists('/usr/bin/yum'):
        # CentOS/RHEL
        try:
            subprocess.run(['sudo', 'yum', 'install', '-y', 'tesseract'], check=True)
            print("OK Tesseract installed via yum")
            return True
        except subprocess.CalledProcessError:
            print("X Failed to install via yum")
            return False
    
    elif os.path.exists('/usr/bin/dnf'):
        # Fedora
        try:
            subprocess.run(['sudo', 'dnf', 'install', '-y', 'tesseract'], check=True)
            print("OK Tesseract installed via dnf")
            return True
        except subprocess.CalledProcessError:
            print("X Failed to install via dnf")
            return False
    
    else:
        print("X Unsupported Linux distribution")
        print("Please install Tesseract manually for your distribution")
        return False

def test_pytesseract():
    """Test if pytesseract can access Tesseract."""
    try:
        import pytesseract
        from PIL import Image
        import io
        
        # Create a simple test image with text
        img = Image.new('RGB', (200, 50), color='white')
        from PIL import ImageDraw, ImageFont
        draw = ImageDraw.Draw(img)
        
        try:
            font = ImageFont.truetype("arial.ttf", 20)
        except:
            font = ImageFont.load_default()
        
        draw.text((10, 15), "123456789012", fill='black', font=font)
        
        # Test OCR
        text = pytesseract.image_to_string(img, config='--psm 6')
        if "123456789012" in text:
            print("OK pytesseract is working correctly")
            return True
        else:
            print("WARNING: pytesseract installed but OCR quality is poor")
            return False
            
    except ImportError:
        print("X pytesseract not installed")
        print("Install with: pip install pytesseract")
        return False
    except Exception as e:
        print(f"X pytesseract test failed: {str(e)}")
        return False

def main():
    """Main setup function."""
    print("Tesseract OCR Setup for FIN Extraction")
    print("=" * 45)
    print("This script will help you install Tesseract OCR")
    print("for automatic FIN extraction from ~1.8-1.9 MB PDFs.")
    print("=" * 45)
    
    # Check current status
    tesseract_installed = check_tesseract()
    pytesseract_working = test_pytesseract()
    
    if tesseract_installed and pytesseract_working:
        print("SUCCESS: Tesseract OCR is fully configured!")
        print("FIN extraction from ~1.8-1.9 MB PDFs should work now.")
        return True
    
    print("\n" + "=" * 45)
    print("INSTALLATION REQUIRED")
    print("=" * 45)
    
    # Install based on operating system
    system = platform.system().lower()
    
    if system == 'windows':
        install_tesseract_windows()
    elif system == 'darwin':  # macOS
        install_tesseract_macos()
    elif system == 'linux':
        install_tesseract_linux()
    else:
        print(f"X Unsupported operating system: {system}")
        return False
    
    print("\n" + "=" * 45)
    print("NEXT STEPS")
    print("=" * 45)
    print("1. Install Tesseract OCR using the instructions above")
    print("2. Restart your terminal/IDE")
    print("3. Run this script again to verify installation")
    print("4. Test FIN extraction with a ~1.8-1.9 MB PDF")
    
    return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
