#!/usr/bin/env python3
"""
MT5 Trading HTTP Server
A Flask-based HTTP server for executing MT5 trades via webhook calls.
"""

import os
import sys
import logging
import time
from datetime import datetime
from flask import Flask, request, jsonify
from flask_cors import CORS

# Add current directory to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from config_manager import ConfigManager
from mt5_connector import MT5Connector
from trading_manager import TradingManager
from utils.logger import setup_logger
from utils.validators import validate_webhook_payload, validate_api_key
from utils.exceptions import MT5Error, ConfigError, ValidationError
from utils.chinese_parser import parse_chinese_message

# Initialize Flask app
app = Flask(__name__)
CORS(app)

# Global variables
config_manager = None
mt5_connector = None
trading_manager = None
logger = None


def initialize_app():
    """Initialize the application components."""
    global config_manager, mt5_connector, trading_manager, logger

    try:
        # Load configuration
        config_manager = ConfigManager()
        config = config_manager.get_config()

        # Setup logging
        logger = setup_logger(config['logging'])
        logger.info("Starting MT5 Trading HTTP Server...")

        # Initialize MT5 connector (使用当前已登录的MT5)
        mt5_connector = MT5Connector(config['mt5'])
        if not mt5_connector.connect():
            raise MT5Error("Failed to connect to MT5 terminal")

        # Initialize trading manager
        trading_config = config['trading'].copy()
        trading_config['custom_intervals'] = config.get('custom_intervals', {})
        trading_manager = TradingManager(mt5_connector, trading_config)

        logger.info("Application initialized successfully")
        return True

    except Exception as e:
        if logger:
            logger.error(f"Failed to initialize application: {e}")
        else:
            print(f"Failed to initialize application: {e}")
        return False


@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint."""
    try:
        mt5_status = mt5_connector.is_connected() if mt5_connector else False

        # Get account info
        account_info = None
        if mt5_connector and mt5_status:
            account_info = mt5_connector.get_account_info()

        return jsonify({
            'status': 'healthy' if mt5_status else 'unhealthy',
            'mt5_connected': mt5_status,
            'account_info': account_info,
            'timestamp': trading_manager.get_server_time() if trading_manager else None
        })
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return jsonify({'status': 'error', 'message': str(e)}), 500


@app.route('/status', methods=['GET'])
def get_status():
    """Get detailed server status."""
    try:
        # Validate API key if required
        if not validate_api_key(request, config_manager.get_config()['server'].get('security', {})):
            return jsonify({'error': 'Invalid API key'}), 401

        # Get account info
        account_info = trading_manager.get_account_info() if trading_manager else None

        return jsonify({
            'server_status': 'running',
            'mt5_connected': mt5_connector.is_connected() if mt5_connector else False,
            'account_info': account_info,
            'timestamp': trading_manager.get_server_time() if trading_manager else None
        })
    except Exception as e:
        logger.error(f"Status check failed: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/positions', methods=['GET'])
def get_positions():
    """Get current positions."""
    try:
        # Validate API key if required
        if not validate_api_key(request, config_manager.get_config()['server'].get('security', {})):
            return jsonify({'error': 'Invalid API key'}), 401

        positions = trading_manager.get_positions() if trading_manager else []
        return jsonify({
            'success': True,
            'positions': positions,
            'count': len(positions),
            'timestamp': trading_manager.get_server_time() if trading_manager else None
        })
    except Exception as e:
        logger.error(f"Get positions failed: {e}")
        return jsonify({'error': str(e)}), 500



@app.route('/webhook', methods=['POST'])
def webhook():
    """Handle TradingView webhook requests."""
    try:
        # Validate API key if required
        if not validate_api_key(request, config_manager.get_config()['server'].get('security', {})):
            return jsonify({'error': 'Invalid API key'}), 401
        
        # Get request data - support both JSON and plain text
        content_type = request.content_type or ''

        if 'application/json' in content_type:
            # JSON format
            payload = request.get_json()
            if not payload:
                return jsonify({'error': 'No JSON payload provided'}), 400
            # 检查是否为测试模式
            if payload.get('test') is True:
                logger.info(f"Test mode enabled, returning mock response for payload: {payload}")
                return jsonify({
                    'success': True,
                    'message': 'Test mode - operation simulated successfully',
                    'result': {
                        'action': payload.get('action', 'unknown'),
                        'symbol': payload.get('symbol', 'TEST'),
                        'volume': payload.get('volume', 0.01),
                        'price': 1.0000,
                        'ticket': 999999999,
                        'timestamp': datetime.now().isoformat(),
                        'test_mode': True
                    }
                })

            # Check if it's Chinese message format in JSON
            if 'message' in payload and isinstance(payload['message'], str):
                try:
                    logger.info(f"Parsing Chinese message from JSON: {payload['message']}")
                    parsed_payload = parse_chinese_message(payload['message'])
                    payload = parsed_payload
                    logger.info(f"Parsed to: {payload}")
                except ValidationError as e:
                    logger.warning(f"Chinese message parsing error: {e}")
                    return jsonify({'error': f'中文消息解析错误: {str(e)}'}), 400
        else:
            # Plain text format - assume it's Chinese message
            message = request.get_data(as_text=True)
            if not message:
                return jsonify({'error': 'No message provided'}), 400

            try:
                logger.info(f"Parsing Chinese message from text: {message}")
                payload = parse_chinese_message(message.strip())
                logger.info(f"Parsed to: {payload}")
            except ValidationError as e:
                logger.warning(f"Chinese message parsing error: {e}")
                return jsonify({'error': f'中文消息解析错误: {str(e)}'}), 400

        # Validate webhook payload
        validation_result = validate_webhook_payload(payload, config_manager.get_config()['webhook'])
        if not validation_result['valid']:
            return jsonify({'error': validation_result['message']}), 400

        # Log webhook received
        logger.info(f"Webhook received: {payload}")

        # 移除账户参数（如果存在），因为现在只使用当前登录的账户
        if 'account_id' in payload:
            del payload['account_id']

        # 计算到这个分钟结束需要等待的秒数
        now = datetime.now()
        seconds_to_next_minute = 60 - now.second # + 60  # 下个分钟的00秒
        logger.info(f"Current time: {now.strftime('%H:%M:%S')}, waiting {seconds_to_next_minute} seconds")
        
        # 等待到下个分钟结束
        time.sleep(seconds_to_next_minute)
        
        # Execute trade
        result = trading_manager.execute_webhook_trade(payload)

        return jsonify({
            'success': True,
            'message': 'Trade executed successfully',
            'result': result
        })
        
    except ValidationError as e:
        logger.warning(f"Webhook validation error: {e}")
        return jsonify({'error': str(e)}), 400
    except MT5Error as e:
        logger.error(f"MT5 error in webhook: {e}")
        return jsonify({'error': str(e)}), 500
    except Exception as e:
        logger.error(f"Unexpected error in webhook: {e}")
        return jsonify({'error': 'Internal server error'}), 500


@app.route('/trade', methods=['POST'])
def manual_trade():
    """Manual trade endpoint for testing."""
    try:
        # Validate API key if required
        if not validate_api_key(request, config_manager.get_config()['server'].get('security', {})):
            return jsonify({'error': 'Invalid API key'}), 401

        payload = request.get_json()
        if not payload:
            return jsonify({'error': 'No JSON payload provided'}), 400

        # 移除账户参数（如果存在），因为现在只使用当前登录的账户
        if 'account_id' in payload:
            del payload['account_id']

        # Execute trade
        result = trading_manager.execute_trade(payload)

        return jsonify({
            'success': True,
            'message': 'Trade executed successfully',
            'result': result
        })

    except Exception as e:
        logger.error(f"Error in manual trade: {e}")
        return jsonify({'error': str(e)}), 500


@app.errorhandler(404)
def not_found(error):
    """Handle 404 errors."""
    return jsonify({'error': 'Endpoint not found'}), 404


@app.errorhandler(500)
def internal_error(error):
    """Handle 500 errors."""
    logger.error(f"Internal server error: {error}")
    return jsonify({'error': 'Internal server error'}), 500


def main():
    """Main function to run the server."""
    if not initialize_app():
        sys.exit(1)
    
    try:
        config = config_manager.get_config()
        server_config = config['server']
        
        logger.info(f"Starting server on {server_config['host']}:{server_config['port']}")
        app.run(
            host=server_config['host'],
            port=server_config['port'],
            debug=server_config['debug']
        )
    except KeyboardInterrupt:
        logger.info("Server stopped by user")
    except Exception as e:
        logger.error(f"Server error: {e}")
    finally:
        if mt5_connector:
            mt5_connector.disconnect()
        logger.info("Server shutdown complete")


if __name__ == '__main__':
    main()
