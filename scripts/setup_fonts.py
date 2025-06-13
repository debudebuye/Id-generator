import os
import requests
import zipfile
from pathlib import Path

def download_inter_font():
    """Download and set up the Inter font."""
    # Create fonts directory if it doesn't exist
    fonts_dir = Path(__file__).parent.parent / 'fonts'
    inter_dir = fonts_dir / 'Inter'
    inter_dir.mkdir(parents=True, exist_ok=True)
    
    # Download Inter font
    url = "https://github.com/rsms/inter/releases/download/v4.0/Inter-4.0.zip"
    zip_path = inter_dir / "Inter.zip"
    
    print("Downloading Inter font...")
    response = requests.get(url)
    with open(zip_path, 'wb') as f:
        f.write(response.content)
    
    print("Extracting Inter font...")
    with zipfile.ZipFile(zip_path, 'r') as zip_ref:
        # Extract only the Bold font file
        for file in zip_ref.namelist():
            if file.endswith('Inter-Bold.ttf'):
                zip_ref.extract(file, inter_dir)
                # Move the file to the correct location
                os.rename(inter_dir / file, inter_dir / 'Inter-Bold.ttf')
                break
    
    # Clean up
    zip_path.unlink()
    print("Inter font setup complete!")

if __name__ == "__main__":
    download_inter_font() 