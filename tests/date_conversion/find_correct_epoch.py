"""Find the correct epoch constant"""
from datetime import date, timedelta

# If Ethiopian 2016/01/01 should be September 11, 2023
# Then we need to find the correct epoch

# Known: JDN 2451545 = January 1, 2000
jdn_ref = 2451545
date_ref = date(2000, 1, 1)

# Target: September 11, 2023
target_date = date(2023, 9, 11)
days_from_ref = (target_date - date_ref).days
jdn_target = jdn_ref + days_from_ref

print("=" * 70)
print("FINDING CORRECT EPOCH CONSTANT")
print("=" * 70)
print()
print(f"If Ethiopian 2016/01/01 = Gregorian 2023-09-11")
print(f"Then JDN should be: {jdn_target}")
print()

# Now calculate what epoch would give us this JDN
# JDN = epoch + 365*(year-1) + floor(year/4) + 30*(month-1) + (day-1)
# For 2016/01/01:
# JDN = epoch + 365*2015 + 504 + 0 + 0
# JDN = epoch + 735979

eth_year = 2016
eth_month = 1
eth_day = 1

term2 = 365 * (eth_year - 1)
term3 = eth_year // 4
term4 = 30 * (eth_month - 1)
term5 = eth_day - 1

sum_terms = term2 + term3 + term4 + term5
required_epoch = jdn_target - sum_terms

print(f"Required epoch = {jdn_target} - ({term2} + {term3} + {term4} + {term5})")
print(f"Required epoch = {jdn_target} - {sum_terms}")
print(f"Required epoch = {required_epoch}")
print()
print(f"Your specified epoch: 1723856")
print(f"Difference: {required_epoch - 1723856} days")
print()

# Let's verify: what is 1 Meskerem 1 EC in Gregorian?
# Using epoch 1723856
jdn_year_1 = 1723856 + 0  # year=1, month=1, day=1
from app.utils.date_utils import jdn_to_gregorian
greg_year_1 = jdn_to_gregorian(jdn_year_1)
print(f"With epoch 1723856:")
print(f"  Ethiopian 1/01/01 = JDN {jdn_year_1} = Gregorian {greg_year_1}")
print()

# What about with the required epoch?
jdn_year_1_new = required_epoch + 0
greg_year_1_new = jdn_to_gregorian(jdn_year_1_new)
print(f"With epoch {required_epoch}:")
print(f"  Ethiopian 1/01/01 = JDN {jdn_year_1_new} = Gregorian {greg_year_1_new}")
print()

# Let's also check: what is the actual Ethiopian date for September 11, 2023?
print("=" * 70)
print("REVERSE CHECK: What is September 11, 2023 in Ethiopian?")
print("=" * 70)
print()

from app.utils.date_utils import gregorian_to_ethiopian
eth_date = gregorian_to_ethiopian(target_date)
print(f"Gregorian 2023-09-11 = Ethiopian {eth_date[0]}/{eth_date[1]:02d}/{eth_date[2]:02d}")
print()
