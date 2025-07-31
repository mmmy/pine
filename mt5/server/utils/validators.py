"""
Validation utilities for MT5 Trading HTTP Server.
"""

import re
import ipaddress
from typing import Dict, Any, List, Optional
from flask import Request
from utils.exceptions import ValidationError


def validate_api_key(request: Request, security_config: Dict[str, Any]) -> bool:
    """
    Validate API key from request.
    
    Args:
        request: Flask request object
        security_config: Security configuration
        
    Returns:
        True if API key is valid or not required, False otherwise
    """
    api_key = security_config.get('api_key', '')
    
    # If no API key is configured, allow all requests
    if not api_key:
        return True
    
    # Check API key in headers
    request_api_key = request.headers.get('X-API-Key') or request.headers.get('Authorization')
    
    # Remove 'Bearer ' prefix if present
    if request_api_key and request_api_key.startswith('Bearer '):
        request_api_key = request_api_key[7:]
    
    return request_api_key == api_key


def validate_ip_address(request: Request, security_config: Dict[str, Any]) -> bool:
    """
    Validate client IP address.
    
    Args:
        request: Flask request object
        security_config: Security configuration
        
    Returns:
        True if IP is allowed, False otherwise
    """
    allowed_ips = security_config.get('allowed_ips', [])
    
    # If no IP restrictions, allow all
    if not allowed_ips:
        return True
    
    # Get client IP (handle proxy headers)
    client_ip = request.headers.get('X-Forwarded-For', request.remote_addr)
    if ',' in client_ip:
        client_ip = client_ip.split(',')[0].strip()
    
    try:
        client_ip_obj = ipaddress.ip_address(client_ip)
        
        for allowed_ip in allowed_ips:
            try:
                # Check if it's a network range
                if '/' in allowed_ip:
                    network = ipaddress.ip_network(allowed_ip, strict=False)
                    if client_ip_obj in network:
                        return True
                else:
                    # Check exact IP match
                    if client_ip_obj == ipaddress.ip_address(allowed_ip):
                        return True
            except ValueError:
                continue
        
        return False
        
    except ValueError:
        return False


def validate_webhook_payload(payload: Dict[str, Any], webhook_config: Dict[str, Any]) -> Dict[str, Any]:
    """
    Validate webhook payload structure and content.
    
    Args:
        payload: Webhook payload
        webhook_config: Webhook configuration
        
    Returns:
        Dictionary with validation result
    """
    result = {'valid': True, 'message': ''}
    
    try:
        # Check required fields based on action type
        action = payload.get('action', '').lower()
        required_fields = webhook_config.get('required_fields', [])

        for field in required_fields:
            if field not in payload:
                result['valid'] = False
                result['message'] = f"Missing required field: {field}"
                return result
        
        # Validate action field
        if 'action' in payload:
            action = payload['action'].lower()
            valid_actions = [
                'buy', 'sell', 'close', 'close_all', 'modify'
            ]
            if action not in valid_actions:
                result['valid'] = False
                result['message'] = f"Invalid action: {action}. Must be one of {valid_actions}"
                return result
        
        # Validate symbol field
        if 'symbol' in payload:
            symbol = payload['symbol']
            if not isinstance(symbol, str) or not symbol.strip():
                result['valid'] = False
                result['message'] = "Symbol must be a non-empty string"
                return result
            
            # Check symbol format (basic validation)
            if not re.match(r'^[A-Z0-9._-]+$', symbol.upper()):
                result['valid'] = False
                result['message'] = f"Invalid symbol format: {symbol}"
                return result
        
        # Validate volume field
        if 'volume' in payload:
            volume = payload['volume']
            if not isinstance(volume, (int, float)) or volume <= 0:
                result['valid'] = False
                result['message'] = "Volume must be a positive number"
                return result
        
        # Validate price fields
        price_fields = ['price', 'sl', 'tp', 'stop_loss', 'take_profit']
        for field in price_fields:
            if field in payload:
                price = payload[field]
                if price is not None and (not isinstance(price, (int, float)) or price < 0):
                    result['valid'] = False
                    result['message'] = f"{field} must be a non-negative number or null"
                    return result
        
        # Validate magic number
        if 'magic' in payload:
            magic = payload['magic']
            if not isinstance(magic, int) or magic < 0:
                result['valid'] = False
                result['message'] = "Magic number must be a non-negative integer"
                return result
        
        # Validate comment field
        if 'comment' in payload:
            comment = payload['comment']
            if not isinstance(comment, str):
                result['valid'] = False
                result['message'] = "Comment must be a string"
                return result
            
            # Check comment length
            if len(comment) > 255:
                result['valid'] = False
                result['message'] = "Comment must be 255 characters or less"
                return result
        
        return result
        
    except Exception as e:
        result['valid'] = False
        result['message'] = f"Validation error: {str(e)}"
        return result


def validate_trade_parameters(symbol: str, volume: float, action: str, 
                            trading_config: Dict[str, Any]) -> None:
    """
    Validate trade parameters against trading configuration.
    
    Args:
        symbol: Trading symbol
        volume: Trade volume
        action: Trade action
        trading_config: Trading configuration
        
    Raises:
        ValidationError: If parameters are invalid
    """
    # Validate volume limits
    min_volume = trading_config.get('min_volume', 0.01)
    max_volume = trading_config.get('max_volume', 100.0)
    
    if volume < min_volume:
        raise ValidationError(f"Volume {volume} is below minimum {min_volume}")
    
    if volume > max_volume:
        raise ValidationError(f"Volume {volume} exceeds maximum {max_volume}")
    
    # Validate allowed symbols
    allowed_symbols = trading_config.get('allowed_symbols', [])
    if allowed_symbols and symbol not in allowed_symbols:
        raise ValidationError(f"Symbol {symbol} is not in allowed symbols list")
    
    # Validate action
    valid_actions = ['buy', 'sell', 'close', 'close_all', 'modify']
    if action.lower() not in valid_actions:
        raise ValidationError(f"Invalid action: {action}")


def validate_symbol_format(symbol: str) -> bool:
    """
    Validate trading symbol format.
    
    Args:
        symbol: Trading symbol
        
    Returns:
        True if format is valid, False otherwise
    """
    if not isinstance(symbol, str) or not symbol.strip():
        return False
    
    # Basic symbol format validation
    # Allows alphanumeric characters, dots, underscores, and hyphens
    pattern = r'^[A-Z0-9._-]+$'
    return bool(re.match(pattern, symbol.upper()))


def sanitize_comment(comment: str) -> str:
    """
    Sanitize trade comment string.
    
    Args:
        comment: Original comment
        
    Returns:
        Sanitized comment
    """
    if not isinstance(comment, str):
        return ""
    
    # Remove potentially harmful characters
    sanitized = re.sub(r'[^\w\s\-_.,()[\]{}]', '', comment)
    
    # Limit length
    return sanitized[:255]



