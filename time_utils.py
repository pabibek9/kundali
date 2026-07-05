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
    if not tz_name:
        try:
            tz_name = tf.closest_timezone_at(lat=lat, lng=lon)
        except Exception:
            pass
    return tz_name

def convert_bs_to_ad(date_str):
    """
    Converts a Nepali BS date string (YYYY-MM-DD) to a standard Gregorian AD date string
    """
    date_str = normalize_date_str(date_str)
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
    raise ValueError("Invalid date format. Use YYYY-MM-DD or DD/MM/YYYY")

def normalize_date_str(date_str):
    """
    Resiliently normalizes date strings from various formats (DD/MM/YYYY, YYYY/MM/DD, DD-MM-YYYY)
    to the standard YYYY-MM-DD format.
    """
    date_str = date_str.replace("/", "-").strip()
    parts = date_str.split("-")
    if len(parts) == 3:
        if len(parts[0]) == 4:
            # YYYY-MM-DD
            return f"{parts[0]:>04}-{parts[1]:>02}-{parts[2]:>02}"
        elif len(parts[2]) == 4:
            # DD-MM-YYYY -> YYYY-MM-DD
            return f"{parts[2]:>04}-{parts[1]:>02}-{parts[0]:>02}"
    return date_str

def parse_time_resilient(time_str):
    """
    Resiliently parses time strings in either 12-hour AM/PM format or 24-hour format,
    handling varying spacing, casing, zero-padding, and lack of colons.
    """
    time_str = time_str.strip().lower()
    
    # Try parsing 12-hour format with AM/PM
    if 'am' in time_str or 'pm' in time_str:
        # Standardize spacing around am/pm (e.g. "5:30am" -> "5:30 am")
        time_str = time_str.replace('am', ' am').replace('pm', ' pm')
        time_str = " ".join(time_str.split()) # normalize whitespace
        
        # Handle cases like "421 am" or "0421 am"
        parts = time_str.split()
        if len(parts) == 2 and parts[0].isdigit():
            val = parts[0]
            if len(val) == 3:
                val = "0" + val
            if len(val) == 4:
                time_str = f"{val[:2]}:{val[2:]} {parts[1]}"
        
        for fmt in ("%I:%M %p", "%H:%M %p", "%I:%M%p", "%H:%M%p", "%I %p", "%H %p"):
            try:
                return datetime.strptime(time_str, fmt).time()
            except ValueError:
                continue
                
    # Normalize clean numeric formats like "421" or "1630"
    if time_str.isdigit():
        if len(time_str) == 3:
            time_str = "0" + time_str
        if len(time_str) == 4:
            time_str = f"{time_str[:2]}:{time_str[2:]}"
            
    # Try parsing 24-hour format
    for fmt in ("%H:%M", "%I:%M", "%H:%M:%S"):
        try:
            return datetime.strptime(time_str, fmt).time()
        except ValueError:
            continue
            
    raise ValueError(f"Time format not recognized: '{time_str}'. Please use HH:MM (24-hour) or HH:MM AM/PM for time.")

def get_utc_time(date_str, time_str, tz_name, calendar_type="AD"):
    """
    Parses local date and time and converts to UTC.
    """
    date_str = normalize_date_str(date_str)
    if calendar_type == "BS":
        date_str = convert_bs_to_ad(date_str)
        
    # 1. Parse date
    local_date = datetime.strptime(date_str, "%Y-%m-%d").date()
    
    # 2. Parse time resiliently
    local_time = parse_time_resilient(time_str)
    
    # 3. Combine date and time
    local_dt = datetime.combine(local_date, local_time)
    
    local_tz = pytz.timezone(tz_name)
    local_dt = local_tz.localize(local_dt)
    utc_dt = local_dt.astimezone(pytz.utc)
    return utc_dt, date_str
