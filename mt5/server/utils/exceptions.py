"""
Custom exceptions for MT5 Trading HTTP Server.
"""


class MT5ServerError(Exception):
    """Base exception for MT5 server errors."""
    pass


class ConfigError(MT5ServerError):
    """Configuration related errors."""
    pass


class MT5Error(MT5ServerError):
    """MT5 connection and trading errors."""
    pass


class ValidationError(MT5ServerError):
    """Data validation errors."""
    pass


class TradingError(MT5ServerError):
    """Trading operation errors."""
    pass


class AuthenticationError(MT5ServerError):
    """Authentication and authorization errors."""
    pass


class ConnectionError(MT5ServerError):
    """Connection related errors."""
    pass
