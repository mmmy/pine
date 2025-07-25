"""
Trading Manager for MT5 Trading HTTP Server.
Handles trade execution and management operations.
"""

import MetaTrader5 as mt5
import logging
from typing import Dict, Any, Optional, List
from datetime import datetime, time
import pytz
from functools import wraps
from trading_hours_manager import TradingHoursManager
from utils.exceptions import TradingError, ValidationError, ConnectionError
from utils.validators import validate_trade_parameters, sanitize_comment
from utils.logger import log_trade_operation, log_error_with_context


def auto_reconnect_trading(func):
    """
    Decorator to automatically reconnect to MT5 if connection is lost during trading operations.
    """
    @wraps(func)
    def wrapper(self, *args, **kwargs):
        try:
            # Check connection before attempting operation
            if not self.mt5_connector.is_connected():
                self.logger.warning(f"MT5 not connected before {func.__name__}, attempting to reconnect...")
                if not self.mt5_connector.connect():
                    raise ConnectionError(f"MT5 connection failed before {func.__name__}")

            # First attempt
            return func(self, *args, **kwargs)
        except Exception as e:
            # Check if it's a connection-related error
            error_str = str(e).lower()
            if (not self.mt5_connector.is_connected() or
                "not connected" in error_str or
                "connection" in error_str or
                isinstance(e, ConnectionError)):

                self.logger.warning(f"MT5 connection lost during {func.__name__}, attempting to reconnect...")

                # Attempt to reconnect
                if self.mt5_connector.connect():
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


class TradingManager:
    """Manages trading operations through MT5."""
    
    def __init__(self, mt5_connector, config: Dict[str, Any]):
        """
        Initialize trading manager.
        
        Args:
            mt5_connector: MT5Connector instance
            config: Trading configuration dictionary
        """
        self.mt5_connector = mt5_connector
        self.config = config
        self.logger = logging.getLogger('mt5_server.trading')

        # Trading hours manager
        self.trading_hours_manager = TradingHoursManager(config)
        
    def execute_webhook_trade(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute trade based on webhook payload.
        
        Args:
            payload: Webhook payload
            
        Returns:
            Trade execution result
        """
        try:
            action = payload['action'].lower()

            # Handle trading hours commands first (they don't need symbol)
            if action == 'enable_trading_hours':
                return self.trading_hours_manager.handle_trading_hours_command(action, payload)

            # For regular trading commands, get symbol and check trading hours
            symbol = payload['symbol'].upper()

            # Check if trading is allowed at current time for regular trading actions
            if action in ['buy', 'sell', 'close', 'close_all', 'modify']:
                if not self.trading_hours_manager.is_trading_allowed():
                    raise TradingError("Trading not allowed at current time due to trading hours restrictions")
            
            # Route to appropriate handler
            if action in ['buy', 'sell']:
                return self._execute_market_order(payload)
            elif action == 'close':
                return self._close_position(payload)
            elif action == 'close_all':
                return self._close_all_positions(payload.get('symbol'))
            elif action == 'modify':
                return self._modify_position(payload)
            else:
                raise ValidationError(f"Unsupported action: {action}")
                
        except Exception as e:
            log_error_with_context(self.logger, e, "Webhook trade execution failed", payload=payload)
            raise
    
    def execute_trade(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute manual trade (same as webhook but with additional validation).
        
        Args:
            payload: Trade payload
            
        Returns:
            Trade execution result
        """
        return self.execute_webhook_trade(payload)
    
    @auto_reconnect_trading
    def _execute_market_order(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute market buy/sell order.
        
        Args:
            payload: Order payload
            
        Returns:
            Order execution result
        """
        action = payload['action'].lower()
        symbol = payload['symbol'].upper()
        volume = payload.get('volume', self.config.get('default_volume', 0.1))
        
        # Validate parameters
        validate_trade_parameters(symbol, volume, action, self.config)
        
        # Check symbol availability
        if not self.mt5_connector.check_symbol_availability(symbol):
            raise TradingError(f"Symbol {symbol} is not available for trading")
        
        # Get symbol info for price and lot size validation
        symbol_info = self.mt5_connector.get_symbol_info(symbol)
        if not symbol_info:
            raise TradingError(f"Failed to get symbol info for {symbol}")
        
        # Validate and adjust volume
        volume = self._validate_and_adjust_volume(volume, symbol_info)
        
        # Prepare order request
        order_type = mt5.ORDER_TYPE_BUY if action == 'buy' else mt5.ORDER_TYPE_SELL
        price = symbol_info['ask'] if action == 'buy' else symbol_info['bid']

        # Get optional parameters
        sl = payload.get('sl') or payload.get('stop_loss')
        tp = payload.get('tp') or payload.get('take_profit')
        magic = payload.get('magic', self.config.get('magic_number', 12345))
        comment = sanitize_comment(payload.get('comment', 'Webhook Trade'))

        # Get MT5 symbol info object for filling mode
        mt5_symbol_info = mt5.symbol_info(symbol)
        if mt5_symbol_info is None:
            raise TradingError(f"Failed to get MT5 symbol info for {symbol}")

        # Determine appropriate filling mode
        filling_mode = mt5.ORDER_FILLING_FOK
        if mt5_symbol_info.filling_mode & 1:  # FOK supported
            filling_mode = mt5.ORDER_FILLING_FOK
        elif mt5_symbol_info.filling_mode & 2:  # IOC supported
            filling_mode = mt5.ORDER_FILLING_IOC
        else:  # Return supported
            filling_mode = mt5.ORDER_FILLING_RETURN

        # Create order request
        request = {
            'action': mt5.TRADE_ACTION_DEAL,
            'symbol': symbol,
            'volume': volume,
            'type': order_type,
            'price': price,
            'sl': sl if sl is not None else 0.0,
            'tp': tp if tp is not None else 0.0,
            'magic': magic,
            'comment': comment,
            'type_time': mt5.ORDER_TIME_GTC,
            'type_filling': filling_mode,
        }
        
        # Add slippage if configured
        max_slippage = self.config.get('max_slippage', 3)
        if max_slippage > 0:
            request['deviation'] = max_slippage
        
        # Execute order
        self.logger.info(f"Sending order request: {request}")
        result = mt5.order_send(request)

        if result is None:
            last_error = mt5.last_error()
            error_msg = f"Failed to send order - no result returned. Last error: {last_error}"
            self.logger.error(error_msg)
            raise TradingError(error_msg)
        
        if result.retcode != mt5.TRADE_RETCODE_DONE:
            error_msg = f"Order failed: {result.retcode} - {result.comment}"
            raise TradingError(error_msg)
        
        # Log successful trade
        log_trade_operation(
            self.logger, action, symbol, volume, 
            result.price, f"Success - Ticket: {result.order}"
        )
        
        return {
            'ticket': result.order,
            'symbol': symbol,
            'action': action,
            'volume': volume,
            'price': result.price,
            'sl': sl,
            'tp': tp,
            'comment': comment,
            'magic': magic,
            'retcode': result.retcode,
            'timestamp': datetime.now().isoformat()
        }
    
    @auto_reconnect_trading
    def _close_position(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """
        Close specific position.
        
        Args:
            payload: Close payload
            
        Returns:
            Close operation result
        """
        symbol = payload['symbol'].upper()
        ticket = payload.get('ticket')
        volume = payload.get('volume')  # Partial close volume
        
        # Get positions for the symbol
        positions = self.mt5_connector.get_positions(symbol)
        if not positions:
            raise TradingError(f"No open positions found for {symbol}")
        
        # If ticket specified, find specific position
        if ticket:
            position = next((p for p in positions if p['ticket'] == ticket), None)
            if not position:
                raise TradingError(f"Position with ticket {ticket} not found")
            positions = [position]
        
        results = []
        for position in positions:
            try:
                # Determine close volume
                close_volume = volume if volume else position['volume']
                if close_volume > position['volume']:
                    close_volume = position['volume']
                
                # Determine order type (opposite of position)
                order_type = mt5.ORDER_TYPE_SELL if position['type'] == 0 else mt5.ORDER_TYPE_BUY
                
                # Get current price
                symbol_info = self.mt5_connector.get_symbol_info(symbol)
                if not symbol_info:
                    raise TradingError(f"Failed to get symbol info for {symbol}")
                
                price = symbol_info['bid'] if position['type'] == 0 else symbol_info['ask']
                
                # Create close request
                request = {
                    'action': mt5.TRADE_ACTION_DEAL,
                    'symbol': symbol,
                    'volume': close_volume,
                    'type': order_type,
                    'position': position['ticket'],
                    'price': price,
                    'magic': position['magic'],
                    'comment': f"Close {position['ticket']}",
                    'type_time': mt5.ORDER_TIME_GTC,
                    'type_filling': mt5.ORDER_FILLING_IOC,
                }
                
                # Execute close order
                result = mt5.order_send(request)
                
                if result is None:
                    raise TradingError(f"Failed to close position {position['ticket']} - no result")
                
                if result.retcode != mt5.TRADE_RETCODE_DONE:
                    raise TradingError(f"Failed to close position {position['ticket']}: {result.comment}")
                
                # Log successful close
                log_trade_operation(
                    self.logger, 'close', symbol, close_volume,
                    result.price, f"Success - Closed ticket: {position['ticket']}"
                )
                
                results.append({
                    'original_ticket': position['ticket'],
                    'close_ticket': result.order,
                    'symbol': symbol,
                    'volume': close_volume,
                    'price': result.price,
                    'profit': position['profit'],
                    'retcode': result.retcode,
                    'timestamp': datetime.now().isoformat()
                })
                
            except Exception as e:
                log_error_with_context(
                    self.logger, e, f"Failed to close position {position['ticket']}"
                )
                results.append({
                    'original_ticket': position['ticket'],
                    'error': str(e),
                    'timestamp': datetime.now().isoformat()
                })
        
        return {'closed_positions': results}
    
    @auto_reconnect_trading
    def _close_all_positions(self, symbol: str = None) -> Dict[str, Any]:
        """
        Close all positions for symbol or all symbols.
        
        Args:
            symbol: Symbol to close (optional, if None closes all)
            
        Returns:
            Close all operation result
        """
        positions = self.mt5_connector.get_positions(symbol)
        if not positions:
            return {'message': 'No positions to close', 'closed_positions': []}
        
        results = []
        for position in positions:
            try:
                close_payload = {
                    'symbol': position['symbol'],
                    'ticket': position['ticket']
                }
                result = self._close_position(close_payload)
                results.extend(result['closed_positions'])
            except Exception as e:
                log_error_with_context(
                    self.logger, e, f"Failed to close position {position['ticket']}"
                )
                results.append({
                    'original_ticket': position['ticket'],
                    'error': str(e),
                    'timestamp': datetime.now().isoformat()
                })
        
        return {'closed_positions': results}
    
    @auto_reconnect_trading
    def _modify_position(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """
        Modify position stop loss and take profit.
        
        Args:
            payload: Modify payload
            
        Returns:
            Modify operation result
        """
        symbol = payload['symbol'].upper()
        ticket = payload.get('ticket')
        new_sl = payload.get('sl') or payload.get('stop_loss')
        new_tp = payload.get('tp') or payload.get('take_profit')
        
        if not ticket:
            raise ValidationError("Ticket is required for position modification")
        
        if new_sl is None and new_tp is None:
            raise ValidationError("At least one of stop_loss or take_profit must be specified")
        
        # Get position
        positions = self.mt5_connector.get_positions(symbol)
        position = next((p for p in positions if p['ticket'] == ticket), None)
        
        if not position:
            raise TradingError(f"Position with ticket {ticket} not found")
        
        # Create modify request
        request = {
            'action': mt5.TRADE_ACTION_SLTP,
            'symbol': symbol,
            'position': ticket,
            'sl': new_sl if new_sl is not None else position['sl'],
            'tp': new_tp if new_tp is not None else position['tp'],
        }
        
        # Execute modification
        result = mt5.order_send(request)
        
        if result is None:
            raise TradingError(f"Failed to modify position {ticket} - no result")
        
        if result.retcode != mt5.TRADE_RETCODE_DONE:
            raise TradingError(f"Failed to modify position {ticket}: {result.comment}")
        
        self.logger.info(f"Position {ticket} modified successfully - SL: {new_sl}, TP: {new_tp}")
        
        return {
            'ticket': ticket,
            'symbol': symbol,
            'sl': new_sl,
            'tp': new_tp,
            'retcode': result.retcode,
            'timestamp': datetime.now().isoformat()
        }

    def _validate_and_adjust_volume(self, volume: float, symbol_info: Dict[str, Any]) -> float:
        """
        Validate and adjust volume according to symbol specifications.

        Args:
            volume: Requested volume
            symbol_info: Symbol information

        Returns:
            Adjusted volume
        """
        min_volume = symbol_info['volume_min']
        max_volume = symbol_info['volume_max']
        volume_step = symbol_info['volume_step']

        # Check minimum volume
        if volume < min_volume:
            volume = min_volume

        # Check maximum volume
        if volume > max_volume:
            volume = max_volume

        # Adjust to volume step
        if volume_step > 0:
            volume = round(volume / volume_step) * volume_step

        return volume

    def get_trading_hours_status(self) -> Dict[str, Any]:
        """
        Get trading hours status.

        Returns:
            Trading hours status dictionary
        """
        return self.trading_hours_manager.get_status()

    def get_positions(self) -> List[Dict[str, Any]]:
        """
        Get all open positions.

        Returns:
            List of position dictionaries
        """
        return self.mt5_connector.get_positions()

    def get_account_info(self) -> Optional[Dict[str, Any]]:
        """
        Get account information.

        Returns:
            Account information dictionary
        """
        return self.mt5_connector.get_account_info()

    def get_server_time(self) -> Optional[str]:
        """
        Get MT5 server time.

        Returns:
            Server time as ISO string
        """
        server_time = self.mt5_connector.get_server_time()
        return server_time.isoformat() if server_time else None
