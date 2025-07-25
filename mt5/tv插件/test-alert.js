// 测试脚本 - 在TradingView页面的Console中运行
// 用于手动触发一个测试警报，验证整个处理流程

console.log('🧪 Alert Test Script - Starting manual alert test');

// 模拟WebSocket警报数据
const testAlertData = {
  id: 37320364580,
  aid: 2687035109,
  fire_time: Math.floor(Date.now() / 1000),
  bar_time: Math.floor(Date.now() / 1000) - 60,
  sym: "OANDA:XAUUSD",
  res: "1",
  desc: "做空 XAUUSD 仓位=0.05",
  snd_file: "alert/fired",
  snd: false,
  popup: true,
  cross_int: false,
  name: null,
  snd_duration: 0
};

// 调用插件的处理函数（如果可用）
if (window.tradingViewAlertForwarder && window.tradingViewAlertForwarder.processWebSocketAlert) {
  console.log('🎯 Found plugin functions, triggering test alert...');
  window.tradingViewAlertForwarder.processWebSocketAlert(testAlertData);
} else {
  console.log('🔧 Plugin functions not found, simulating manual trigger...');
  
  // 手动触发消息发送
  const formattedAlert = {
    message: testAlertData.desc || 'Test alert',
    html: '',
    className: 'test-websocket-alert',
    timestamp: new Date(testAlertData.fire_time * 1000).toISOString(),
    symbol: testAlertData.sym ? testAlertData.sym.split(':')[1] : 'XAUUSD',
    price: '2650.00',
    type: 'SELL',
    source: 'manual-test',
    alertId: testAlertData.id,
    aid: testAlertData.aid,
    fireTime: testAlertData.fire_time,
    barTime: testAlertData.bar_time,
    resolution: testAlertData.res
  };
  
  console.log('📦 Formatted test alert:', formattedAlert);
  
  // 发送到background script
  chrome.runtime.sendMessage({
    type: 'TRADINGVIEW_ALERT',
    data: formattedAlert,
    timestamp: formattedAlert.timestamp,
    url: window.location.href,
    source: 'manual-test'
  }, (response) => {
    console.log('📬 Background script response:', response);
    
    if (chrome.runtime.lastError) {
      console.error('❌ Chrome runtime error:', chrome.runtime.lastError);
    }
    
    if (response) {
      console.log('✅ Test alert sent successfully!');
    } else {
      console.log('❌ No response from background script');
    }
  });
}

console.log('🧪 Test script complete - Check background script logs for webhook request details');