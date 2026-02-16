"""
Test Ethiopian ↔ Gregorian date conversion
Verifies correctness of the algorithm
"""

from datetime import date
from app.utils.date_utils import ethiopian_to_gregorian, gregorian_to_ethiopian, parse_ethiopian_date

def test_ethiopian_to_gregorian():
    """Test Ethiopian to Gregorian conversion"""
    
    print("=" * 70)
    print("TESTING ETHIOPIAN → GREGORIAN CONVERSION")
    print("=" * 70)
    print()
    
    test_cases = [
        # (eth_year, eth_month, eth_day, expected_greg_date, description)
        (2016, 1, 1, date(2023, 9, 11), "Ethiopian New Year 2016 (normal year)"),
        (2015, 1, 1, date(2022, 9, 11), "Ethiopian New Year 2015 (normal year)"),
        (2016, 6, 15, date(2024, 2, 23), "Mid-year date (Yekatit 15)"),
        (2015, 13, 5, date(2023, 9, 5), "Pagume 5 (13th month, normal year)"),
        (2015, 13, 6, date(2023, 9, 6), "Pagume 6 (13th month, leap year)"),
        (2016, 12, 30, date(2024, 9, 10), "Last day of 12th month"),
        (2000, 1, 1, date(2007, 9, 11), "Year 2000 Ethiopian"),
        (2010, 7, 15, date(2018, 3, 25), "Random mid-year date"),
    ]
    
    passed = 0
    failed = 0
    
    for eth_year, eth_month, eth_day, expected, description in test_cases:
        try:
            result = ethiopian_to_gregorian(eth_year, eth_month, eth_day)
            
            if result == expected:
                status = "✅ PASS"
                passed += 1
            else:
                status = "❌ FAIL"
                failed += 1
            
            print(f"{status} | {description}")
            print(f"   Ethiopian: {eth_year}/{eth_month:02d}/{eth_day:02d}")
            print(f"   Expected:  {expected}")
            print(f"   Got:       {result}")
            
            if result != expected:
                diff = (result - expected).days
                print(f"   Difference: {diff} days")
            print()
            
        except Exception as e:
            print(f"❌ ERROR | {description}")
            print(f"   Ethiopian: {eth_year}/{eth_month:02d}/{eth_day:02d}")
            print(f"   Error: {e}")
            print()
            failed += 1
    
    print("=" * 70)
    print(f"RESULTS: {passed} passed, {failed} failed out of {len(test_cases)} tests")
    print("=" * 70)
    print()
    
    return passed, failed

def test_gregorian_to_ethiopian():
    """Test Gregorian to Ethiopian conversion"""
    
    print("=" * 70)
    print("TESTING GREGORIAN → ETHIOPIAN CONVERSION")
    print("=" * 70)
    print()
    
    test_cases = [
        # (greg_date, expected_eth, description)
        (date(2023, 9, 11), (2016, 1, 1), "Ethiopian New Year 2016"),
        (date(2024, 2, 23), (2016, 6, 15), "Mid-year date"),
        (date(2023, 9, 5), (2015, 13, 5), "Pagume 5"),
        (date(2024, 9, 10), (2016, 12, 30), "Last day of 12th month"),
        (date(2024, 1, 1), (2016, 4, 22), "Gregorian New Year"),
    ]
    
    passed = 0
    failed = 0
    
    for greg_date, expected_eth, description in test_cases:
        try:
            result = gregorian_to_ethiopian(greg_date)
            
            if result == expected_eth:
                status = "✅ PASS"
                passed += 1
            else:
                status = "❌ FAIL"
                failed += 1
            
            print(f"{status} | {description}")
            print(f"   Gregorian: {greg_date}")
            print(f"   Expected:  {expected_eth[0]}/{expected_eth[1]:02d}/{expected_eth[2]:02d}")
            print(f"   Got:       {result[0]}/{result[1]:02d}/{result[2]:02d}")
            print()
            
        except Exception as e:
            print(f"❌ ERROR | {description}")
            print(f"   Gregorian: {greg_date}")
            print(f"   Error: {e}")
            print()
            failed += 1
    
    print("=" * 70)
    print(f"RESULTS: {passed} passed, {failed} failed out of {len(test_cases)} tests")
    print("=" * 70)
    print()
    
    return passed, failed

def test_round_trip():
    """Test round-trip conversion (Ethiopian → Gregorian → Ethiopian)"""
    
    print("=" * 70)
    print("TESTING ROUND-TRIP CONVERSION")
    print("=" * 70)
    print()
    
    test_dates = [
        (2016, 1, 1, "Ethiopian New Year"),
        (2016, 6, 15, "Mid-year date"),
        (2015, 13, 5, "Pagume 5"),
        (2016, 12, 30, "Last day of 12th month"),
    ]
    
    passed = 0
    failed = 0
    
    for eth_year, eth_month, eth_day, description in test_dates:
        try:
            # Ethiopian → Gregorian → Ethiopian
            greg = ethiopian_to_gregorian(eth_year, eth_month, eth_day)
            eth_back = gregorian_to_ethiopian(greg)
            
            original = (eth_year, eth_month, eth_day)
            
            if eth_back == original:
                status = "✅ PASS"
                passed += 1
            else:
                status = "❌ FAIL"
                failed += 1
            
            print(f"{status} | {description}")
            print(f"   Original:  {original[0]}/{original[1]:02d}/{original[2]:02d}")
            print(f"   → Gregorian: {greg}")
            print(f"   → Ethiopian: {eth_back[0]}/{eth_back[1]:02d}/{eth_back[2]:02d}")
            
            if eth_back != original:
                print(f"   ⚠️  Round-trip failed!")
            print()
            
        except Exception as e:
            print(f"❌ ERROR | {description}")
            print(f"   Error: {e}")
            print()
            failed += 1
    
    print("=" * 70)
    print(f"RESULTS: {passed} passed, {failed} failed out of {len(test_dates)} tests")
    print("=" * 70)
    print()
    
    return passed, failed

def test_leap_years():
    """Test leap year handling"""
    
    print("=" * 70)
    print("TESTING LEAP YEAR HANDLING")
    print("=" * 70)
    print()
    
    print("Ethiopian Leap Year Rule: (year % 4) == 3")
    print("Pagume has 6 days in leap years, 5 in normal years")
    print()
    
    test_years = [
        (2015, True, "2015 is leap year (2015 % 4 = 3)"),
        (2016, False, "2016 is not leap year (2016 % 4 = 0)"),
        (2019, True, "2019 is leap year (2019 % 4 = 3)"),
        (2020, False, "2020 is not leap year (2020 % 4 = 0)"),
    ]
    
    for eth_year, is_leap, description in test_years:
        print(f"{'✓' if is_leap else '○'} {description}")
        
        # Test Pagume 5 (should work in all years)
        try:
            greg5 = ethiopian_to_gregorian(eth_year, 13, 5)
            print(f"   Pagume 5: {eth_year}/13/05 → {greg5}")
        except Exception as e:
            print(f"   ❌ Pagume 5 failed: {e}")
        
        # Test Pagume 6 (should only work in leap years)
        try:
            greg6 = ethiopian_to_gregorian(eth_year, 13, 6)
            if is_leap:
                print(f"   Pagume 6: {eth_year}/13/06 → {greg6} ✅")
            else:
                print(f"   Pagume 6: {eth_year}/13/06 → {greg6} ⚠️ (should fail in non-leap year)")
        except Exception as e:
            if not is_leap:
                print(f"   Pagume 6: Correctly rejected (non-leap year) ✅")
            else:
                print(f"   ❌ Pagume 6 failed in leap year: {e}")
        
        print()
    
    print("=" * 70)
    print()

def test_edge_cases():
    """Test edge cases and boundary conditions"""
    
    print("=" * 70)
    print("TESTING EDGE CASES")
    print("=" * 70)
    print()
    
    edge_cases = [
        # Test dates around Ethiopian New Year
        (2016, 1, 1, "First day of Ethiopian year"),
        (2015, 13, 5, "Last day of Ethiopian year (normal)"),
        (2015, 13, 6, "Last day of Ethiopian year (leap)"),
        
        # Test month boundaries
        (2016, 1, 30, "Last day of Meskerem"),
        (2016, 2, 1, "First day of Tikimt"),
        (2016, 12, 30, "Last day of Nehase"),
        
        # Test Pagume
        (2016, 13, 1, "First day of Pagume"),
    ]
    
    for eth_year, eth_month, eth_day, description in edge_cases:
        try:
            greg = ethiopian_to_gregorian(eth_year, eth_month, eth_day)
            print(f"✅ {description}")
            print(f"   {eth_year}/{eth_month:02d}/{eth_day:02d} → {greg}")
        except Exception as e:
            print(f"❌ {description}")
            print(f"   {eth_year}/{eth_month:02d}/{eth_day:02d} → Error: {e}")
        print()
    
    print("=" * 70)
    print()

if __name__ == '__main__':
    print()
    print("╔════════════════════════════════════════════════════════════════════╗")
    print("║     ETHIOPIAN ↔ GREGORIAN DATE CONVERSION TEST SUITE              ║")
    print("╚════════════════════════════════════════════════════════════════════╝")
    print()
    
    # Run all tests
    total_passed = 0
    total_failed = 0
    
    p, f = test_ethiopian_to_gregorian()
    total_passed += p
    total_failed += f
    
    p, f = test_gregorian_to_ethiopian()
    total_passed += p
    total_failed += f
    
    p, f = test_round_trip()
    total_passed += p
    total_failed += f
    
    test_leap_years()
    test_edge_cases()
    
    # Final summary
    print()
    print("╔════════════════════════════════════════════════════════════════════╗")
    print("║                        FINAL SUMMARY                               ║")
    print("╠════════════════════════════════════════════════════════════════════╣")
    print(f"║  Total Tests Passed: {total_passed:3d}                                          ║")
    print(f"║  Total Tests Failed: {total_failed:3d}                                          ║")
    print(f"║  Success Rate:       {(total_passed/(total_passed+total_failed)*100):.1f}%                                       ║")
    print("╚════════════════════════════════════════════════════════════════════╝")
    print()
    
    if total_failed == 0:
        print("🎉 All tests passed! The algorithm appears to be working correctly.")
    else:
        print("⚠️  Some tests failed. Review the algorithm for correctness.")
    print()
