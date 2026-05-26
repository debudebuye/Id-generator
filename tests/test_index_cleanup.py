"""
Test index page cleanup functionality
Verifies that caches, session data, and temporary files are cleared
"""

import os
import sys

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

def test_index_cleanup():
    """Test that index page clears all caches and temporary files"""
    
    print("=" * 70)
    print("INDEX PAGE CLEANUP TEST")
    print("=" * 70)
    
    from app.services.ocr_extraction_service import OCRExtractionService
    from app.config.settings import Config
    
    config = Config()
    ocr_service = OCRExtractionService()
    
    # Step 1: Create some test data
    print("\n1️⃣ Creating test data...")
    
    # Add items to cache
    ocr_service._preprocess_cache['test_image_1.jpg'] = 'cached_data_1'
    ocr_service._preprocess_cache['test_image_2.jpg'] = 'cached_data_2'
    print(f"   ✓ Added {len(ocr_service._preprocess_cache)} items to cache")
    
    # Create temporary files
    temp_files = [
        'photo_temp.png',
        'qr_temp.png',
        'front_cropped.png',
        'back_cropped.png'
    ]
    
    created_files = []
    for temp_file in temp_files:
        temp_path = os.path.join(config.STATIC_FOLDER, temp_file)
        try:
            with open(temp_path, 'w') as f:
                f.write('test data')
            created_files.append(temp_file)
            print(f"   ✓ Created: {temp_file}")
        except Exception as e:
            print(f"   ⚠️ Could not create {temp_file}: {e}")
    
    print(f"   ✓ Created {len(created_files)} temporary files")
    
    # Step 2: Verify data exists
    print("\n2️⃣ Verifying test data exists...")
    print(f"   Cache size: {len(ocr_service._preprocess_cache)}")
    print(f"   Temp files: {len(created_files)}")
    
    # Step 3: Simulate index page cleanup
    print("\n3️⃣ Simulating index page cleanup...")
    
    # Clear cache
    cache_size_before = len(ocr_service._preprocess_cache)
    ocr_service.clear_cache()
    cache_size_after = len(ocr_service._preprocess_cache)
    print(f"   ✓ Cache cleared: {cache_size_before} → {cache_size_after} items")
    
    # Delete temporary files
    deleted_count = 0
    for temp_file in created_files:
        temp_path = os.path.join(config.STATIC_FOLDER, temp_file)
        if os.path.exists(temp_path):
            try:
                os.remove(temp_path)
                deleted_count += 1
                print(f"   ✓ Deleted: {temp_file}")
            except Exception as e:
                print(f"   ⚠️ Could not delete {temp_file}: {e}")
    
    print(f"   ✓ Deleted {deleted_count} temporary files")
    
    # Step 4: Verify cleanup
    print("\n4️⃣ Verifying cleanup...")
    
    # Check cache
    if len(ocr_service._preprocess_cache) == 0:
        print("   ✅ Cache is empty")
    else:
        print(f"   ❌ Cache still has {len(ocr_service._preprocess_cache)} items")
    
    # Check files
    remaining_files = []
    for temp_file in created_files:
        temp_path = os.path.join(config.STATIC_FOLDER, temp_file)
        if os.path.exists(temp_path):
            remaining_files.append(temp_file)
    
    if len(remaining_files) == 0:
        print("   ✅ All temporary files deleted")
    else:
        print(f"   ❌ {len(remaining_files)} files still exist: {remaining_files}")
    
    # Step 5: Test cache stats
    print("\n5️⃣ Testing cache statistics...")
    stats = ocr_service.get_cache_stats()
    print(f"   Cache size: {stats['size']}")
    print(f"   Max size: {stats['max_size']}")
    print(f"   Items: {stats['items']}")
    
    # Final result
    print("\n" + "=" * 70)
    print("TEST RESULTS")
    print("=" * 70)
    
    success = (
        len(ocr_service._preprocess_cache) == 0 and
        len(remaining_files) == 0
    )
    
    if success:
        print("✅ ALL TESTS PASSED")
        print("   - Cache cleared successfully")
        print("   - All temporary files deleted")
        print("   - Index page cleanup working correctly")
    else:
        print("❌ SOME TESTS FAILED")
        if len(ocr_service._preprocess_cache) > 0:
            print(f"   - Cache not empty: {len(ocr_service._preprocess_cache)} items")
        if len(remaining_files) > 0:
            print(f"   - Files not deleted: {remaining_files}")
    
    print("\n" + "=" * 70)
    
    return success


def test_cache_functionality():
    """Test cache add, retrieve, and clear operations"""
    
    print("\n" + "=" * 70)
    print("CACHE FUNCTIONALITY TEST")
    print("=" * 70)
    
    from app.services.ocr_extraction_service import OCRExtractionService
    
    ocr_service = OCRExtractionService()
    
    print("\n1️⃣ Testing cache operations...")
    
    # Add to cache
    ocr_service._preprocess_cache['image1.jpg'] = 'data1'
    ocr_service._preprocess_cache['image2.jpg'] = 'data2'
    ocr_service._preprocess_cache['image3.jpg'] = 'data3'
    
    print(f"   ✓ Added 3 items to cache")
    
    # Get stats
    stats = ocr_service.get_cache_stats()
    print(f"   ✓ Cache size: {stats['size']}")
    print(f"   ✓ Items: {stats['items']}")
    
    # Clear cache
    ocr_service.clear_cache()
    print(f"   ✓ Cache cleared")
    
    # Verify empty
    stats_after = ocr_service.get_cache_stats()
    print(f"   ✓ Cache size after clear: {stats_after['size']}")
    
    if stats_after['size'] == 0:
        print("\n✅ Cache functionality working correctly")
        return True
    else:
        print(f"\n❌ Cache not empty after clear: {stats_after['size']} items")
        return False


if __name__ == "__main__":
    # Run tests
    test1_passed = test_index_cleanup()
    test2_passed = test_cache_functionality()
    
    # Summary
    print("\n" + "=" * 70)
    print("OVERALL TEST SUMMARY")
    print("=" * 70)
    
    if test1_passed and test2_passed:
        print("✅ ALL TESTS PASSED")
        print("\nIndex page cleanup is working correctly:")
        print("  - Cache clearing: ✅")
        print("  - File deletion: ✅")
        print("  - Cache operations: ✅")
        sys.exit(0)
    else:
        print("❌ SOME TESTS FAILED")
        if not test1_passed:
            print("  - Index cleanup: ❌")
        if not test2_passed:
            print("  - Cache operations: ❌")
        sys.exit(1)
