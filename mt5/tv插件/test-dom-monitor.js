// DOM警报监听测试脚本
// 在TradingView页面控制台中运行此脚本来测试DOM监听功能

console.log('🧪 DOM警报监听测试开始');

// 创建测试警报元素
function createTestAlert(message, type = 'info') {
  console.log(`🔧 创建测试警报: ${message}`);
  
  const alertDiv = document.createElement('div');
  alertDiv.className = `test-alert alert notification ${type}`;
  alertDiv.style.cssText = `
    position: fixed;
    top: 20px;
    right: 20px;
    background: #f44336;
    color: white;
    padding: 15px;
    border-radius: 5px;
    z-index: 10000;
    max-width: 300px;
    box-shadow: 0 2px 10px rgba(0,0,0,0.3);
  `;
  
  alertDiv.textContent = message;
  document.body.appendChild(alertDiv);
  
  // 3秒后自动移除
  setTimeout(() => {
    if (alertDiv.parentNode) {
      alertDiv.parentNode.removeChild(alertDiv);
    }
  }, 3000);
  
  return alertDiv;
}

// 测试不同类型的警报
function testDifferentAlerts() {
  console.log('🎯 测试不同类型的警报...');
  
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
      createTestAlert(message, index % 2 === 0 ? 'buy' : 'sell');
    }, index * 2000);
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

// 主测试函数
function runDOMMonitorTest() {
  console.log('🚀 开始DOM监听测试...\n');
  
  console.log('📋 测试计划:');
  console.log('1. 创建不同类型的测试警报');
  console.log('2. 测试动态内容变化');
  console.log('3. 测试现有元素扫描');
  console.log('4. 创建TradingView样式警报');
  console.log('5. 测试关键词检测');
  
  // 按顺序执行测试
  setTimeout(testDifferentAlerts, 1000);
  setTimeout(testDynamicContent, 8000);
  setTimeout(testExistingElementScan, 12000);
  setTimeout(createTradingViewStyleAlert, 16000);
  setTimeout(testKeywordDetection, 20000);
  
  console.log('\n✅ 测试已开始，请观察控制台输出和页面上的测试警报');
  console.log('💡 如果DOM监听工作正常，你应该看到警报检测的日志');
}

// 暴露测试函数
window.domMonitorTest = {
  run: runDOMMonitorTest,
  createAlert: createTestAlert,
  testDynamic: testDynamicContent,
  testExisting: testExistingElementScan,
  testTVStyle: createTradingViewStyleAlert,
  testKeywords: testKeywordDetection
};

// 自动运行测试
runDOMMonitorTest();

console.log('\n🔧 测试函数已暴露到 window.domMonitorTest');
console.log('可以单独运行: window.domMonitorTest.createAlert("Test Alert")');
