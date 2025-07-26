#!/usr/bin/env python3
"""
Startup script for MT5 Trading HTTP Server.
Provides additional startup options and environment handling.
"""

import os
import sys
import argparse
from dotenv import load_dotenv

# Add current directory to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app import main


def setup_environment():
    """Setup environment variables from .env file."""
    env_file = os.path.join(os.path.dirname(__file__), '.env')
    if os.path.exists(env_file):
        load_dotenv(env_file)
        print(f"Loaded environment from {env_file}")
    else:
        print("No .env file found, using system environment variables")


def parse_arguments():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description='MT5 Trading HTTP Server')
    
    parser.add_argument(
        '--config', '-c',
        default='config.yaml',
        help='Configuration file path (default: config.yaml)'
    )
    
    parser.add_argument(
        '--host',
        help='Server host (overrides config)'
    )
    
    parser.add_argument(
        '--port', '-p',
        type=int,
        help='Server port (overrides config)'
    )
    
    parser.add_argument(
        '--debug',
        action='store_true',
        help='Enable debug mode'
    )
    
    parser.add_argument(
        '--log-level',
        choices=['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL'],
        help='Log level (overrides config)'
    )
    
    return parser.parse_args()


def update_config_from_args(args):
    """Update configuration based on command line arguments."""
    # This would be implemented to override config values
    # For now, we'll use environment variables
    
    if args.host:
        os.environ['SERVER_HOST'] = args.host
    
    if args.port:
        os.environ['SERVER_PORT'] = str(args.port)
    
    if args.debug:
        os.environ['DEBUG_MODE'] = 'true'
    
    if args.log_level:
        os.environ['LOG_LEVEL'] = args.log_level


def check_requirements():
    """Check if all required dependencies are installed."""
    # Package name mapping: pip package name -> import name
    required_packages = {
        'MetaTrader5': 'MetaTrader5',
        'Flask': 'flask',
        'PyYAML': 'yaml',
        'pandas': 'pandas',
        'pytz': 'pytz',
        'python-dotenv': 'dotenv',
        'Flask-CORS': 'flask_cors'
    }

    missing_packages = []
    for pip_name, import_name in required_packages.items():
        try:
            __import__(import_name)
        except ImportError:
            missing_packages.append(pip_name)

    if missing_packages:
        print("Error: Missing required packages:")
        for package in missing_packages:
            print(f"  - {package}")
        print("\nPlease install missing packages using:")
        print("  pip install -r requirements.txt")
        return False

    return True


def main_startup():
    """Main startup function."""
    print("MT5 Trading HTTP Server")
    print("=" * 50)
    
    # Parse command line arguments
    args = parse_arguments()
    
    # Check requirements
    if not check_requirements():
        sys.exit(1)
    
    # Setup environment
    setup_environment()
    
    # Update config from arguments
    update_config_from_args(args)
    
    # Set config file path
    if args.config:
        os.environ['CONFIG_FILE'] = args.config
    
    print(f"Starting server with config: {args.config}")
    print("Press Ctrl+C to stop the server")
    print("-" * 50)
    
    try:
        # Start the main application
        main()
    except KeyboardInterrupt:
        print("\nServer stopped by user")
    except Exception as e:
        print(f"Server error: {e}")
        sys.exit(1)


if __name__ == '__main__':
    main_startup()
