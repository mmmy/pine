# MT5 自动重连功能

## 🔧 功能概述

MT5交易服务器现在具备智能自动重连功能，当检测到MT5连接断开时，会自动尝试重新连接一次，确保交易操作的连续性和可靠性。

## 🎯 工作原理

### 自动重连机制
1. **连接检查**: 在执行任何MT5操作前，先检查连接状态
2. **错误捕获**: 捕获连接相关的异常和错误
3. **自动重连**: 检测到连接断开时，立即尝试重新连接
4. **操作重试**: 重连成功后，自动重试原始操作
5. **错误处理**: 重连失败时，抛出明确的错误信息

### 触发条件
自动重连会在以下情况下触发：
- MT5连接状态为断开
- 收到"not connected"相关错误
- 收到"connection"相关错误
- 抛出ConnectionError异常

## 📝 覆盖范围

### MT5Connector方法
以下方法已添加自动重连装饰器：
- `get_account_info()` - 获取账户信息
- `get_symbol_info()` - 获取交易品种信息
- `get_positions()` - 获取持仓信息
- `get_orders()` - 获取订单信息
- `get_server_time()` - 获取服务器时间
- `check_symbol_availability()` - 检查品种可用性

### TradingManager方法
以下交易方法已添加自动重连装饰器：
- `_execute_market_order()` - 执行市价单
- `_close_position()` - 平仓操作
- `_close_all_positions()` - 全平操作
- `_modify_position()` - 修改持仓

## 🚀 使用示例

### 正常使用
```python
# 无需任何特殊代码，自动重连在后台工作
account_info = mt5_connector.get_account_info()
positions = mt5_connector.get_positions()
```

### 日志输出示例
```
2025-07-25 13:19:18 - WARNING - MT5 connection lost during get_account_info, attempting to reconnect...
2025-07-25 13:19:18 - INFO - MT5 reconnection successful, retrying get_account_info
```

## 🧪 测试功能

### 自动测试脚本
运行自动重连测试：
```bash
python test_auto_reconnect.py
```

### VSCode调试配置
- **调试配置**: "测试自动重连"
- **任务配置**: "测试自动重连"

### 测试步骤
1. 建立MT5连接
2. 执行正常操作
3. 模拟连接断开
4. 测试自动重连
5. 验证操作恢复

## ⚡ 性能特点

### 优势
- **透明性**: 对用户代码完全透明
- **快速恢复**: 连接断开后立即尝试重连
- **操作连续性**: 重连后自动重试原始操作
- **错误处理**: 提供清晰的错误信息

### 限制
- **重试次数**: 每次操作只重试一次
- **重连时间**: 重连过程可能需要几秒钟
- **操作幂等性**: 确保重试操作的安全性

## 🔍 错误处理

### 成功重连
```json
{
  "success": true,
  "data": "操作结果"
}
```

### 重连失败
```json
{
  "success": false,
  "error": "MT5 reconnection failed during operation_name: original_error"
}
```

## 📊 监控和日志

### 日志级别
- **INFO**: 重连成功
- **WARNING**: 检测到连接断开，开始重连
- **ERROR**: 重连失败

### 监控指标
- 重连触发次数
- 重连成功率
- 操作恢复时间

## 🛠️ 配置选项

当前版本使用默认配置，未来可能添加：
- 重连超时时间
- 最大重试次数
- 重连间隔时间

## 🎉 总结

自动重连功能大大提高了MT5交易服务器的稳定性和可靠性，确保在网络波动或MT5客户端重启时，交易操作能够自动恢复，无需人工干预。
