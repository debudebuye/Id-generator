#!/usr/bin/env python3
"""
Manual FIN Override Script
This script helps you manually set the correct FIN when automatic extraction fails.
"""

import os
import sys

def main():
    print("Manual FIN Override")
    print("=" * 30)
    print("Since automatic FIN extraction is not working correctly,")
    print("you can manually enter the correct FIN number.")
    print()
    print("From your image, the correct FIN is: 679571631281")
    print()
    
    # Get user input
    manual_fin = input("Enter the correct FIN number (or press Enter to use 679571631281): ").strip()
    
    if not manual_fin:
        manual_fin = "679571631281"
    
    # Validate FIN
    if len(manual_fin) == 12 and manual_fin.isdigit():
        print(f"✅ Valid FIN: {manual_fin}")
        print()
        print("To use this FIN:")
        print("1. Go to the ID generation page")
        print("2. Upload your PDF")
        print("3. When prompted for FIN, enter:", manual_fin)
        print("4. Continue with ID generation")
        print()
        print("This will bypass the automatic extraction and use your manual input.")
    else:
        print(f"❌ Invalid FIN format: {manual_fin}")
        print("FIN must be exactly 12 digits (numbers only)")

if __name__ == "__main__":
    main()








