"""Final check before changing epoch"""
from datetime import date
from app.utils.date_utils import ethiopian_to_gregorian

# Your example: Ethiopian 2016/01/01 should be September 11, 2023
result_2016 = ethiopian_to_gregorian(2016, 1, 1)
print(f"Ethiopian 2016/01/01 → {result_2016}")
print(f"Expected: 2023-09-11")
print(f"Match: {'✅' if result_2016 == date(2023, 9, 11) else '❌'}")
print()

# Also check 2015
result_2015 = ethiopian_to_gregorian(2015, 1, 1)
print(f"Ethiopian 2015/01/01 → {result_2015}")
print(f"Expected: 2022-09-11 (Ethiopian New Year always on Sept 11)")
print(f"Match: {'✅' if result_2015 == date(2022, 9, 11) else '❌'}")
print()

# If we change epoch to 1724221, what happens to 2016/01/01?
jdn_2016_with_new_epoch = 1724221 + 365 * (2016 - 1) + (2016 // 4) + 0 + 0
jdn_2016_with_old_epoch = 1724220 + 365 * (2016 - 1) + (2016 // 4) + 0 + 0

print(f"With epoch 1724220: JDN = {jdn_2016_with_old_epoch}")
print(f"With epoch 1724221: JDN = {jdn_2016_with_new_epoch}")
print(f"Difference: {jdn_2016_with_new_epoch - jdn_2016_with_old_epoch} day")
print()

# So if we add 1 to the epoch, 2016/01/01 will become September 12, 2023 instead of September 11
# That would break the example you provided!

print("CONCLUSION:")
print("If we change epoch to 1724221:")
print("  - Ethiopian 2015/01/01 → 2022-09-11 ✅")
print("  - Ethiopian 2016/01/01 → 2023-09-12 ❌ (should be 2023-09-11)")
print()
print("Current epoch 1724220:")
print("  - Ethiopian 2015/01/01 → 2022-09-10 ❌ (should be 2022-09-11)")
print("  - Ethiopian 2016/01/01 → 2023-09-11 ✅")
print()
print("There's a contradiction! Let me check if the expected dates are correct...")
print()

# Check: is 2023 a Gregorian leap year?
is_2023_leap = (2023 % 4 == 0 and 2023 % 100 != 0) or (2023 % 400 == 0)
print(f"Is 2023 a Gregorian leap year? {is_2023_leap}")

# Check: is 2022 a Gregorian leap year?
is_2022_leap = (2022 % 4 == 0 and 2022 % 100 != 0) or (2022 % 400 == 0)
print(f"Is 2022 a Gregorian leap year? {is_2022_leap}")

print()
print("Ethiopian New Year falls on:")
print("  - September 11 in non-leap Gregorian years")
print("  - September 12 in Gregorian leap years (the year BEFORE the leap year)")
print()
print("So:")
print("  - 2022 is not a leap year → Ethiopian New Year = September 11, 2022")
print("  - 2023 is not a leap year → Ethiopian New Year = September 11, 2023")
print()
print("Both should be September 11!")
