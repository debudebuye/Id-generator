"""Check what September 11, 2022 should be in Ethiopian"""
from datetime import date
from app.utils.date_utils import gregorian_to_ethiopian, ethiopian_to_gregorian

# According to reliable sources, September 11 is Ethiopian New Year
# Let's check what our algorithm says

greg_date = date(2022, 9, 11)
eth_date = gregorian_to_ethiopian(greg_date)

print("=" * 70)
print("CHECKING SEPTEMBER 11, 2022")
print("=" * 70)
print()
print(f"Gregorian: {greg_date}")
print(f"Ethiopian (our algorithm): {eth_date[0]}/{eth_date[1]:02d}/{eth_date[2]:02d}")
print()
print("Expected: 2015/01/01 (Ethiopian New Year)")
print(f"Match: {'✅' if eth_date == (2015, 1, 1) else '❌'}")
print()

# Let's also check September 10, 2022
greg_date_prev = date(2022, 9, 10)
eth_date_prev = gregorian_to_ethiopian(greg_date_prev)

print(f"September 10, 2022 → {eth_date_prev[0]}/{eth_date_prev[1]:02d}/{eth_date_prev[2]:02d}")
print("Expected: 2014/13/05 or 2014/13/06 (last day of previous year)")
print()

# Check what our algorithm gives for 2015/01/01
eth_2015_01_01 = ethiopian_to_gregorian(2015, 1, 1)
print(f"Ethiopian 2015/01/01 → {eth_2015_01_01}")
print("Expected: 2022-09-11")
print(f"Match: {'✅' if eth_2015_01_01 == date(2022, 9, 11) else '❌'}")
print()

# The issue: our algorithm gives 2022-09-10, not 2022-09-11
# This means the epoch is off by 1 day

print("=" * 70)
print("DIAGNOSIS")
print("=" * 70)
print()
print("Our algorithm: Ethiopian 2015/01/01 → 2022-09-10")
print("Expected:      Ethiopian 2015/01/01 → 2022-09-11")
print()
print("The epoch constant is off by 1 day!")
print(f"Current epoch: 1724220")
print(f"Correct epoch should be: 1724221")
