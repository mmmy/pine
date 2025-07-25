#!/usr/bin/env python3
"""
Test filling mode functionality.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

import MetaTrader5 as mt5
from config_manager import ConfigManager
from mt5_connector import MT5Connector
from trading_manager import TradingManager


def test_filling_mode():
    """Test filling mode detection for different symbols."""
    
    print("Testing MT5 Filling Mode Detection")
    print("=" * 50)
    
    try:
        # Load configuration
        config_manager = ConfigManager()
        config = config_manager.get_config()
        
        # Initialize MT5 connector
        mt5_connector = MT5Connector(config['mt5'])
        
        print("1. Connecting to MT5...")
        if not mt5_connector.connect():
            print("❌ Failed to connect to MT5")
            return
        print("✅ Connected to MT5")
        
        # Initialize trading manager
        trading_config = config['trading'].copy()
        trading_config['custom_intervals'] = config.get('custom_intervals', {})
        trading_manager = TradingManager(mt5_connector, trading_config)
        
        # Test symbols
        test_symbols = ['XAUUSD', 'EURUSD', 'GBPUSD', 'USDJPY']
        
        print("\n2. Testing filling mode detection...")
        
        for symbol in test_symbols:
            print(f"\n--- Testing {symbol} ---")
            
            # Get MT5 symbol info
            mt5_symbol_info = mt5.symbol_info(symbol)
            if mt5_symbol_info is None:
                print(f"❌ {symbol}: Symbol not available")
                continue
            
            # Test filling mode detection
            try:
                filling_mode = trading_manager._get_optimal_filling_mode(mt5_symbol_info)
                
                # Convert filling mode to readable name
                mode_names = {
                    mt5.ORDER_FILLING_FOK: "FOK (Fill or Kill)",
                    mt5.ORDER_FILLING_IOC: "IOC (Immediate or Cancel)", 
                    mt5.ORDER_FILLING_RETURN: "RETURN"
                }
                
                mode_name = mode_names.get(filling_mode, f"Unknown ({filling_mode})")
                
                print(f"✅ {symbol}: Optimal filling mode = {mode_name}")
                print(f"   Filling mode flags: {mt5_symbol_info.filling_mode}")
                
                # Show supported modes
                supported_modes = []
                if mt5_symbol_info.filling_mode & 1:  # FOK
                    supported_modes.append("FOK")
                if mt5_symbol_info.filling_mode & 2:  # IOC
                    supported_modes.append("IOC")
                if mt5_symbol_info.filling_mode & 4:  # RETURN
                    supported_modes.append("RETURN")
                
                print(f"   Supported modes: {', '.join(supported_modes) if supported_modes else 'None detected'}")
                
            except Exception as e:
                print(f"❌ {symbol}: Error detecting filling mode - {e}")
        
        print("\n3. Testing actual trade with XAUUSD...")
        
        # Test a small trade to verify filling mode works
        test_payload = {
            'action': 'buy',
            'symbol': 'XAUUSD',
            'volume': 0.01,
            'comment': 'Filling mode test'
        }
        
        # Enable trading hours first
        trading_manager.trading_hours_manager.enable_trading_hours()
        
        try:
            result = trading_manager._execute_market_order(test_payload)
            if result.get('success'):
                print("✅ Test trade executed successfully with optimal filling mode")
                print(f"   Order ticket: {result.get('ticket')}")
                
                # Close the test position immediately
                close_payload = {
                    'action': 'close',
                    'symbol': 'XAUUSD',
                    'ticket': result.get('ticket')
                }
                
                close_result = trading_manager._close_position(close_payload)
                if close_result.get('success'):
                    print("✅ Test position closed successfully")
                else:
                    print(f"⚠️ Failed to close test position: {close_result.get('error', 'Unknown error')}")
            else:
                print(f"❌ Test trade failed: {result.get('error', 'Unknown error')}")
                
        except Exception as e:
            print(f"❌ Test trade error: {e}")
        
        print("\n🎉 Filling mode test completed!")
        
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
    test_filling_mode()
