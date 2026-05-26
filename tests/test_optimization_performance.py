"""
Performance test for OCR extraction optimizations
Run this to compare before/after optimization performance
"""

import time
import os
from app.services.ocr_extraction_service import OCRExtractionService

def test_extraction_performance():
    """Test extraction performance with sample images"""
    
    print("=" * 70)
    print("OCR EXTRACTION PERFORMANCE TEST")
    print("=" * 70)
    
    # Initialize service
    service = OCRExtractionService()
    
    # Test images (update paths as needed)
    test_images = {
        'front': 'app/static/Test_User_Mini_Front_Color.jpg',
        'back': 'app/static/Dinke_Mandera_Ifa_Old_Reverse_Color.png'
    }
    
    # Check if test images exist
    for card_type, path in test_images.items():
        if not os.path.exists(path):
            print(f"⚠️  Test image not found: {path}")
            print(f"   Please update the path in the test script")
            return
    
    print("\n📊 Testing Front Card Extraction...")
    print("-" * 70)
    
    # Test front card
    start_time = time.time()
    front_data = service.parse_front_card_data("", image_path=test_images['front'])
    front_time = time.time() - start_time
    
    print(f"\n✓ Front card processed in {front_time:.2f} seconds")
    print(f"  Fields extracted: {sum(1 for v in front_data.values() if v)}/{len(front_data)}")
    print(f"  Sample data:")
    for key, value in list(front_data.items())[:5]:
        if value:
            print(f"    - {key}: {str(value)[:50]}")
    
    print("\n📊 Testing Back Card Extraction...")
    print("-" * 70)
    
    # Test back card
    start_time = time.time()
    back_data = service.parse_back_card_data("", image_path=test_images['back'])
    back_time = time.time() - start_time
    
    print(f"\n✓ Back card processed in {back_time:.2f} seconds")
    print(f"  Fields extracted: {sum(1 for v in back_data.values() if v)}/{len(back_data)}")
    print(f"  Sample data:")
    for key, value in list(back_data.items())[:5]:
        if value:
            print(f"    - {key}: {str(value)[:50]}")
    
    # Total time
    total_time = front_time + back_time
    
    print("\n" + "=" * 70)
    print("PERFORMANCE SUMMARY")
    print("=" * 70)
    print(f"Front card:  {front_time:.2f}s")
    print(f"Back card:   {back_time:.2f}s")
    print(f"Total time:  {total_time:.2f}s")
    print()
    print("Expected performance (after optimization):")
    print("  - Front card: 1-2 seconds")
    print("  - Back card:  1-2 seconds")
    print("  - Total:      2-4 seconds")
    print()
    
    if total_time <= 4:
        print("✅ EXCELLENT - Performance is optimal!")
    elif total_time <= 6:
        print("✓ GOOD - Performance is acceptable")
    elif total_time <= 10:
        print("⚠️  FAIR - Performance could be improved")
    else:
        print("❌ SLOW - Performance needs optimization")
    
    print("\n" + "=" * 70)
    
    # Test cache performance
    print("\n📊 Testing Cache Performance...")
    print("-" * 70)
    
    # Second run should be faster due to cache
    start_time = time.time()
    front_data_cached = service.parse_front_card_data("", image_path=test_images['front'])
    cached_time = time.time() - start_time
    
    print(f"\n✓ Cached front card processed in {cached_time:.2f} seconds")
    
    if cached_time < front_time * 0.8:
        print(f"✅ Cache is working! {((front_time - cached_time) / front_time * 100):.1f}% faster")
    else:
        print("ℹ️  Cache may not be active or image preprocessing is not the bottleneck")
    
    print("\n" + "=" * 70)

if __name__ == "__main__":
    test_extraction_performance()
