from timezonefinder import TimezoneFinder
from datetime import datetime
import pytz
import nepali_datetime

def get_timezone_from_coords(lat, lon):
    """
    Finds the timezone string (e.g., 'America/New_York') given latitude and longitude.
    """
    tf = TimezoneFinder()
    tz_name = tf.timezone_at(lat=lat, lng=lon)
    return tz_name

def convert_bs_to_ad(date_str):
    """
    Converts a Nepali BS date string (YYYY-MM-DD) to a standard Gregorian AD date string
    """
    parts = date_str.split("-")
    if len(parts) == 3:
        year = int(parts[0])
        month = int(parts[1])
        day = int(parts[2])
        if year < 1900:
            raise ValueError("BS year is too low.")
        bs_date = nepali_datetime.date(year, month, day)
        ad_date = bs_date.to_datetime_date()
        return ad_date.strftime("%Y-%m-%d")
    raise ValueError("Invalid date format. Use YYYY-MM-DD")

def get_utc_time(date_str, time_str, tz_name, calendar_type="AD"):
    """
    Parses local date and time and converts to UTC.
    """
    if calendar_type == "BS":
        date_str = convert_bs_to_ad(date_str)
        
    local_dt = datetime.strptime(f"{date_str} {time_str}", "%Y-%m-%d %H:%M")
    local_tz = pytz.timezone(tz_name)
    local_dt = local_tz.localize(local_dt)
    utc_dt = local_dt.astimezone(pytz.utc)
    return utc_dt, date_str
