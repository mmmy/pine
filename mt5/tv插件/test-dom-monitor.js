// WebSocket警报监听测试脚本
// 在TradingView页面控制台中运行此脚本来测试WebSocket监听功能

console.log('🧪 WebSocket警报监听测试开始');

// 创建测试弹窗警报元素
function createTestPopupAlert(message, type = 'info') {
  console.log(`🔧 创建测试弹窗警报: ${message}`);

  const alertDiv = document.createElement('div');
  alertDiv.className = `test-popup-alert tv-dialog popup-dialog alert-dialog ${type}`;
  alertDiv.setAttribute('role', 'dialog');
  alertDiv.setAttribute('data-name', 'alert-popup');
  alertDiv.style.cssText = `
    position: fixed;
    top: 50%;
    left: 50%;
    transform: translate(-50%, -50%);
    background: #fff;
    color: #333;
    padding: 20px;
    border-radius: 8px;
    z-index: 10000;
    max-width: 400px;
    min-width: 300px;
    box-shadow: 0 4px 20px rgba(0,0,0,0.3);
    border: 1px solid #ddd;
  `;

  alertDiv.innerHTML = `
    <div class="alert-header" style="margin-bottom: 15px; font-weight: bold; color: #f44336;">
      🚨 TradingView Alert
    </div>
    <div class="alert-content" style="margin-bottom: 15px;">
      ${message}
    </div>
    <div class="alert-footer">
      <button onclick="this.parentElement.parentElement.remove()"
              style="background: #007bff; color: white; border: none; padding: 8px 16px; border-radius: 4px; cursor: pointer;">
        Close
      </button>
    </div>
  `;

  document.body.appendChild(alertDiv);

  // 5秒后自动移除
  setTimeout(() => {
    if (alertDiv.parentNode) {
      alertDiv.parentNode.removeChild(alertDiv);
    }
  }, 5000);

  return alertDiv;
}

// 测试不同类型的弹窗警报
function testDifferentPopupAlerts() {
  console.log('🎯 测试不同类型的弹窗警报...');

  const testAlerts = [
    'Alert: BTCUSD price reached 50000',
    '警报: ETHUSD 突破 3000 价格',
    'BUY signal triggered for XAUUSD at 2650.50',
    '做空 EURUSD 在 1.0850 价格',
    'Price alert: AAPL crossed above 150.00',
    'Notification: Stop loss triggered at 45000'
  ];

  testAlerts.forEach((message, index) => {
    setTimeout(() => {
      createTestPopupAlert(message, index % 2 === 0 ? 'buy' : 'sell');
    }, index * 3000); // 增加间隔时间，便于观察
  });
}

// 测试动态内容变化
function testDynamicContent() {
  console.log('🔄 测试动态内容变化...');
  
  const container = document.createElement('div');
  container.className = 'dynamic-alert-container';
  container.style.cssText = `
    position: fixed;
    bottom: 20px;
    left: 20px;
    background: #2196F3;
    color: white;
    padding: 10px;
    border-radius: 5px;
    z-index: 10000;
  `;
  
  document.body.appendChild(container);
  
  let counter = 0;
  const interval = setInterval(() => {
    counter++;
    container.textContent = `Dynamic Alert #${counter}: BTCUSD price update ${50000 + counter * 10}`;
    
    if (counter >= 5) {
      clearInterval(interval);
      setTimeout(() => {
        if (container.parentNode) {
          container.parentNode.removeChild(container);
        }
      }, 2000);
    }
  }, 1500);
}

// 测试现有元素扫描
function testExistingElementScan() {
  console.log('🔍 测试现有元素扫描...');
  
  // 创建一些"现有"的警报元素
  const existingAlerts = [
    'Existing alert: GBPUSD trend change detected',
    'Pre-existing notification: Market volatility high'
  ];
  
  existingAlerts.forEach((message, index) => {
    const alertDiv = document.createElement('div');
    alertDiv.className = 'existing-alert tv-alert';
    alertDiv.textContent = message;
    alertDiv.style.cssText = `
      position: fixed;
      top: ${100 + index * 60}px;
      left: 20px;
      background: #FF9800;
      color: white;
      padding: 10px;
      border-radius: 3px;
      z-index: 10000;
    `;
    
    document.body.appendChild(alertDiv);
    
    // 5秒后移除
    setTimeout(() => {
      if (alertDiv.parentNode) {
        alertDiv.parentNode.removeChild(alertDiv);
      }
    }, 5000);
  });
}

// 模拟TradingView警报样式
function createTradingViewStyleAlert() {
  console.log('📊 创建TradingView样式警报...');
  
  const tvAlert = document.createElement('div');
  tvAlert.className = 'tv-dialog tv-alert-dialog';
  tvAlert.setAttribute('data-name', 'alert-dialog');
  tvAlert.style.cssText = `
    position: fixed;
    top: 50%;
    left: 50%;
    transform: translate(-50%, -50%);
    background: white;
    border: 1px solid #ccc;
    border-radius: 8px;
    padding: 20px;
    z-index: 10000;
    box-shadow: 0 4px 20px rgba(0,0,0,0.3);
    min-width: 300px;
  `;
  
  tvAlert.innerHTML = `
    <div class="tv-alert-header">
      <h3>Price Alert</h3>
    </div>
    <div class="tv-alert-content">
      <p>BTCUSD has crossed above 52,000.00</p>
      <p>Time: ${new Date().toLocaleString()}</p>
      <p>Action: BUY signal triggered</p>
    </div>
    <div class="tv-alert-footer">
      <button onclick="this.parentElement.parentElement.remove()">Close</button>
    </div>
  `;
  
  document.body.appendChild(tvAlert);
  
  // 10秒后自动关闭
  setTimeout(() => {
    if (tvAlert.parentNode) {
      tvAlert.parentNode.removeChild(tvAlert);
    }
  }, 10000);
}

// 测试警报关键词检测
function testKeywordDetection() {
  console.log('🔤 测试关键词检测...');
  
  const keywordTests = [
    { text: 'This contains alert keyword', expected: true },
    { text: '这里有警报关键词', expected: true },
    { text: 'Buy signal for EURUSD', expected: true },
    { text: 'Sell order executed', expected: true },
    { text: 'Price target reached', expected: true },
    { text: 'Regular text without keywords', expected: false },
    { text: 'Just some random content', expected: false }
  ];
  
  keywordTests.forEach((test, index) => {
    setTimeout(() => {
      const testDiv = document.createElement('div');
      testDiv.className = 'keyword-test';
      testDiv.textContent = test.text;
      testDiv.style.cssText = `
        position: fixed;
        top: ${200 + index * 30}px;
        right: 20px;
        background: ${test.expected ? '#4CAF50' : '#9E9E9E'};
        color: white;
        padding: 5px 10px;
        border-radius: 3px;
        z-index: 10000;
        font-size: 12px;
      `;
      
      document.body.appendChild(testDiv);
      
      setTimeout(() => {
        if (testDiv.parentNode) {
          testDiv.parentNode.removeChild(testDiv);
        }
      }, 2000);
    }, index * 500);
  });
}

// 测试WebSocket警报功能
function testWebSocketAlert() {
  console.log('🧪 测试WebSocket警报功能...');

  if (window.tvAlertForwarder) {
    console.log('✅ 发现调试接口，开始测试...');

    // 获取当前状态
    const status = window.tvAlertForwarder.getStatus();
    console.log('📊 当前状态:', status);

    // 测试警报
    console.log('🚨 发送测试警报...');
    window.tvAlertForwarder.testAlert('测试警报: XAUUSD 做空 仓位=0.05');

    setTimeout(() => {
      const newStatus = window.tvAlertForwarder.getStatus();
      console.log('📊 测试后状态:', newStatus);
    }, 2000);

  } else {
    console.log('❌ 未找到调试接口，请确保插件已正确加载');
  }
}

// 检查WebSocket连接状态
function checkWebSocketConnections() {
  console.log('🔍 检查WebSocket连接状态...');

  if (window.tvAlertForwarder) {
    const connections = window.tvAlertForwarder.getConnections();
    const allConnections = window.tvAlertForwarder.getAllConnections();

    console.log('📡 TradingView WebSocket连接状态:', connections);
    console.log(`📊 总WebSocket连接数: ${allConnections.length}`);

    if (connections.total === 0) {
      console.log('⚠️ 没有检测到TradingView WebSocket连接');

      if (allConnections.length > 0) {
        console.log('🔍 但检测到其他WebSocket连接:');
        window.tvAlertForwarder.showAllConnections();
        console.log('💡 可能需要更新URL匹配模式');
      } else {
        console.log('💡 没有检测到任何WebSocket连接，可能需要:');
        console.log('   1. 刷新页面');
        console.log('   2. 等待TradingView完全加载');
        console.log('   3. 重新安装拦截器: window.tvAlertForwarder.reinstallInterceptor()');
      }
    } else {
      console.log(`✅ 检测到 ${connections.total} 个TradingView WebSocket连接`);
      connections.connections.forEach((conn, index) => {
        console.log(`📡 连接 ${index + 1}:`, conn.url);
      });
    }
  } else {
    console.log('❌ 调试接口不可用，插件可能未正确加载');
  }
}

// 主测试函数
function runWebSocketMonitorTest() {
  console.log('🚀 开始WebSocket监听测试...\n');

  console.log('📋 测试计划:');
  console.log('1. 检查WebSocket连接状态');
  console.log('2. 测试WebSocket警报功能');
  console.log('3. 创建模拟弹窗（兼容性测试）');
  console.log('4. 检查插件状态');

  // 按顺序执行测试
  setTimeout(checkWebSocketConnections, 1000);
  setTimeout(testWebSocketAlert, 3000);
  setTimeout(createTradingViewStyleAlert, 6000);
  setTimeout(() => {
    if (window.tvAlertForwarder) {
      console.log('📊 最终状态:', window.tvAlertForwarder.getStatus());
    }
  }, 10000);

  console.log('\n✅ 测试已开始，请观察控制台输出');
  console.log('💡 如果WebSocket监听工作正常，你应该看到警报检测的日志');
  console.log('🎯 注意：此版本通过拦截WebSocket消息获取警报数据');
}

// 测试显示/隐藏状态变化
function testVisibilityToggle() {
  console.log('👁️ 测试显示/隐藏状态变化...');

  // 创建一个隐藏的弹窗
  const hiddenAlert = document.createElement('div');
  hiddenAlert.className = 'tv-dialog alert-dialog hidden-popup';
  hiddenAlert.setAttribute('role', 'dialog');
  hiddenAlert.setAttribute('data-name', 'alert-popup');
  hiddenAlert.style.cssText = `
    position: fixed;
    top: 30%;
    left: 30%;
    background: #ff9800;
    color: white;
    padding: 20px;
    border-radius: 8px;
    z-index: 10000;
    display: none;
  `;
  hiddenAlert.textContent = 'Hidden Alert: GBPUSD breakout detected';

  document.body.appendChild(hiddenAlert);

  // 2秒后显示
  setTimeout(() => {
    console.log('🔄 显示隐藏的弹窗...');
    hiddenAlert.style.display = 'block';
  }, 2000);

  // 5秒后移除
  setTimeout(() => {
    if (hiddenAlert.parentNode) {
      hiddenAlert.parentNode.removeChild(hiddenAlert);
    }
  }, 7000);
}

// 暴露测试函数
window.webSocketMonitorTest = {
  run: runWebSocketMonitorTest,
  checkConnections: checkWebSocketConnections,
  testAlert: testWebSocketAlert,
  createPopup: createTestPopupAlert,
  testTVStyle: createTradingViewStyleAlert,

  // 便捷方法
  status: () => window.tvAlertForwarder ? window.tvAlertForwarder.getStatus() : null,
  connections: () => window.tvAlertForwarder ? window.tvAlertForwarder.getConnections() : null
};

// 自动运行测试
runWebSocketMonitorTest();

console.log('\n🔧 测试函数已暴露到 window.webSocketMonitorTest');
console.log('可以单独运行:');
console.log('- window.webSocketMonitorTest.checkConnections()');
console.log('- window.webSocketMonitorTest.testAlert()');
console.log('- window.webSocketMonitorTest.status()');
console.log('- window.tvAlertForwarder.testAlert("自定义消息")');
