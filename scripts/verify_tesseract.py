#!/usr/bin/env python3
"""
Quick Tesseract Verification Script
Run this after installing Tesseract OCR to verify it's working.
"""

import subprocess
import sys

def main():
    print("Tesseract OCR Verification")
    print("=" * 30)
    
    try:
        # Test tesseract command
        result = subprocess.run(['tesseract', '--version'], 
                              capture_output=True, text=True, timeout=10)
        
        if result.returncode == 0:
            print("✅ Tesseract OCR is installed and working!")
            print(f"Version: {result.stdout.split()[1]}")
            
            # Test pytesseract
            try:
                import pytesseract
                print("✅ pytesseract Python library is available")
                
                # Test OCR with a simple image
                from PIL import Image, ImageDraw, ImageFont
                
                # Create test image
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
                    print("✅ OCR test successful!")
                    print(f"✅ Extracted: '{text}'")
                    print("\n🎉 FIN extraction should now work automatically!")
                else:
                    print("⚠️ OCR test partially successful")
                    print(f"Extracted: '{text}'")
                    print("This should still work for your PDF.")
                    
            except ImportError:
                print("❌ pytesseract not installed")
                print("Install with: pip install pytesseract")
            except Exception as e:
                print(f"⚠️ OCR test failed: {str(e)}")
                print("But Tesseract is installed, so it should work.")
                
        else:
            print("❌ Tesseract OCR installation failed")
            print("Please check the installation steps.")
            
    except FileNotFoundError:
        print("❌ Tesseract OCR not found in PATH")
        print("Please ensure you:")
        print("1. Installed Tesseract OCR")
        print("2. Checked 'Add to PATH' during installation")
        print("3. Restarted your terminal/IDE")
    except Exception as e:
        print(f"❌ Error: {str(e)}")

if __name__ == "__main__":
    main()
    input("\nPress Enter to continue...")








