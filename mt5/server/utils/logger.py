"""
Logging utilities for MT5 Trading HTTP Server.
"""

import os
import logging
import logging.handlers
from typing import Dict, Any


def setup_logger(config: Dict[str, Any]) -> logging.Logger:
    """
    Setup and configure logger based on configuration.
    
    Args:
        config: Logging configuration dictionary
        
    Returns:
        Configured logger instance
    """
    # Get logger
    logger = logging.getLogger('mt5_server')
    
    # Clear any existing handlers
    logger.handlers.clear()
    
    # Set log level
    level = config.get('level', 'INFO')
    logger.setLevel(getattr(logging, level))
    
    # Create formatter
    log_format = config.get('format', '%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    formatter = logging.Formatter(log_format)
    
    # Console handler
    if config.get('console', True):
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)
    
    # File handler
    log_file = config.get('file', 'mt5_server.log')
    if log_file:
        # Create logs directory if it doesn't exist
        log_dir = os.path.dirname(log_file)
        if log_dir and not os.path.exists(log_dir):
            os.makedirs(log_dir)
        
        # Rotating file handler
        max_size = config.get('max_size', 10485760)  # 10MB default
        backup_count = config.get('backup_count', 5)
        
        file_handler = logging.handlers.RotatingFileHandler(
            log_file,
            maxBytes=max_size,
            backupCount=backup_count,
            encoding='utf-8'
        )
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
    
    return logger


def log_trade_operation(logger: logging.Logger, operation: str, symbol: str, 
                       volume: float, price: float = None, result: str = None):
    """
    Log trade operation with standardized format.
    
    Args:
        logger: Logger instance
        operation: Trade operation (buy, sell, close, etc.)
        symbol: Trading symbol
        volume: Trade volume
        price: Trade price (optional)
        result: Operation result (optional)
    """
    message = f"TRADE: {operation.upper()} {volume} {symbol}"
    if price:
        message += f" @ {price}"
    if result:
        message += f" - {result}"
    
    logger.info(message)


def log_webhook_received(logger: logging.Logger, payload: Dict[str, Any], source_ip: str = None):
    """
    Log webhook received with relevant information.
    
    Args:
        logger: Logger instance
        payload: Webhook payload
        source_ip: Source IP address (optional)
    """
    action = payload.get('action', 'unknown')
    symbol = payload.get('symbol', 'unknown')
    volume = payload.get('volume', 'unknown')
    
    message = f"WEBHOOK: {action} {symbol} {volume}"
    if source_ip:
        message += f" from {source_ip}"
    
    logger.info(message)


def log_mt5_connection(logger: logging.Logger, status: str, account: int = None, server: str = None):
    """
    Log MT5 connection status.
    
    Args:
        logger: Logger instance
        status: Connection status (connected, disconnected, failed)
        account: MT5 account number (optional)
        server: MT5 server name (optional)
    """
    message = f"MT5: {status.upper()}"
    if account:
        message += f" - Account: {account}"
    if server:
        message += f" - Server: {server}"
    
    logger.info(message)


def log_error_with_context(logger: logging.Logger, error: Exception, context: str = None, **kwargs):
    """
    Log error with additional context information.
    
    Args:
        logger: Logger instance
        error: Exception object
        context: Additional context description
        **kwargs: Additional context data
    """
    message = f"ERROR: {str(error)}"
    if context:
        message += f" - Context: {context}"
    
    # Add additional context data
    if kwargs:
        context_data = ", ".join([f"{k}={v}" for k, v in kwargs.items()])
        message += f" - Data: {context_data}"
    
    logger.error(message, exc_info=True)
