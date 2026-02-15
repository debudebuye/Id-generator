"""
Automatic Amharic Language Data Installer for Tesseract OCR
Downloads and installs amh.traineddata automatically
"""
import os
import urllib.request
import sys

def install_amharic_language():
    """Download and install Amharic language data for Tesseract"""
    
    print("=" * 70)
    print("Amharic Language Data Installer for Tesseract OCR")
    print("=" * 70)
    print()
    
    # Tesseract tessdata directory
    tessdata_dir = r"C:\Program Files\Tesseract-OCR\tessdata"
    
    # Check if tessdata directory exists
    if not os.path.exists(tessdata_dir):
        print(f"❌ Tesseract tessdata directory not found: {tessdata_dir}")
        print("   Please check your Tesseract installation path")
        return False
    
    print(f"✓ Found Tesseract tessdata directory: {tessdata_dir}")
    
    # Target file path
    target_file = os.path.join(tessdata_dir, "amh.traineddata")
    
    # Check if already installed
    if os.path.exists(target_file):
        print(f"✓ Amharic language data is already installed!")
        print(f"  Location: {target_file}")
        return True
    
    # Download URL
    url = "https://github.com/tesseract-ocr/tessdata/raw/main/amh.traineddata"
    
    print()
    print(f"📥 Downloading Amharic language data from GitHub...")
    print(f"   URL: {url}")
    print(f"   Target: {target_file}")
    print()
    
    try:
        # Download with progress
        def download_progress(block_num, block_size, total_size):
            downloaded = block_num * block_size
            percent = min(100, (downloaded / total_size) * 100)
            bar_length = 40
            filled = int(bar_length * percent / 100)
            bar = '█' * filled + '░' * (bar_length - filled)
            print(f'\r   Progress: [{bar}] {percent:.1f}%', end='', flush=True)
        
        urllib.request.urlretrieve(url, target_file, download_progress)
        print()  # New line after progress bar
        print()
        print("✅ Download complete!")
        print(f"✓ Amharic language data installed successfully!")
        print(f"  Location: {target_file}")
        print()
        print("=" * 70)
        print("🎉 Installation Complete!")
        print("=" * 70)
        print()
        print("Next steps:")
        print("1. Restart your Flask application (Ctrl+C and run again)")
        print("2. Upload your ID card images")
        print("3. Amharic text should now be extracted correctly")
        print()
        
        return True
        
    except PermissionError:
        print()
        print("❌ Permission denied!")
        print()
        print("You need administrator privileges to install to Program Files.")
        print()
        print("Please run this script as Administrator:")
        print("1. Right-click on Command Prompt or PowerShell")
        print("2. Select 'Run as Administrator'")
        print("3. Navigate to this directory and run: python install_amharic_auto.py")
        print()
        print("OR manually download and copy:")
        print(f"1. Download: {url}")
        print(f"2. Copy to: {tessdata_dir}")
        print()
        return False
        
    except Exception as e:
        print()
        print(f"❌ Error during installation: {e}")
        print()
        print("Manual installation steps:")
        print(f"1. Download: {url}")
        print(f"2. Copy to: {tessdata_dir}")
        print()
        return False

if __name__ == "__main__":
    success = install_amharic_language()
    
    if success:
        print("Press Enter to exit...")
        input()
        sys.exit(0)
    else:
        print("Press Enter to exit...")
        input()
        sys.exit(1)
