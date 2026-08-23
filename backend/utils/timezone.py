import os
import pytz
from datetime import datetime, timezone

DEFAULT_TIMEZONE_NAME = os.environ.get("DEFAULT_TIMEZONE", "Asia/Kolkata")

def get_timezone(tz_name: str = None) -> pytz.timezone:
    name = tz_name or DEFAULT_TIMEZONE_NAME
    try:
        return pytz.timezone(name)
    except pytz.UnknownTimeZoneError:
        return pytz.timezone("Asia/Kolkata")

def get_local_timezone() -> pytz.timezone:
    return get_timezone(DEFAULT_TIMEZONE_NAME)

def now_utc() -> datetime:
    """Returns current timezone-aware UTC datetime."""
    return datetime.now(pytz.utc)

def now_local(tz_name: str = None) -> datetime:
    """Returns current timezone-aware datetime in target or default timezone."""
    tz = get_timezone(tz_name)
    return now_utc().astimezone(tz)

def format_iso(dt: datetime) -> str:
    """Formats datetime object to standard ISO 8601 string."""
    if dt is None:
        return ""
    if dt.tzinfo is None:
        dt = pytz.utc.localize(dt)
    return dt.isoformat()

def format_display_time(dt: datetime, tz_name: str = None) -> str:
    """Formats datetime object to 12-hour AM/PM time string in target timezone."""
    if dt is None:
        return ""
    if dt.tzinfo is None:
        dt = pytz.utc.localize(dt)
    local_dt = dt.astimezone(get_timezone(tz_name))
    return local_dt.strftime("%I:%M %p")

def format_log_timestamp(dt: datetime = None) -> str:
    """Formats datetime for clean logger output."""
    target_dt = dt or now_local()
    if target_dt.tzinfo is None:
        target_dt = pytz.utc.localize(target_dt).astimezone(get_local_timezone())
    return target_dt.strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
