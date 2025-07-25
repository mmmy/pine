// WebSocket注入器 - 在页面最早期运行
// 这个脚本会在所有其他脚本之前运行，确保能拦截到WebSocket连接

(function() {
  'use strict';
  
  console.log('🚀 WebSocket注入器启动 - 时间:', new Date().toISOString());
  console.log('🚀 页面状态:', document.readyState);
  console.log('🚀 URL:', window.location.href);
  
  // 立即保存原始WebSocket
  const OriginalWebSocket = window.WebSocket;
  const connections = [];
  let messageCount = 0;
  
  // 立即替换WebSocket构造函数
  window.WebSocket = function(url, protocols) {
    console.log('🔍 WebSocket连接拦截:', url);
    
    const ws = new OriginalWebSocket(url, protocols);
    const connectionInfo = {
      url: url,
      created: new Date().toISOString(),
      ws: ws,
      messageCount: 0
    };
    
    connections.push(connectionInfo);
    
    // 拦截onmessage
    const originalOnMessage = ws.onmessage;
    ws.onmessage = function(event) {
      messageCount++;
      connectionInfo.messageCount++;
      
      console.log(`📨 消息 #${messageCount} [${url}]:`, event.data.substring(0, 150) + '...');
      
      // 检查是否是警报消息
      try {
        const data = JSON.parse(event.data);
        
        // 检查TradingView警报格式
        if (data.text && data.text.channel === 'alert' && data.text.content) {
          console.log('🚨🚨🚨 TradingView警报检测到!');
          console.log('🚨 完整数据:', data);
          
          try {
            const alertContent = JSON.parse(data.text.content);
            console.log('🚨 警报内容:', alertContent);
            
            if (alertContent.m === 'event' && alertContent.p) {
              const alertData = alertContent.p;
              console.log('🚨 警报详情:');
              console.log('  - ID:', alertData.id);
              console.log('  - 描述:', alertData.desc);
              console.log('  - 交易对:', alertData.sym);
              console.log('  - 触发时间:', new Date(alertData.fire_time * 1000).toISOString());
              
              // 通过自定义事件发送到content script
              const alertEvent = new CustomEvent('tradingview-alert', {
                detail: {
                  type: 'TRADINGVIEW_ALERT',
                  data: {
                    message: alertData.desc,
                    symbol: alertData.sym,
                    alertId: alertData.id,
                    aid: alertData.aid,
                    fireTime: alertData.fire_time,
                    barTime: alertData.bar_time,
                    resolution: alertData.res,
                    soundEnabled: alertData.snd,
                    popupEnabled: alertData.popup,
                    timestamp: new Date().toISOString()
                  },
                  timestamp: new Date().toISOString(),
                  url: window.location.href,
                  source: 'websocket-injector'
                }
              });

              document.dispatchEvent(alertEvent);
              console.log('✅ 警报事件已发送到content script');
            }
          } catch (e) {
            console.log('🚨 警报内容解析失败:', e);
          }
        }
        
        // 检查其他可能的警报格式
        if (data.channel === 'alert' || 
            (typeof data === 'object' && JSON.stringify(data).includes('alert'))) {
          console.log('🔔 其他格式的警报消息:', data);
        }
        
      } catch (e) {
        // 不是JSON，检查文本内容
        if (typeof event.data === 'string') {
          const lowerData = event.data.toLowerCase();
          if (lowerData.includes('alert') || lowerData.includes('警报') ||
              lowerData.includes('buy') || lowerData.includes('sell') ||
              lowerData.includes('做多') || lowerData.includes('做空')) {
            console.log('🔔 文本警报消息:', event.data);
          }
        }
      }
      
      // 调用原始处理器
      if (originalOnMessage) {
        originalOnMessage.call(this, event);
      }
    };
    
    // 监听连接状态
    ws.addEventListener('open', () => {
      console.log('🔗 WebSocket连接已打开:', url);
    });
    
    ws.addEventListener('close', () => {
      console.log('🔌 WebSocket连接已关闭:', url);
    });
    
    ws.addEventListener('error', (error) => {
      console.log('❌ WebSocket连接错误:', url, error);
    });
    
    return ws;
  };
  
  // 保持原型链
  window.WebSocket.prototype = OriginalWebSocket.prototype;
  Object.setPrototypeOf(window.WebSocket, OriginalWebSocket);
  
  // 暴露调试接口
  window.wsInjectorDebug = {
    getConnections: () => connections,
    getStats: () => ({
      totalConnections: connections.length,
      totalMessages: messageCount,
      connections: connections.map(c => ({
        url: c.url,
        created: c.created,
        messageCount: c.messageCount,
        readyState: c.ws.readyState
      }))
    }),
    showStats: () => {
      const stats = window.wsInjectorDebug.getStats();
      console.log('=== WebSocket注入器统计 ===');
      console.log(`总连接数: ${stats.totalConnections}`);
      console.log(`总消息数: ${stats.totalMessages}`);
      stats.connections.forEach((conn, index) => {
        console.log(`${index + 1}. ${conn.url}`);
        console.log(`   创建时间: ${conn.created}`);
        console.log(`   消息数: ${conn.messageCount}`);
        console.log(`   状态: ${conn.readyState}`);
      });
      return stats;
    }
  };
  
  console.log('✅ WebSocket注入器已安装');
  console.log('🔧 使用 window.wsInjectorDebug.showStats() 查看统计');
  
})();
