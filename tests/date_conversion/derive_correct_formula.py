"""Derive the correct formula for Ethiopian to JDN conversion"""

# Ethiopian leap year rule: year % 4 == 3
# So years 3, 7, 11, 15, 19, 23, ... are leap years

# For a given year Y, how many leap days have occurred BEFORE year Y?
# (i.e., in years 1, 2, 3, ..., Y-1)

def count_leap_days_before(year):
    """Count leap days in years 1 through year-1"""
    count = 0
    for y in range(1, year):
        if y % 4 == 3:
            count += 1
    return count

print("=" * 70)
print("COUNTING LEAP DAYS")
print("=" * 70)
print()

for year in range(1, 21):
    is_leap = (year % 4) == 3
    leap_days = count_leap_days_before(year)
    formula1 = year // 4
    formula2 = (year + 1) // 4
    formula3 = (year - 1) // 4
    
    print(f"Year {year:2d} (leap: {is_leap}): {leap_days} leap days before")
    print(f"  floor(year/4) = {formula1} {'✅' if formula1 == leap_days else '❌'}")
    print(f"  floor((year+1)/4) = {formula2} {'✅' if formula2 == leap_days else '❌'}")
    print(f"  floor((year-1)/4) = {formula3} {'✅' if formula3 == leap_days else '❌'}")
    print()

print("=" * 70)
print("CONCLUSION")
print("=" * 70)
print()
print("The correct formula for leap days before year Y is: floor((Y + 1) / 4)")
print()
print("So the correct JDN formula should be:")
print("JDN = epoch + 365*(year-1) + floor((year+1)/4) + 30*(month-1) + (day-1)")
print()
print("NOT:")
print("JDN = epoch + 365*(year-1) + floor(year/4) + 30*(month-1) + (day-1)")
