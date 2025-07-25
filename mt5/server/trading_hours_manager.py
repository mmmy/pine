"""
Trading Hours Manager for MT5 Trading HTTP Server.
Manages trading time restrictions based on webhook commands.
"""

import logging
from datetime import datetime, time
from typing import Dict, Any, Optional
import pytz
from utils.exceptions import ValidationError


class TradingHoursManager:
    """Manages trading hours restrictions."""
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize trading hours manager.

        Args:
            config: Trading configuration dictionary
        """
        self.config = config
        self.logger = logging.getLogger('mt5_server.trading_hours')

        # Trading hours configuration
        self.trading_hours_config = config.get('trading_hours', {})
        self.default_timezone = self.trading_hours_config.get('timezone', 'UTC')
        self.predefined_intervals = self.trading_hours_config.get('intervals', {})

        # Active trading hours state
        self.enabled = False
        self.active_intervals = []  # List of active interval IDs

        self.logger.info(f"Trading hours manager initialized with {len(self.predefined_intervals)} predefined intervals")
    
    def enable_trading_hours(self, intervals: str = None) -> Dict[str, Any]:
        """
        Enable trading hours restriction.

        Args:
            intervals: Comma-separated list of interval IDs to enable (e.g., "europe,america")

        Returns:
            Result dictionary
        """
        try:
            if intervals:
                # Enable predefined intervals
                interval_ids = [id.strip() for id in intervals.split(',')]
                enabled_intervals = []

                for interval_id in interval_ids:
                    if interval_id in self.predefined_intervals:
                        enabled_intervals.append(interval_id)
                        self.logger.info(f"Enabled predefined interval: {interval_id}")
                    else:
                        self.logger.warning(f"Unknown interval ID: {interval_id}")

                if enabled_intervals:
                    self.enabled = True
                    self.active_intervals = enabled_intervals

                    return {
                        'success': True,
                        'message': f'Trading hours enabled for intervals: {", ".join(enabled_intervals)}',
                        'enabled_intervals': enabled_intervals,
                        'enabled': True
                    }
                else:
                    raise ValidationError(f"No valid intervals found in: {intervals}")

            else:
                # Show available intervals if no specific intervals provided
                return {
                    'success': True,
                    'message': 'Available predefined intervals',
                    'available_intervals': {
                        id: {
                            'name': interval['name'],
                            'time': f"{interval['start_time']}-{interval['end_time']}",
                            'timezone': interval['timezone'],
                            'description': interval.get('description', '')
                        }
                        for id, interval in self.predefined_intervals.items()
                    },
                    'usage_examples': [
                        '开启时间区间 时间区间=europe,america',
                        '开启时间区间 时间区间=asia'
                    ]
                }

        except Exception as e:
            error_msg = f"Failed to enable trading hours: {e}"
            self.logger.error(error_msg)
            raise ValidationError(error_msg)
    
    def disable_trading_hours(self, intervals: str = None) -> Dict[str, Any]:
        """
        Disable trading hours restriction.

        Args:
            intervals: Comma-separated list of interval IDs to disable, or None to disable all

        Returns:
            Result dictionary
        """
        if intervals:
            # Disable specific intervals
            interval_ids = [id.strip() for id in intervals.split(',')]
            disabled_intervals = []

            for interval_id in interval_ids:
                if interval_id in self.active_intervals:
                    self.active_intervals.remove(interval_id)
                    disabled_intervals.append(interval_id)
                    self.logger.info(f"Disabled interval: {interval_id}")

            # If no active intervals left, disable completely
            if not self.active_intervals:
                self.enabled = False

            return {
                'success': True,
                'message': f'Disabled intervals: {", ".join(disabled_intervals)}',
                'disabled_intervals': disabled_intervals,
                'enabled': self.enabled,
                'active_intervals': self.active_intervals
            }
        else:
            # Disable all trading hours
            self.enabled = False
            self.active_intervals = []

            self.logger.info("All trading hours disabled")

            return {
                'success': True,
                'message': 'All trading hours disabled',
                'enabled': False
            }
    
    def set_trading_hours(self, start_time: str, end_time: str, timezone: str = None) -> Dict[str, Any]:
        """
        Set trading hours (same as enable).
        
        Args:
            start_time: Start time in HH:MM format
            end_time: End time in HH:MM format
            timezone: Timezone (optional)
            
        Returns:
            Result dictionary
        """
        return self.enable_trading_hours(start_time, end_time, timezone)
    
    def is_trading_allowed(self) -> bool:
        """
        Check if trading is currently allowed based on time restrictions.

        Returns:
            True if trading is allowed, False otherwise
        """
        if not self.enabled or not self.active_intervals:
            return True

        try:
            # Check each active interval
            for interval_id in self.active_intervals:
                if interval_id not in self.predefined_intervals:
                    continue

                interval = self.predefined_intervals[interval_id]

                # Get current time in the interval's timezone
                tz = pytz.timezone(interval['timezone'])
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

            # No active intervals allow trading at current time
            self.logger.warning(f"Trading not allowed at current time. Active intervals: {self.active_intervals}")
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
            'trading_allowed': self.is_trading_allowed(),
            'active_intervals': self.active_intervals,
            'available_intervals': list(self.predefined_intervals.keys())
        }

        if self.enabled and self.active_intervals:
            # Add details for each active interval
            intervals_detail = {}
            for interval_id in self.active_intervals:
                if interval_id in self.predefined_intervals:
                    interval = self.predefined_intervals[interval_id]

                    # Get current time in this interval's timezone
                    try:
                        tz = pytz.timezone(interval['timezone'])
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

            status['intervals_detail'] = intervals_detail

        # Add predefined intervals info
        predefined_info = {}
        for interval_id, interval in self.predefined_intervals.items():
            predefined_info[interval_id] = {
                'name': interval['name'],
                'start_time': interval['start_time'],
                'end_time': interval['end_time'],
                'timezone': interval['timezone'],
                'description': interval.get('description', ''),
                'active': interval_id in self.active_intervals
            }

        status['predefined_intervals'] = predefined_info

        return status
    
    def handle_trading_hours_command(self, action: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Handle trading hours related commands.

        Args:
            action: Action to perform (enable_trading_hours, disable_trading_hours, set_trading_hours)
            params: Parameters for the action

        Returns:
            Result dictionary
        """
        try:
            if action == 'enable_trading_hours' or action == 'set_trading_hours':
                # Check for predefined intervals
                intervals = params.get('intervals') or params.get('时间区间')

                # Enable predefined intervals or show available intervals
                return self.enable_trading_hours(intervals=intervals)

            elif action == 'disable_trading_hours':
                intervals = params.get('intervals') or params.get('时间区间')
                return self.disable_trading_hours(intervals=intervals)

            else:
                raise ValidationError(f"Unknown trading hours action: {action}")

        except Exception as e:
            error_msg = f"Failed to handle trading hours command: {e}"
            self.logger.error(error_msg)
            return {
                'success': False,
                'error': error_msg
            }
