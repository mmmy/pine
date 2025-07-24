#!/usr/bin/env python3
"""
Installation and setup script for MT5 Trading HTTP Server.
"""

import os
import sys
import subprocess
import shutil
from pathlib import Path


def check_python_version():
    """Check if Python version is compatible."""
    if sys.version_info < (3, 7):
        print("Error: Python 3.7 or higher is required.")
        print(f"Current version: {sys.version}")
        return False
    print(f"✓ Python version: {sys.version.split()[0]}")
    return True


def check_platform():
    """Check if platform is Windows (required for MT5)."""
    if sys.platform != 'win32':
        print("Warning: MetaTrader 5 Python API only works on Windows.")
        print("You can still install the server, but MT5 connection will not work.")
        return False
    print("✓ Platform: Windows")
    return True


def install_requirements():
    """Install Python requirements."""
    print("Installing Python dependencies...")
    try:
        subprocess.check_call([
            sys.executable, '-m', 'pip', 'install', '-r', 'requirements.txt'
        ])
        print("✓ Dependencies installed successfully")
        return True
    except subprocess.CalledProcessError as e:
        print(f"Error installing dependencies: {e}")
        return False


def create_directories():
    """Create necessary directories."""
    directories = ['logs', 'config', 'tests']
    
    for directory in directories:
        path = Path(directory)
        if not path.exists():
            path.mkdir(parents=True, exist_ok=True)
            print(f"✓ Created directory: {directory}")
        else:
            print(f"✓ Directory exists: {directory}")


def setup_config_files():
    """Setup configuration files."""
    # Copy .env.example to .env if it doesn't exist
    if not os.path.exists('.env'):
        if os.path.exists('.env.example'):
            shutil.copy('.env.example', '.env')
            print("✓ Created .env file from template")
        else:
            print("Warning: .env.example not found")
    else:
        print("✓ .env file already exists")
    
    # Check config.yaml
    if os.path.exists('config.yaml'):
        print("✓ config.yaml file exists")
    else:
        print("Warning: config.yaml not found. Please create it based on the documentation.")


def test_imports():
    """Test if all required modules can be imported."""
    print("Testing module imports...")
    
    required_modules = [
        'flask',
        'yaml',
        'pandas',
        'pytz',
        'requests'
    ]
    
    # MetaTrader5 only on Windows
    if sys.platform == 'win32':
        required_modules.append('MetaTrader5')
    
    failed_imports = []
    
    for module in required_modules:
        try:
            __import__(module)
            print(f"✓ {module}")
        except ImportError:
            print(f"✗ {module}")
            failed_imports.append(module)
    
    if failed_imports:
        print(f"\nError: Failed to import: {', '.join(failed_imports)}")
        return False
    
    print("✓ All modules imported successfully")
    return True


def create_startup_scripts():
    """Create platform-specific startup scripts."""
    
    # Windows batch file
    batch_content = """@echo off
echo Starting MT5 Trading HTTP Server...
python start_server.py
pause
"""
    
    with open('start_server.bat', 'w') as f:
        f.write(batch_content)
    print("✓ Created start_server.bat")
    
    # PowerShell script
    ps_content = """# MT5 Trading HTTP Server Startup Script
Write-Host "Starting MT5 Trading HTTP Server..." -ForegroundColor Green
python start_server.py
Read-Host "Press Enter to exit"
"""
    
    with open('start_server.ps1', 'w') as f:
        f.write(ps_content)
    print("✓ Created start_server.ps1")


def display_next_steps():
    """Display next steps for the user."""
    print("\n" + "="*60)
    print("Installation completed!")
    print("="*60)
    print("\nNext steps:")
    print("1. Edit config.yaml with your MT5 account details:")
    print("   - MT5 login number")
    print("   - MT5 password")
    print("   - Broker server name")
    print()
    print("2. (Optional) Edit .env file for environment variables")
    print()
    print("3. Make sure MetaTrader 5 terminal is running")
    print()
    print("4. Start the server:")
    print("   python start_server.py")
    print("   or")
    print("   start_server.bat")
    print()
    print("5. Test the installation:")
    print("   python test_api.py")
    print()
    print("For detailed configuration, see README.md")
    print("\n" + "="*60)


def main():
    """Main installation function."""
    print("MT5 Trading HTTP Server - Installation Script")
    print("=" * 50)
    
    # Check requirements
    if not check_python_version():
        sys.exit(1)
    
    platform_ok = check_platform()
    
    # Create directories
    create_directories()
    
    # Install dependencies
    if not install_requirements():
        print("Installation failed. Please check the error messages above.")
        sys.exit(1)
    
    # Test imports
    if not test_imports():
        print("Some modules failed to import. Please check the installation.")
        if not platform_ok:
            print("Note: MetaTrader5 module will not work on non-Windows platforms.")
        sys.exit(1)
    
    # Setup config files
    setup_config_files()
    
    # Create startup scripts
    create_startup_scripts()
    
    # Display next steps
    display_next_steps()


if __name__ == '__main__':
    main()
