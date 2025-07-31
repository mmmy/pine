# MT5 Trading HTTP Server

一个基于 Python Flask 的 MT5 交易 HTTP 服务器，可以接收 TradingView webhook 警报并执行 MT5 交易操作。

## 功能特点

- 🔗 **MT5 集成**: 直接连接 MetaTrader 5 终端执行交易
- 🌐 **HTTP API**: RESTful API 接口，支持 webhook 和手动调用
- 🔒 **安全认证**: API 密钥认证和 IP 白名单功能
- 📊 **实时监控**: 账户信息、持仓查询、服务状态监控
- 📝 **完整日志**: 详细的交易日志和错误记录

- 🛡️ **风险管理**: 交易量限制、滑点控制等安全措施

## 支持的交易操作

- **开仓**: 市价买入/卖出
- **平仓**: 指定持仓或全部平仓
- **修改**: 修改止损和止盈
- **查询**: 持仓、账户信息、服务状态

## 快速开始

### 1. 环境要求

- Python 3.7+
- MetaTrader 5 终端
- Windows 操作系统（MT5 Python API 限制）

### 2. 安装依赖

```bash
# 克隆或下载项目文件
cd mt5/server

# 安装Python依赖
pip install -r requirements.txt
```

### 3. 配置设置

复制配置模板并修改：

```bash
# 复制环境变量模板
cp .env.example .env

# 编辑配置文件
# 修改 config.yaml 中的MT5账户信息
```

在 `config.yaml` 中配置你的 MT5 账户信息（支持多个账户）：

```yaml
mt5:
  accounts:
    # 账户ID: 账户配置
    demo1:
      login: 你的MT5账户号1
      password: "你的MT5密码1"
      server: "你的经纪商服务器1"
      name: "主要账户"
      description: "主要交易账户"

    demo2:
      login: 你的MT5账户号2
      password: "你的MT5密码2"
      server: "你的经纪商服务器2"
      name: "备用账户"
      description: "备用交易账户"

  # 默认账户ID (如果webhook中没有指定账户)
  default_account: "demo1"
```

### 4. 启动服务

```bash
# 方式1: 使用启动脚本
python start_server.py

# 方式2: 直接运行
python app.py

# 方式3: 指定配置文件
python start_server.py --config custom_config.yaml --port 8080
```

### 5. 测试连接

```bash
# 测试健康检查
curl http://127.0.0.1:5000/health

# 或使用PowerShell
Invoke-RestMethod -Uri "http://127.0.0.1:5000/health"
```

## API 接口文档

### 基础端点

#### 健康检查

```http
GET /health
```

响应示例：

```json
{
  "status": "healthy",
  "mt5_connected": true,
  "timestamp": "2025-01-15T10:30:00"
}
```

#### 服务状态

```http
GET /status
```

需要 API 密钥认证。

响应示例：

```json
{
  "server_status": "running",
  "mt5_connected": true,
  "account_info": {
    "login": 67424067,
    "balance": 99594.28,
    "equity": 99623.28,
    "currency": "USD",
    "name": "Yqtest3 Yq3",
    "server": "ForexTimeFXTM-Demo02",
    "trade_allowed": true
  },

  "timestamp": "2025-01-26T20:55:00"
}
```

**字段说明：**

- `server_status`: 服务器运行状态
- `mt5_connected`: MT5 连接状态
- `account_info`: MT5 账户详细信息

#### 查询持仓

```http
GET /positions?account_id=demo1
```

需要 API 密钥认证。可选参数：

- `account_id`: 指定账户 ID，不指定则使用默认账户

响应示例：

```json
{
  "success": true,
  "account_id": "demo1",
  "positions": [
    {
      "ticket": 123456,
      "symbol": "EURUSD",
      "type_name": "BUY",
      "volume": 0.1,
      "price_open": 1.085,
      "price_current": 1.086,
      "profit": 10.0,
      "sl": 1.08,
      "tp": 1.09
    }
  ],
  "count": 1
}
```

### 交易端点

#### Webhook 交易

```http
POST /webhook
```

支持三种请求格式：

**格式 1：传统 JSON 格式**

```http
Content-Type: application/json

{
  "action": "buy",
  "symbol": "EURUSD",
  "volume": 0.1,
  "sl": 1.0800,
  "tp": 1.0900,
  "comment": "TradingView Signal"
}
```

**格式 2：JSON 包装的中文格式**

```http
Content-Type: application/json

{
  "message": "开多 XAUUSD 仓位=0.1 止损=3350.0 止盈=3380.0 备注=TradingView信号"
}
```

**格式 3：纯中文字符串格式（推荐）**

```http
Content-Type: text/plain

开多 XAUUSD 仓位=0.1 止损=3350.0 止盈=3380.0 账户=demo1 备注=TradingView信号
```

### 中文格式说明：

- **第一个词**：操作方向

  - 开多、买入、做多 → 买入
  - 开空、卖出、做空 → 卖出
  - 平多 → 平多头仓位
  - 平空 → 平空头仓位
  - 平仓 → 平指定仓位
  - 全平 → 平所有仓位
  - 修改 → 修改仓位

- **第二个词**：交易品种（如 XAUUSD、EURUSD 等）

- **后续参数**：中文=值的格式

  - 仓位=0.1 或 数量=0.1 或 手数=0.1
  - 止损=3350.0 或 止损价=3350.0
  - 止盈=3380.0 或 止盈价=3380.0
  - 备注=交易说明 或 注释=交易说明
  - 订单号=123456 或 票号=123456
  - 滑点=5 或 最大滑点=5

- **开关参数**：只写中文名称，不带等号
  - 开启时间区间 允许滑点、强制平仓、部分平仓、立即执行等

#### 手动交易

```http
POST /trade
Content-Type: application/json
```

与 webhook 端点相同的请求格式。

### 交易参数说明

| 参数    | 类型   | 必需 | 说明                                          |
| ------- | ------ | ---- | --------------------------------------------- |
| action  | string | 是   | 交易动作: buy, sell, close, close_all, modify |
| symbol  | string | 是   | 交易品种，如 EURUSD                           |
| volume  | number | 否   | 交易量，默认使用配置中的默认值                |
| sl      | number | 否   | 止损价格                                      |
| tp      | number | 否   | 止盈价格                                      |
| ticket  | number | 否   | 持仓票号（平仓和修改时使用）                  |
| comment | string | 否   | 交易备注                                      |
| magic   | number | 否   | 魔术数字                                      |

### 交易动作详解

#### 开仓 (buy/sell)

```json
{
  "action": "buy",
  "symbol": "EURUSD",
  "volume": 0.1,
  "sl": 1.08,
  "tp": 1.09
}
```

#### 平仓 (close)

```json
{
  "action": "close",
  "symbol": "EURUSD",
  "ticket": 123456
}
```

#### 全部平仓 (close_all)

```json
{
  "action": "close_all",
  "symbol": "EURUSD"
}
```

#### 修改持仓 (modify)

```json
{
  "action": "modify",
  "symbol": "EURUSD",
  "ticket": 123456,
  "sl": 1.075,
  "tp": 1.095
}
```

## TradingView Webhook 配置

### 1. 在 TradingView 中设置警报

1. 打开你的策略或指标
2. 点击"创建警报"
3. 在"通知"选项卡中，启用"Webhook URL"
4. 输入你的服务器地址：`http://你的服务器IP:5000/webhook`

### 2. Webhook 消息格式

在 TradingView 警报的"消息"字段中使用 JSON 格式：

```json
{
  "action": "{{strategy.order.action}}",
  "symbol": "{{ticker}}",
  "volume": 0.1,
  "comment": "TradingView Alert"
}
```

### 3. 动态参数示例

使用 TradingView 的动态变量：

```json
{
  "action": "buy",
  "symbol": "{{ticker}}",
  "volume": {{strategy.position_size}},
  "price": {{close}},
  "comment": "Signal at {{time}}"
}
```

## 安全配置

### API 密钥认证

在 `config.yaml` 中设置 API 密钥：

```yaml
server:
  security:
    api_key: "your_secret_api_key_here"
```

在请求头中包含 API 密钥：

```http
X-API-Key: your_secret_api_key_here
```

### IP 白名单

限制允许访问的 IP 地址：

```yaml
server:
  security:
    allowed_ips:
      - "192.168.1.100"
      - "10.0.0.0/8"
      - "172.16.0.0/12"
```

## 配置文件详解

### MT5 配置

```yaml
mt5:
  terminal_path: "" # MT5终端路径（可选）
  account:
    login: 你的账户号
    password: "你的密码"
    server: "经纪商服务器"
  timeout:
    connect: 30 # 连接超时（秒）
    trade: 10 # 交易超时（秒）
```

### 交易配置

```yaml
trading:
  default_volume: 0.1 # 默认交易量
  max_volume: 10.0 # 最大交易量
  min_volume: 0.01 # 最小交易量
  max_slippage: 3 # 最大滑点
  magic_number: 12345 # 魔术数字
  allowed_symbols: [] # 允许的交易品种（空=全部）

```

### 日志配置

```yaml
logging:
  level: "INFO"
  file: "mt5_server.log"
  max_size: 10485760 # 10MB
  backup_count: 5
  console: true
```

## 故障排除

### 常见问题

1. **MT5 连接失败**

   - 确保 MT5 终端正在运行
   - 检查账户信息是否正确
   - 确认经纪商允许 API 交易

2. **API 认证失败**

   - 检查 API 密钥是否正确
   - 确认请求头格式正确

3. **交易失败**
   - 检查交易品种是否可用
   - 确认交易量在允许范围内
   - 查看日志文件获取详细错误信息

### 日志查看

```bash
# 查看日志文件
type mt5_server.log

# 查看错误日志
findstr "ERROR" mt5_server.log
```

## 开发和调试

### 开发模式

```bash
# 启用调试模式
python start_server.py --debug --log-level DEBUG
```

### 手动测试

可以使用 curl 或 PowerShell 测试 API：

```bash
# 测试纯文本webhook
curl -X POST http://127.0.0.1:5000/webhook -H "Content-Type: text/plain" -d "开多 XAUUSD 仓位=0.01 备注=测试"

# 测试时间区间控制
curl -X POST http://127.0.0.1:5000/webhook -H "Content-Type: text/plain" -d "开启时间区间"
```

```powershell
# PowerShell测试
$body = "开多 XAUUSD 仓位=0.01 备注=测试"
Invoke-RestMethod -Uri "http://127.0.0.1:5000/webhook" -Method POST -Body $body -ContentType "text/plain; charset=utf-8"

# 时间区间控制测试
$body = "开启时间区间"
Invoke-RestMethod -Uri "http://127.0.0.1:5000/webhook" -Method POST -Body $body -ContentType "text/plain; charset=utf-8"
```

## 许可证

本项目采用 MIT 许可证。

## 免责声明

本软件仅供学习和研究使用。使用本软件进行实际交易的风险由用户自行承担。作者不对任何交易损失负责。

在使用真实账户之前，请务必在模拟账户上充分测试。
