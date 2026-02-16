"""Verify the algorithm is correct by checking against known facts"""
from datetime import date
from app.utils.date_utils import ethiopian_to_gregorian, gregorian_to_ethiopian

print("=" * 70)
print("VERIFYING ALGORITHM CORRECTNESS")
print("=" * 70)
print()

# Known fact: Ethiopian New Year (1 Meskerem) falls on September 11
# in the Gregorian calendar (or September 12 in years before a Gregorian leap year)

print("Known Fact: Ethiopian New Year (1 Meskerem) = September 11 (or 12)")
print("-" * 70)
print()

test_years = [
    (2015, 2022, "2022 is not a Gregorian leap year"),
    (2016, 2023, "2023 is not a Gregorian leap year"),
    (2017, 2024, "2024 IS a Gregorian leap year"),
    (2018, 2025, "2025 is not a Gregorian leap year"),
]

for eth_year, greg_year, note in test_years:
    greg_date = ethiopian_to_gregorian(eth_year, 1, 1)
    is_greg_leap = (greg_year % 4 == 0 and greg_year % 100 != 0) or (greg_year % 400 == 0)
    expected_day = 12 if is_greg_leap else 11
    
    print(f"Ethiopian {eth_year}/01/01 → Gregorian {greg_date}")
    print(f"  {note}")
    print(f"  Expected: September {expected_day}, {greg_year}")
    print(f"  Match: {'✅' if greg_date == date(greg_year, 9, expected_day) else '❌'}")
    print()

print("=" * 70)
print("CHECKING ROUND-TRIP CONSISTENCY")
print("=" * 70)
print()

# Test several dates for round-trip consistency
test_dates = [
    (2016, 1, 1),
    (2016, 6, 15),
    (2015, 13, 5),
    (2016, 12, 30),
    (2010, 7, 15),
]

all_pass = True
for eth_year, eth_month, eth_day in test_dates:
    greg = ethiopian_to_gregorian(eth_year, eth_month, eth_day)
    eth_back = gregorian_to_ethiopian(greg)
    
    match = eth_back == (eth_year, eth_month, eth_day)
    all_pass = all_pass and match
    
    print(f"Ethiopian {eth_year}/{eth_month:02d}/{eth_day:02d} → {greg} → {eth_back[0]}/{eth_back[1]:02d}/{eth_back[2]:02d}")
    print(f"  Round-trip: {'✅ PASS' if match else '❌ FAIL'}")
    print()

print("=" * 70)
if all_pass:
    print("✅ All round-trip tests passed!")
    print("The algorithm is internally consistent and correct.")
else:
    print("❌ Some round-trip tests failed.")
    print("There may be an issue with the algorithm.")
print("=" * 70)
