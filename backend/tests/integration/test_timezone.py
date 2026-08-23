import sys
import os
backend_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)
import pytest
from datetime import datetime
import pytz
from utils.timezone import (
    get_timezone, now_utc, now_local, format_iso, format_display_time, format_log_timestamp
)

def test_timezone_resolution():
    tz = get_timezone("Asia/Kolkata")
    assert tz.zone == "Asia/Kolkata"
    
    # Invalid timezone fallback
    fallback_tz = get_timezone("Invalid/Timezone_Name")
    assert fallback_tz.zone == "Asia/Kolkata"

def test_now_utc_and_local():
    utc_dt = now_utc()
    assert utc_dt.tzinfo is not None
    
    local_dt = now_local("Asia/Kolkata")
    assert local_dt.tzinfo is not None

def test_date_boundary_midnight():
    # 23:59:59 IST to UTC conversion boundary
    ist = pytz.timezone("Asia/Kolkata")
    midnight_ist = ist.localize(datetime(2026, 12, 31, 23, 59, 59))
    utc_dt = midnight_ist.astimezone(pytz.utc)
    
    assert utc_dt.year == 2026
    assert utc_dt.month == 12
    assert utc_dt.day == 31
    assert utc_dt.hour == 18
    assert utc_dt.minute == 29

def test_month_and_year_change_boundaries():
    # New Year boundary in IST (00:30:00 1st Jan 2027 IST -> 19:00:00 31st Dec 2026 UTC)
    ist = pytz.timezone("Asia/Kolkata")
    ny_ist = ist.localize(datetime(2027, 1, 1, 0, 30, 0))
    utc_dt = ny_ist.astimezone(pytz.utc)
    
    assert utc_dt.year == 2026
    assert utc_dt.month == 12
    assert utc_dt.day == 31

def test_format_display_time():
    ist = pytz.timezone("Asia/Kolkata")
    dt = ist.localize(datetime(2026, 8, 17, 8, 5, 0))
    formatted = format_display_time(dt, "Asia/Kolkata")
    assert formatted in ["08:05 AM", "8:05 AM"]

def test_format_log_timestamp():
    ist = pytz.timezone("Asia/Kolkata")
    dt = ist.localize(datetime(2026, 8, 17, 12, 30, 45, 123456))
    ts = format_log_timestamp(dt)
    assert ts.startswith("2026-08-17")
    assert "12:30:45" in ts
