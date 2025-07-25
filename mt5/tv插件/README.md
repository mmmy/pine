# TradingView Alert Forwarder

一个Chrome浏览器插件，用于监听TradingView的警报并自动转发到指定的Webhook URL。

## 功能特点

- 🎯 通过DOM监听实时检测TradingView警报通知
- 📡 自动将警报信息转发到可配置的Webhook URL
- 🔧 支持自定义请求头和认证令牌
- 📊 统计功能：记录警报总数和最后警报时间
- 🔄 一键启用/禁用功能
- 🧪 连接测试功能
- ⚡ 轻量级设计，稳定可靠的DOM监听技术

## 安装教程

### 方法一：开发者模式安装（推荐）

1. **下载插件文件**
   - 将所有插件文件保存到一个文件夹中（如：`TradingView-Alert-Forwarder`）

2. **打开Chrome扩展管理页面**
   - 在Chrome浏览器中输入：`chrome://extensions/`
   - 或者：菜单 → 更多工具 → 扩展程序

3. **启用开发者模式**
   - 在扩展程序页面右上角，打开"开发者模式"开关

4. **加载插件**
   - 点击"加载已解压的扩展程序"
   - 选择包含插件文件的文件夹
   - 点击"选择文件夹"

5. **确认安装**
   - 插件会出现在扩展程序列表中
   - 可以看到"TradingView Alert Forwarder"插件

## 配置教程

### 第一步：基本配置

1. **打开插件设置**
   - 点击浏览器工具栏中的插件图标
   - 点击"打开配置"按钮

2. **配置Webhook URL**
   - 在"Webhook URL"字段中输入你的服务器地址
   - 默认值：`http://localhost:5000/webhook`
   - 示例：`https://your-server.com/api/alerts`

3. **配置认证（可选）**
   - 如果你的服务器需要认证，在"认证令牌"字段输入Bearer Token
   - 示例：`your-api-token-here`

4. **自定义请求头（可选）**
   - 支持JSON格式的自定义HTTP头
   - 示例：
   ```json
   {
     "X-API-Key": "your-api-key",
     "Content-Type": "application/json"
   }
   ```

5. **保存配置**
   - 点击"保存配置"按钮
   - 看到"配置已保存"提示即成功

### 第二步：测试连接

1. **运行连接测试**
   - 在配置页面点击"测试连接"按钮
   - 或在插件弹窗中点击"测试连接"

2. **检查测试结果**
   - 成功：显示"连接测试成功！HTTP 200"
   - 失败：显示具体错误信息，检查URL和网络

### 第三步：启用插件

1. **启用警报转发**
   - 点击插件图标打开弹窗
   - 确保"启用警报转发"开关处于开启状态（绿色）
   - 状态显示应为"插件已启用"

## 使用教程

### 1. 正常使用流程

1. **打开TradingView**
   - 访问 `https://tradingview.com` 或 `https://www.tradingview.com`
   - 登录你的TradingView账户

2. **设置警报**
   - 在TradingView中正常设置你的价格警报或指标警报
   - 插件会通过DOM监听自动检测警报通知

3. **查看转发状态**
   - 当警报触发并显示通知时，插件会自动捕获并转发到你的Webhook URL
   - Console中会显示"警报检测到"的日志

### 2. 监控和管理

1. **查看统计信息**
   - 点击插件图标查看：
     - 总警报数：已转发的警报总数
     - 最后警报：最近一次警报的时间

2. **启用/禁用功能**
   - 使用弹窗中的开关随时启用或禁用插件
   - 禁用时插件不会监听或转发任何警报

3. **重置配置**
   - 在配置页面点击"重置"按钮
   - 将清除所有配置和统计数据

## 数据格式

插件发送到你的Webhook URL的数据格式：

```json
{
  "message": "警报消息内容",
  "alert": {
    "message": "警报消息内容",
    "symbol": "BTCUSDT",
    "price": "50000",
    "type": "BUY",
    "html": "原始HTML内容",
    "className": "CSS类名",
    "timestamp": "2023-01-01T12:00:00.000Z"
  },
  "timestamp": "2023-01-01T12:00:00.000Z",
  "source": "https://tradingview.com/chart/...",
  "extension": "TradingView Alert Forwarder v1.0"
}
```

### 字段说明

- `message`: 警报的主要消息内容（顶级字段，便于直接访问）
- `alert.message`: 完整的警报消息文本
- `alert.symbol`: 交易对/品种（如BTCUSDT）
- `alert.price`: 触发价格
- `alert.type`: 警报类型（BUY/SELL/ALERT等）
- `timestamp`: 警报触发时间
- `source`: 触发警报的TradingView页面URL

## 服务器端示例

### Python Flask 示例

```python
from flask import Flask, request, jsonify
import json

app = Flask(__name__)

@app.route('/webhook', methods=['POST'])
def handle_alert():
    data = request.get_json()
    
    # 获取警报消息
    message = data.get('message')
    alert_info = data.get('alert', {})
    symbol = alert_info.get('symbol')
    price = alert_info.get('price')
    
    print(f"收到TradingView警报: {message}")
    print(f"交易对: {symbol}, 价格: {price}")
    
    # 在这里添加你的处理逻辑
    # 例如：发送邮件、执行交易、记录数据库等
    
    return jsonify({"status": "success"})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
```

### Node.js Express 示例

```javascript
const express = require('express');
const app = express();

app.use(express.json());

app.post('/webhook', (req, res) => {
    const { message, alert, timestamp, source } = req.body;
    
    console.log('收到TradingView警报:', message);
    console.log('详细信息:', alert);
    
    // 在这里添加你的处理逻辑
    
    res.json({ status: 'success' });
});

app.listen(5000, () => {
    console.log('Webhook服务器运行在端口5000');
});
```

## 故障排除

### 🚨 插件不工作的解决方案

#### 第一步：基础检查

1. **确认环境**
   - ✅ 必须在 `https://tradingview.com` 或 `https://www.tradingview.com` 页面使用
   - ✅ 确保插件已正确安装并启用
   - ✅ 检查插件图标是否显示在浏览器工具栏中

2. **检查插件状态**
   - 点击插件图标，确保显示"插件已启用"（绿色状态）
   - 如果显示"插件已禁用"，点击开关启用
   - 如果显示"未配置URL"，先完成配置

3. **确认警报通知设置**
   - 在TradingView中确保警报通知已启用
   - 检查浏览器是否允许TradingView显示通知

#### 第二步：使用调试工具

1. **打开测试页面**
   - 在任意页面打开 `test.html`（包含在插件文件中）
   - 或者直接在TradingView页面的控制台中运行调试代码

2. **加载DOM监听测试脚本**
   ```javascript
   // 在TradingView页面的控制台中运行
   const script = document.createElement('script');
   script.src = chrome.runtime.getURL('test-dom-monitor.js');
   document.head.appendChild(script);
   ```

3. **测试DOM监听功能**
   ```javascript
   // 运行DOM监听测试
   window.domMonitorTest.run();

   // 创建测试警报
   window.domMonitorTest.createAlert("Test Alert: BTCUSD 50000");
   ```

#### 第三步：检查WebSocket连接

1. **打开开发者工具**
   - 按 F12 打开开发者工具
   - 切换到 "Console" 标签
   - 刷新TradingView页面

2. **查找关键日志**
   - 寻找 "WebSocket monitoring started" 消息
   - 查找 "New WebSocket connection detected" 消息
   - 确认是否有 "TradingView WebSocket detected" 消息

3. **如果没有WebSocket连接**
   - TradingView可能更改了WebSocket URL模式
   - 使用调试脚本查看所有WebSocket连接
   - 检查是否有其他脚本干扰了WebSocket拦截

#### 第四步：验证警报触发

1. **在TradingView中设置测试警报**
   - 创建一个简单的价格警报
   - 设置一个容易触发的条件
   - 确保警报已激活

2. **监控控制台输出**
   - 当警报触发时，应该看到相关日志
   - 查找 "Alert detected" 或 "WebSocket message received" 消息

3. **检查消息格式**
   - 如果看到WebSocket消息但没有警报检测，可能是消息格式变化
   - 使用调试脚本分析消息结构

### 常见问题解决

1. **插件无法检测到警报**
   ```
   原因：WebSocket URL模式可能已更改
   解决：使用调试脚本监控所有WebSocket连接，找到新的URL模式
   ```

2. **连接测试失败**
   ```
   原因：Webhook URL配置错误或服务器不可访问
   解决：检查URL格式，确保服务器运行，测试网络连接
   ```

3. **警报发送失败**
   ```
   原因：认证问题或请求头配置错误
   解决：检查认证令牌，验证自定义请求头格式
   ```

4. **WebSocket拦截失败**
   ```
   原因：其他脚本干扰或页面加载时机问题
   解决：尝试刷新页面，或使用调试脚本手动拦截
   ```

### 高级调试

1. **手动测试WebSocket拦截**
   ```javascript
   // 在控制台中运行
   const originalWS = window.WebSocket;
   window.WebSocket = function(url, protocols) {
     console.log('WebSocket intercepted:', url);
     return new originalWS(url, protocols);
   };
   ```

2. **监控所有网络请求**
   - 打开开发者工具的 "Network" 标签
   - 筛选 "WS" (WebSocket) 连接
   - 查看实际的WebSocket连接URL

3. **检查TradingView页面结构**
   ```javascript
   // 查找可能的警报元素
   document.querySelectorAll('[class*="alert"]');
   document.querySelectorAll('[class*="notification"]');
   ```

### 获取帮助

如果以上步骤都无法解决问题：

1. **收集调试信息**
   - 浏览器版本和操作系统
   - TradingView页面URL
   - 控制台错误信息
   - WebSocket连接报告

2. **提供详细描述**
   - 具体的错误现象
   - 重现步骤
   - 预期行为vs实际行为

## 支持与反馈

如有问题或建议，请：
1. 检查本教程的故障排除部分
2. 查看浏览器Console日志
3. 确认服务器端配置正确

## 版本信息

- 版本：v1.0
- 支持的浏览器：Chrome (Manifest V3)
- 支持的网站：TradingView.com

## 更新日志

### v1.0 (初始版本)
- 基本警报监听和转发功能
- 可配置的Webhook URL
- 自定义请求头支持
- 启用/禁用开关
- 连接测试功能
- 统计信息显示