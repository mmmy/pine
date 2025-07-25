"""
Trading Hours Manager for MT5 Trading HTTP Server.
Manages trading time restrictions based on webhook commands.
"""

import logging
import re
from datetime import datetime, time, timezone, timedelta
from typing import Dict, Any, Optional
import pytz
from utils.exceptions import ValidationError


class TradingHoursManager:
    """Manages trading hours restrictions."""

    @staticmethod
    def _parse_timezone(timezone_str: str):
        """
        Parse timezone string, supporting both standard names and GMT+/-N format.

        Args:
            timezone_str: Timezone string (e.g., 'Asia/Shanghai', 'GMT+8', 'UTC-5')

        Returns:
            timezone object
        """
        if not timezone_str:
            return pytz.UTC

        # Check for GMT+/-N or UTC+/-N format
        gmt_pattern = r'^(GMT|UTC)([+-])(\d{1,2})$'
        match = re.match(gmt_pattern, timezone_str.upper())

        if match:
            prefix, sign, hours = match.groups()
            hours = int(hours)

            # Create timezone offset
            if sign == '+':
                offset = timedelta(hours=hours)
            else:
                offset = timedelta(hours=-hours)

            return timezone(offset)

        # Try standard timezone names
        try:
            return pytz.timezone(timezone_str)
        except pytz.exceptions.UnknownTimeZoneError:
            raise ValidationError(f"Invalid timezone: {timezone_str}. Use standard names like 'Asia/Shanghai' or GMT+/-N format like 'GMT+8'")
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize trading hours manager.

        Args:
            config: Trading configuration dictionary
        """
        self.config = config
        self.logger = logging.getLogger('mt5_server.trading_hours')

        # Trading hours configuration
        self.default_timezone = 'UTC'
        self.custom_intervals = config.get('custom_intervals', {})

        # Trading hours state (只能通过"开启时间区间"控制)
        self.enabled = False

        self.logger.info(f"Trading hours manager initialized with {len(self.custom_intervals)} custom intervals")
    
    def enable_trading_hours(self) -> Dict[str, Any]:
        """
        Enable trading hours restriction using all configured custom intervals.

        Returns:
            Result dictionary
        """
        try:
            if not self.custom_intervals:
                return {
                    'success': False,
                    'message': 'No custom intervals configured',
                    'enabled': False
                }

            # Enable all custom intervals
            self.enabled = True

            self.logger.info("Trading hours enabled for all custom intervals")

            return {
                'success': True,
                'message': 'Trading hours enabled for all custom intervals',
                'enabled': True,
                'custom_intervals': {
                    id: {
                        'name': interval['name'],
                        'time': f"{interval['start_time']}-{interval['end_time']}",
                        'timezone': interval['timezone'],
                        'description': interval.get('description', '')
                    }
                    for id, interval in self.custom_intervals.items()
                }
            }

        except Exception as e:
            error_msg = f"Failed to enable trading hours: {e}"
            self.logger.error(error_msg)
            raise ValidationError(error_msg)
    
    def disable_trading_hours(self) -> Dict[str, Any]:
        """
        Disable trading hours restriction.

        Returns:
            Result dictionary
        """
        self.enabled = False

        self.logger.info("Trading hours disabled")

        return {
            'success': True,
            'message': 'Trading hours disabled',
            'enabled': False
        }
    

    
    def is_trading_allowed(self) -> bool:
        """
        Check if trading is currently allowed based on time restrictions.

        Returns:
            True if trading is allowed, False otherwise
        """
        if not self.enabled:
            return True

        try:
            # Check each custom interval
            for interval_id, interval in self.custom_intervals.items():
                # Get current time in the interval's timezone
                tz = self._parse_timezone(interval['timezone'])
                current_time = datetime.now(tz).time()

                # Parse interval times
                start_time = datetime.strptime(interval['start_time'], "%H:%M").time()
                end_time = datetime.strptime(interval['end_time'], "%H:%M").time()

                # Check if current time is within this interval
                if start_time <= end_time:
                    # Same day trading hours (e.g., 09:00 - 17:00)
                    if start_time <= current_time <= end_time:
                        self.logger.debug(f"Trading allowed in interval {interval_id} ({interval['name']})")
                        return True
                else:
                    # Overnight trading hours (e.g., 22:00 - 06:00)
                    if current_time >= start_time or current_time <= end_time:
                        self.logger.debug(f"Trading allowed in interval {interval_id} ({interval['name']})")
                        return True

            # No intervals allow trading at current time
            self.logger.warning("Trading not allowed at current time")
            return False

        except Exception as e:
            self.logger.error(f"Error checking trading hours: {e}")
            # If there's an error, allow trading to avoid blocking legitimate trades
            return True
    
    def get_status(self) -> Dict[str, Any]:
        """
        Get current trading hours status.

        Returns:
            Status dictionary
        """
        status = {
            'enabled': self.enabled,
            'default_timezone': self.default_timezone,
            'trading_allowed': self.is_trading_allowed()
        }

        if self.enabled:
            # Add details for each custom interval
            intervals_detail = {}
            for interval_id, interval in self.custom_intervals.items():
                # Get current time in this interval's timezone
                try:
                    tz = self._parse_timezone(interval['timezone'])
                    current_time = datetime.now(tz)

                    intervals_detail[interval_id] = {
                        'name': interval['name'],
                        'start_time': interval['start_time'],
                        'end_time': interval['end_time'],
                        'timezone': interval['timezone'],
                        'description': interval.get('description', ''),
                        'current_time': current_time.strftime("%H:%M"),
                        'current_date': current_time.strftime("%Y-%m-%d")
                    }
                except Exception as e:
                    self.logger.error(f"Error getting time for interval {interval_id}: {e}")
                    intervals_detail[interval_id] = {
                        'name': interval['name'],
                        'error': str(e)
                    }

            status['custom_intervals'] = intervals_detail

        return status
    
    def handle_trading_hours_command(self, action: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Handle trading hours related commands.

        Args:
            action: Action to perform (enable_trading_hours, disable_trading_hours)
            params: Parameters for the action (not used, kept for compatibility)

        Returns:
            Result dictionary
        """
        try:
            if action == 'enable_trading_hours':
                return self.enable_trading_hours()

            elif action == 'disable_trading_hours':
                return self.disable_trading_hours()

            else:
                raise ValidationError(f"Unknown trading hours action: {action}")

        except Exception as e:
            error_msg = f"Failed to handle trading hours command: {e}"
            self.logger.error(error_msg)
            return {
                'success': False,
                'error': error_msg
            }
