#!/usr/bin/env python3
"""
Setup script for offline background removal feature.
This script helps users set up the rembg library and download the required model.
"""

import os
import sys
import subprocess
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def check_python_version():
    """Check if Python version is compatible."""
    if sys.version_info < (3, 7):
        logger.error("❌ Python 3.7 or higher is required")
        return False
    logger.info(f"✅ Python version: {sys.version}")
    return True

def install_rembg():
    """Install the rembg library."""
    try:
        logger.info("📦 Installing rembg library...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", "rembg>=2.0.50"])
        logger.info("✅ rembg library installed successfully")
        return True
    except subprocess.CalledProcessError as e:
        logger.error(f"❌ Failed to install rembg: {e}")
        return False

def test_rembg_installation():
    """Test if rembg is properly installed."""
    try:
        import rembg
        logger.info("✅ rembg library imported successfully")
        return True
    except ImportError as e:
        logger.error(f"❌ Failed to import rembg: {e}")
        return False

def download_model():
    """Download the U²-Net model."""
    try:
        logger.info("🔄 Downloading U²-Net model (this may take a few minutes)...")
        from rembg import new_session
        
        # Create a session to trigger model download
        session = new_session('u2net')
        logger.info("✅ U²-Net model downloaded successfully")
        return True
    except Exception as e:
        logger.error(f"❌ Failed to download model: {e}")
        return False

def test_background_removal():
    """Test the background removal functionality."""
    try:
        logger.info("🧪 Testing background removal...")
        
        # Add app directory to path
        app_dir = os.path.join(os.path.dirname(__file__), '..', 'app')
        sys.path.insert(0, app_dir)
        
        from services.offline_bg_removal import OfflineBackgroundRemoval
        
        # Create service instance
        bg_removal = OfflineBackgroundRemoval()
        
        if not bg_removal.is_available():
            logger.error("❌ Background removal service not available")
            return False
        
        # Get model info
        info = bg_removal.get_model_info()
        logger.info(f"📊 Model Info: {info}")
        
        logger.info("✅ Background removal test passed")
        return True
        
    except Exception as e:
        logger.error(f"❌ Background removal test failed: {e}")
        return False

def main():
    """Main setup function."""
    print("🚀 Offline Background Removal Setup")
    print("=" * 50)
    print("This script will set up the offline background removal feature")
    print("using the rembg library and U²-Net model.")
    print("=" * 50)
    
    steps = [
        ("Checking Python version", check_python_version),
        ("Installing rembg library", install_rembg),
        ("Testing rembg installation", test_rembg_installation),
        ("Downloading U²-Net model", download_model),
        ("Testing background removal", test_background_removal)
    ]
    
    success_count = 0
    total_steps = len(steps)
    
    for step_name, step_function in steps:
        logger.info(f"🔄 {step_name}...")
        try:
            if step_function():
                success_count += 1
                logger.info(f"✅ {step_name} completed")
            else:
                logger.error(f"❌ {step_name} failed")
        except Exception as e:
            logger.error(f"❌ {step_name} failed with error: {e}")
        print()
    
    print("=" * 50)
    print(f"Setup Results: {success_count}/{total_steps} steps completed")
    
    if success_count == total_steps:
        print("🎉 Setup completed successfully!")
        print()
        print("The offline background removal feature is now ready to use.")
        print("You can:")
        print("1. Use 'Offline AI Background Removal' in the web interface")
        print("2. Run the test script: python tests/test_offline_bg_removal.py")
        print("3. Use the service programmatically in your code")
        print()
        print("The U²-Net model has been downloaded and cached locally.")
        print("All future background removal operations will work offline.")
    else:
        print("⚠️ Setup incomplete. Please check the errors above.")
        print()
        print("Common solutions:")
        print("1. Ensure you have Python 3.7 or higher")
        print("2. Check your internet connection for model download")
        print("3. Try running: pip install --upgrade pip")
        print("4. Try running: pip install rembg --no-cache-dir")
    
    return success_count == total_steps

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)










