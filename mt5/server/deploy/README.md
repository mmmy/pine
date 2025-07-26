# MT5 Trading Server - 部署文件说明

本目录包含了在腾讯云Windows服务器上部署MT5 Trading Server的所有必要文件和脚本。

## 文件列表

### 🚀 自动化部署脚本
- **`deploy.ps1`** - 主要的自动化部署脚本，一键完成整个部署过程
- **`install_service.bat`** - MT5服务安装脚本
- **`install_nginx.bat`** - Nginx安装和配置脚本
- **`check_deployment.ps1`** - 部署状态检查脚本

### ⚙️ 配置文件
- **`nginx.conf`** - 优化的Nginx配置文件
- **`production_config.yaml`** - 生产环境配置模板

### 📚 文档
- **`README.md`** - 本文件，部署文件说明
- **`../腾讯云部署文档.md`** - 详细的部署文档

## 快速开始

### 方法一：自动化部署（推荐）

1. **以管理员身份运行PowerShell**
```powershell
# 右键点击PowerShell图标，选择"以管理员身份运行"
```

2. **设置执行策略**
```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

3. **运行自动化部署**
```powershell
cd C:\path\to\mt5\server\deploy
.\deploy.ps1
```

### 方法二：分步部署

1. **安装MT5服务**
```batch
# 以管理员身份运行命令提示符
cd C:\path\to\mt5\server\deploy
install_service.bat
```

2. **安装Nginx**
```batch
install_nginx.bat
```

3. **检查部署状态**
```powershell
.\check_deployment.ps1
```

## 部署选项

### deploy.ps1 参数说明

```powershell
# 基本用法
.\deploy.ps1

# 自定义安装目录
.\deploy.ps1 -InstallDir "D:\mt5-server" -NginxDir "D:\nginx"

# 跳过某些组件
.\deploy.ps1 -SkipPython    # 跳过Python安装
.\deploy.ps1 -SkipNginx     # 跳过Nginx安装
.\deploy.ps1 -SkipService   # 跳过服务安装

# 强制覆盖现有安装
.\deploy.ps1 -Force

# 组合使用
.\deploy.ps1 -InstallDir "D:\mt5-server" -SkipPython -Force
```

### check_deployment.ps1 参数说明

```powershell
# 基本检查
.\check_deployment.ps1

# 详细检查（包含日志内容）
.\check_deployment.ps1 -Detailed

# 自定义目录检查
.\check_deployment.ps1 -InstallDir "D:\mt5-server" -NginxDir "D:\nginx"
```

## 部署后配置

### 1. 修改配置文件

```powershell
# 复制生产配置模板
copy production_config.yaml ..\config.yaml

# 编辑配置文件
notepad ..\config.yaml
```

**重要配置项：**
- `server.security.api_key` - 修改为强密码
- `server.security.allowed_ips` - 添加允许访问的IP地址
- `logging.level` - 生产环境建议使用"INFO"

### 2. 配置防火墙

```powershell
# 允许HTTP流量
New-NetFirewallRule -DisplayName "Allow HTTP" -Direction Inbound -Protocol TCP -LocalPort 80 -Action Allow

# 允许HTTPS流量（如果使用SSL）
New-NetFirewallRule -DisplayName "Allow HTTPS" -Direction Inbound -Protocol TCP -LocalPort 443 -Action Allow
```

### 3. 腾讯云安全组配置

在腾讯云控制台配置安全组：
- **入站规则**: HTTP(80), HTTPS(443), RDP(3389)
- **出站规则**: 全部流量

## 服务管理

### 常用命令

```powershell
# 查看服务状态
Get-Service MT5Server, nginx

# 启动服务
net start MT5Server
net start nginx

# 停止服务
net stop MT5Server
net stop nginx

# 重启服务
Restart-Service MT5Server
Restart-Service nginx

# 重新加载Nginx配置
C:\nginx\nginx.exe -s reload
```

### 日志文件位置

- **应用日志**: `C:\mt5-server\mt5_server.log`
- **服务日志**: `C:\mt5-server\logs\service_output.log`
- **Nginx访问日志**: `C:\nginx\logs\access.log`
- **Nginx错误日志**: `C:\nginx\logs\error.log`

## 测试部署

### 健康检查

```powershell
# 测试MT5服务
Invoke-RestMethod -Uri "http://127.0.0.1:5000/health"

# 测试Nginx代理
Invoke-RestMethod -Uri "http://127.0.0.1/health"
```

### Webhook测试

```powershell
# 测试webhook端点
$headers = @{"X-API-Key" = "your_api_key_here"}
$body = @{
    action = "buy"
    symbol = "EURUSD"
    volume = 0.01
} | ConvertTo-Json

Invoke-RestMethod -Uri "http://127.0.0.1/webhook" -Method POST -Headers $headers -Body $body -ContentType "application/json"
```

## 故障排除

### 常见问题

1. **服务无法启动**
   - 检查Python路径和依赖
   - 查看服务日志文件
   - 确保MT5客户端已登录

2. **端口被占用**
   - 检查IIS是否占用80端口
   - 使用 `netstat -an | findstr ":80 :5000"` 查看端口占用

3. **权限问题**
   - 确保以管理员身份运行脚本
   - 检查文件夹权限设置

4. **配置文件错误**
   - 使用 `check_deployment.ps1` 检查配置
   - 验证YAML格式是否正确

### 调试步骤

1. **运行部署检查**
```powershell
.\check_deployment.ps1 -Detailed
```

2. **查看详细日志**
```powershell
# 查看最新的应用日志
Get-Content C:\mt5-server\mt5_server.log -Tail 20

# 查看服务日志
Get-Content C:\mt5-server\logs\service_output.log -Tail 20
```

3. **手动测试服务**
```powershell
# 进入安装目录
cd C:\mt5-server

# 手动运行服务
python start_server.py
```

## 安全建议

1. **强密码**: 使用强API密钥
2. **IP限制**: 配置IP白名单
3. **HTTPS**: 生产环境启用SSL
4. **防火墙**: 只开放必要端口
5. **更新**: 定期更新依赖包
6. **监控**: 定期检查日志文件

## 性能优化

1. **Nginx优化**: 调整worker_processes数量
2. **连接池**: 配置upstream keepalive
3. **缓存**: 启用适当的缓存策略
4. **压缩**: 启用gzip压缩
5. **日志轮转**: 配置日志文件轮转

## 备份和恢复

### 备份重要文件

```powershell
# 创建备份目录
$backupDir = "C:\mt5-server-backup-$(Get-Date -Format 'yyyyMMdd')"
New-Item -ItemType Directory -Path $backupDir

# 备份配置文件
Copy-Item "C:\mt5-server\config.yaml" $backupDir
Copy-Item "C:\nginx\conf\nginx.conf" $backupDir

# 备份日志文件
Copy-Item "C:\mt5-server\*.log" $backupDir
```

### 恢复配置

```powershell
# 恢复配置文件
Copy-Item "$backupDir\config.yaml" "C:\mt5-server\"
Copy-Item "$backupDir\nginx.conf" "C:\nginx\conf\"

# 重启服务
Restart-Service MT5Server, nginx
```

---

**支持**: 如果遇到问题，请查看详细的部署文档或检查日志文件获取更多信息。
