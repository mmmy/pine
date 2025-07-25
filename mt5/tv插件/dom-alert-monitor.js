// TradingView Alert Forwarder - WebSocket监听版本
// 通过拦截WebSocket消息来获取实时警报数据

(() => {
  console.log('🚀 TradingView Alert Forwarder: WebSocket监听模式启动');
  console.log('🚀 当前时间:', new Date().toISOString());
  console.log('🚀 当前URL:', window.location.href);

  let alertCount = 0;
  let isEnabled = true;
  let originalWebSocket = null;
  let processedAlerts = new Set(); // 记录已处理的警报，避免重复
  let monitoredConnections = new Map(); // 记录监听的WebSocket连接

  // 检查插件是否启用
  function checkEnabled(callback) {
    if (typeof chrome !== 'undefined' && chrome.storage) {
      chrome.storage.sync.get({enabled: true}, (config) => {
        isEnabled = config.enabled;
        callback(isEnabled);
      });
    } else {
      callback(true); // 如果无法访问存储，默认启用
    }
  }

  // WebSocket URL模式匹配 - 更全面的模式
  const WEBSOCKET_PATTERNS = [
    /wss:\/\/pushstream\.tradingview\.com\/message-pipe-ws\/private_/,
    /wss:\/\/.*\.tradingview\.com.*\/message-pipe-ws/,
    /wss:\/\/.*tradingview.*\/ws/,
    /wss:\/\/.*tradingview\.com/,
    /ws:\/\/.*tradingview\.com/,
    /wss:\/\/.*\.tradingview\./,
    /ws:\/\/.*\.tradingview\./
  ];

  let allWebSocketConnections = []; // 记录所有WebSocket连接用于调试

  // 检查是否是TradingView的WebSocket连接
  function isTradingViewWebSocket(url) {
    const isMatch = WEBSOCKET_PATTERNS.some(pattern => pattern.test(url));
    console.log(`🔍 WebSocket URL检查: ${url} -> ${isMatch ? '✅匹配' : '❌不匹配'}`);
    return isMatch;
  }

  // 解析WebSocket警报消息
  function parseAlertMessage(data) {
    try {
      const message = JSON.parse(data);

      // 检查是否是警报频道的消息
      if (message.text && message.text.channel === 'alert' && message.text.content) {
        const content = JSON.parse(message.text.content);

        // 检查是否是事件消息且包含警报数据
        if (content.m === 'event' && content.p) {
          const alertData = content.p;

          // 生成唯一标识符避免重复处理
          const alertId = `${alertData.id}_${alertData.fire_time}`;

          if (processedAlerts.has(alertId)) {
            console.log('⚠️ 警报已处理，跳过:', alertId);
            return null;
          }

          processedAlerts.add(alertId);

          // 清理旧的记录，避免内存泄漏
          if (processedAlerts.size > 100) {
            const firstItem = processedAlerts.values().next().value;
            processedAlerts.delete(firstItem);
          }

          return {
            message: alertData.desc || 'TradingView Alert',
            symbol: alertData.sym || 'UNKNOWN',
            price: null, // WebSocket消息中没有直接的价格信息
            type: determineAlertType(alertData.desc || ''),
            alertId: alertData.id,
            aid: alertData.aid,
            fireTime: alertData.fire_time,
            barTime: alertData.bar_time,
            resolution: alertData.res,
            soundEnabled: alertData.snd,
            popupEnabled: alertData.popup,
            timestamp: new Date().toISOString()
          };
        }
      }
    } catch (error) {
      console.warn('解析WebSocket消息失败:', error, data);
    }

    return null;
  }

  // 判断警报类型
  function determineAlertType(description) {
    if (!description) return 'ALERT';

    const lowerDesc = description.toLowerCase();
    if (lowerDesc.includes('买入') || lowerDesc.includes('做多') || lowerDesc.includes('buy') || lowerDesc.includes('long')) {
      return 'BUY';
    }
    if (lowerDesc.includes('卖出') || lowerDesc.includes('做空') || lowerDesc.includes('sell') || lowerDesc.includes('short')) {
      return 'SELL';
    }
    return 'ALERT';
  }

  // WebSocket消息拦截器
  function interceptWebSocket() {
    if (originalWebSocket) {
      console.log('⚠️ WebSocket已被拦截，跳过重复拦截');
      return;
    }

    originalWebSocket = window.WebSocket;

    window.WebSocket = function(url, protocols) {
      console.log('🔍 WebSocket连接检测:', url);

      // 记录所有WebSocket连接用于调试
      allWebSocketConnections.push({
        url: url,
        timestamp: new Date().toISOString(),
        isTradingView: isTradingViewWebSocket(url)
      });

      const ws = new originalWebSocket(url, protocols);

      // 检查是否是TradingView的WebSocket
      if (isTradingViewWebSocket(url)) {
        console.log('🎯 TradingView WebSocket连接已拦截:', url);

        const connectionId = Date.now() + Math.random();
        monitoredConnections.set(connectionId, {
          url: url,
          ws: ws,
          startTime: new Date().toISOString()
        });

        // 拦截消息接收
        const originalOnMessage = ws.onmessage;
        ws.onmessage = function(event) {
          console.log('📨 WebSocket消息接收:', event.data.substring(0, 200) + '...');

          if (isEnabled) {
            handleWebSocketMessage(event.data, url);
          }

          // 调用原始的消息处理器
          if (originalOnMessage) {
            originalOnMessage.call(this, event);
          }
        };

        // 监听连接打开
        const originalOnOpen = ws.onopen;
        ws.onopen = function(event) {
          console.log('🔗 TradingView WebSocket连接已打开:', url);

          if (originalOnOpen) {
            originalOnOpen.call(this, event);
          }
        };

        // 监听连接关闭
        const originalOnClose = ws.onclose;
        ws.onclose = function(event) {
          console.log('🔌 TradingView WebSocket连接关闭:', url);
          monitoredConnections.delete(connectionId);

          if (originalOnClose) {
            originalOnClose.call(this, event);
          }
        };

        // 监听连接错误
        const originalOnError = ws.onerror;
        ws.onerror = function(event) {
          console.error('❌ TradingView WebSocket连接错误:', url, event);

          if (originalOnError) {
            originalOnError.call(this, event);
          }
        };
      } else {
        console.log('⏭️ 非TradingView WebSocket，跳过监听:', url);
      }

      return ws;
    };

    // 保持原始WebSocket的属性
    Object.setPrototypeOf(window.WebSocket, originalWebSocket);
    window.WebSocket.prototype = originalWebSocket.prototype;

    console.log('✅ WebSocket拦截器已安装');
  }

  // 处理WebSocket消息
  function handleWebSocketMessage(data, url) {
    try {
      const alertData = parseAlertMessage(data);

      if (alertData) {
        alertCount++;
        console.log(`🚨 WebSocket警报 #${alertCount} 检测到:`, alertData.message);
        console.log('📊 警报详情:', alertData);

        // 发送到background script
        if (typeof chrome !== 'undefined' && chrome.runtime) {
          chrome.runtime.sendMessage({
            type: 'TRADINGVIEW_ALERT',
            data: alertData,
            timestamp: alertData.timestamp,
            url: window.location.href,
            source: 'websocket'
          }, (response) => {
            if (response && response.success) {
              console.log('✅ WebSocket警报已发送到background script');
            } else {
              console.log('❌ 发送WebSocket警报失败', response);
            }
          });
        }
      }
    } catch (error) {
      console.warn('处理WebSocket消息时出错:', error);
    }
  }

  // 获取WebSocket连接状态
  function getWebSocketStatus() {
    const connections = Array.from(monitoredConnections.values());
    return {
      total: connections.length,
      connections: connections.map(conn => ({
        url: conn.url,
        startTime: conn.startTime,
        readyState: conn.ws.readyState
      }))
    };
  }

  // 清理函数
  function cleanup() {
    if (originalWebSocket) {
      window.WebSocket = originalWebSocket;
      originalWebSocket = null;
      console.log('🧹 WebSocket拦截器已清理');
    }

    monitoredConnections.clear();
    processedAlerts.clear();
  }

  // 启动WebSocket监听
  function startWebSocketMonitoring() {
    console.log('🔍 启动WebSocket警报监听...');

    // 安装WebSocket拦截器
    interceptWebSocket();

    console.log('✅ WebSocket警报监听已启动');

    // 定期检查WebSocket连接状态
    setInterval(() => {
      const status = getWebSocketStatus();
      console.log(`📊 WebSocket状态: ${status.total} 个连接监听中`);

      if (status.total === 0) {
        console.log('⚠️ 没有检测到TradingView WebSocket连接，请确保页面已完全加载');
      }
    }, 30000);
  }

  // 暴露调试接口
  function exposeDebugInterface() {
    window.tvAlertForwarder = {
      getStatus: () => ({
        enabled: isEnabled,
        alertCount: alertCount,
        processedAlerts: processedAlerts.size,
        webSocketStatus: getWebSocketStatus(),
        allConnections: allWebSocketConnections.length
      }),

      getConnections: () => getWebSocketStatus(),

      getAllConnections: () => allWebSocketConnections,

      showAllConnections: () => {
        console.log('📡 所有WebSocket连接:');
        allWebSocketConnections.forEach((conn, index) => {
          console.log(`${index + 1}. ${conn.isTradingView ? '✅' : '❌'} ${conn.url} (${conn.timestamp})`);
        });
        return allWebSocketConnections;
      },

      cleanup: cleanup,

      reinstallInterceptor: () => {
        cleanup();
        setTimeout(() => {
          interceptWebSocket();
          console.log('🔄 WebSocket拦截器已重新安装');
        }, 100);
      },

      testAlert: (message = '测试警报: BTCUSD 50000') => {
        const testData = {
          message: message,
          symbol: 'BTCUSD',
          price: '50000',
          type: 'BUY',
          alertId: Date.now(),
          aid: 123456,
          fireTime: Math.floor(Date.now() / 1000),
          barTime: Math.floor(Date.now() / 1000),
          resolution: '1',
          soundEnabled: false,
          popupEnabled: true,
          timestamp: new Date().toISOString()
        };

        handleWebSocketMessage(JSON.stringify({
          text: {
            channel: 'alert',
            content: JSON.stringify({
              m: 'event',
              p: {
                id: testData.alertId,
                aid: testData.aid,
                fire_time: testData.fireTime,
                bar_time: testData.barTime,
                sym: testData.symbol,
                res: testData.resolution,
                desc: testData.message,
                snd: testData.soundEnabled,
                popup: testData.popupEnabled
              }
            })
          }
        }), 'test://localhost');
      }
    };

    console.log('🔧 调试接口已暴露到 window.tvAlertForwarder');
    console.log('💡 使用 window.tvAlertForwarder.showAllConnections() 查看所有WebSocket连接');
  }

  // 初始化
  function initialize() {
    console.log('🚀 初始化WebSocket警报监听器...');

    // 立即安装WebSocket拦截器，不等待页面加载
    startWebSocketMonitoring();
    exposeDebugInterface();

    // 检查插件是否启用
    checkEnabled((enabled) => {
      if (!enabled) {
        console.log('⚠️ 插件已禁用，但WebSocket拦截器仍然工作（用于调试）');
      } else {
        console.log('✅ 插件已启用，WebSocket监听已激活');
      }
    });

    // 定期检查状态
    setInterval(() => {
      const status = getWebSocketStatus();
      console.log(`📊 WebSocket监听状态: ${alertCount} 个警报检测到`);
      console.log(`📊 已处理警报数量: ${processedAlerts.size}`);
      console.log(`📊 监听连接数: ${status.total}`);
      console.log(`📊 总连接数: ${allWebSocketConnections.length}`);

      if (status.total === 0 && allWebSocketConnections.length > 0) {
        console.log('💡 提示: 检测到WebSocket连接但没有TradingView连接，使用 window.tvAlertForwarder.showAllConnections() 查看详情');
      }
    }, 60000); // 减少日志频率
  }

  // 页面可见性变化时检查WebSocket连接状态
  document.addEventListener('visibilitychange', () => {
    if (!document.hidden) {
      console.log('👁️ 页面重新可见，检查WebSocket连接状态...');
      const status = getWebSocketStatus();
      if (status.total === 0) {
        console.log('⚠️ 没有活跃的WebSocket连接，可能需要刷新页面');
      }
    }
  });

  // 页面卸载时清理
  window.addEventListener('beforeunload', cleanup);

  // 立即启动 - 在脚本加载时就安装WebSocket拦截器
  console.log('🚀 TradingView WebSocket警报监听器开始加载...');

  // 立即安装WebSocket拦截器，确保不错过任何连接
  if (document.readyState === 'loading') {
    // 如果页面还在加载，立即安装
    initialize();
  } else {
    // 如果页面已加载，也立即安装
    initialize();
  }

  console.log('✅ TradingView WebSocket警报监听器已加载');
  console.log('🎯 通过拦截WebSocket消息获取实时警报数据');
  console.log('🔧 使用 window.tvAlertForwarder 访问调试接口');
  console.log('🔍 使用 window.tvAlertForwarder.showAllConnections() 查看所有WebSocket连接');
})();
