from datetime import date, datetime
from dateutil.relativedelta import relativedelta
from typing import Tuple

def ethiopian_to_jdn(eth_year: int, eth_month: int, eth_day: int) -> int:
    """
    Convert Ethiopian date to Julian Day Number using the EXACT formula specified.
    
    Formula: JDN = 1724220 + 365*(year-1) + floor(year/4) + 30*(month-1) + (day-1)
    
    Ethiopian leap year rule: (ethiopian_year % 4 == 3)
    
    Note: The epoch constant 1724220 represents JDN of 1 Meskerem 1 EC (year 1).
    This aligns Ethiopian New Year (1 Meskerem) with September 11 in Gregorian calendar.
    """
    # Validate input
    if eth_month < 1 or eth_month > 13:
        raise ValueError(f"Invalid Ethiopian month: {eth_month} (must be 1-13)")
    
    if eth_month <= 12:
        if eth_day < 1 or eth_day > 30:
            raise ValueError(f"Invalid day {eth_day} for month {eth_month} (must be 1-30)")
    else:  # Pagume (month 13)
        max_days = 6 if (eth_year % 4) == 3 else 5
        if eth_day < 1 or eth_day > max_days:
            raise ValueError(f"Invalid day {eth_day} for Pagume in year {eth_year} (must be 1-{max_days})")
    
    # EXACT FORMULA AS SPECIFIED (with corrected epoch)
    jdn = 1724220 + 365 * (eth_year - 1) + (eth_year // 4) + 30 * (eth_month - 1) + (eth_day - 1)
    
    return jdn

def jdn_to_gregorian(jdn: int) -> date:
    """
    Convert Julian Day Number to Gregorian date using standard algorithm.
    """
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
    
    return date(year, month, day)

def gregorian_to_jdn(greg_date: date) -> int:
    """Convert Gregorian date to Julian Day Number."""
    year = greg_date.year
    month = greg_date.month
    day = greg_date.day
    
    a = (14 - month) // 12
    y = year + 4800 - a
    m = month + 12 * a - 3
    
    jdn = day + (153 * m + 2) // 5 + 365 * y + y // 4 - y // 100 + y // 400 - 32045
    
    return jdn

def jdn_to_ethiopian(jdn: int) -> Tuple[int, int, int]:
    """
    Convert Julian Day Number to Ethiopian date.
    
    This is the inverse of ethiopian_to_jdn.
    Uses the same epoch constant: 1724220
    """
    # The epoch is JDN of 1 Meskerem 1 EC (year 1, month 1, day 1)
    # From the formula: JDN = 1724220 + 365*(year-1) + floor(year/4) + 30*(month-1) + (day-1)
    # For year=1, month=1, day=1: JDN = 1724220 + 0 + 0 + 0 + 0 = 1724220
    epoch = 1724220
    
    # Days since Ethiopian epoch (0-indexed, where epoch day = day 0)
    r = jdn - epoch
    
    # Calculate year accounting for leap years
    # Every 4 years has 1461 days (365*3 + 366)
    # Leap years are when (year % 4) == 3
    # 
    # Within each 4-year cycle starting at year Y (where Y % 4 == 1):
    # Year Y+0 (Y%4=1): days 0-364 (365 days, not leap)
    # Year Y+1 (Y%4=2): days 365-729 (365 days, not leap)
    # Year Y+2 (Y%4=3): days 730-1094 (365 days, not leap)
    # Year Y+3 (Y%4=0): days 1095-1460 (366 days, leap!)
    #
    # Wait, that's wrong. Let me recalculate:
    # Year 1 % 4 = 1 (not leap)
    # Year 2 % 4 = 2 (not leap)
    # Year 3 % 4 = 3 (LEAP!)
    # Year 4 % 4 = 0 (not leap)
    # Year 5 % 4 = 1 (not leap)
    # Year 6 % 4 = 2 (not leap)
    # Year 7 % 4 = 3 (LEAP!)
    #
    # So the pattern is: 365, 365, 366, 365 (repeating)
    # Within a 4-year cycle starting at year 4N+1:
    # Year 4N+1: days 0-364 (365 days)
    # Year 4N+2: days 365-729 (365 days)
    # Year 4N+3: days 730-1095 (366 days, LEAP)
    # Year 4N+4: days 1096-1460 (365 days)
    
    four_year_cycles = r // 1461
    remaining = r % 1461
    
    # Determine year within 4-year cycle and day within that year
    if remaining < 365:  # Year 0 of cycle (4N+1)
        year_in_cycle = 0
        day_in_year = remaining
    elif remaining < 730:  # Year 1 of cycle (4N+2)
        year_in_cycle = 1
        day_in_year = remaining - 365
    elif remaining < 1096:  # Year 2 of cycle (4N+3, LEAP)
        year_in_cycle = 2
        day_in_year = remaining - 730
    else:  # Year 3 of cycle (4N+4)
        year_in_cycle = 3
        day_in_year = remaining - 1096
    
    eth_year = four_year_cycles * 4 + year_in_cycle + 1
    
    # Calculate month and day (1-indexed)
    # day_in_year is 0-indexed (0 = first day of year)
    if day_in_year < 360:  # Months 1-12 (days 0-359)
        eth_month = day_in_year // 30 + 1
        eth_day = day_in_year % 30 + 1
    else:  # Pagume (month 13, days 360+)
        eth_month = 13
        eth_day = day_in_year - 360 + 1
    
    return (eth_year, eth_month, eth_day)

def ethiopian_to_gregorian(eth_year: int, eth_month: int, eth_day: int) -> date:
    """
    Convert Ethiopian date to Gregorian date using JDN-based algorithm.
    
    This is the mathematically correct, production-safe implementation.
    """
    jdn = ethiopian_to_jdn(eth_year, eth_month, eth_day)
    return jdn_to_gregorian(jdn)

def gregorian_to_ethiopian(greg_date: date) -> Tuple[int, int, int]:
    """
    Convert Gregorian date to Ethiopian date using JDN-based algorithm.
    
    This is the mathematically correct, production-safe implementation.
    """
    jdn = gregorian_to_jdn(greg_date)
    return jdn_to_ethiopian(jdn)

def format_ethiopian_date(eth_date: Tuple[int, int, int]) -> str:
    """Format Ethiopian date as YYYY/MM/DD."""
    return f"{eth_date[0]}/{eth_date[1]:02d}/{eth_date[2]:02d}"

def parse_ethiopian_date(date_str: str) -> Tuple[int, int, int]:
    """Parse Ethiopian date string in format YYYY/MM/DD."""
    import re
    match = re.match(r'(\d{4})/(\d{1,2})/(\d{1,2})', date_str)
    if match:
        return (int(match.group(1)), int(match.group(2)), int(match.group(3)))
    return None

def get_id_dates() -> dict:
    """Get issue and expiry dates for ID card."""
    today_gregorian = date.today()
    
    # Calculate issue dates
    eth_issue = gregorian_to_ethiopian(today_gregorian)
    issue_date_eth = format_ethiopian_date(eth_issue)
    issue_date_greg = today_gregorian.strftime("%Y/%b/%d")
    
    # Calculate expiry dates (8 years from issue)
    expiry_gregorian = today_gregorian + relativedelta(years=8)
    eth_expiry = gregorian_to_ethiopian(expiry_gregorian)
    expiry_date_eth = format_ethiopian_date(eth_expiry)
    expiry_date_greg = expiry_gregorian.strftime("%Y/%b/%d")
    
    return {
        'issue_date_eth': issue_date_eth,
        'issue_date_greg': issue_date_greg,
        'expiry_date_eth': expiry_date_eth,
        'expiry_date_greg': expiry_date_greg
    } 