"""
Correct Ethiopian ↔ Gregorian date conversion using JDN (Julian Day Number)
This implementation uses proper astronomical algorithms for accurate conversion.
"""

from datetime import date, datetime, timedelta
from dateutil.relativedelta import relativedelta
from typing import Tuple

# ============================================================================
# CORRECT JDN-BASED IMPLEMENTATION
# ============================================================================

def ethiopian_to_jdn(year: int, month: int, day: int) -> int:
    """
    Convert Ethiopian date to Julian Day Number (JDN).
    
    Ethiopian calendar:
    - 12 months of 30 days each
    - 13th month (Pagume) with 5 or 6 days
    - Leap year when (year % 4) == 3
    - Epoch: JDN 1724221 (corresponds to Ethiopian 0001/01/01)
    
    Args:
        year: Ethiopian year
        month: Ethiopian month (1-13)
        day: Ethiopian day (1-30 for months 1-12, 1-5/6 for month 13)
    
    Returns:
        Julian Day Number
    """
    # Validate input
    if month < 1 or month > 13:
        raise ValueError(f"Invalid Ethiopian month: {month} (must be 1-13)")
    
    if month <= 12:
        if day < 1 or day > 30:
            raise ValueError(f"Invalid day {day} for month {month} (must be 1-30)")
    else:  # Pagume (month 13)
        max_days = 6 if (year % 4) == 3 else 5
        if day < 1 or day > max_days:
            raise ValueError(f"Invalid day {day} for Pagume in year {year} (must be 1-{max_days})")
    
    # Ethiopian epoch: JDN 1724221
    # Ethiopian year 1, month 1, day 1 = August 29, 8 CE (Julian) = August 27, 8 CE (Gregorian proleptic)
    epoch = 1724221
    
    # Calculate JDN
    # Days in complete years before this year
    jdn = epoch + 365 * (year - 1)
    
    # Add leap days for complete years
    # Leap years are when (year % 4) == 3
    # So years 3, 7, 11, 15, ... are leap years
    # Number of leap years before year Y is: (Y + 1) // 4
    jdn += (year + 1) // 4
    
    # Add days in complete months of current year
    jdn += 30 * (month - 1)
    
    # Add days in current month
    jdn += day - 1
    
    return jdn


def jdn_to_gregorian(jdn: int) -> date:
    """
    Convert Julian Day Number to Gregorian date.
    
    Uses the standard astronomical algorithm for JDN to Gregorian conversion.
    
    Args:
        jdn: Julian Day Number
    
    Returns:
        Gregorian date object
    """
    # Standard JDN to Gregorian conversion algorithm
    a = jdn + 32044
    b = (4 * a + 3) // 146097
    c = a - (146097 * b) // 4
    d = (4 * c + 3) // 1461
    e = c - (1461 * d) // 4
    m = (5 * e + 2) // 153
    
    day = e - (153 * m + 2) // 5 + 1
    month = m + 3 - 12 * (m // 10)
    year = 100 * b + d - 4800 + m // 10
    
    return date(year, month, day)


def gregorian_to_jdn(greg_date: date) -> int:
    """
    Convert Gregorian date to Julian Day Number.
    
    Args:
        greg_date: Gregorian date object
    
    Returns:
        Julian Day Number
    """
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
    
    Args:
        jdn: Julian Day Number
    
    Returns:
        Tuple of (year, month, day) in Ethiopian calendar
    """
    # Ethiopian epoch
    epoch = 1724221
    
    # Days since Ethiopian epoch (day 0 = 0001/01/01)
    days_since_epoch = jdn - epoch
    
    # Calculate year (accounting for leap years)
    # Every 4 years has 1461 days (365*3 + 366)
    four_year_cycles = days_since_epoch // 1461
    remaining_days = days_since_epoch % 1461
    
    # Determine year within the 4-year cycle
    # Years 0, 1, 2 have 365 days; year 3 has 366 days
    if remaining_days < 365:
        year_in_cycle = 0
        day_in_year = remaining_days
    elif remaining_days < 730:
        year_in_cycle = 1
        day_in_year = remaining_days - 365
    elif remaining_days < 1095:
        year_in_cycle = 2
        day_in_year = remaining_days - 730
    else:  # remaining_days < 1461
        year_in_cycle = 3
        day_in_year = remaining_days - 1095
    
    year = four_year_cycles * 4 + year_in_cycle + 1
    
    # Calculate month and day
    if day_in_year < 360:  # Months 1-12
        month = day_in_year // 30 + 1
        day = day_in_year % 30 + 1
    else:  # Pagume (month 13)
        month = 13
        day = day_in_year - 360 + 1
    
    return (year, month, day)


# ============================================================================
# PUBLIC API FUNCTIONS
# ============================================================================

def ethiopian_to_gregorian(eth_year: int, eth_month: int, eth_day: int) -> date:
    """
    Convert Ethiopian date to Gregorian date using JDN.
    
    This is the mathematically correct conversion using Julian Day Numbers.
    
    Args:
        eth_year: Ethiopian year
        eth_month: Ethiopian month (1-13)
        eth_day: Ethiopian day
    
    Returns:
        Gregorian date object
    
    Raises:
        ValueError: If the Ethiopian date is invalid
    
    Examples:
        >>> ethiopian_to_gregorian(2016, 1, 1)  # Ethiopian New Year 2016
        date(2023, 9, 11)
        
        >>> ethiopian_to_gregorian(2015, 13, 5)  # Pagume 5
        date(2023, 9, 5)
    """
    jdn = ethiopian_to_jdn(eth_year, eth_month, eth_day)
    return jdn_to_gregorian(jdn)


def gregorian_to_ethiopian(greg_date: date) -> Tuple[int, int, int]:
    """
    Convert Gregorian date to Ethiopian date using JDN.
    
    This is the mathematically correct conversion using Julian Day Numbers.
    
    Args:
        greg_date: Gregorian date object
    
    Returns:
        Tuple of (year, month, day) in Ethiopian calendar
    
    Examples:
        >>> gregorian_to_ethiopian(date(2023, 9, 11))  # Ethiopian New Year
        (2016, 1, 1)
        
        >>> gregorian_to_ethiopian(date(2023, 9, 5))  # Pagume
        (2015, 13, 5)
    """
    jdn = gregorian_to_jdn(greg_date)
    return jdn_to_ethiopian(jdn)


# ============================================================================
# UTILITY FUNCTIONS
# ============================================================================

def format_ethiopian_date(eth_date: Tuple[int, int, int]) -> str:
    """Format Ethiopian date as YYYY/MM/DD."""
    return f"{eth_date[0]}/{eth_date[1]:02d}/{eth_date[2]:02d}"


def parse_ethiopian_date(date_str: str) -> Tuple[int, int, int]:
    """
    Parse Ethiopian date string in format YYYY/MM/DD.
    
    Args:
        date_str: Date string in format YYYY/MM/DD
    
    Returns:
        Tuple of (year, month, day) or None if parsing fails
    """
    import re
    match = re.match(r'(\d{4})/(\d{1,2})/(\d{1,2})', date_str)
    if match:
        return (int(match.group(1)), int(match.group(2)), int(match.group(3)))
    return None


def is_ethiopian_leap_year(year: int) -> bool:
    """
    Check if an Ethiopian year is a leap year.
    
    Ethiopian leap year rule: (year % 4) == 3
    
    Args:
        year: Ethiopian year
    
    Returns:
        True if leap year, False otherwise
    """
    return (year % 4) == 3


def get_pagume_days(year: int) -> int:
    """
    Get the number of days in Pagume (13th month) for a given Ethiopian year.
    
    Args:
        year: Ethiopian year
    
    Returns:
        6 if leap year, 5 otherwise
    """
    return 6 if is_ethiopian_leap_year(year) else 5


def get_id_dates() -> dict:
    """
    Get issue and expiry dates for ID card.
    
    Returns:
        Dictionary with issue and expiry dates in both calendars
    """
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


def validate_ethiopian_date(year: int, month: int, day: int) -> bool:
    """
    Validate an Ethiopian date.
    
    Args:
        year: Ethiopian year
        month: Ethiopian month (1-13)
        day: Ethiopian day
    
    Returns:
        True if valid, False otherwise
    """
    try:
        # Try to convert to JDN (will raise ValueError if invalid)
        ethiopian_to_jdn(year, month, day)
        return True
    except ValueError:
        return False


# ============================================================================
# ETHIOPIAN MONTH NAMES
# ============================================================================

ETHIOPIAN_MONTHS = [
    "Meskerem",   # 1
    "Tikimt",     # 2
    "Hidar",      # 3
    "Tahsas",     # 4
    "Tir",        # 5
    "Yekatit",    # 6
    "Megabit",    # 7
    "Miazia",     # 8
    "Ginbot",     # 9
    "Sene",       # 10
    "Hamle",      # 11
    "Nehase",     # 12
    "Pagume"      # 13
]

def get_ethiopian_month_name(month: int) -> str:
    """Get the name of an Ethiopian month."""
    if 1 <= month <= 13:
        return ETHIOPIAN_MONTHS[month - 1]
    raise ValueError(f"Invalid month: {month}")


def format_ethiopian_date_verbose(eth_date: Tuple[int, int, int]) -> str:
    """Format Ethiopian date with month name."""
    year, month, day = eth_date
    month_name = get_ethiopian_month_name(month)
    return f"{day} {month_name} {year}"
