#!/usr/bin/env python3
"""
Script to download a pre-trained ONNX model for background removal.
This script downloads a U²-Net model that can be used for high-quality background removal.
"""

import os
import requests
import hashlib
from pathlib import Path

def download_file(url: str, filepath: str, expected_hash: str = None):
    """Download a file with optional hash verification."""
    print(f"Downloading {os.path.basename(filepath)}...")
    
    response = requests.get(url, stream=True)
    response.raise_for_status()
    
    total_size = int(response.headers.get('content-length', 0))
    downloaded = 0
    
    with open(filepath, 'wb') as f:
        for chunk in response.iter_content(chunk_size=8192):
            if chunk:
                f.write(chunk)
                downloaded += len(chunk)
                if total_size > 0:
                    percent = (downloaded / total_size) * 100
                    print(f"\rProgress: {percent:.1f}%", end='', flush=True)
    
    print(f"\nDownloaded: {filepath}")
    
    # Verify hash if provided
    if expected_hash:
        with open(filepath, 'rb') as f:
            file_hash = hashlib.sha256(f.read()).hexdigest()
        if file_hash != expected_hash:
            print(f"WARNING: Hash mismatch! Expected: {expected_hash}, Got: {file_hash}")
            return False
        else:
            print("Hash verification passed!")
    
    return True

def main():
    """Download ONNX model for background removal."""
    # Create models directory
    models_dir = Path(__file__).parent.parent / "app" / "models"
    models_dir.mkdir(exist_ok=True)
    
    # Model information
    # Note: These are placeholder URLs - in production, you would use actual model URLs
    model_info = {
        "u2net.onnx": {
            "url": "https://github.com/xuebinqin/U-2-Net/raw/master/saved_models/u2net/u2net.onnx",
            "description": "U²-Net model for salient object detection and background removal",
            "size": "~176MB"
        }
    }
    
    print("ONNX Model Downloader for Background Removal")
    print("=" * 50)
    
    for model_name, info in model_info.items():
        model_path = models_dir / model_name
        
        if model_path.exists():
            print(f"Model {model_name} already exists at {model_path}")
            continue
        
        print(f"\nModel: {model_name}")
        print(f"Description: {info['description']}")
        print(f"Size: {info['size']}")
        print(f"URL: {info['url']}")
        
        try:
            # Note: In a real implementation, you would provide the actual hash
            success = download_file(info['url'], str(model_path))
            if success:
                print(f"✅ Successfully downloaded {model_name}")
            else:
                print(f"❌ Failed to download {model_name}")
        except Exception as e:
            print(f"❌ Error downloading {model_name}: {str(e)}")
            print("You can manually download the model from the URL above")
    
    print("\n" + "=" * 50)
    print("Setup complete!")
    print(f"Models directory: {models_dir}")
    print("\nTo use the ONNX background removal:")
    print("1. Ensure the model file is in the models directory")
    print("2. The ONNX runtime will automatically detect and use the model")
    print("3. If no model is found, the system will fall back to simple color-based removal")

if __name__ == "__main__":
    main()











