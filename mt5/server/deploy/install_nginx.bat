@echo off
setlocal enabledelayedexpansion

echo ========================================
echo Nginx Installation and Configuration
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
set "NGINX_DIR=C:\nginx"
set "NGINX_VERSION=1.24.0"
set "NGINX_URL=http://nginx.org/download/nginx-%NGINX_VERSION%.zip"
set "SERVICE_NAME=nginx"

echo Installing nginx to: %NGINX_DIR%
echo.

REM 创建nginx目录
if not exist "%NGINX_DIR%" (
    echo Creating nginx directory...
    mkdir "%NGINX_DIR%"
)

cd /d "%NGINX_DIR%"

REM 下载nginx
if not exist "nginx.exe" (
    echo Downloading nginx %NGINX_VERSION%...
    powershell -Command "try { Invoke-WebRequest -Uri '%NGINX_URL%' -OutFile 'nginx.zip' -UseBasicParsing } catch { Write-Host 'Failed to download nginx'; exit 1 }"
    if %errorLevel% neq 0 (
        echo Error: Failed to download nginx.
        pause
        exit /b 1
    )
    
    echo Extracting nginx...
    powershell -Command "try { Expand-Archive -Path 'nginx.zip' -DestinationPath '.' -Force } catch { Write-Host 'Failed to extract nginx'; exit 1 }"
    if %errorLevel% neq 0 (
        echo Error: Failed to extract nginx.
        pause
        exit /b 1
    )
    
    echo Moving files...
    move "nginx-%NGINX_VERSION%\*" . >nul 2>&1
    rmdir /s /q "nginx-%NGINX_VERSION%" >nul 2>&1
    del "nginx.zip" >nul 2>&1
)

REM 创建必要的目录
if not exist "logs" mkdir "logs"
if not exist "temp" mkdir "temp"

REM 备份原配置文件
if exist "conf\nginx.conf" (
    echo Backing up existing configuration...
    copy "conf\nginx.conf" "conf\nginx.conf.backup.%date:~0,4%%date:~5,2%%date:~8,2%" >nul
)

REM 复制新的配置文件（如果存在）
set "CONFIG_SOURCE=%~dp0nginx.conf"
if exist "%CONFIG_SOURCE%" (
    echo Installing new nginx configuration...
    copy "%CONFIG_SOURCE%" "conf\nginx.conf" >nul
    if %errorLevel% neq 0 (
        echo Warning: Failed to copy configuration file.
        echo Using default configuration.
    )
) else (
    echo Warning: nginx.conf not found in deploy directory.
    echo Using default nginx configuration.
)

REM 测试nginx配置
echo Testing nginx configuration...
nginx.exe -t
if %errorLevel% neq 0 (
    echo Error: nginx configuration test failed.
    echo Please check the configuration file.
    pause
    exit /b 1
)

echo.
echo Downloading NSSM for service installation...
if not exist "nssm.exe" (
    powershell -Command "try { Invoke-WebRequest -Uri 'https://nssm.cc/release/nssm-2.24.zip' -OutFile 'nssm.zip' -UseBasicParsing } catch { Write-Host 'Failed to download NSSM'; exit 1 }"
    if %errorLevel% neq 0 (
        echo Error: Failed to download NSSM.
        pause
        exit /b 1
    )
    
    powershell -Command "try { Expand-Archive -Path 'nssm.zip' -DestinationPath '.' -Force } catch { Write-Host 'Failed to extract NSSM'; exit 1 }"
    copy "nssm-2.24\win64\nssm.exe" "nssm.exe" >nul
    rmdir /s /q "nssm-2.24" >nul 2>&1
    del "nssm.zip" >nul 2>&1
)

REM 检查服务是否已存在
echo.
echo Checking if nginx service already exists...
sc query "%SERVICE_NAME%" >nul 2>&1
if %errorLevel% equ 0 (
    echo Service already exists. Stopping and removing...
    net stop "%SERVICE_NAME%" >nul 2>&1
    nssm.exe remove "%SERVICE_NAME%" confirm >nul 2>&1
    timeout /t 2 >nul
)

REM 安装nginx服务
echo Installing nginx as Windows service...
nssm.exe install "%SERVICE_NAME%" "%NGINX_DIR%\nginx.exe"
if %errorLevel% neq 0 (
    echo Error: Failed to install nginx service.
    pause
    exit /b 1
)

REM 配置服务属性
echo Configuring service properties...
nssm.exe set "%SERVICE_NAME%" AppDirectory "%NGINX_DIR%"
nssm.exe set "%SERVICE_NAME%" DisplayName "Nginx Web Server"
nssm.exe set "%SERVICE_NAME%" Description "Nginx HTTP Server for MT5 API Proxy"

REM 设置服务启动类型为自动
nssm.exe set "%SERVICE_NAME%" Start SERVICE_AUTO_START

REM 设置服务恢复选项
nssm.exe set "%SERVICE_NAME%" AppExit Default Restart
nssm.exe set "%SERVICE_NAME%" AppRestartDelay 5000

REM 设置日志文件
nssm.exe set "%SERVICE_NAME%" AppStdout "%NGINX_DIR%\logs\service_output.log"
nssm.exe set "%SERVICE_NAME%" AppStderr "%NGINX_DIR%\logs\service_error.log"

REM 配置防火墙规则
echo.
echo Configuring Windows Firewall...
netsh advfirewall firewall delete rule name="Allow HTTP (nginx)" >nul 2>&1
netsh advfirewall firewall add rule name="Allow HTTP (nginx)" dir=in action=allow protocol=TCP localport=80
if %errorLevel% neq 0 (
    echo Warning: Failed to configure firewall rule for HTTP.
    echo You may need to configure it manually.
)

REM 启动服务
echo.
echo Starting nginx service...
net start "%SERVICE_NAME%"
if %errorLevel% neq 0 (
    echo Warning: Failed to start nginx service automatically.
    echo You can start it manually using: net start %SERVICE_NAME%
) else (
    echo Nginx service started successfully!
)

echo.
echo Waiting for nginx to initialize...
timeout /t 3 >nul

REM 测试nginx
echo.
echo Testing nginx installation...
powershell -Command "try { $response = Invoke-WebRequest -Uri 'http://127.0.0.1' -UseBasicParsing -TimeoutSec 10; Write-Host 'Nginx test successful. Status:' $response.StatusCode } catch { Write-Host 'Nginx test failed:' $_.Exception.Message }"

echo.
echo ========================================
echo Installation Summary
echo ========================================
echo Nginx Directory: %NGINX_DIR%
echo Service Name: %SERVICE_NAME%
echo Configuration: %NGINX_DIR%\conf\nginx.conf
echo.
echo Service Management Commands:
echo   Start:   net start %SERVICE_NAME%
echo   Stop:    net stop %SERVICE_NAME%
echo   Restart: net stop %SERVICE_NAME% ^&^& net start %SERVICE_NAME%
echo   Reload:  %NGINX_DIR%\nginx.exe -s reload
echo   Test:    %NGINX_DIR%\nginx.exe -t
echo   Remove:  nssm.exe remove %SERVICE_NAME% confirm
echo.
echo Log Files:
echo   Access Log:     %NGINX_DIR%\logs\access.log
echo   Error Log:      %NGINX_DIR%\logs\error.log
echo   Service Output: %NGINX_DIR%\logs\service_output.log
echo   Service Error:  %NGINX_DIR%\logs\service_error.log
echo.
echo URLs:
echo   HTTP:        http://localhost
echo   Health:      http://localhost/health
echo   API:         http://localhost/api/
echo   Webhook:     http://localhost/webhook
echo   Status:      http://localhost/nginx_status (localhost only)
echo.
echo Installation completed!
echo.
pause
