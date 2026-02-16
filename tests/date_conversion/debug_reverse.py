"""Debug reverse conversion"""
from datetime import date
from app.utils.date_utils import gregorian_to_jdn, jdn_to_ethiopian, ethiopian_to_jdn

# Test: 2023-09-11 should be 2016/01/01
greg_date = date(2023, 9, 11)
jdn = gregorian_to_jdn(greg_date)

print("=" * 70)
print("DEBUGGING REVERSE CONVERSION")
print("=" * 70)
print()
print(f"Gregorian: {greg_date}")
print(f"JDN: {jdn}")
print()

# Manual calculation
epoch = 1724220
r = jdn - epoch

print(f"Days since epoch: {r}")
print()

# Calculate year
four_year_cycles = r // 1461
remaining = r % 1461

print(f"Four-year cycles: {four_year_cycles}")
print(f"Remaining days: {remaining}")
print()

# Determine year within cycle
if remaining < 365:
    year_in_cycle = 0
    day_in_year = remaining
elif remaining < 730:
    year_in_cycle = 1
    day_in_year = remaining - 365
elif remaining < 1095:
    year_in_cycle = 2
    day_in_year = remaining - 730
else:
    year_in_cycle = 3
    day_in_year = remaining - 1095

eth_year = four_year_cycles * 4 + year_in_cycle + 1

print(f"Year in cycle: {year_in_cycle}")
print(f"Day in year: {day_in_year}")
print(f"Ethiopian year: {eth_year}")
print()

# Calculate month and day
if day_in_year < 360:
    eth_month = day_in_year // 30 + 1
    eth_day = day_in_year % 30 + 1
else:
    eth_month = 13
    eth_day = day_in_year - 360 + 1

print(f"Ethiopian month: {eth_month}")
print(f"Ethiopian day: {eth_day}")
print()
print(f"Result: {eth_year}/{eth_month:02d}/{eth_day:02d}")
print(f"Expected: 2016/01/01")
print()

# Now test with the function
result = jdn_to_ethiopian(jdn)
print(f"Function result: {result[0]}/{result[1]:02d}/{result[2]:02d}")
print()

# Let's verify by converting back
jdn_back = ethiopian_to_jdn(result[0], result[1], result[2])
print(f"Converting back to JDN: {jdn_back}")
print(f"Original JDN: {jdn}")
print(f"Match: {'✅' if jdn_back == jdn else '❌'}")
print()

# What about 2016/01/01?
jdn_2016_01_01 = ethiopian_to_jdn(2016, 1, 1)
print(f"Ethiopian 2016/01/01 → JDN {jdn_2016_01_01}")
print(f"Difference: {jdn - jdn_2016_01_01} days")
