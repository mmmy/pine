#!/usr/bin/env python3
"""
Test auto-reconnect functionality.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from config_manager import ConfigManager
from mt5_connector import MT5Connector
from trading_manager import TradingManager
import MetaTrader5 as mt5


def test_auto_reconnect():
    """Test auto-reconnect functionality."""
    
    print("Testing MT5 Auto-Reconnect Functionality")
    print("=" * 50)
    
    try:
        # Load configuration
        config_manager = ConfigManager()
        config = config_manager.get_config()
        
        # Initialize MT5 connector
        mt5_connector = MT5Connector(config['mt5'])
        
        print("1. Initial connection...")
        if not mt5_connector.connect():
            print("❌ Failed to connect to MT5")
            return
        print("✅ Connected to MT5")
        
        # Initialize trading manager
        trading_config = config['trading'].copy()
        trading_config['custom_intervals'] = config.get('custom_intervals', {})
        trading_manager = TradingManager(mt5_connector, trading_config)
        
        print("\n2. Testing normal operations...")
        
        # Test account info
        account_info = mt5_connector.get_account_info()
        if account_info:
            print(f"✅ Account info: {account_info['login']} - {account_info['name']}")
        else:
            print("❌ Failed to get account info")
        
        # Test positions
        positions = mt5_connector.get_positions()
        print(f"✅ Positions: {len(positions)} found")
        
        print("\n3. Simulating connection loss...")
        
        # Simulate connection loss by shutting down MT5
        mt5.shutdown()
        print("🔌 MT5 connection manually closed")
        
        print("\n4. Testing auto-reconnect...")
        
        # Try to get account info again - should trigger auto-reconnect
        print("Attempting to get account info (should trigger reconnect)...")
        account_info = mt5_connector.get_account_info()
        if account_info:
            print(f"✅ Auto-reconnect successful! Account: {account_info['login']}")
        else:
            print("❌ Auto-reconnect failed")
        
        # Test positions again
        positions = mt5_connector.get_positions()
        print(f"✅ Positions after reconnect: {len(positions)} found")
        
        print("\n5. Testing trading operations after reconnect...")
        
        # Test a simple webhook operation
        test_payload = {
            'action': 'enable_trading_hours'
        }
        
        result = trading_manager.execute_webhook_trade(test_payload)
        if result.get('success'):
            print("✅ Trading operation successful after reconnect")
        else:
            print("❌ Trading operation failed after reconnect")
        
        print("\n🎉 Auto-reconnect test completed!")
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        # Clean up
        try:
            if 'mt5_connector' in locals():
                mt5_connector.disconnect()
        except:
            pass


if __name__ == '__main__':
    test_auto_reconnect()
