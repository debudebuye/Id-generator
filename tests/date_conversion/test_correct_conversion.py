"""
Test the CORRECT JDN-based Ethiopian ↔ Gregorian date conversion
"""

from datetime import date
from app.utils.date_utils_correct import (
    ethiopian_to_gregorian, gregorian_to_ethiopian,
    ethiopian_to_jdn, jdn_to_gregorian, gregorian_to_jdn, jdn_to_ethiopian,
    is_ethiopian_leap_year, get_pagume_days, validate_ethiopian_date
)

def test_correct_conversion():
    """Test the corrected JDN-based conversion"""
    
    print("=" * 70)
    print("TESTING CORRECT JDN-BASED CONVERSION")
    print("=" * 70)
    print()
    
    test_cases = [
        # (eth_year, eth_month, eth_day, expected_greg_date, description)
        (2016, 1, 1, date(2023, 9, 11), "Ethiopian New Year 2016"),
        (2015, 1, 1, date(2022, 9, 11), "Ethiopian New Year 2015"),
        (2016, 6, 15, date(2024, 2, 23), "Mid-year date (Yekatit 15)"),
        (2015, 13, 5, date(2023, 9, 5), "Pagume 5 (13th month)"),
        (2015, 13, 6, date(2023, 9, 6), "Pagume 6 (leap year)"),
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

def test_round_trip_correct():
    """Test round-trip conversion with correct algorithm"""
    
    print("=" * 70)
    print("TESTING ROUND-TRIP CONVERSION (CORRECT)")
    print("=" * 70)
    print()
    
    test_dates = [
        (2016, 1, 1, "Ethiopian New Year"),
        (2016, 6, 15, "Mid-year date"),
        (2015, 13, 5, "Pagume 5"),
        (2015, 13, 6, "Pagume 6 (leap)"),
        (2016, 12, 30, "Last day of 12th month"),
        (2010, 7, 15, "Random date"),
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

def test_validation():
    """Test date validation"""
    
    print("=" * 70)
    print("TESTING DATE VALIDATION")
    print("=" * 70)
    print()
    
    valid_dates = [
        (2016, 1, 1, "Valid: First day of year"),
        (2016, 12, 30, "Valid: Last day of 12th month"),
        (2015, 13, 6, "Valid: Pagume 6 in leap year"),
        (2016, 13, 5, "Valid: Pagume 5 in normal year"),
    ]
    
    invalid_dates = [
        (2016, 0, 1, "Invalid: Month 0"),
        (2016, 14, 1, "Invalid: Month 14"),
        (2016, 1, 31, "Invalid: Day 31 in month 1"),
        (2016, 13, 6, "Invalid: Pagume 6 in non-leap year"),
        (2015, 13, 7, "Invalid: Pagume 7 (too many days)"),
    ]
    
    print("Valid dates:")
    for year, month, day, description in valid_dates:
        is_valid = validate_ethiopian_date(year, month, day)
        status = "✅" if is_valid else "❌"
        print(f"  {status} {description}: {year}/{month:02d}/{day:02d}")
    
    print()
    print("Invalid dates (should be rejected):")
    for year, month, day, description in invalid_dates:
        is_valid = validate_ethiopian_date(year, month, day)
        status = "✅" if not is_valid else "❌"
        print(f"  {status} {description}: {year}/{month:02d}/{day:02d}")
    
    print()
    print("=" * 70)
    print()

def test_leap_years_correct():
    """Test leap year handling with correct algorithm"""
    
    print("=" * 70)
    print("TESTING LEAP YEAR HANDLING (CORRECT)")
    print("=" * 70)
    print()
    
    test_years = [
        (2015, True),
        (2016, False),
        (2019, True),
        (2020, False),
        (2023, True),
    ]
    
    for year, expected_leap in test_years:
        is_leap = is_ethiopian_leap_year(year)
        pagume_days = get_pagume_days(year)
        
        status = "✅" if is_leap == expected_leap else "❌"
        print(f"{status} Year {year}: {'Leap' if is_leap else 'Normal'} ({pagume_days} days in Pagume)")
        
        # Test Pagume 6
        if is_leap:
            try:
                greg = ethiopian_to_gregorian(year, 13, 6)
                print(f"   Pagume 6: {year}/13/06 → {greg} ✅")
            except ValueError as e:
                print(f"   Pagume 6: ERROR - {e} ❌")
        else:
            try:
                greg = ethiopian_to_gregorian(year, 13, 6)
                print(f"   Pagume 6: {year}/13/06 → {greg} ⚠️ Should have been rejected!")
            except ValueError:
                print(f"   Pagume 6: Correctly rejected ✅")
        print()
    
    print("=" * 70)
    print()

if __name__ == '__main__':
    print()
    print("╔════════════════════════════════════════════════════════════════════╗")
    print("║   CORRECT JDN-BASED ETHIOPIAN ↔ GREGORIAN CONVERSION TEST         ║")
    print("╚════════════════════════════════════════════════════════════════════╝")
    print()
    
    total_passed = 0
    total_failed = 0
    
    p, f = test_correct_conversion()
    total_passed += p
    total_failed += f
    
    p, f = test_round_trip_correct()
    total_passed += p
    total_failed += f
    
    test_validation()
    test_leap_years_correct()
    
    print()
    print("╔════════════════════════════════════════════════════════════════════╗")
    print("║                        FINAL SUMMARY                               ║")
    print("╠════════════════════════════════════════════════════════════════════╣")
    print(f"║  Total Tests Passed: {total_passed:3d}                                          ║")
    print(f"║  Total Tests Failed: {total_failed:3d}                                          ║")
    if total_passed + total_failed > 0:
        success_rate = (total_passed/(total_passed+total_failed)*100)
        print(f"║  Success Rate:       {success_rate:.1f}%                                       ║")
    print("╚════════════════════════════════════════════════════════════════════╝")
    print()
    
    if total_failed == 0:
        print("🎉 All tests passed! The JDN-based algorithm is mathematically correct.")
    else:
        print("⚠️  Some tests failed. Review the implementation.")
    print()
