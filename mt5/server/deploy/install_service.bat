@echo off
setlocal enabledelayedexpansion

echo ========================================
echo MT5 Trading Server Service Installer
echo ========================================
echo.

REM 检查管理员权限
net session >nul 2>&1
if %errorLevel% neq 0 (
    echo Error: This script requires administrator privileges.
    echo Please run as administrator.
    pause
    exit /b 1
)

REM 设置变量
set "SERVICE_NAME=MT5Server"
set "SERVICE_DISPLAY_NAME=MT5 Trading HTTP Server"
set "SERVICE_DESCRIPTION=MT5 Trading HTTP Server for TradingView Webhooks"
set "INSTALL_DIR=C:\mt5-server"
set "PYTHON_EXE=python"
set "SCRIPT_PATH=%INSTALL_DIR%\start_server.py"

echo Checking installation directory...
if not exist "%INSTALL_DIR%" (
    echo Error: Installation directory not found: %INSTALL_DIR%
    echo Please ensure the MT5 server files are installed.
    pause
    exit /b 1
)

echo Checking Python installation...
%PYTHON_EXE% --version >nul 2>&1
if %errorLevel% neq 0 (
    echo Error: Python not found or not in PATH.
    echo Please install Python and add it to PATH.
    pause
    exit /b 1
)

echo Checking MT5 server script...
if not exist "%SCRIPT_PATH%" (
    echo Error: MT5 server script not found: %SCRIPT_PATH%
    pause
    exit /b 1
)

echo.
echo Downloading NSSM (Non-Sucking Service Manager)...
if not exist "nssm.exe" (
    powershell -Command "try { Invoke-WebRequest -Uri 'https://nssm.cc/release/nssm-2.24.zip' -OutFile 'nssm.zip' -UseBasicParsing } catch { Write-Host 'Failed to download NSSM'; exit 1 }"
    if %errorLevel% neq 0 (
        echo Error: Failed to download NSSM.
        pause
        exit /b 1
    )
    
    echo Extracting NSSM...
    powershell -Command "try { Expand-Archive -Path 'nssm.zip' -DestinationPath '.' -Force } catch { Write-Host 'Failed to extract NSSM'; exit 1 }"
    if %errorLevel% neq 0 (
        echo Error: Failed to extract NSSM.
        pause
        exit /b 1
    )
    
    copy "nssm-2.24\win64\nssm.exe" "nssm.exe" >nul
    if %errorLevel% neq 0 (
        echo Error: Failed to copy NSSM executable.
        pause
        exit /b 1
    )
    
    echo Cleaning up...
    rmdir /s /q "nssm-2.24" >nul 2>&1
    del "nssm.zip" >nul 2>&1
)

echo.
echo Checking if service already exists...
sc query "%SERVICE_NAME%" >nul 2>&1
if %errorLevel% equ 0 (
    echo Service already exists. Stopping and removing...
    net stop "%SERVICE_NAME%" >nul 2>&1
    nssm.exe remove "%SERVICE_NAME%" confirm >nul 2>&1
    timeout /t 2 >nul
)

echo.
echo Installing MT5 Server service...

REM 安装服务（使用生产模式启动脚本）
set "PRODUCTION_SCRIPT=%INSTALL_DIR%\start_production.py"
if exist "%PRODUCTION_SCRIPT%" (
    echo Using production startup script...
    nssm.exe install "%SERVICE_NAME%" "%PYTHON_EXE%" "%PRODUCTION_SCRIPT%"
) else (
    echo Using development startup script...
    nssm.exe install "%SERVICE_NAME%" "%PYTHON_EXE%" "%SCRIPT_PATH%"
)
if %errorLevel% neq 0 (
    echo Error: Failed to install service.
    pause
    exit /b 1
)

REM 设置服务属性
echo Configuring service properties...
nssm.exe set "%SERVICE_NAME%" AppDirectory "%INSTALL_DIR%"
nssm.exe set "%SERVICE_NAME%" DisplayName "%SERVICE_DISPLAY_NAME%"
nssm.exe set "%SERVICE_NAME%" Description "%SERVICE_DESCRIPTION%"

REM 设置服务启动类型为自动
nssm.exe set "%SERVICE_NAME%" Start SERVICE_AUTO_START

REM 设置服务依赖
nssm.exe set "%SERVICE_NAME%" DependOnService LanmanServer

REM 设置服务恢复选项
nssm.exe set "%SERVICE_NAME%" AppExit Default Restart
nssm.exe set "%SERVICE_NAME%" AppRestartDelay 5000

REM 设置日志文件
nssm.exe set "%SERVICE_NAME%" AppStdout "%INSTALL_DIR%\logs\service_output.log"
nssm.exe set "%SERVICE_NAME%" AppStderr "%INSTALL_DIR%\logs\service_error.log"

REM 创建日志目录
if not exist "%INSTALL_DIR%\logs" (
    mkdir "%INSTALL_DIR%\logs"
)

REM 设置环境变量
nssm.exe set "%SERVICE_NAME%" AppEnvironmentExtra "PYTHONPATH=%INSTALL_DIR%" "CONFIG_FILE=config.yaml"

echo.
echo Starting service...
net start "%SERVICE_NAME%"
if %errorLevel% neq 0 (
    echo Warning: Failed to start service automatically.
    echo You can start it manually using: net start %SERVICE_NAME%
) else (
    echo Service started successfully!
)

echo.
echo Waiting for service to initialize...
timeout /t 5 >nul

echo.
echo Testing service...
powershell -Command "try { $response = Invoke-RestMethod -Uri 'http://127.0.0.1:5000/health' -TimeoutSec 10; Write-Host 'Service test successful:'; Write-Host ($response | ConvertTo-Json) } catch { Write-Host 'Service test failed:' $_.Exception.Message }"

echo.
echo ========================================
echo Installation Summary
echo ========================================
echo Service Name: %SERVICE_NAME%
echo Display Name: %SERVICE_DISPLAY_NAME%
echo Install Directory: %INSTALL_DIR%
echo Python Executable: %PYTHON_EXE%
echo Script Path: %SCRIPT_PATH%
echo.
echo Service Management Commands:
echo   Start:   net start %SERVICE_NAME%
echo   Stop:    net stop %SERVICE_NAME%
echo   Restart: net stop %SERVICE_NAME% ^&^& net start %SERVICE_NAME%
echo   Status:  sc query %SERVICE_NAME%
echo   Remove:  nssm.exe remove %SERVICE_NAME% confirm
echo.
echo Log Files:
echo   Service Output: %INSTALL_DIR%\logs\service_output.log
echo   Service Error:  %INSTALL_DIR%\logs\service_error.log
echo   Application:    %INSTALL_DIR%\mt5_server.log
echo.
echo Installation completed!
echo.
pause
