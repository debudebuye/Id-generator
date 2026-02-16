"""Check if the leap year formula is correct"""

# The formula: JDN = 1724220 + 365*(year-1) + floor(year/4) + 30*(month-1) + (day-1)

# Let's manually calculate for a few years
print("=" * 70)
print("CHECKING LEAP YEAR FORMULA")
print("=" * 70)
print()

# Calculate JDN for 1/01/01 of several years
for year in range(2014, 2020):
    is_leap = (year % 4) == 3
    jdn = 1724220 + 365 * (year - 1) + (year // 4) + 0 + 0
    
    print(f"Year {year} (leap: {is_leap})")
    print(f"  JDN = 1724220 + 365*{year-1} + {year//4} = {jdn}")
    
    # Calculate difference from previous year
    if year > 2014:
        prev_jdn = 1724220 + 365 * (year - 2) + ((year-1) // 4) + 0 + 0
        diff = jdn - prev_jdn
        print(f"  Days from previous year: {diff}")
        
        # Check if this matches the expected number of days in the previous year
        prev_year = year - 1
        prev_is_leap = (prev_year % 4) == 3
        expected_days = 366 if prev_is_leap else 365
        print(f"  Expected (year {prev_year} has {expected_days} days): {expected_days}")
        print(f"  Match: {'✅' if diff == expected_days else '❌'}")
    
    print()

print("=" * 70)
print("ISSUE IDENTIFIED")
print("=" * 70)
print()
print("The formula floor(year/4) adds one extra day for every 4 years,")
print("but it doesn't correctly account for which years are leap years.")
print()
print("Ethiopian leap years: year % 4 == 3")
print("So years 3, 7, 11, 15, 19, 23, ... are leap years")
print()
print("The formula floor(year/4) gives:")
print("  Year 1: floor(1/4) = 0")
print("  Year 2: floor(2/4) = 0")
print("  Year 3: floor(3/4) = 0 (but year 3 IS a leap year!)")
print("  Year 4: floor(4/4) = 1")
print("  Year 5: floor(5/4) = 1")
print("  Year 6: floor(6/4) = 1")
print("  Year 7: floor(7/4) = 1 (but year 7 IS a leap year!)")
print("  Year 8: floor(8/4) = 2")
print()
print("The formula is counting leap days AFTER the leap year, not during it!")
print()
print("Correct formula should be: floor((year + 1) / 4)")
print("Or equivalently: floor((year - 1 + 4) / 4) = floor((year + 3) / 4)")
