from .id_card_service import IDCardService
from .ocr_extraction_service_optimized import OCRExtractionServiceOptimized

# Alias for backward compatibility
OCRExtractionService = OCRExtractionServiceOptimized

__all__ = ['IDCardService', 'OCRExtractionService', 'OCRExtractionServiceOptimized'] 