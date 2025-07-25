(() => {
  console.log('TradingView Alert Forwarder: Content script loaded on', window.location.href);

  function observeAlerts() {
    console.log('TradingView Alert Forwarder: Starting alert observation');
    
    // 更全面的页面变化监听
    const observer = new MutationObserver((mutations) => {
      mutations.forEach((mutation) => {
        mutation.addedNodes.forEach((node) => {
          if (node.nodeType === Node.ELEMENT_NODE) {
            checkForAlert(node);
          }
        });
      });
    });

    observer.observe(document.body, {
      childList: true,
      subtree: true,
      attributes: true,
      attributeOldValue: true
    });

    // 定期检查现有警报
    setInterval(() => {
      checkExistingAlerts();
    }, 2000);

    // 立即检查一次
    setTimeout(() => {
      checkExistingAlerts();
    }, 1000);
  }

  function checkForAlert(element) {
    // TradingView 实际使用的更精确的选择器
    const alertSelectors = [
      // TradingView 警报面板
      '[data-name="alerts-dialog"]',
      '[data-name="alerts-popup"]', 
      '[data-name="alert-item"]',
      // 通知相关
      '.js-toast',
      '.toast-wrapper', 
      '.tv-toast',
      '.tv-notification',
      '[class*="toast"]',
      '[class*="notification"]',
      '[class*="alert"]',
      // 可能的警报触发提示
      '[data-name="notification-popup"]',
      '.notification-popup',
      '.alert-popup',
      // 通用类名
      '[role="alert"]',
      '[role="notification"]'
    ];

    alertSelectors.forEach(selector => {
      const alerts = element.querySelectorAll ? element.querySelectorAll(selector) : [];
      alerts.forEach(alert => {
        if (alert && !alert.dataset.processed) {
          processAlert(alert);
          alert.dataset.processed = 'true';
        }
      });

      if (element.matches && element.matches(selector) && !element.dataset.processed) {
        processAlert(element);
        element.dataset.processed = 'true';
      }
    });
  }

  function checkExistingAlerts() {
    console.log('TradingView Alert Forwarder: Checking existing alerts');
    
    const alertSelectors = [
      // TradingView 警报面板
      '[data-name="alerts-dialog"]',
      '[data-name="alerts-popup"]', 
      '[data-name="alert-item"]',
      // 通知相关
      '.js-toast',
      '.toast-wrapper', 
      '.tv-toast',
      '.tv-notification',
      '[class*="toast"]',
      '[class*="notification"]',
      '[class*="alert"]',
      // 可能的警报触发提示
      '[data-name="notification-popup"]',
      '.notification-popup',
      '.alert-popup',
      // 通用类名
      '[role="alert"]',
      '[role="notification"]'
    ];

    alertSelectors.forEach(selector => {
      const alerts = document.querySelectorAll(selector);
      alerts.forEach(alert => {
        if (!alert.dataset.processed) {
          processAlert(alert);
          alert.dataset.processed = 'true';
        }
      });
    });
  }

  function processAlert(alertElement) {
    try {
      console.log('TradingView Alert Forwarder: Processing element:', alertElement);
      
      // 检查插件是否启用
      chrome.storage.sync.get({enabled: true}, (config) => {
        if (!config.enabled) {
          console.log('TradingView Alert Forwarder: Extension is disabled, skipping alert');
          return;
        }
        
        const alertData = extractAlertData(alertElement);
        if (alertData) {
          console.log('TradingView Alert detected:', alertData);
          
          chrome.runtime.sendMessage({
            type: 'TRADINGVIEW_ALERT',
            data: alertData,
            timestamp: new Date().toISOString(),
            url: window.location.href
          }, (response) => {
            console.log('Message sent to background script:', response);
          });
        } else {
          console.log('TradingView Alert Forwarder: No valid alert data extracted from element');
        }
      });
    } catch (error) {
      console.error('Error processing alert:', error);
    }
  }

  function extractAlertData(element) {
    const text = element.innerText || element.textContent || '';
    
    if (!text || text.length < 3) {
      return null;
    }

    const alertData = {
      message: text.trim(),
      html: element.innerHTML,
      className: element.className,
      timestamp: new Date().toISOString(),
      symbol: extractSymbol(),
      price: extractPrice(text),
      type: determineAlertType(text)
    };

    return alertData;
  }

  function extractSymbol() {
    try {
      const symbolElement = document.querySelector('[data-name="legend-source-title"]') ||
                           document.querySelector('.tv-symbol-header__short-title') ||
                           document.querySelector('[class*="symbol"]');
      
      if (symbolElement) {
        return symbolElement.textContent.trim();
      }

      const titleMatch = document.title.match(/([A-Z]{2,})/);
      return titleMatch ? titleMatch[1] : 'UNKNOWN';
    } catch {
      return 'UNKNOWN';
    }
  }

  function extractPrice(text) {
    const priceMatch = text.match(/[\d,]+\.?\d*/);
    return priceMatch ? priceMatch[0] : null;
  }

  function determineAlertType(text) {
    const lowerText = text.toLowerCase();
    if (lowerText.includes('buy') || lowerText.includes('long')) return 'BUY';
    if (lowerText.includes('sell') || lowerText.includes('short')) return 'SELL';
    if (lowerText.includes('alert') || lowerText.includes('trigger')) return 'ALERT';
    return 'UNKNOWN';
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', observeAlerts);
  } else {
    observeAlerts();
  }

  window.addEventListener('focus', () => {
    setTimeout(checkExistingAlerts, 1000);
  });
})();