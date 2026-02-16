"""
Performance comparison between original and optimized OCR extraction
"""

import time
import os
from app.services.ocr_extraction_service import OCRExtractionService
from app.services.ocr_extraction_service_optimized import OCRExtractionServiceOptimized

def test_extraction_performance():
    """Compare performance of original vs optimized extraction"""
    
    # Find test images
    test_images = {
        'front': None,
        'back': None
    }
    
    # Look for test images in static folder
    static_dir = 'app/static'
    for filename in os.listdir(static_dir):
        if 'Front' in filename and filename.endswith(('.jpg', '.png')):
            test_images['front'] = os.path.join(static_dir, filename)
        elif 'Reverse' in filename and filename.endswith(('.jpg', '.png')):
            test_images['back'] = os.path.join(static_dir, filename)
        
        if test_images['front'] and test_images['back']:
            break
    
    if not test_images['front'] or not test_images['back']:
        print("❌ Test images not found. Please ensure you have front and back ID card images in app/static/")
        return
    
    print(f"📸 Using test images:")
    print(f"   Front: {test_images['front']}")
    print(f"   Back: {test_images['back']}")
    print()
    
    # Test original service
    print("=" * 60)
    print("TESTING ORIGINAL SERVICE")
    print("=" * 60)
    
    original_service = OCRExtractionService()
    start_time = time.time()
    
    original_result = original_service.extract_all_data(
        test_images['front'],
        test_images['back'],
        'app/static/temp/photo_test_original.png'
    )
    
    original_time = time.time() - start_time
    print(f"\n⏱️  Original service time: {original_time:.2f}s")
    print(f"📊 Fields extracted: {sum(1 for v in original_result['combined_data'].values() if v)}")
    print()
    
    # Test optimized service
    print("=" * 60)
    print("TESTING OPTIMIZED SERVICE")
    print("=" * 60)
    
    optimized_service = OCRExtractionServiceOptimized(enable_debug=False, max_workers=4)
    start_time = time.time()
    
    optimized_result = optimized_service.extract_all_data(
        test_images['front'],
        test_images['back'],
        'app/static/temp/photo_test_optimized.png'
    )
    
    optimized_time = time.time() - start_time
    print(f"\n⏱️  Optimized service time: {optimized_time:.2f}s")
    print(f"📊 Fields extracted: {sum(1 for v in optimized_result['combined_data'].values() if v)}")
    print()
    
    # Performance comparison
    print("=" * 60)
    print("PERFORMANCE COMPARISON")
    print("=" * 60)
    speedup = original_time / optimized_time if optimized_time > 0 else 0
    improvement = ((original_time - optimized_time) / original_time * 100) if original_time > 0 else 0
    
    print(f"Original time:  {original_time:.2f}s")
    print(f"Optimized time: {optimized_time:.2f}s")
    print(f"Speedup:        {speedup:.2f}x")
    print(f"Improvement:    {improvement:.1f}%")
    print()
    
    # Data quality comparison
    print("=" * 60)
    print("DATA QUALITY COMPARISON")
    print("=" * 60)
    
    original_fields = original_result['combined_data']
    optimized_fields = optimized_result['combined_data']
    
    all_keys = set(original_fields.keys()) | set(optimized_fields.keys())
    
    matches = 0
    differences = 0
    
    for key in sorted(all_keys):
        orig_val = original_fields.get(key, '')
        opt_val = optimized_fields.get(key, '')
        
        if orig_val == opt_val:
            matches += 1
            status = "✓"
        else:
            differences += 1
            status = "⚠️"
        
        if orig_val or opt_val:
            print(f"{status} {key}:")
            if orig_val != opt_val:
                print(f"   Original:  {orig_val}")
                print(f"   Optimized: {opt_val}")
    
    print()
    print(f"Matching fields: {matches}")
    print(f"Different fields: {differences}")
    print()
    
    if speedup > 1.5:
        print("🎉 Optimization successful! Significant performance improvement achieved.")
    elif speedup > 1.0:
        print("✅ Optimization provides moderate performance improvement.")
    else:
        print("⚠️  Optimization did not improve performance significantly.")

if __name__ == '__main__':
    # Create temp directory if it doesn't exist
    os.makedirs('app/static/temp', exist_ok=True)
    
    test_extraction_performance()
