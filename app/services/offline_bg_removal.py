"""
Offline Background Removal Service using rembg library.
This service provides 100% offline background removal capabilities using pre-trained U²-Net models.
"""

import os
import logging
from typing import Optional, Union
from PIL import Image
import io
import base64

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class OfflineBackgroundRemoval:
    """
    Offline background removal service using rembg library.
    
    This service provides high-quality background removal that works completely offline
    after the initial model download. It uses U²-Net models for accurate results.
    """
    
    def __init__(self):
        """Initialize the offline background removal service."""
        self.rembg_session = None
        self.model_loaded = False
        self._initialize_rembg()
    
    def _initialize_rembg(self):
        """Initialize the rembg library and download models if needed."""
        try:
            from rembg import remove, new_session
            
            # Create a new session with U²-Net model (best for general use)
            # This will automatically download the model on first use
            logger.info("Initializing rembg with U²-Net model...")
            self.rembg_session = new_session('u2net')
            self.model_loaded = True
            logger.info("✅ rembg initialized successfully with U²-Net model")
            
        except ImportError:
            logger.error("❌ rembg library not installed. Please install with: pip install rembg")
            self.model_loaded = False
        except Exception as e:
            logger.error(f"❌ Failed to initialize rembg: {str(e)}")
            self.model_loaded = False
    
    def remove_background(self, input_image: Union[str, Image.Image, bytes]) -> Optional[Image.Image]:
        """
        Remove background from an image using rembg.
        
        Args:
            input_image: Input image as file path, PIL Image, or bytes
            
        Returns:
            PIL Image with background removed (RGBA format) or None if failed
        """
        if not self.model_loaded:
            logger.error("rembg model not loaded. Cannot remove background.")
            return None
        
        try:
            from rembg import remove
            
            logger.info("🔄 Starting background removal...")
            
            # Handle different input types
            if isinstance(input_image, str):
                # File path
                if not os.path.exists(input_image):
                    logger.error(f"Image file not found: {input_image}")
                    return None
                with open(input_image, 'rb') as f:
                    input_bytes = f.read()
            elif isinstance(input_image, Image.Image):
                # PIL Image
                buffer = io.BytesIO()
                input_image.save(buffer, format='PNG')
                input_bytes = buffer.getvalue()
            elif isinstance(input_image, bytes):
                # Raw bytes
                input_bytes = input_image
            else:
                logger.error("Unsupported input type. Expected file path, PIL Image, or bytes.")
                return None
            
            # Remove background using rembg
            logger.info("🎯 Processing image with U²-Net model...")
            output_bytes = remove(input_bytes, session=self.rembg_session)
            
            # Convert output to PIL Image
            output_image = Image.open(io.BytesIO(output_bytes))
            
            # Ensure it's in RGBA format
            if output_image.mode != 'RGBA':
                output_image = output_image.convert('RGBA')
            
            logger.info("✅ Background removal completed successfully")
            return output_image
            
        except Exception as e:
            logger.error(f"❌ Background removal failed: {str(e)}")
            return None
    
    def remove_background_from_file(self, input_path: str, output_path: Optional[str] = None) -> bool:
        """
        Remove background from an image file and save the result.
        
        Args:
            input_path: Path to input image file
            output_path: Path to save output image (optional, defaults to input_path with '_nobg' suffix)
            
        Returns:
            True if successful, False otherwise
        """
        try:
            if not os.path.exists(input_path):
                logger.error(f"Input file not found: {input_path}")
                return False
            
            # Generate output path if not provided
            if output_path is None:
                name, ext = os.path.splitext(input_path)
                output_path = f"{name}_nobg{ext}"
            
            logger.info(f"📁 Processing file: {input_path}")
            
            # Remove background
            result_image = self.remove_background(input_path)
            if result_image is None:
                return False
            
            # Save result
            result_image.save(output_path, 'PNG')
            logger.info(f"💾 Saved result to: {output_path}")
            
            return True
            
        except Exception as e:
            logger.error(f"❌ File processing failed: {str(e)}")
            return False
    
    def remove_background_to_bytes(self, input_image: Union[str, Image.Image, bytes]) -> Optional[bytes]:
        """
        Remove background and return result as bytes.
        
        Args:
            input_image: Input image as file path, PIL Image, or bytes
            
        Returns:
            Bytes of the processed image (PNG format) or None if failed
        """
        try:
            result_image = self.remove_background(input_image)
            if result_image is None:
                return None
            
            # Convert to bytes
            buffer = io.BytesIO()
            result_image.save(buffer, format='PNG')
            return buffer.getvalue()
            
        except Exception as e:
            logger.error(f"❌ Failed to convert to bytes: {str(e)}")
            return None
    
    def is_available(self) -> bool:
        """
        Check if the background removal service is available.
        
        Returns:
            True if service is ready, False otherwise
        """
        return self.model_loaded
    
    def get_model_info(self) -> dict:
        """
        Get information about the loaded model.
        
        Returns:
            Dictionary with model information
        """
        return {
            'model_loaded': self.model_loaded,
            'model_name': 'U²-Net' if self.model_loaded else None,
            'library': 'rembg',
            'offline_capable': True
        }

# Global instance for reuse
_offline_bg_removal = None

def get_offline_bg_removal() -> OfflineBackgroundRemoval:
    """Get global offline background removal instance."""
    global _offline_bg_removal
    if _offline_bg_removal is None:
        _offline_bg_removal = OfflineBackgroundRemoval()
    return _offline_bg_removal

def remove_background_offline(input_image: Union[str, Image.Image, bytes]) -> Optional[Image.Image]:
    """
    Convenience function for offline background removal.
    
    Args:
        input_image: Input image as file path, PIL Image, or bytes
        
    Returns:
        PIL Image with background removed or None if failed
    """
    bg_removal = get_offline_bg_removal()
    return bg_removal.remove_background(input_image)

def remove_background_to_bytes_offline(input_image: Union[str, Image.Image, bytes]) -> Optional[bytes]:
    """
    Convenience function for offline background removal returning bytes.
    
    Args:
        input_image: Input image as file path, PIL Image, or bytes
        
    Returns:
        Bytes of processed image or None if failed
    """
    bg_removal = get_offline_bg_removal()
    return bg_removal.remove_background_to_bytes(input_image)

def is_offline_bg_removal_available() -> bool:
    """
    Check if offline background removal is available.
    
    Returns:
        True if available, False otherwise
    """
    bg_removal = get_offline_bg_removal()
    return bg_removal.is_available()

def get_offline_bg_removal_info() -> dict:
    """
    Get information about the offline background removal service.
    
    Returns:
        Dictionary with service information
    """
    bg_removal = get_offline_bg_removal()
    return bg_removal.get_model_info()










