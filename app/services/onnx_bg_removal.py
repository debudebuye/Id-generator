"""
ONNX-based background removal service for offline processing.
Uses pre-trained models for high-quality background removal without external API calls.
"""

import os
import cv2
import numpy as np
import onnxruntime as ort
from PIL import Image
from typing import Optional, Tuple
import logging

logger = logging.getLogger(__name__)

class ONNXBackgroundRemoval:
    """ONNX-based background removal using pre-trained models."""
    
    def __init__(self, model_path: Optional[str] = None):
        """
        Initialize ONNX background removal service.
        
        Args:
            model_path: Path to ONNX model file. If None, will use default model.
        """
        self.model_path = model_path or self._get_default_model_path()
        self.session = None
        self.input_name = None
        self.output_name = None
        self.input_shape = None
        
        # Initialize the model
        self._load_model()
    
    def _get_default_model_path(self) -> str:
        """Get default model path or download if not exists."""
        # For now, we'll use a placeholder path
        # In production, you would download a pre-trained model like U²-Net or MODNet
        model_dir = os.path.join(os.path.dirname(__file__), '..', 'models')
        os.makedirs(model_dir, exist_ok=True)
        
        # Placeholder for actual model file
        model_path = os.path.join(model_dir, 'u2net.onnx')
        
        if not os.path.exists(model_path):
            logger.warning(f"ONNX model not found at {model_path}. Using fallback method.")
            return None
            
        return model_path
    
    def _load_model(self):
        """Load ONNX model and initialize session."""
        if not self.model_path or not os.path.exists(self.model_path):
            logger.warning("ONNX model not available, using fallback background removal")
            return
        
        try:
            # Initialize ONNX Runtime session
            providers = ['CPUExecutionProvider']
            if ort.get_device() == 'GPU':
                providers = ['CUDAExecutionProvider', 'CPUExecutionProvider']
            
            self.session = ort.InferenceSession(
                self.model_path,
                providers=providers
            )
            
            # Get input/output details
            self.input_name = self.session.get_inputs()[0].name
            self.output_name = self.session.get_outputs()[0].name
            self.input_shape = self.session.get_inputs()[0].shape
            
            logger.info(f"ONNX model loaded successfully: {self.model_path}")
            logger.info(f"Input shape: {self.input_shape}")
            
        except Exception as e:
            logger.error(f"Failed to load ONNX model: {str(e)}")
            self.session = None
    
    def remove_background_onnx(self, image: Image.Image) -> Image.Image:
        """
        Remove background using ONNX model.
        
        Args:
            image: Input PIL Image
            
        Returns:
            PIL Image with background removed (transparent)
        """
        if self.session is None:
            logger.warning("ONNX model not available, using fallback method")
            return self._fallback_background_removal(image)
        
        try:
            # Preprocess image
            input_tensor = self._preprocess_image(image)
            
            # Run inference
            outputs = self.session.run([self.output_name], {self.input_name: input_tensor})
            mask = outputs[0]
            
            # Postprocess mask with improved logic
            processed_mask = self._postprocess_mask(mask)
            
            # Apply mask to original image with better edge handling
            result_image = self._apply_mask_improved(image, processed_mask)
            
            return result_image
            
        except Exception as e:
            logger.error(f"ONNX background removal failed: {str(e)}")
            return self._fallback_background_removal(image)
    
    def _preprocess_image(self, image: Image.Image) -> np.ndarray:
        """Preprocess image for ONNX model input."""
        # Resize to model input size
        if len(self.input_shape) == 4:  # NCHW format
            target_size = (self.input_shape[3], self.input_shape[2])  # (width, height)
        else:
            target_size = (320, 320)  # Default size
        
        # Resize image
        resized = image.resize(target_size, Image.Resampling.LANCZOS)
        
        # Convert to RGB if needed
        if resized.mode != 'RGB':
            resized = resized.convert('RGB')
        
        # Convert to numpy array and normalize
        img_array = np.array(resized).astype(np.float32) / 255.0
        
        # Transpose to CHW format if needed
        if len(self.input_shape) == 4 and self.input_shape[1] == 3:
            img_array = np.transpose(img_array, (2, 0, 1))
        
        # Add batch dimension
        img_array = np.expand_dims(img_array, axis=0)
        
        return img_array
    
    def _postprocess_mask(self, mask: np.ndarray) -> np.ndarray:
        """Postprocess model output mask with improved logic."""
        # Remove batch dimension if present
        if len(mask.shape) == 4:
            mask = mask[0]
        
        # Get the first channel if multiple channels
        if len(mask.shape) == 3:
            mask = mask[0]
        
        # Apply adaptive threshold for better edge detection
        # Use a lower threshold to preserve more of the subject
        threshold = 0.3  # Lower threshold to be more conservative
        mask = (mask > threshold).astype(np.uint8) * 255
        
        # Apply morphological operations to clean up the mask
        kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (3, 3))
        mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel)
        mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel)
        
        # Apply Gaussian blur to soften edges
        mask = cv2.GaussianBlur(mask, (3, 3), 0)
        
        return mask
    
    def _apply_mask(self, original_image: Image.Image, mask: np.ndarray) -> Image.Image:
        """Apply mask to original image to create transparent background."""
        # Resize mask to match original image
        mask_resized = cv2.resize(mask, original_image.size, interpolation=cv2.INTER_NEAREST)
        
        # Convert original image to RGBA
        if original_image.mode != 'RGBA':
            original_rgba = original_image.convert('RGBA')
        else:
            original_rgba = original_image.copy()
        
        # Create alpha channel from mask
        alpha_channel = Image.fromarray(mask_resized, mode='L')
        
        # Apply alpha channel
        original_rgba.putalpha(alpha_channel)
        
        return original_rgba
    
    def _apply_mask_improved(self, original_image: Image.Image, mask: np.ndarray) -> Image.Image:
        """Apply mask with improved edge handling to preserve face details."""
        # Resize mask to match original image
        mask_resized = cv2.resize(mask, original_image.size, interpolation=cv2.INTER_CUBIC)
        
        # Convert original image to RGBA
        if original_image.mode != 'RGBA':
            original_rgba = original_image.convert('RGBA')
        else:
            original_rgba = original_image.copy()
        
        # Apply additional smoothing to the mask to preserve face details
        # Use bilateral filter to preserve edges while smoothing
        mask_smoothed = cv2.bilateralFilter(mask_resized, 9, 75, 75)
        
        # Create a more conservative mask that preserves more of the subject
        # Dilate the mask slightly to ensure we don't cut off parts of the face
        kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5, 5))
        mask_dilated = cv2.dilate(mask_smoothed, kernel, iterations=1)
        
        # Apply feathering to the edges for smoother transitions
        mask_feathered = cv2.GaussianBlur(mask_dilated, (5, 5), 0)
        
        # Create alpha channel from processed mask
        alpha_channel = Image.fromarray(mask_feathered, mode='L')
        
        # Apply alpha channel
        original_rgba.putalpha(alpha_channel)
        
        return original_rgba
    
    def _fallback_background_removal(self, image: Image.Image) -> Image.Image:
        """
        Improved fallback background removal using OpenCV-based methods.
        This is used when ONNX model is not available.
        """
        try:
            # Convert PIL to OpenCV
            cv_image = cv2.cvtColor(np.array(image), cv2.COLOR_RGB2BGR)
            original_size = cv_image.shape[:2]
            
            # Resize for processing (faster and more stable)
            scale_factor = 0.5
            new_size = (int(original_size[1] * scale_factor), int(original_size[0] * scale_factor))
            cv_image_small = cv2.resize(cv_image, new_size)
            
            # Convert to HSV for better color segmentation
            hsv = cv2.cvtColor(cv_image_small, cv2.COLOR_BGR2HSV)
            
            # Create masks for different background types
            masks = []
            
            # White/light background detection (more conservative)
            lower_white = np.array([0, 0, 180])  # Lower threshold
            upper_white = np.array([180, 50, 255])
            mask_white = cv2.inRange(hsv, lower_white, upper_white)
            masks.append(mask_white)
            
            # Very light gray backgrounds
            lower_light_gray = np.array([0, 0, 150])
            upper_light_gray = np.array([180, 30, 200])
            mask_light_gray = cv2.inRange(hsv, lower_light_gray, upper_light_gray)
            masks.append(mask_light_gray)
            
            # Combine all background masks
            combined_mask = np.zeros_like(mask_white)
            for mask in masks:
                combined_mask = cv2.bitwise_or(combined_mask, mask)
            
            # Apply morphological operations to clean up the mask
            kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (3, 3))
            combined_mask = cv2.morphologyEx(combined_mask, cv2.MORPH_CLOSE, kernel)
            combined_mask = cv2.morphologyEx(combined_mask, cv2.MORPH_OPEN, kernel)
            
            # Dilate the mask slightly to be more conservative (preserve more of the subject)
            kernel_dilate = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5, 5))
            combined_mask = cv2.dilate(combined_mask, kernel_dilate, iterations=1)
            
            # Apply Gaussian blur to soften edges
            combined_mask = cv2.GaussianBlur(combined_mask, (5, 5), 0)
            
            # Resize mask back to original size
            mask_resized = cv2.resize(combined_mask, (original_size[1], original_size[0]), interpolation=cv2.INTER_CUBIC)
            
            # Invert mask (we want to keep the subject, remove background)
            mask_final = cv2.bitwise_not(mask_resized)
            
            # Convert back to PIL
            result_image = Image.fromarray(cv_image)
            result_image = result_image.convert('RGBA')
            
            # Apply mask as alpha channel
            alpha_channel = Image.fromarray(mask_final, mode='L')
            result_image.putalpha(alpha_channel)
            
            return result_image
            
        except Exception as e:
            logger.error(f"Fallback background removal failed: {str(e)}")
            # Return original image if all methods fail
            return image.convert('RGBA')
    
    def remove_background_simple(self, image: Image.Image, remove_white: bool = True, remove_black: bool = True) -> Image.Image:
        """
        Improved simple color-based background removal with better face preservation.
        
        Args:
            image: Input PIL Image
            remove_white: Whether to remove white backgrounds
            remove_black: Whether to remove black backgrounds
            
        Returns:
            PIL Image with background removed
        """
        try:
            # Convert to numpy array
            img_array = np.array(image)
            
            if image.mode != 'RGBA':
                # Convert to RGBA
                if image.mode == 'RGB':
                    img_array = np.concatenate([img_array, np.full((*img_array.shape[:2], 1), 255, dtype=np.uint8)], axis=2)
                else:
                    image = image.convert('RGBA')
                    img_array = np.array(image)
            
            # Create alpha channel
            alpha = np.ones(img_array.shape[:2], dtype=np.uint8) * 255
            
            if remove_white:
                # More conservative white background removal
                # Use lower threshold to be more careful with skin tones
                white_threshold = 220  # Lowered from 240
                # Check if pixels are consistently bright across all channels
                white_mask = np.all(img_array[:, :, :3] > white_threshold, axis=2)
                
                # Additional check: ensure the area is large enough to be background
                # This helps avoid removing small bright areas on the face
                from scipy import ndimage
                white_mask = ndimage.binary_opening(white_mask, structure=np.ones((5, 5)))
                
                alpha[white_mask] = 0
            
            if remove_black:
                # More conservative black background removal
                black_threshold = 30  # Raised from 15
                # Check if pixels are consistently dark across all channels
                black_mask = np.all(img_array[:, :, :3] < black_threshold, axis=2)
                
                # Additional check: ensure the area is large enough to be background
                black_mask = ndimage.binary_opening(black_mask, structure=np.ones((5, 5)))
                
                alpha[black_mask] = 0
            
            # Apply alpha channel
            img_array[:, :, 3] = alpha
            
            return Image.fromarray(img_array, 'RGBA')
            
        except Exception as e:
            logger.error(f"Simple background removal failed: {str(e)}")
            # Fallback to even simpler method
            return self._ultra_simple_background_removal(image, remove_white, remove_black)
    
    def _ultra_simple_background_removal(self, image: Image.Image, remove_white: bool = True, remove_black: bool = True) -> Image.Image:
        """Ultra-simple background removal that's very conservative."""
        try:
            # Convert to numpy array
            img_array = np.array(image)
            
            if image.mode != 'RGBA':
                if image.mode == 'RGB':
                    img_array = np.concatenate([img_array, np.full((*img_array.shape[:2], 1), 255, dtype=np.uint8)], axis=2)
                else:
                    image = image.convert('RGBA')
                    img_array = np.array(image)
            
            # Create alpha channel
            alpha = np.ones(img_array.shape[:2], dtype=np.uint8) * 255
            
            if remove_white:
                # Very conservative white removal - only pure white
                white_threshold = 250
                white_mask = np.all(img_array[:, :, :3] > white_threshold, axis=2)
                alpha[white_mask] = 0
            
            if remove_black:
                # Very conservative black removal - only pure black
                black_threshold = 5
                black_mask = np.all(img_array[:, :, :3] < black_threshold, axis=2)
                alpha[black_mask] = 0
            
            # Apply alpha channel
            img_array[:, :, 3] = alpha
            
            return Image.fromarray(img_array, 'RGBA')
            
        except Exception as e:
            logger.error(f"Ultra-simple background removal failed: {str(e)}")
            return image.convert('RGBA')

# Global instance for reuse
_onnx_bg_removal = None

def get_onnx_bg_removal() -> ONNXBackgroundRemoval:
    """Get global ONNX background removal instance."""
    global _onnx_bg_removal
    if _onnx_bg_removal is None:
        _onnx_bg_removal = ONNXBackgroundRemoval()
    return _onnx_bg_removal

def remove_background_onnx(image: Image.Image) -> Image.Image:
    """
    Convenience function for ONNX background removal.
    
    Args:
        image: Input PIL Image
        
    Returns:
        PIL Image with background removed
    """
    bg_removal = get_onnx_bg_removal()
    return bg_removal.remove_background_onnx(image)

def remove_background_simple(image: Image.Image, remove_white: bool = True, remove_black: bool = True) -> Image.Image:
    """
    Convenience function for simple background removal.
    
    Args:
        image: Input PIL Image
        remove_white: Whether to remove white backgrounds
        remove_black: Whether to remove black backgrounds
        
    Returns:
        PIL Image with background removed
    """
    bg_removal = get_onnx_bg_removal()
    return bg_removal.remove_background_simple(image, remove_white, remove_black)

def remove_background_portrait_safe(image: Image.Image) -> Image.Image:
    """
    Portrait-safe background removal that prioritizes preserving the subject's face.
    This method is very conservative and designed specifically for ID photos.
    
    Args:
        image: Input PIL Image
        
    Returns:
        PIL Image with background removed (very conservative)
    """
    try:
        # Convert to numpy array
        img_array = np.array(image)
        
        if image.mode != 'RGBA':
            if image.mode == 'RGB':
                img_array = np.concatenate([img_array, np.full((*img_array.shape[:2], 1), 255, dtype=np.uint8)], axis=2)
            else:
                image = image.convert('RGBA')
                img_array = np.array(image)
        
        # Create alpha channel - start with everything visible
        alpha = np.ones(img_array.shape[:2], dtype=np.uint8) * 255
        
        # Only remove very pure white backgrounds (RGB > 245)
        # This is extremely conservative to avoid removing any part of the face
        white_threshold = 245
        white_mask = np.all(img_array[:, :, :3] > white_threshold, axis=2)
        
        # Only remove large white areas (likely background)
        # Use morphological operations to ensure we only remove connected white regions
        from scipy import ndimage
        white_mask = ndimage.binary_opening(white_mask, structure=np.ones((10, 10)))
        white_mask = ndimage.binary_closing(white_mask, structure=np.ones((15, 15)))
        
        # Apply mask
        alpha[white_mask] = 0
        
        # Apply alpha channel
        img_array[:, :, 3] = alpha
        
        return Image.fromarray(img_array, 'RGBA')
        
    except Exception as e:
        logger.error(f"Portrait-safe background removal failed: {str(e)}")
        return image.convert('RGBA')
