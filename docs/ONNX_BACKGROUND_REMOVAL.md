# ONNX Background Removal

This document explains how to use the ONNX-based background removal feature for high-quality, offline background removal in the ID card generation system.

## Overview

The system now supports three background removal options:

1. **Simple White Background Removal** - Removes white/light colored backgrounds
2. **Simple Black Background Removal** - Removes black/dark colored backgrounds  
3. **AI Background Removal (ONNX)** - Uses pre-trained neural network models for intelligent background removal

## Features

- **Offline Processing**: No external API calls required
- **High Quality**: Uses state-of-the-art neural network models
- **Fast Processing**: Optimized ONNX runtime for speed
- **Fallback Support**: Automatically falls back to simple methods if ONNX model is unavailable
- **GPU Acceleration**: Supports CUDA acceleration when available

## Setup

### 1. Install Dependencies

The required dependencies are already included in `requirements.txt`:

```bash
pip install onnxruntime opencv-python numpy
```

### 2. Download ONNX Model

Run the model download script:

```bash
python scripts/download_onnx_model.py
```

This will download a pre-trained U²-Net model to `app/models/u2net.onnx`.

### 3. Manual Model Setup (Alternative)

If the automatic download fails, you can manually download a model:

1. Download a pre-trained ONNX model (e.g., U²-Net, MODNet, or RemBG)
2. Place it in `app/models/` directory
3. Name it `u2net.onnx` or update the model path in the code

## Usage

### In the Web Interface

1. Upload your PDF and extract data as usual
2. In the "Background Options" section, select "AI Background Removal (ONNX)"
3. The system will automatically use the ONNX model for background removal
4. Generate your ID card as normal

### Programmatically

```python
from app.services.id_card_service import IDCardService
from app.services.onnx_bg_removal import remove_background_onnx

# Initialize service
id_service = IDCardService()

# Generate ID with ONNX background removal
generated_files = id_service.generate_id_card(
    data=extracted_data,
    use_onnx_bg=True  # Enable ONNX background removal
)

# Or use the ONNX service directly
from PIL import Image
image = Image.open("photo.jpg")
processed_image = remove_background_onnx(image)
```

## Model Information

### Supported Models

- **U²-Net**: Salient object detection model, good for general background removal
- **MODNet**: Real-time portrait matting model, optimized for people
- **RemBG**: Specialized background removal models

### Model Requirements

- Format: ONNX (.onnx)
- Input: RGB image
- Output: Single-channel mask (0-255)
- Recommended size: 320x320 or 512x512

## Performance

### Processing Speed

- **CPU**: ~2-5 seconds per image (depending on model and image size)
- **GPU**: ~0.5-1 second per image (with CUDA support)
- **Memory**: ~500MB-1GB RAM usage during processing

### Quality Comparison

| Method | Quality | Speed | Offline | GPU Support |
|--------|---------|-------|---------|-------------|
| Simple Color | ⭐⭐ | ⭐⭐⭐⭐⭐ | ✅ | ❌ |
| ONNX AI | ⭐⭐⭐⭐⭐ | ⭐⭐⭐ | ✅ | ✅ |

## Troubleshooting

### Common Issues

1. **Model Not Found**
   ```
   WARNING: ONNX model not found at app/models/u2net.onnx. Using fallback method.
   ```
   **Solution**: Download the model using the script or place it manually

2. **ONNX Runtime Error**
   ```
   Error: ONNX background removal failed: [error details]
   ```
   **Solution**: Check model compatibility and ONNX runtime installation

3. **Memory Issues**
   ```
   Error: Out of memory during ONNX processing
   ```
   **Solution**: Reduce image size or use CPU-only processing

### Debug Mode

Enable debug logging to see detailed information:

```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

### Fallback Behavior

If ONNX processing fails, the system automatically falls back to:

1. Simple color-based background removal
2. Original image (if all methods fail)

## Advanced Configuration

### Custom Model Path

```python
from app.services.onnx_bg_removal import ONNXBackgroundRemoval

# Use custom model
bg_removal = ONNXBackgroundRemoval(model_path="path/to/your/model.onnx")
processed_image = bg_removal.remove_background_onnx(image)
```

### GPU Acceleration

The system automatically detects and uses GPU acceleration when available:

```python
# Check available providers
import onnxruntime as ort
print("Available providers:", ort.get_available_providers())
```

### Model Optimization

For production use, consider:

1. **Model Quantization**: Use INT8 quantized models for faster inference
2. **Model Pruning**: Remove unnecessary weights to reduce model size
3. **Batch Processing**: Process multiple images together when possible

## Integration with Existing Code

The ONNX background removal is fully integrated with the existing system:

- **Preview Page**: New checkbox option in the web interface
- **ID Generation**: Automatic parameter passing to generation functions
- **Photo Processing**: Seamless integration with existing photo processing pipeline
- **Error Handling**: Graceful fallback to simple methods

## Future Enhancements

Planned improvements include:

1. **Multiple Model Support**: Support for different models (portrait, general, etc.)
2. **Model Selection**: User choice of background removal model
3. **Batch Processing**: Process multiple photos simultaneously
4. **Real-time Preview**: Live preview of background removal results
5. **Custom Training**: Support for custom-trained models

## Support

For issues or questions:

1. Check the troubleshooting section above
2. Review the debug logs for error details
3. Ensure all dependencies are properly installed
4. Verify the ONNX model is compatible and properly formatted

## License

The ONNX background removal feature uses pre-trained models that may have their own licensing requirements. Please check the model licenses before using in production.











