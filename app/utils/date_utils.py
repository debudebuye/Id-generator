from datetime import date, datetime
from dateutil.relativedelta import relativedelta
from typing import Tuple

def gregorian_to_ethiopian(greg_date: date) -> Tuple[int, int, int]:
    """Convert Gregorian date to Ethiopian date."""
    year = greg_date.year
    month = greg_date.month
    day = greg_date.day
    
    if (month > 9) or (month == 9 and day >= 11):
        eth_year = year - 7
        new_year = date(year, 9, 11)
    else:
        eth_year = year - 8
        new_year = date(year - 1, 9, 11)
        
    days_since = (greg_date - new_year).days
    eth_month = (days_since // 30) + 1
    eth_day = (days_since % 30) + 1
    
    if eth_month == 13:
        pagume_days = 6 if (eth_year % 4) == 3 else 5
        if eth_day > pagume_days:
            eth_month = 1
            eth_day -= pagume_days
            eth_year += 1
            
    return (eth_year, eth_month, eth_day)

def format_ethiopian_date(eth_date: Tuple[int, int, int]) -> str:
    """Format Ethiopian date as YYYY/MM/DD."""
    return f"{eth_date[0]}/{eth_date[1]:02d}/{eth_date[2]:02d}"

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