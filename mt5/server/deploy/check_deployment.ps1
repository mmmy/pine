# MT5 Trading Server - 部署检查脚本
# 检查部署状态和服务健康状况

param(
    [string]$InstallDir = "C:\mt5-server",
    [string]$NginxDir = "C:\nginx",
    [switch]$Detailed
)

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

# 检查服务状态
function Test-ServiceStatus {
    param([string]$ServiceName)
    try {
        $service = Get-Service -Name $ServiceName -ErrorAction Stop
        return @{
            Exists = $true
            Status = $service.Status
            StartType = $service.StartType
        }
    } catch {
        return @{
            Exists = $false
            Status = "Not Found"
            StartType = "N/A"
        }
    }
}

# 检查端口状态
function Test-Port {
    param([int]$Port, [string]$Description = "")
    try {
        $connection = New-Object System.Net.Sockets.TcpClient
        $connection.Connect("127.0.0.1", $Port)
        $connection.Close()
        return @{
            Open = $true
            Description = $Description
        }
    } catch {
        return @{
            Open = $false
            Description = $Description
        }
    }
}

# 检查HTTP端点
function Test-HttpEndpoint {
    param(
        [string]$Url,
        [string]$Description = "",
        [int]$TimeoutSec = 10
    )
    try {
        $response = Invoke-WebRequest -Uri $Url -UseBasicParsing -TimeoutSec $TimeoutSec
        return @{
            Success = $true
            StatusCode = $response.StatusCode
            Description = $Description
            ResponseTime = $null
        }
    } catch {
        return @{
            Success = $false
            StatusCode = $null
            Description = $Description
            Error = $_.Exception.Message
        }
    }
}

# 主检查函数
function Main {
    Write-Host "========================================" -ForegroundColor Cyan
    Write-Host "MT5 Trading Server - 部署状态检查" -ForegroundColor Cyan
    Write-Host "========================================" -ForegroundColor Cyan
    Write-Host ""

    $issues = @()
    $warnings = @()

    # 1. 检查安装目录
    Write-ColorLog "检查安装目录..." "Yellow"
    
    if (Test-Path $InstallDir) {
        Write-ColorLog "✓ 安装目录存在: $InstallDir" "Green"
        
        # 检查关键文件
        $requiredFiles = @("app.py", "config.yaml", "requirements.txt", "start_server.py")
        foreach ($file in $requiredFiles) {
            $filePath = Join-Path $InstallDir $file
            if (Test-Path $filePath) {
                Write-ColorLog "  ✓ $file" "Green"
            } else {
                Write-ColorLog "  ✗ $file 缺失" "Red"
                $issues += "$file 文件缺失"
            }
        }
    } else {
        Write-ColorLog "✗ 安装目录不存在: $InstallDir" "Red"
        $issues += "安装目录不存在"
    }

    # 2. 检查Python环境
    Write-ColorLog "检查Python环境..." "Yellow"
    
    try {
        $pythonVersion = python --version 2>&1
        Write-ColorLog "✓ Python已安装: $pythonVersion" "Green"
        
        # 检查关键包
        $requiredPackages = @("flask", "MetaTrader5", "pandas", "PyYAML")
        foreach ($package in $requiredPackages) {
            try {
                python -c "import $package" 2>$null
                Write-ColorLog "  ✓ $package" "Green"
            } catch {
                Write-ColorLog "  ✗ $package 未安装" "Red"
                $issues += "$package Python包未安装"
            }
        }
    } catch {
        Write-ColorLog "✗ Python未安装或不在PATH中" "Red"
        $issues += "Python未安装"
    }

    # 3. 检查MT5服务
    Write-ColorLog "检查MT5服务..." "Yellow"
    
    $mt5Service = Test-ServiceStatus "MT5Server"
    if ($mt5Service.Exists) {
        if ($mt5Service.Status -eq "Running") {
            Write-ColorLog "✓ MT5服务运行中" "Green"
        } else {
            Write-ColorLog "⚠ MT5服务已安装但未运行 (状态: $($mt5Service.Status))" "Yellow"
            $warnings += "MT5服务未运行"
        }
        Write-ColorLog "  启动类型: $($mt5Service.StartType)" "Gray"
    } else {
        Write-ColorLog "✗ MT5服务未安装" "Red"
        $issues += "MT5服务未安装"
    }

    # 4. 检查Nginx
    Write-ColorLog "检查Nginx..." "Yellow"
    
    if (Test-Path $NginxDir) {
        Write-ColorLog "✓ Nginx目录存在: $NginxDir" "Green"
        
        $nginxService = Test-ServiceStatus "nginx"
        if ($nginxService.Exists) {
            if ($nginxService.Status -eq "Running") {
                Write-ColorLog "✓ Nginx服务运行中" "Green"
            } else {
                Write-ColorLog "⚠ Nginx服务已安装但未运行 (状态: $($nginxService.Status))" "Yellow"
                $warnings += "Nginx服务未运行"
            }
        } else {
            Write-ColorLog "✗ Nginx服务未安装" "Red"
            $issues += "Nginx服务未安装"
        }
    } else {
        Write-ColorLog "✗ Nginx目录不存在: $NginxDir" "Red"
        $issues += "Nginx未安装"
    }

    # 5. 检查端口状态
    Write-ColorLog "检查端口状态..." "Yellow"
    
    $ports = @(
        @{Port = 5000; Description = "MT5服务端口"},
        @{Port = 80; Description = "HTTP端口"},
        @{Port = 443; Description = "HTTPS端口"}
    )
    
    foreach ($portInfo in $ports) {
        $portStatus = Test-Port $portInfo.Port $portInfo.Description
        if ($portStatus.Open) {
            Write-ColorLog "✓ 端口 $($portInfo.Port) 开放 ($($portInfo.Description))" "Green"
        } else {
            if ($portInfo.Port -eq 443) {
                Write-ColorLog "⚠ 端口 $($portInfo.Port) 关闭 ($($portInfo.Description)) - 可选" "Yellow"
            } else {
                Write-ColorLog "✗ 端口 $($portInfo.Port) 关闭 ($($portInfo.Description))" "Red"
                $issues += "端口 $($portInfo.Port) 不可访问"
            }
        }
    }

    # 6. 检查HTTP端点
    Write-ColorLog "检查HTTP端点..." "Yellow"
    
    $endpoints = @(
        @{Url = "http://127.0.0.1:5000/health"; Description = "MT5服务健康检查"},
        @{Url = "http://127.0.0.1/health"; Description = "Nginx代理健康检查"},
        @{Url = "http://127.0.0.1/nginx_status"; Description = "Nginx状态页面"}
    )
    
    foreach ($endpoint in $endpoints) {
        $result = Test-HttpEndpoint $endpoint.Url $endpoint.Description
        if ($result.Success) {
            Write-ColorLog "✓ $($endpoint.Description) (状态码: $($result.StatusCode))" "Green"
        } else {
            Write-ColorLog "✗ $($endpoint.Description) 失败: $($result.Error)" "Red"
            $issues += "$($endpoint.Description) 不可访问"
        }
    }

    # 7. 检查日志文件
    Write-ColorLog "检查日志文件..." "Yellow"
    
    $logFiles = @(
        @{Path = "$InstallDir\mt5_server.log"; Description = "应用日志"},
        @{Path = "$InstallDir\logs\service_output.log"; Description = "服务输出日志"},
        @{Path = "$NginxDir\logs\access.log"; Description = "Nginx访问日志"},
        @{Path = "$NginxDir\logs\error.log"; Description = "Nginx错误日志"}
    )
    
    foreach ($logFile in $logFiles) {
        if (Test-Path $logFile.Path) {
            $fileInfo = Get-Item $logFile.Path
            Write-ColorLog "✓ $($logFile.Description) (大小: $([math]::Round($fileInfo.Length/1KB, 2)) KB)" "Green"
            
            if ($Detailed) {
                # 显示最后几行日志
                try {
                    $lastLines = Get-Content $logFile.Path -Tail 3 -ErrorAction SilentlyContinue
                    if ($lastLines) {
                        Write-ColorLog "  最新日志:" "Gray"
                        foreach ($line in $lastLines) {
                            Write-ColorLog "    $line" "Gray"
                        }
                    }
                } catch {
                    Write-ColorLog "  无法读取日志内容" "Yellow"
                }
            }
        } else {
            Write-ColorLog "⚠ $($logFile.Description) 不存在" "Yellow"
            $warnings += "$($logFile.Description) 文件不存在"
        }
    }

    # 8. 检查配置文件
    Write-ColorLog "检查配置文件..." "Yellow"
    
    $configFile = Join-Path $InstallDir "config.yaml"
    if (Test-Path $configFile) {
        Write-ColorLog "✓ 配置文件存在" "Green"
        
        try {
            # 简单检查配置文件格式
            $config = Get-Content $configFile -Raw | ConvertFrom-Yaml -ErrorAction Stop
            Write-ColorLog "✓ 配置文件格式正确" "Green"
            
            # 检查关键配置项
            if ($config.server.security.api_key -and $config.server.security.api_key -ne "") {
                Write-ColorLog "✓ API密钥已配置" "Green"
            } else {
                Write-ColorLog "⚠ API密钥未配置" "Yellow"
                $warnings += "API密钥未配置"
            }
        } catch {
            Write-ColorLog "✗ 配置文件格式错误" "Red"
            $issues += "配置文件格式错误"
        }
    } else {
        Write-ColorLog "✗ 配置文件不存在" "Red"
        $issues += "配置文件不存在"
    }

    # 9. 显示总结
    Write-Host ""
    Write-Host "========================================" -ForegroundColor Cyan
    Write-Host "检查结果总结" -ForegroundColor Cyan
    Write-Host "========================================" -ForegroundColor Cyan
    
    if ($issues.Count -eq 0 -and $warnings.Count -eq 0) {
        Write-ColorLog "🎉 所有检查通过！部署状态良好。" "Green"
    } else {
        if ($issues.Count -gt 0) {
            Write-ColorLog "发现 $($issues.Count) 个严重问题:" "Red"
            foreach ($issue in $issues) {
                Write-ColorLog "  ✗ $issue" "Red"
            }
        }
        
        if ($warnings.Count -gt 0) {
            Write-ColorLog "发现 $($warnings.Count) 个警告:" "Yellow"
            foreach ($warning in $warnings) {
                Write-ColorLog "  ⚠ $warning" "Yellow"
            }
        }
    }
    
    Write-Host ""
    Write-Host "建议操作:" -ForegroundColor Yellow
    if ($issues.Count -gt 0) {
        Write-Host "1. 解决上述严重问题" -ForegroundColor Gray
        Write-Host "2. 重新运行部署脚本" -ForegroundColor Gray
    }
    if ($warnings.Count -gt 0) {
        Write-Host "3. 检查警告项目" -ForegroundColor Gray
    }
    Write-Host "4. 查看日志文件获取详细信息" -ForegroundColor Gray
    Write-Host "5. 运行 Get-Service MT5Server, nginx 检查服务状态" -ForegroundColor Gray
    
    Write-Host ""
}

# 执行主函数
try {
    Main
} catch {
    Write-ColorLog "检查过程中发生错误: $($_.Exception.Message)" "Red" "ERROR"
    exit 1
}
