"""Verify JDN to Gregorian conversion"""
from datetime import date, timedelta

# Let's verify JDN 2459835 using Python's datetime
# JDN 0 = January 1, 4713 BC (proleptic Julian calendar)
# But we can use a known reference point

# Known reference: JDN 2451545 = January 1, 2000 (Gregorian)
jdn_ref = 2451545
date_ref = date(2000, 1, 1)

jdn_target = 2459835
days_diff = jdn_target - jdn_ref

result_date = date_ref + timedelta(days=days_diff)

print("=" * 70)
print("VERIFYING JDN 2459835 → Gregorian")
print("=" * 70)
print()
print(f"Reference: JDN {jdn_ref} = {date_ref}")
print(f"Target JDN: {jdn_target}")
print(f"Days difference: {days_diff}")
print(f"Result: {result_date}")
print()
print(f"Expected (from your spec): 2023-09-11")
print(f"Actual: {result_date}")
print(f"Match: {'✅' if str(result_date) == '2023-09-11' else '❌'}")
print()

# Now let's test the JDN → Gregorian algorithm
from app.utils.date_utils import jdn_to_gregorian

result_algo = jdn_to_gregorian(jdn_target)
print(f"Algorithm result: {result_algo}")
print(f"Match with Python datetime: {'✅' if result_algo == result_date else '❌'}")
print()

# Let's also verify the algorithm with the known reference point
result_ref = jdn_to_gregorian(jdn_ref)
print(f"Testing with reference JDN {jdn_ref}:")
print(f"  Expected: {date_ref}")
print(f"  Got: {result_ref}")
print(f"  Match: {'✅' if result_ref == date_ref else '❌'}")
