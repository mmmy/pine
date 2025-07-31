# TradingView Webhook 配置示例

本文档提供了在 TradingView 中配置 webhook 警报的详细示例，用于与 MT5 交易服务器集成。

## 基础配置

### 1. 服务器地址设置

在 TradingView 警报设置中，Webhook URL 应该设置为：

```
http://你的服务器IP:5000/webhook
```

例如：

- 本地测试: `http://127.0.0.1:5000/webhook`
- 远程服务器: `http://192.168.1.100:5000/webhook`
- 域名: `http://your-domain.com:5000/webhook`

### 2. 消息格式选择

支持三种消息格式：

#### 格式 1：纯中文字符串（推荐）

直接在消息框中输入中文命令：

```
开多 XAUUSD 仓位=0.1 备注=TradingView信号
```

#### 格式 2：JSON 包装的中文格式

```json
{
  "message": "开多 XAUUSD 仓位=0.1 备注=TradingView信号"
}
```

#### 格式 3：传统 JSON 格式

```json
{
  "action": "buy",
  "symbol": "EURUSD",
  "volume": 0.1,
  "comment": "TradingView Alert"
}
```

## 中文格式详细说明

### 基础语法

```
操作方向 交易品种 参数1=值1 参数2=值2 开关参数
```

### 操作方向

- **开多、买入、做多** → 买入开仓
- **开空、卖出、做空** → 卖出开仓
- **平多** → 平多头仓位
- **平空** → 平空头仓位
- **平仓** → 平指定仓位
- **全平** → 平所有仓位

### 参数说明

- **仓位=0.1** 或 **数量=0.1** 或 **手数=0.1** → 交易量
- **止损=3350.0** 或 **止损价=3350.0** → 止损价格
- **止盈=3380.0** 或 **止盈价=3380.0** → 止盈价格
- **备注=说明文字** 或 **注释=说明文字** → 交易备注
- **订单号=123456** 或 **票号=123456** → 订单票号（平仓/修改时使用）

## 动态变量示例

### 中文格式动态变量

```
开多 {{ticker}} 仓位=0.1 备注=价格{{close}}的信号
```

```
{{strategy.order.action == "buy" ? "开多" : "开空"}} {{ticker}} 仓位={{strategy.position_size}} 备注=策略信号
```

### JSON 格式动态变量

```json
{
  "action": "buy",
  "symbol": "{{ticker}}",
  "volume": 0.1,
  "price": {{close}},
  "time": "{{time}}",
  "comment": "Alert at {{time}}"
}
```

### 策略相关变量

```json
{
  "action": "{{strategy.order.action}}",
  "symbol": "{{ticker}}",
  "volume": {{strategy.position_size}},
  "contracts": {{strategy.order.contracts}},
  "comment": "Strategy: {{strategy.order.comment}}"
}
```

## 不同交易场景的配置

### 1. 简单买卖信号

#### 中文格式买入信号

```
开多 {{ticker}} 仓位=0.1 备注=买入信号价格{{close}}
```

#### 中文格式卖出信号

```
开空 {{ticker}} 仓位=0.1 备注=卖出信号价格{{close}}
```

#### JSON 格式买入信号

```json
{
  "action": "buy",
  "symbol": "{{ticker}}",
  "volume": 0.1,
  "comment": "Buy signal at {{close}}"
}
```

#### JSON 格式卖出信号

```json
{
  "action": "sell",
  "symbol": "{{ticker}}",
  "volume": 0.1,
  "comment": "Sell signal at {{close}}"
}
```

### 2. 带止损止盈的交易

#### 中文格式

```
开多 {{ticker}} 仓位=0.1 止损={{close * 0.99}} 止盈={{close * 1.02}} 备注=带止损止盈
```

#### JSON 格式

```json
{
  "action": "buy",
  "symbol": "{{ticker}}",
  "volume": 0.1,
  "sl": {{close}} * 0.99,
  "tp": {{close}} * 1.02,
  "comment": "Buy with SL/TP"
}
```

### 3. 平仓信号

#### 中文格式平仓

```
平仓 {{ticker}} 备注=平仓信号
```

#### 中文格式全平

```
全平 {{ticker}} 备注=紧急平仓
```

#### JSON 格式平仓特定品种

```json
{
  "action": "close",
  "symbol": "{{ticker}}",
  "comment": "Close signal"
}
```

#### JSON 格式平仓所有持仓

```json
{
  "action": "close_all",
  "comment": "Close all positions"
}
```

### 5. 时间区间控制

#### 中文格式时间区间控制

```
开启时间区间 开多 XAUUSD 仓位=0.1
开启时间区间 开空 EURUSD 仓位=0.05
开启时间区间 平多 XAUUSD
开启时间区间 全平 XAUUSD
```

#### JSON 格式时间区间控制

```json
{
  "action": "buy",
  "symbol": "XAUUSD",
  "volume": 0.1,
  "enable_time_check": true
}
```

**说明**：

- 当包含"开启时间区间"或 `"enable_time_check": true` 时，系统会检查当前时间是否在配置的时间段内
- 只有当前时间在 `custom_intervals` 配置的任一时间段内时，交易才会被执行
- 如果不在时间段内，会返回错误信息

### 4. 修改持仓

```json
{
  "action": "modify",
  "symbol": "{{ticker}}",
  "sl": {{close}} * 0.995,
  "tp": {{close}} * 1.015,
  "comment": "Modify SL/TP"
}
```

````

#### 自定义时间段说明
系统配置了3个自定义时间段，使用"开启时间区间"命令会同时启用所有时间段：
- **自定义时段1**: 欧洲交易时段 (08:00-16:00 Europe/London)
- **自定义时段2**: 美洲交易时段 (14:00-22:00 America/New_York)
- **自定义时段3**: 亚洲交易时段 (01:00-09:00 GMT+8)

当前时间在任意一个时间段内时，交易被允许。

#### 时区格式支持
支持以下时区格式：
- **标准时区名称**: `Asia/Shanghai`, `Europe/London`, `America/New_York`
- **GMT格式**: `GMT+8`, `GMT-5`, `UTC+9`, `UTC-3`

## 高级配置示例

### 1. 条件交易

根据不同条件执行不同的交易：

```json
{
  "action": "{{strategy.order.action}}",
  "symbol": "{{ticker}}",
  "volume": {{strategy.position_size}},
  "sl": {{strategy.order.action}} == "buy" ? {{close}} * 0.99 : {{close}} * 1.01,
  "tp": {{strategy.order.action}} == "buy" ? {{close}} * 1.02 : {{close}} * 0.98,
  "comment": "Conditional trade"
}
````

### 2. 多时间框架信号

```json
{
  "action": "buy",
  "symbol": "{{ticker}}",
  "volume": 0.1,
  "timeframe": "{{interval}}",
  "price": {{close}},
  "comment": "{{interval}} signal"
}
```

### 3. 风险管理

```json
{
  "action": "buy",
  "symbol": "{{ticker}}",
  "volume": 0.05,
  "sl": {{low}} * 0.998,
  "tp": {{high}} * 1.002,
  "magic": 12345,
  "comment": "Risk managed trade"
}
```

## 策略集成示例

### 1. 移动平均线交叉策略

```json
{
  "action": "{{strategy.order.action}}",
  "symbol": "{{ticker}}",
  "volume": 0.1,
  "entry_price": {{close}},
  "ma_fast": {{plot_0}},
  "ma_slow": {{plot_1}},
  "comment": "MA Cross {{strategy.order.action}}"
}
```

### 2. RSI 超买超卖策略

```json
{
  "action": "{{strategy.order.action}}",
  "symbol": "{{ticker}}",
  "volume": 0.1,
  "rsi": {{plot_0}},
  "sl": {{strategy.order.action}} == "buy" ? {{close}} * 0.99 : {{close}} * 1.01,
  "comment": "RSI {{plot_0}} signal"
}
```

### 3. 突破策略

```json
{
  "action": "buy",
  "symbol": "{{ticker}}",
  "volume": 0.15,
  "breakout_level": {{high}},
  "sl": {{low}} * 0.999,
  "tp": {{high}} * 1.005,
  "comment": "Breakout above {{high}}"
}
```

## 错误处理和调试

### 1. 测试消息格式

在实际使用前，可以先发送测试消息：

```json
{
  "action": "test",
  "symbol": "EURUSD",
  "volume": 0.01,
  "comment": "Test message"
}
```

### 2. 包含调试信息

```json
{
  "action": "buy",
  "symbol": "{{ticker}}",
  "volume": 0.1,
  "debug": {
    "time": "{{time}}",
    "timeframe": "{{interval}}",
    "close": {{close}},
    "volume_traded": {{volume}}
  },
  "comment": "Debug trade"
}
```

## 安全考虑

### 1. 限制交易量

```json
{
  "action": "buy",
  "symbol": "{{ticker}}",
  "volume": 0.01,
  "max_volume": 0.1,
  "comment": "Limited volume trade"
}
```

### 2. 添加验证字段

```json
{
  "action": "buy",
  "symbol": "{{ticker}}",
  "volume": 0.1,
  "source": "tradingview",
  "strategy": "my_strategy_v1",
  "timestamp": "{{time}}",
  "comment": "Verified trade"
}
```

## 常见问题解决

### 1. JSON 格式错误

确保 JSON 格式正确，常见错误：

- 缺少引号
- 多余的逗号
- 括号不匹配

正确格式：

```json
{
  "action": "buy",
  "symbol": "EURUSD",
  "volume": 0.1
}
```

### 2. 动态变量问题

确保动态变量格式正确：

- 字符串变量需要引号: `"{{ticker}}"`
- 数值变量不需要引号: `{{close}}`

### 3. 特殊字符处理

避免在 comment 中使用特殊字符：

```json
{
  "comment": "Simple comment without special chars"
}
```

## 测试建议

1. **先在模拟账户测试**: 确保所有配置正确
2. **使用小交易量**: 初始测试使用最小交易量
3. **监控日志**: 查看服务器日志确认消息接收
4. **逐步增加复杂度**: 从简单配置开始，逐步添加功能

## 示例策略代码

以下是一个简单的 Pine Script 策略示例，展示如何发送 webhook：

```pinescript
//@version=5
strategy("Webhook Example", overlay=true)

// 简单移动平均线
ma20 = ta.sma(close, 20)
ma50 = ta.sma(close, 50)

// 交易条件
longCondition = ta.crossover(ma20, ma50)
shortCondition = ta.crossunder(ma20, ma50)

// 执行交易
if longCondition
    strategy.entry("Long", strategy.long, alert_message='{"action":"buy","symbol":"{{ticker}}","volume":0.1,"comment":"MA Cross Long"}')

if shortCondition
    strategy.entry("Short", strategy.short, alert_message='{"action":"sell","symbol":"{{ticker}}","volume":0.1,"comment":"MA Cross Short"}')

// 绘制移动平均线
plot(ma20, color=color.blue)
plot(ma50, color=color.red)
```

记住在策略中设置警报时选择"Webhook URL"选项，并输入你的服务器地址。
