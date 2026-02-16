"""Debug JDN calculation"""

# Your example: Ethiopian 2016/01/01 should give September 11, 2023

eth_year = 2016
eth_month = 1
eth_day = 1

print("=" * 70)
print("DEBUGGING JDN CALCULATION")
print("=" * 70)
print()
print(f"Ethiopian Date: {eth_year}/{eth_month:02d}/{eth_day:02d}")
print(f"Expected Gregorian: 2023-09-11")
print()

# Step 1: Calculate JDN using the formula
print("Step 1: Ethiopian → JDN")
print("-" * 70)
print("Formula: JDN = 1723856 + 365*(year-1) + floor(year/4) + 30*(month-1) + (day-1)")
print()

term1 = 1723856
term2 = 365 * (eth_year - 1)
term3 = eth_year // 4
term4 = 30 * (eth_month - 1)
term5 = eth_day - 1

print(f"  1723856                    = {term1}")
print(f"  365 * ({eth_year} - 1)          = 365 * {eth_year - 1} = {term2}")
print(f"  floor({eth_year} / 4)           = {term3}")
print(f"  30 * ({eth_month} - 1)              = 30 * {eth_month - 1} = {term4}")
print(f"  ({eth_day} - 1)                  = {term5}")
print()

jdn = term1 + term2 + term3 + term4 + term5
print(f"  JDN = {term1} + {term2} + {term3} + {term4} + {term5}")
print(f"  JDN = {jdn}")
print()

# Step 2: Convert JDN to Gregorian
print("Step 2: JDN → Gregorian")
print("-" * 70)
print(f"JDN = {jdn}")
print()

l = jdn + 68569
n = (4 * l) // 146097
l = l - (146097 * n + 3) // 4
i = (4000 * (l + 1)) // 1461001
l = l - (1461 * i) // 4 + 31
j = (80 * l) // 2447
day = l - (2447 * j) // 80
l = j // 11
month = j + 2 - 12 * l
year = 100 * (n - 49) + i + l

print(f"  l = {jdn} + 68569 = {jdn + 68569}")
print(f"  n = floor((4 * {jdn + 68569}) / 146097) = {n}")
print(f"  ... (intermediate calculations)")
print()
print(f"  Final Gregorian Date: {year}-{month:02d}-{day:02d}")
print()

# Now test with the actual function
from app.utils.date_utils import ethiopian_to_gregorian, ethiopian_to_jdn, jdn_to_gregorian

print("=" * 70)
print("TESTING WITH ACTUAL FUNCTIONS")
print("=" * 70)
print()

jdn_actual = ethiopian_to_jdn(eth_year, eth_month, eth_day)
print(f"ethiopian_to_jdn({eth_year}, {eth_month}, {eth_day}) = {jdn_actual}")
print(f"Expected JDN: {jdn}")
print(f"Match: {'✅' if jdn_actual == jdn else '❌'}")
print()

greg_actual = jdn_to_gregorian(jdn_actual)
print(f"jdn_to_gregorian({jdn_actual}) = {greg_actual}")
print(f"Expected: 2023-09-11")
print(f"Match: {'✅' if str(greg_actual) == '2023-09-11' else '❌'}")
print()

greg_direct = ethiopian_to_gregorian(eth_year, eth_month, eth_day)
print(f"ethiopian_to_gregorian({eth_year}, {eth_month}, {eth_day}) = {greg_direct}")
print(f"Expected: 2023-09-11")
print(f"Match: {'✅' if str(greg_direct) == '2023-09-11' else '❌'}")
print()
