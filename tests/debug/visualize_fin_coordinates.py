#!/usr/bin/env python3
"""
Script to visualize the FIN extraction coordinates on the PDF.
This helps verify that the coordinates are correctly positioned.
"""

import os
import sys
from io import BytesIO

def visualize_fin_region():
    """Visualize the FIN region on the PDF to verify coordinates."""
    print("Visualizing FIN extraction region")
    print("=" * 40)
    
    try:
        import fitz  # PyMuPDF
        from PIL import Image, ImageDraw
        import io
        
        # PDF file path
        pdf_path = "app/templates/cbac40b8-2574-4487-aedc-03638680c3ab.pdf"
        
        if not os.path.exists(pdf_path):
            print(f"❌ PDF file not found: {pdf_path}")
            return False
        
        # Open PDF
        doc = fitz.open(pdf_path)
        page = doc[0]  # First page
        
        # Convert page to image with high resolution
        mat = fitz.Matrix(2.0, 2.0)  # 2x zoom for better visualization
        pix = page.get_pixmap(matrix=mat)
        
        # Convert to PIL Image
        img_data = pix.tobytes("png")
        img = Image.open(io.BytesIO(img_data))
        
        # Get image dimensions
        width, height = img.size
        print(f"📏 Image size: {width}x{height}")
        
        # FIN coordinates from Photoshop (already scaled for the 2x image)
        fin_x = 2141
        fin_y = 1984
        fin_width = 184
        fin_height = 26
        
        # Calculate region bounds
        fin_region_left = max(0, int(fin_x))
        fin_region_right = min(width, int(fin_x + fin_width))
        fin_region_top = max(0, int(fin_y))
        fin_region_bottom = min(height, int(fin_y + fin_height))
        
        print(f"📍 FIN coordinates from Photoshop: x={fin_x}, y={fin_y}, width={fin_width}, height={fin_height}")
        print(f"📍 FIN region: left={fin_region_left}, top={fin_region_top}, right={fin_region_right}, bottom={fin_region_bottom}")
        
        # Create a copy of the image for drawing
        img_with_overlay = img.copy()
        draw = ImageDraw.Draw(img_with_overlay)
        
        # Draw rectangle around FIN region
        draw.rectangle(
            [fin_region_left, fin_region_top, fin_region_right, fin_region_bottom],
            outline="red",
            width=3
        )
        
        # Add label
        draw.text((fin_region_left, fin_region_top - 25), "FIN REGION", fill="red")
        
        # Save the visualization
        output_path = "fin_coordinates_visualization.png"
        img_with_overlay.save(output_path)
        print(f"✅ Visualization saved to: {output_path}")
        
        # Also save just the FIN region
        fin_region = img.crop((fin_region_left, fin_region_top, fin_region_right, fin_region_bottom))
        region_path = "fin_region_only.png"
        fin_region.save(region_path)
        print(f"✅ FIN region saved to: {region_path}")
        
        # Close PDF
        doc.close()
        
        print("\n📋 Files created:")
        print(f"  1. {output_path} - Full page with FIN region highlighted")
        print(f"  2. {region_path} - Just the FIN region")
        print("\nOpen these files to verify the coordinates are correct!")
        
        return True
        
    except ImportError as e:
        print(f"❌ Missing required library: {str(e)}")
        print("Install with: pip install PyMuPDF Pillow")
        return False
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        return False

def main():
    """Main function."""
    print("FIN Coordinates Visualization Tool")
    print("=" * 40)
    print("This tool creates visual representations of the FIN extraction region.")
    print("=" * 40)
    
    success = visualize_fin_region()
    
    if success:
        print("\n🎉 Visualization completed!")
        print("Check the generated PNG files to verify the coordinates.")
    else:
        print("\n❌ Visualization failed.")
        print("Make sure PyMuPDF and Pillow are installed.")

if __name__ == "__main__":
    main()