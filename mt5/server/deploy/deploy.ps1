# MT5 Trading Server - 腾讯云部署脚本
# PowerShell自动化部署脚本

param(
    [string]$InstallDir = "C:\mt5-server",
    [string]$NginxDir = "C:\nginx",
    [string]$PythonVersion = "3.11.7",
    [switch]$SkipPython,
    [switch]$SkipNginx,
    [switch]$SkipService,
    [switch]$Force
)

# 检查管理员权限
function Test-Administrator {
    $currentUser = [Security.Principal.WindowsIdentity]::GetCurrent()
    $principal = New-Object Security.Principal.WindowsPrincipal($currentUser)
    return $principal.IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
}

# 写入彩色日志
function Write-ColorLog {
    param(
        [string]$Message,
        [string]$Color = "White",
        [string]$Level = "INFO"
    )
    $timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    Write-Host "[$timestamp] [$Level] $Message" -ForegroundColor $Color
}

# 检查端口占用
function Test-Port {
    param([int]$Port)
    try {
        $connection = New-Object System.Net.Sockets.TcpClient
        $connection.Connect("127.0.0.1", $Port)
        $connection.Close()
        return $true
    } catch {
        return $false
    }
}

# 下载文件
function Download-File {
    param(
        [string]$Url,
        [string]$OutputPath
    )
    try {
        Write-ColorLog "Downloading from $Url..." "Yellow"
        Invoke-WebRequest -Uri $Url -OutFile $OutputPath -UseBasicParsing
        Write-ColorLog "Download completed: $OutputPath" "Green"
        return $true
    } catch {
        Write-ColorLog "Download failed: $($_.Exception.Message)" "Red" "ERROR"
        return $false
    }
}

# 主函数
function Main {
    Write-Host "========================================" -ForegroundColor Cyan
    Write-Host "MT5 Trading Server - 腾讯云自动部署脚本" -ForegroundColor Cyan
    Write-Host "========================================" -ForegroundColor Cyan
    Write-Host ""

    # 检查管理员权限
    if (-not (Test-Administrator)) {
        Write-ColorLog "此脚本需要管理员权限，请以管理员身份运行PowerShell" "Red" "ERROR"
        exit 1
    }

    Write-ColorLog "开始部署MT5 Trading Server..." "Green"
    Write-ColorLog "安装目录: $InstallDir" "Cyan"
    Write-ColorLog "Nginx目录: $NginxDir" "Cyan"

    # 1. 安装Python
    if (-not $SkipPython) {
        Write-ColorLog "步骤 1: 检查Python安装..." "Yellow"
        
        try {
            $pythonVersion = python --version 2>&1
            Write-ColorLog "Python已安装: $pythonVersion" "Green"
        } catch {
            Write-ColorLog "Python未安装，开始安装Python $PythonVersion..." "Yellow"
            
            $pythonUrl = "https://www.python.org/ftp/python/$PythonVersion/python-$PythonVersion-amd64.exe"
            $pythonInstaller = "$env:TEMP\python-installer.exe"
            
            if (Download-File $pythonUrl $pythonInstaller) {
                Write-ColorLog "安装Python..." "Yellow"
                Start-Process -FilePath $pythonInstaller -ArgumentList "/quiet", "InstallAllUsers=1", "PrependPath=1", "Include_test=0" -Wait
                
                # 刷新环境变量
                $env:Path = [System.Environment]::GetEnvironmentVariable("Path","Machine") + ";" + [System.Environment]::GetEnvironmentVariable("Path","User")
                
                # 验证安装
                try {
                    $pythonVersion = python --version 2>&1
                    Write-ColorLog "Python安装成功: $pythonVersion" "Green"
                } catch {
                    Write-ColorLog "Python安装失败，请手动安装" "Red" "ERROR"
                    exit 1
                }
                
                Remove-Item $pythonInstaller -Force -ErrorAction SilentlyContinue
            } else {
                Write-ColorLog "Python下载失败" "Red" "ERROR"
                exit 1
            }
        }
    }

    # 2. 创建安装目录
    Write-ColorLog "步骤 2: 创建安装目录..." "Yellow"
    if (-not (Test-Path $InstallDir)) {
        New-Item -ItemType Directory -Path $InstallDir -Force | Out-Null
        Write-ColorLog "创建目录: $InstallDir" "Green"
    } else {
        Write-ColorLog "目录已存在: $InstallDir" "Green"
    }

    # 创建子目录
    @("logs", "deploy", "backup") | ForEach-Object {
        $subDir = Join-Path $InstallDir $_
        if (-not (Test-Path $subDir)) {
            New-Item -ItemType Directory -Path $subDir -Force | Out-Null
        }
    }

    # 3. 复制应用文件
    Write-ColorLog "步骤 3: 复制应用文件..." "Yellow"
    $sourceDir = Split-Path -Parent $PSScriptRoot
    
    # 复制Python文件
    $pythonFiles = @("*.py", "*.yaml", "*.txt", "*.md")
    foreach ($pattern in $pythonFiles) {
        $files = Get-ChildItem -Path $sourceDir -Filter $pattern -File
        foreach ($file in $files) {
            Copy-Item $file.FullName -Destination $InstallDir -Force
            Write-ColorLog "复制文件: $($file.Name)" "Gray"
        }
    }

    # 复制utils目录
    $utilsSource = Join-Path $sourceDir "utils"
    $utilsTarget = Join-Path $InstallDir "utils"
    if (Test-Path $utilsSource) {
        if (Test-Path $utilsTarget) {
            Remove-Item $utilsTarget -Recurse -Force
        }
        Copy-Item $utilsSource -Destination $utilsTarget -Recurse -Force
        Write-ColorLog "复制utils目录" "Gray"
    }

    # 4. 安装Python依赖
    Write-ColorLog "步骤 4: 安装Python依赖..." "Yellow"
    Set-Location $InstallDir
    
    try {
        python -m pip install --upgrade pip
        pip install -r requirements.txt
        Write-ColorLog "Python依赖安装完成" "Green"
    } catch {
        Write-ColorLog "Python依赖安装失败: $($_.Exception.Message)" "Red" "ERROR"
        exit 1
    }

    # 5. 配置应用
    Write-ColorLog "步骤 5: 配置应用..." "Yellow"
    
    # 检查配置文件
    $configFile = Join-Path $InstallDir "config.yaml"
    if (-not (Test-Path $configFile)) {
        Write-ColorLog "配置文件不存在，请手动创建config.yaml" "Red" "ERROR"
        exit 1
    }

    # 创建.env文件
    $envFile = Join-Path $InstallDir ".env"
    $envContent = @"
# MT5 Server Environment Variables
CONFIG_FILE=config.yaml
FLASK_ENV=production
PYTHONPATH=$InstallDir
"@
    Set-Content -Path $envFile -Value $envContent -Encoding UTF8
    Write-ColorLog "创建.env文件" "Green"

    # 6. 安装MT5服务
    if (-not $SkipService) {
        Write-ColorLog "步骤 6: 安装MT5服务..." "Yellow"
        
        # 检查端口占用
        if (Test-Port 5000) {
            Write-ColorLog "端口5000已被占用，请检查其他服务" "Red" "ERROR"
            if (-not $Force) {
                exit 1
            }
        }

        $serviceScript = Join-Path $PSScriptRoot "install_service.bat"
        if (Test-Path $serviceScript) {
            Start-Process -FilePath $serviceScript -Wait -Verb RunAs
        } else {
            Write-ColorLog "服务安装脚本不存在: $serviceScript" "Red" "ERROR"
        }
    }

    # 7. 安装Nginx
    if (-not $SkipNginx) {
        Write-ColorLog "步骤 7: 安装Nginx..." "Yellow"
        
        # 检查端口占用
        if (Test-Port 80) {
            Write-ColorLog "端口80已被占用，请检查IIS或其他Web服务" "Red" "ERROR"
            if (-not $Force) {
                exit 1
            }
        }

        $nginxScript = Join-Path $PSScriptRoot "install_nginx.bat"
        if (Test-Path $nginxScript) {
            Start-Process -FilePath $nginxScript -Wait -Verb RunAs
        } else {
            Write-ColorLog "Nginx安装脚本不存在: $nginxScript" "Red" "ERROR"
        }
    }

    # 8. 验证部署
    Write-ColorLog "步骤 8: 验证部署..." "Yellow"
    
    Start-Sleep -Seconds 5
    
    # 测试MT5服务
    try {
        $response = Invoke-RestMethod -Uri "http://127.0.0.1:5000/health" -TimeoutSec 10
        Write-ColorLog "MT5服务测试成功" "Green"
        Write-ColorLog "响应: $($response | ConvertTo-Json -Compress)" "Gray"
    } catch {
        Write-ColorLog "MT5服务测试失败: $($_.Exception.Message)" "Red" "ERROR"
    }

    # 测试Nginx代理
    if (-not $SkipNginx) {
        try {
            $response = Invoke-WebRequest -Uri "http://127.0.0.1/health" -UseBasicParsing -TimeoutSec 10
            Write-ColorLog "Nginx代理测试成功，状态码: $($response.StatusCode)" "Green"
        } catch {
            Write-ColorLog "Nginx代理测试失败: $($_.Exception.Message)" "Red" "ERROR"
        }
    }

    # 9. 显示部署总结
    Write-Host ""
    Write-Host "========================================" -ForegroundColor Cyan
    Write-Host "部署完成总结" -ForegroundColor Cyan
    Write-Host "========================================" -ForegroundColor Cyan
    
    Write-ColorLog "安装目录: $InstallDir" "Cyan"
    Write-ColorLog "Nginx目录: $NginxDir" "Cyan"
    Write-ColorLog "配置文件: $configFile" "Cyan"
    
    Write-Host ""
    Write-Host "服务管理命令:" -ForegroundColor Yellow
    Write-Host "  启动MT5服务:  net start MT5Server" -ForegroundColor Gray
    Write-Host "  停止MT5服务:  net stop MT5Server" -ForegroundColor Gray
    Write-Host "  启动Nginx:    net start nginx" -ForegroundColor Gray
    Write-Host "  停止Nginx:    net stop nginx" -ForegroundColor Gray
    
    Write-Host ""
    Write-Host "测试URL:" -ForegroundColor Yellow
    Write-Host "  健康检查:     http://localhost/health" -ForegroundColor Gray
    Write-Host "  API接口:      http://localhost/api/" -ForegroundColor Gray
    Write-Host "  Webhook:      http://localhost/webhook" -ForegroundColor Gray
    
    Write-Host ""
    Write-Host "日志文件:" -ForegroundColor Yellow
    Write-Host "  应用日志:     $InstallDir\mt5_server.log" -ForegroundColor Gray
    Write-Host "  服务日志:     $InstallDir\logs\service_output.log" -ForegroundColor Gray
    Write-Host "  Nginx日志:    $NginxDir\logs\access.log" -ForegroundColor Gray
    
    Write-ColorLog "部署完成！" "Green"
}

# 执行主函数
try {
    Main
} catch {
    Write-ColorLog "部署过程中发生错误: $($_.Exception.Message)" "Red" "ERROR"
    Write-ColorLog "错误详情: $($_.ScriptStackTrace)" "Red" "ERROR"
    exit 1
}
