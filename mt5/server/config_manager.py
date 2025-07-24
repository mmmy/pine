"""
Configuration Manager for MT5 Trading HTTP Server
Handles loading and validation of configuration files.
"""

import os
import yaml
import logging
from typing import Dict, Any, Optional
from utils.exceptions import ConfigError


class ConfigManager:
    """Manages application configuration."""
    
    def __init__(self, config_file: str = "config.yaml"):
        """
        Initialize configuration manager.
        
        Args:
            config_file: Path to configuration file
        """
        self.config_file = config_file
        self.config = None
        self._load_config()
        self._validate_config()
    
    def _load_config(self) -> None:
        """Load configuration from file."""
        try:
            if not os.path.exists(self.config_file):
                raise ConfigError(f"Configuration file not found: {self.config_file}")
            
            with open(self.config_file, 'r', encoding='utf-8') as f:
                self.config = yaml.safe_load(f)
            
            if not self.config:
                raise ConfigError("Configuration file is empty or invalid")
                
        except yaml.YAMLError as e:
            raise ConfigError(f"Invalid YAML in configuration file: {e}")
        except Exception as e:
            raise ConfigError(f"Error loading configuration: {e}")
    
    def _validate_config(self) -> None:
        """Validate configuration structure and values."""
        required_sections = ['mt5', 'server', 'trading', 'logging', 'webhook']
        
        for section in required_sections:
            if section not in self.config:
                raise ConfigError(f"Missing required configuration section: {section}")
        
        # Validate MT5 configuration
        self._validate_mt5_config()
        
        # Validate server configuration
        self._validate_server_config()
        
        # Validate trading configuration
        self._validate_trading_config()
        
        # Validate logging configuration
        self._validate_logging_config()
    
    def _validate_mt5_config(self) -> None:
        """Validate MT5 configuration section."""
        mt5_config = self.config['mt5']

        # 简化验证，只检查基本配置
        # 不再需要账户配置，直接使用MT5客户端当前登录的账户
        pass
        
        # Validate timeout settings
        if 'timeout' in mt5_config:
            timeout = mt5_config['timeout']
            if 'connect' in timeout and (not isinstance(timeout['connect'], int) or timeout['connect'] <= 0):
                raise ConfigError("MT5 connect timeout must be a positive integer")
            if 'trade' in timeout and (not isinstance(timeout['trade'], int) or timeout['trade'] <= 0):
                raise ConfigError("MT5 trade timeout must be a positive integer")
    
    def _validate_server_config(self) -> None:
        """Validate server configuration section."""
        server_config = self.config['server']
        
        # Validate required fields
        required_fields = ['host', 'port']
        for field in required_fields:
            if field not in server_config:
                raise ConfigError(f"Missing server configuration field: {field}")
        
        # Validate port
        port = server_config['port']
        if not isinstance(port, int) or port < 1 or port > 65535:
            raise ConfigError("Server port must be an integer between 1 and 65535")
        
        # Validate security settings if present
        if 'security' in server_config:
            security = server_config['security']
            if 'allowed_ips' in security and not isinstance(security['allowed_ips'], list):
                raise ConfigError("allowed_ips must be a list")
    
    def _validate_trading_config(self) -> None:
        """Validate trading configuration section."""
        trading_config = self.config['trading']
        
        # Validate volume settings
        volume_fields = ['default_volume', 'max_volume', 'min_volume']
        for field in volume_fields:
            if field in trading_config:
                value = trading_config[field]
                if not isinstance(value, (int, float)) or value <= 0:
                    raise ConfigError(f"Trading {field} must be a positive number")
        
        # Validate volume relationships
        if all(field in trading_config for field in volume_fields):
            min_vol = trading_config['min_volume']
            default_vol = trading_config['default_volume']
            max_vol = trading_config['max_volume']
            
            if not (min_vol <= default_vol <= max_vol):
                raise ConfigError("Volume settings must satisfy: min_volume <= default_volume <= max_volume")
        
        # Validate magic number
        if 'magic_number' in trading_config:
            magic = trading_config['magic_number']
            if not isinstance(magic, int) or magic < 0:
                raise ConfigError("Magic number must be a non-negative integer")
        
        # Validate allowed symbols
        if 'allowed_symbols' in trading_config:
            symbols = trading_config['allowed_symbols']
            if not isinstance(symbols, list):
                raise ConfigError("allowed_symbols must be a list")
    
    def _validate_logging_config(self) -> None:
        """Validate logging configuration section."""
        logging_config = self.config['logging']
        
        # Validate log level
        if 'level' in logging_config:
            level = logging_config['level']
            valid_levels = ['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL']
            if level not in valid_levels:
                raise ConfigError(f"Invalid log level: {level}. Must be one of {valid_levels}")
        
        # Validate numeric settings
        numeric_fields = ['max_size', 'backup_count']
        for field in numeric_fields:
            if field in logging_config:
                value = logging_config[field]
                if not isinstance(value, int) or value < 0:
                    raise ConfigError(f"Logging {field} must be a non-negative integer")
    
    def get_config(self) -> Dict[str, Any]:
        """
        Get the complete configuration.
        
        Returns:
            Complete configuration dictionary
        """
        return self.config.copy()
    
    def get_section(self, section: str) -> Dict[str, Any]:
        """
        Get a specific configuration section.
        
        Args:
            section: Section name
            
        Returns:
            Configuration section dictionary
            
        Raises:
            ConfigError: If section doesn't exist
        """
        if section not in self.config:
            raise ConfigError(f"Configuration section not found: {section}")
        
        return self.config[section].copy()
    
    def get_value(self, section: str, key: str, default: Any = None) -> Any:
        """
        Get a specific configuration value.
        
        Args:
            section: Section name
            key: Key name
            default: Default value if key doesn't exist
            
        Returns:
            Configuration value or default
        """
        if section not in self.config:
            return default
        
        return self.config[section].get(key, default)
    
    def reload_config(self) -> None:
        """Reload configuration from file."""
        self._load_config()
        self._validate_config()
    
    def update_config(self, section: str, key: str, value: Any) -> None:
        """
        Update a configuration value.
        
        Args:
            section: Section name
            key: Key name
            value: New value
        """
        if section not in self.config:
            self.config[section] = {}
        
        self.config[section][key] = value
    
    def save_config(self) -> None:
        """Save current configuration to file."""
        try:
            with open(self.config_file, 'w', encoding='utf-8') as f:
                yaml.dump(self.config, f, default_flow_style=False, indent=2)
        except Exception as e:
            raise ConfigError(f"Error saving configuration: {e}")
