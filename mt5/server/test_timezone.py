#!/usr/bin/env python3
"""
Test timezone parsing functionality.
"""

from trading_hours_manager import TradingHoursManager
from datetime import datetime


def test_timezone_parsing():
    """Test timezone parsing with different formats."""
    
    test_timezones = [
        "GMT+8",
        "GMT-5", 
        "UTC+9",
        "UTC-3",
        "Asia/Shanghai",
        "Europe/London",
        "America/New_York"
    ]
    
    print("Testing timezone parsing:")
    print("=" * 50)
    
    for tz_str in test_timezones:
        try:
            tz = TradingHoursManager._parse_timezone(tz_str)
            current_time = datetime.now(tz)
            print(f"✅ {tz_str:15} -> {current_time.strftime('%Y-%m-%d %H:%M:%S %Z')}")
        except Exception as e:
            print(f"❌ {tz_str:15} -> Error: {e}")
    
    print("\nTesting invalid timezones:")
    print("=" * 50)
    
    invalid_timezones = [
        "GMT+25",  # Invalid hour
        "Invalid/Timezone",
        "GMT+",
        "UTC-"
    ]
    
    for tz_str in invalid_timezones:
        try:
            tz = TradingHoursManager._parse_timezone(tz_str)
            current_time = datetime.now(tz)
            print(f"❌ {tz_str:15} -> Should have failed but got: {current_time}")
        except Exception as e:
            print(f"✅ {tz_str:15} -> Correctly failed: {e}")


if __name__ == '__main__':
    test_timezone_parsing()
