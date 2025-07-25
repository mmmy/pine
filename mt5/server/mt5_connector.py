"""
MT5 Connector for MT5 Trading HTTP Server.
Handles connection and communication with MetaTrader 5 terminal.
"""

import MetaTrader5 as mt5
import logging
from typing import Dict, Any, Optional, List, Tuple
from datetime import datetime
import pandas as pd
from functools import wraps
from utils.exceptions import MT5Error, ConnectionError
from utils.logger import log_mt5_connection, log_error_with_context


def auto_reconnect(func):
    """
    Decorator to automatically reconnect to MT5 if connection is lost.
    """
    @wraps(func)
    def wrapper(self, *args, **kwargs):
        try:
            # Check connection before attempting operation
            if not self.is_connected():
                self.logger.warning(f"MT5 not connected before {func.__name__}, attempting to reconnect...")
                if not self.connect():
                    raise ConnectionError(f"MT5 connection failed before {func.__name__}")

            # First attempt
            return func(self, *args, **kwargs)
        except Exception as e:
            # Check if it's a connection-related error
            error_str = str(e).lower()
            if (not self.is_connected() or
                "not connected" in error_str or
                "connection" in error_str or
                isinstance(e, ConnectionError)):

                self.logger.warning(f"MT5 connection lost during {func.__name__}, attempting to reconnect...")

                # Attempt to reconnect
                if self.connect():
                    self.logger.info(f"MT5 reconnection successful, retrying {func.__name__}")
                    # Retry the operation after successful reconnection
                    return func(self, *args, **kwargs)
                else:
                    self.logger.error(f"MT5 reconnection failed for {func.__name__}")
                    raise ConnectionError(f"MT5 reconnection failed during {func.__name__}: {e}")
            else:
                # Not a connection error, re-raise original exception
                raise
    return wrapper


class MT5Connector:
    """Manages connection to MetaTrader 5 terminal."""
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize MT5 connector.
        
        Args:
            config: MT5 configuration dictionary
        """
        self.config = config
        self.logger = logging.getLogger('mt5_server.connector')
        self.connected = False
        self.account_info = None
        
    def connect(self) -> bool:
        """
        Connect to MT5 terminal.
        
        Returns:
            True if connection successful, False otherwise
        """
        try:
            # Initialize MT5 connection
            terminal_path = self.config.get('terminal_path', '')
            if terminal_path:
                if not mt5.initialize(path=terminal_path):
                    raise MT5Error(f"Failed to initialize MT5 with path: {terminal_path}")
            else:
                if not mt5.initialize():
                    raise MT5Error("Failed to initialize MT5")

            # 直接获取当前已登录账户的信息，不需要重新登录
            self.account_info = mt5.account_info()
            if self.account_info is None:
                raise MT5Error("Failed to get account information. Please ensure MT5 is logged in.")

            self.connected = True

            # 记录连接成功
            login = self.account_info.login
            server = self.account_info.server
            log_mt5_connection(self.logger, "connected", login, server)

            # Log account details
            self.logger.info(f"MT5 Account: {self.account_info.name} - "
                           f"Balance: {self.account_info.balance} {self.account_info.currency}")

            return True
            
        except Exception as e:
            self.connected = False
            log_error_with_context(self.logger, e, "MT5 connection failed")
            return False
    
    def disconnect(self) -> None:
        """Disconnect from MT5 terminal."""
        try:
            if self.connected:
                mt5.shutdown()
                self.connected = False
                log_mt5_connection(self.logger, "disconnected")
        except Exception as e:
            log_error_with_context(self.logger, e, "MT5 disconnection error")
    
    def is_connected(self) -> bool:
        """
        Check if connected to MT5.
        
        Returns:
            True if connected, False otherwise
        """
        if not self.connected:
            return False
        
        try:
            # Test connection by getting account info
            account_info = mt5.account_info()
            return account_info is not None
        except:
            self.connected = False
            return False
    
    @auto_reconnect
    def get_account_info(self) -> Optional[Dict[str, Any]]:
        """
        Get account information.
        
        Returns:
            Account information dictionary or None if failed
        """
        try:
            if not self.is_connected():
                raise ConnectionError("Not connected to MT5")
            
            account_info = mt5.account_info()
            if account_info is None:
                return None
            
            return {
                'login': account_info.login,
                'name': account_info.name,
                'server': account_info.server,
                'currency': account_info.currency,
                'balance': account_info.balance,
                'equity': account_info.equity,
                'margin': account_info.margin,
                'free_margin': account_info.margin_free,
                'margin_level': account_info.margin_level,
                'profit': account_info.profit,
                'company': account_info.company,
                'trade_allowed': account_info.trade_allowed,
                'trade_expert': account_info.trade_expert,
                'leverage': account_info.leverage
            }
            
        except Exception as e:
            log_error_with_context(self.logger, e, "Failed to get account info")
            return None
    
    @auto_reconnect
    def get_symbol_info(self, symbol: str) -> Optional[Dict[str, Any]]:
        """
        Get symbol information.
        
        Args:
            symbol: Trading symbol
            
        Returns:
            Symbol information dictionary or None if failed
        """
        try:
            if not self.is_connected():
                raise ConnectionError("Not connected to MT5")
            
            symbol_info = mt5.symbol_info(symbol)
            if symbol_info is None:
                return None
            
            return {
                'name': symbol_info.name,
                'description': symbol_info.description,
                'currency_base': symbol_info.currency_base,
                'currency_profit': symbol_info.currency_profit,
                'currency_margin': symbol_info.currency_margin,
                'digits': symbol_info.digits,
                'point': symbol_info.point,
                'spread': symbol_info.spread,
                'volume_min': symbol_info.volume_min,
                'volume_max': symbol_info.volume_max,
                'volume_step': symbol_info.volume_step,
                'trade_mode': symbol_info.trade_mode,
                'bid': symbol_info.bid,
                'ask': symbol_info.ask,
                'time': symbol_info.time
            }
            
        except Exception as e:
            log_error_with_context(self.logger, e, f"Failed to get symbol info for {symbol}")
            return None
    
    @auto_reconnect
    def get_positions(self, symbol: str = None) -> List[Dict[str, Any]]:
        """
        Get open positions.
        
        Args:
            symbol: Filter by symbol (optional)
            
        Returns:
            List of position dictionaries
        """
        try:
            if not self.is_connected():
                raise ConnectionError("Not connected to MT5")
            
            if symbol:
                positions = mt5.positions_get(symbol=symbol)
            else:
                positions = mt5.positions_get()
            
            if positions is None:
                return []
            
            result = []
            for pos in positions:
                result.append({
                    'ticket': pos.ticket,
                    'symbol': pos.symbol,
                    'type': pos.type,
                    'type_name': 'BUY' if pos.type == 0 else 'SELL',
                    'volume': pos.volume,
                    'price_open': pos.price_open,
                    'price_current': pos.price_current,
                    'sl': pos.sl,
                    'tp': pos.tp,
                    'profit': pos.profit,
                    'swap': pos.swap,
                    'comment': pos.comment,
                    'magic': pos.magic,
                    'time': pos.time,
                    'time_update': pos.time_update
                })
            
            return result
            
        except Exception as e:
            log_error_with_context(self.logger, e, "Failed to get positions")
            return []
    
    @auto_reconnect
    def get_orders(self, symbol: str = None) -> List[Dict[str, Any]]:
        """
        Get pending orders.
        
        Args:
            symbol: Filter by symbol (optional)
            
        Returns:
            List of order dictionaries
        """
        try:
            if not self.is_connected():
                raise ConnectionError("Not connected to MT5")
            
            if symbol:
                orders = mt5.orders_get(symbol=symbol)
            else:
                orders = mt5.orders_get()
            
            if orders is None:
                return []
            
            result = []
            for order in orders:
                result.append({
                    'ticket': order.ticket,
                    'symbol': order.symbol,
                    'type': order.type,
                    'volume_initial': order.volume_initial,
                    'volume_current': order.volume_current,
                    'price_open': order.price_open,
                    'sl': order.sl,
                    'tp': order.tp,
                    'comment': order.comment,
                    'magic': order.magic,
                    'time_setup': order.time_setup,
                    'time_expiration': order.time_expiration
                })
            
            return result
            
        except Exception as e:
            log_error_with_context(self.logger, e, "Failed to get orders")
            return []
    
    @auto_reconnect
    def get_server_time(self) -> Optional[datetime]:
        """
        Get MT5 server time.
        
        Returns:
            Server time as datetime object or None if failed
        """
        try:
            if not self.is_connected():
                return None
            
            # Get latest tick to get server time
            symbols = mt5.symbols_get()
            if symbols and len(symbols) > 0:
                tick = mt5.symbol_info_tick(symbols[0].name)
                if tick:
                    return datetime.fromtimestamp(tick.time)
            
            return None
            
        except Exception as e:
            log_error_with_context(self.logger, e, "Failed to get server time")
            return None
    
    @auto_reconnect
    def check_symbol_availability(self, symbol: str) -> bool:
        """
        Check if symbol is available for trading.
        
        Args:
            symbol: Trading symbol
            
        Returns:
            True if symbol is available, False otherwise
        """
        try:
            if not self.is_connected():
                return False
            
            symbol_info = mt5.symbol_info(symbol)
            if symbol_info is None:
                return False
            
            # Check if symbol is visible and tradeable
            return symbol_info.visible and symbol_info.trade_mode != 0
            
        except Exception as e:
            log_error_with_context(self.logger, e, f"Failed to check symbol availability for {symbol}")
            return False
