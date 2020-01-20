"""
Utility functions to call the CDS API 
"""

from dateutil.relativedelta import relativedelta
from datetime import datetime, timedelta


def datetime_range(start, end, delta={'days': 1}):
    """
    Build a generator with dates within a range of datetime objects
    """

    current = start
    if not isinstance(delta, (timedelta, relativedelta)):
        delta = relativedelta(**delta)
    while current < end:
        yield current
        current += delta

def day_hours(delta={'hours': 1}):
    """
    Build a generator of daily hours. 
    """

    day_start = datetime(2000, 1, 1 )
    day_end = datetime(2000, 1, 2)
    step = timedelta(**delta)

    day_hours_list = []
    while day_start < day_end:
        day_hours_list.append(day_start.strftime("%H:%M:%S"))
        day_start += step

    return day_hours_list






