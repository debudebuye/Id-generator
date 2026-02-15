"""
Automatic installer for Amharic Tesseract language data
"""
import os
import sys
import urllib.request
import shutil

def check_admin():
    """Check if running with admin privileges"""
    try:
        import ctypes
        return ctypes.windll.shell32.IsUserAnAdmin()
    except:
        return False

def download_amharic_data(url, output_path):
    """Download Amharic language data file"""
    print(f"📥 Downloading Amharic language data...")
    print(f"   URL: {url}")
    print(f"   Destination: {output_path}")
    
    try:
        # Download with progress
        def report_progress(block_num, block_size, total_size):
            downloaded = block_num * block_size
            percent = min(100, (downloaded / total_size) * 100)
            sys.stdout.write(f"\r   Progress: {percent:.1f}% ({downloaded}/{total_size} bytes)")
            sys.stdout.flush()
        
        urllib.request.urlretrieve(url, output_path, reporthook=report_progress)
        print("\n✅ Download complete!")
        return True
    except Exception as e:
        print(f"\n❌ Download failed: {e}")
        return False

def install_amharic():
    """Install Amharic language data for Tesseract"""
    print("=" * 60)
    print("AMHARIC TESSERACT LANGUAGE DATA INSTALLER")
    print("=" * 60)
    
    # Check if running as admin
    if not check_admin():
        print("\n⚠️  WARNING: Not running as Administrator")
        print("   You may need Administrator privileges to copy files to Program Files")
        print("   If installation fails, please run this script as Administrator")
        print()
    
    # Define paths
    tesseract_dir = r"C:\Program Files\Tesseract-OCR"
    tessdata_dir = os.path.join(tesseract_dir, "tessdata")
    amh_file = os.path.join(tessdata_dir, "amh.traineddata")
    
    # Check if Tesseract is installed
    if not os.path.exists(tesseract_dir):
        print(f"❌ Tesseract not found at: {tesseract_dir}")
        print("   Please install Tesseract OCR first")
        return False
    
    print(f"✓ Tesseract found at: {tesseract_dir}")
    
    # Check if tessdata directory exists
    if not os.path.exists(tessdata_dir):
        print(f"❌ Tessdata directory not found: {tessdata_dir}")
        return False
    
    print(f"✓ Tessdata directory found: {tessdata_dir}")
    
    # Check if Amharic is already installed
    if os.path.exists(amh_file):
        file_size = os.path.getsize(amh_file)
        print(f"\n⚠️  Amharic language data already exists!")
        print(f"   File: {amh_file}")
        print(f"   Size: {file_size:,} bytes")
        
        response = input("\n   Do you want to reinstall? (y/n): ")
        if response.lower() != 'y':
            print("   Installation cancelled")
            return False
        
        print("   Removing existing file...")
        try:
            os.remove(amh_file)
            print("   ✓ Existing file removed")
        except Exception as e:
            print(f"   ❌ Could not remove existing file: {e}")
            print("   Please run as Administrator or manually delete the file")
            return False
    
    # Download Amharic language data
    print("\n" + "-" * 60)
    url = "https://github.com/tesseract-ocr/tessdata/raw/main/amh.traineddata"
    temp_file = "amh.traineddata"
    
    if not download_amharic_data(url, temp_file):
        return False
    
    # Verify downloaded file
    if not os.path.exists(temp_file):
        print(f"❌ Downloaded file not found: {temp_file}")
        return False
    
    file_size = os.path.getsize(temp_file)
    print(f"✓ Downloaded file size: {file_size:,} bytes")
    
    if file_size < 100000:  # Less than 100KB is suspicious
        print(f"⚠️  Warning: File size is unusually small")
        print(f"   Expected: ~1.2 MB, Got: {file_size:,} bytes")
        print(f"   The download may have failed")
        return False
    
    # Copy to Tesseract directory
    print("\n" + "-" * 60)
    print(f"📋 Copying to Tesseract directory...")
    print(f"   From: {temp_file}")
    print(f"   To: {amh_file}")
    
    try:
        shutil.copy2(temp_file, amh_file)
        print("✅ File copied successfully!")
    except PermissionError:
        print("❌ Permission denied!")
        print("\n   Please run this script as Administrator:")
        print("   1. Right-click on Command Prompt or PowerShell")
        print("   2. Select 'Run as Administrator'")
        print("   3. Run: python install_amharic_tesseract.py")
        
        # Clean up temp file
        try:
            os.remove(temp_file)
        except:
            pass
        return False
    except Exception as e:
        print(f"❌ Copy failed: {e}")
        
        # Clean up temp file
        try:
            os.remove(temp_file)
        except:
            pass
        return False
    
    # Clean up temp file
    try:
        os.remove(temp_file)
        print("✓ Temporary file cleaned up")
    except:
        pass
    
    # Verify installation
    print("\n" + "=" * 60)
    print("VERIFYING INSTALLATION")
    print("=" * 60)
    
    if os.path.exists(amh_file):
        file_size = os.path.getsize(amh_file)
        print(f"✅ Amharic language data installed successfully!")
        print(f"   File: {amh_file}")
        print(f"   Size: {file_size:,} bytes")
    else:
        print(f"❌ Installation verification failed")
        print(f"   File not found: {amh_file}")
        return False
    
    # Test with pytesseract
    print("\n" + "-" * 60)
    print("Testing Tesseract recognition...")
    
    try:
        import pytesseract
        import platform
        
        if platform.system() == 'Windows':
            pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'
        
        langs = pytesseract.get_languages(config='')
        
        if 'amh' in langs:
            print("✅ Amharic language detected by Tesseract!")
            print(f"   Available languages: {', '.join(sorted(langs))}")
        else:
            print("⚠️  Amharic not detected by Tesseract")
            print(f"   Available languages: {', '.join(sorted(langs))}")
            print("\n   This may be a caching issue. Try:")
            print("   1. Restart your Flask application")
            print("   2. Run: python test_amharic_ocr.py")
    except ImportError:
        print("⚠️  pytesseract not installed, skipping test")
        print("   Install with: pip install pytesseract")
    except Exception as e:
        print(f"⚠️  Could not test Tesseract: {e}")
    
    # Final instructions
    print("\n" + "=" * 60)
    print("NEXT STEPS")
    print("=" * 60)
    print("1. ✅ Amharic language data installed")
    print("2. 🔄 Restart your Flask application:")
    print("      - Press CTRL+C to stop the server")
    print("      - Run: python app.py")
    print("3. 🧪 Test the installation:")
    print("      - Run: python test_amharic_ocr.py")
    print("4. 📸 Upload a new ID card image to test Amharic extraction")
    print("=" * 60)
    
    return True

if __name__ == "__main__":
    try:
        success = install_amharic()
        if success:
            print("\n✅ Installation completed successfully!")
        else:
            print("\n❌ Installation failed")
            sys.exit(1)
    except KeyboardInterrupt:
        print("\n\n⚠️  Installation cancelled by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
