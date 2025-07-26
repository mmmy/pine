#!/usr/bin/env python3
"""
Production startup script for MT5 Trading HTTP Server using Waitress WSGI server.
"""

import os
import sys
import argparse
from dotenv import load_dotenv

# Add current directory to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

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
    parser = argparse.ArgumentParser(description='MT5 Trading HTTP Server - Production')
    
    parser.add_argument(
        '--config', '-c',
        default='config.yaml',
        help='Configuration file path (default: config.yaml)'
    )
    
    parser.add_argument(
        '--host',
        default='127.0.0.1',
        help='Server host (default: 127.0.0.1)'
    )
    
    parser.add_argument(
        '--port', '-p',
        type=int,
        default=5000,
        help='Server port (default: 5000)'
    )
    
    parser.add_argument(
        '--threads',
        type=int,
        default=4,
        help='Number of threads (default: 4)'
    )
    
    parser.add_argument(
        '--connection-limit',
        type=int,
        default=1000,
        help='Connection limit (default: 1000)'
    )
    
    return parser.parse_args()

def check_requirements():
    """Check if all required dependencies are installed."""
    required_packages = {
        'waitress': 'waitress',
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
        print("  pip install waitress")
        print("  pip install -r requirements.txt")
        return False
    
    return True

def main():
    """Main function to run the production server."""
    print("MT5 Trading HTTP Server - Production Mode")
    print("=" * 50)
    
    # Parse arguments
    args = parse_arguments()
    
    # Check requirements
    if not check_requirements():
        sys.exit(1)
    
    # Setup environment
    setup_environment()
    
    # Set config file path
    if args.config:
        os.environ['CONFIG_FILE'] = args.config
    
    print(f"Configuration file: {args.config}")
    print(f"Server address: {args.host}:{args.port}")
    print(f"Threads: {args.threads}")
    print(f"Connection limit: {args.connection_limit}")
    print("-" * 50)
    
    try:
        # Import the Flask app
        from app import app
        
        # Import waitress
        from waitress import serve
        
        print("Starting Waitress WSGI server...")
        print("Press Ctrl+C to stop the server")
        
        # Start the production server
        serve(
            app,
            host=args.host,
            port=args.port,
            threads=args.threads,
            connection_limit=args.connection_limit,
            cleanup_interval=30,
            channel_timeout=120,
            log_socket_errors=True
        )
        
    except KeyboardInterrupt:
        print("\nServer stopped by user")
    except Exception as e:
        print(f"Server error: {e}")
        sys.exit(1)

if __name__ == '__main__':
    main()
