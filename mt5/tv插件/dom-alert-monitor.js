// TradingView Alert Forwarder - DOM监听版本
// 通过监听DOM变化来检测警报通知

(() => {
  console.log('🚀 TradingView Alert Forwarder: DOM监听模式启动');
  console.log('🚀 当前时间:', new Date().toISOString());
  console.log('🚀 当前URL:', window.location.href);

  let alertCount = 0;
  let isEnabled = true;
  let observer = null;

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

  // 警报检测的选择器模式
  const alertSelectors = [
    // 通用警报选择器
    '[class*="alert"]',
    '[class*="notification"]',
    '[class*="toast"]',
    '[class*="popup"]',
    '[class*="dialog"]',
    '[role="alert"]',
    '[role="dialog"]',
    '[aria-live="polite"]',
    '[aria-live="assertive"]',
    
    // TradingView特定选择器
    '[class*="tv-alert"]',
    '[class*="tv-notification"]',
    '[class*="tv-toast"]',
    '[data-name*="alert"]',
    '[data-name*="notification"]',
    
    // 可能的警报容器
    '.js-alert',
    '.js-notification',
    '.js-toast',
    '#alerts',
    '#notifications'
  ];

  // 检测元素是否可能是警报
  function isLikelyAlert(element) {
    if (!element || !element.textContent) return false;

    const text = element.textContent.toLowerCase();
    const className = element.className ? element.className.toLowerCase() : '';
    const id = element.id ? element.id.toLowerCase() : '';

    // 检查文本内容中的警报关键词
    const alertKeywords = [
      'alert', '警报', '提醒', 'notification', 'triggered', '触发',
      'buy', 'sell', '买入', '卖出', '做多', '做空',
      'price', '价格', 'target', '目标', 'stop', '止损',
      'breakout', '突破', 'support', '支撑', 'resistance', '阻力'
    ];

    const hasAlertKeyword = alertKeywords.some(keyword => text.includes(keyword));

    // 检查CSS类名和ID中的警报相关词汇
    const alertClassKeywords = ['alert', 'notification', 'toast', 'popup', 'dialog'];
    const hasAlertClass = alertClassKeywords.some(keyword => 
      className.includes(keyword) || id.includes(keyword)
    );

    // 检查元素的可见性
    const isVisible = element.offsetWidth > 0 && element.offsetHeight > 0;

    return (hasAlertKeyword || hasAlertClass) && isVisible;
  }

  // 提取警报信息
  function extractAlertInfo(element) {
    const text = element.textContent.trim();
    
    // 尝试提取交易对
    const symbolMatch = text.match(/([A-Z]{2,10}[\/:]?[A-Z]{2,10})/);
    const symbol = symbolMatch ? symbolMatch[1] : 'UNKNOWN';

    // 尝试提取价格
    const priceMatch = text.match(/[\d,]+\.?\d*/);
    const price = priceMatch ? priceMatch[0] : null;

    // 判断警报类型
    let type = 'ALERT';
    const lowerText = text.toLowerCase();
    if (lowerText.includes('buy') || lowerText.includes('做多') || lowerText.includes('买入')) {
      type = 'BUY';
    } else if (lowerText.includes('sell') || lowerText.includes('做空') || lowerText.includes('卖出')) {
      type = 'SELL';
    }

    return {
      message: text,
      symbol: symbol,
      price: price,
      type: type,
      html: element.outerHTML,
      className: element.className,
      timestamp: new Date().toISOString()
    };
  }

  // 处理检测到的警报
  function processAlert(alertData) {
    alertCount++;
    console.log(`🚨 警报 #${alertCount} 检测到:`, alertData.message);
    
    // 发送到background script
    if (typeof chrome !== 'undefined' && chrome.runtime) {
      chrome.runtime.sendMessage({
        type: 'TRADINGVIEW_ALERT',
        data: alertData,
        timestamp: alertData.timestamp,
        url: window.location.href,
        source: 'dom'
      }, (response) => {
        if (response && response.success) {
          console.log('✅ 警报已发送到background script');
        } else {
          console.log('❌ 发送警报失败');
        }
      });
    }
  }

  // DOM变化监听器
  function handleDOMChanges(mutations) {
    if (!isEnabled) return;

    mutations.forEach(mutation => {
      // 检查新增的节点
      mutation.addedNodes.forEach(node => {
        if (node.nodeType === Node.ELEMENT_NODE) {
          // 检查节点本身
          if (isLikelyAlert(node)) {
            const alertData = extractAlertInfo(node);
            processAlert(alertData);
          }

          // 检查节点的子元素
          alertSelectors.forEach(selector => {
            try {
              const alertElements = node.querySelectorAll ? node.querySelectorAll(selector) : [];
              alertElements.forEach(element => {
                if (isLikelyAlert(element)) {
                  const alertData = extractAlertInfo(element);
                  processAlert(alertData);
                }
              });
            } catch (error) {
              // 忽略选择器错误
            }
          });
        }
      });

      // 检查文本变化
      if (mutation.type === 'characterData' && mutation.target.parentElement) {
        const parentElement = mutation.target.parentElement;
        if (isLikelyAlert(parentElement)) {
          const alertData = extractAlertInfo(parentElement);
          processAlert(alertData);
        }
      }
    });
  }

  // 启动DOM监听
  function startDOMMonitoring() {
    console.log('🔍 启动DOM变化监听...');

    observer = new MutationObserver(handleDOMChanges);
    
    observer.observe(document.body, {
      childList: true,
      subtree: true,
      characterData: true,
      attributes: true,
      attributeFilter: ['class', 'style', 'data-name']
    });

    console.log('✅ DOM监听已启动');
  }

  // 扫描现有元素
  function scanExistingElements() {
    console.log('🔍 扫描现有警报元素...');
    
    alertSelectors.forEach(selector => {
      try {
        const elements = document.querySelectorAll(selector);
        elements.forEach(element => {
          if (isLikelyAlert(element)) {
            console.log('📋 发现现有警报元素:', element);
            const alertData = extractAlertInfo(element);
            processAlert(alertData);
          }
        });
      } catch (error) {
        // 忽略选择器错误
      }
    });
  }

  // 监听点击事件（可能触发警报）
  function setupClickMonitoring() {
    document.addEventListener('click', (event) => {
      const target = event.target;
      
      // 检查是否点击了警报相关按钮
      if (target && (
        target.textContent.includes('警报') ||
        target.textContent.includes('Alert') ||
        target.className.includes('alert') ||
        target.className.includes('notification')
      )) {
        console.log('🖱️ 检测到警报相关点击:', target);
        
        // 延迟检查新出现的警报
        setTimeout(() => {
          scanExistingElements();
        }, 1000);
      }
    });
  }

  // 初始化
  function initialize() {
    checkEnabled((enabled) => {
      if (!enabled) {
        console.log('⚠️ 插件已禁用，跳过DOM监听');
        return;
      }

      console.log('🚀 初始化DOM警报监听器...');
      
      // 等待页面完全加载
      if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', () => {
          setTimeout(() => {
            startDOMMonitoring();
            scanExistingElements();
            setupClickMonitoring();
          }, 1000);
        });
      } else {
        setTimeout(() => {
          startDOMMonitoring();
          scanExistingElements();
          setupClickMonitoring();
        }, 1000);
      }

      // 定期检查状态
      setInterval(() => {
        console.log(`📊 DOM监听状态: ${alertCount} 个警报检测到`);
      }, 30000);
    });
  }

  // 页面可见性变化时重新检查
  document.addEventListener('visibilitychange', () => {
    if (!document.hidden) {
      console.log('👁️ 页面重新可见，扫描警报...');
      setTimeout(scanExistingElements, 500);
    }
  });

  // 启动
  initialize();

  console.log('✅ TradingView DOM警报监听器已加载');
})();
