// TradingView Alert Forwarder - 弹窗警报监听版本
// 专门监听刚触发的弹窗警报，不处理已存在的警报

(() => {
  console.log('🚀 TradingView Alert Forwarder: 弹窗警报监听模式启动');
  console.log('🚀 当前时间:', new Date().toISOString());
  console.log('🚀 当前URL:', window.location.href);

  let alertCount = 0;
  let isEnabled = true;
  let observer = null;
  let processedAlerts = new Set(); // 记录已处理的警报，避免重复

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

  // TradingView弹窗警报的特定选择器
  const popupAlertSelectors = [
    // TradingView弹窗对话框
    '[data-name="alerts-popup"]',
    '[data-name="alert-popup"]',
    '[data-name="notification-popup"]',
    '[data-name="toast-popup"]',

    // 弹窗容器类
    '.tv-dialog',
    '.tv-popup',
    '.tv-toast',
    '.tv-notification-popup',

    // 通用弹窗选择器（但要确保是新出现的）
    '[role="dialog"][aria-live]',
    '[role="alertdialog"]',
    '.popup-dialog',
    '.alert-dialog',

    // 可能的警报弹窗类名模式
    '[class*="popup"][class*="alert"]',
    '[class*="dialog"][class*="alert"]',
    '[class*="toast"][class*="show"]',
    '[class*="notification"][class*="show"]'
  ];

  // 检测元素是否是新出现的弹窗警报
  function isNewPopupAlert(element) {
    if (!element || !element.textContent) return false;

    const text = element.textContent.toLowerCase();
    const className = element.className ? element.className.toLowerCase() : '';
    const dataName = element.getAttribute('data-name') || '';

    // 检查是否是弹窗元素
    const isPopup = className.includes('popup') ||
                   className.includes('dialog') ||
                   className.includes('toast') ||
                   dataName.includes('popup') ||
                   dataName.includes('dialog') ||
                   element.getAttribute('role') === 'dialog' ||
                   element.getAttribute('role') === 'alertdialog';

    // 检查是否包含警报关键词
    const alertKeywords = [
      'alert', '警报', '提醒', 'notification', 'triggered', '触发',
      'buy', 'sell', '买入', '卖出', '做多', '做空',
      'price', '价格', 'target', '目标', 'stop', '止损',
      'breakout', '突破', 'support', '支撑', 'resistance', '阻力'
    ];

    const hasAlertKeyword = alertKeywords.some(keyword => text.includes(keyword));

    // 检查元素的可见性和位置（弹窗通常是fixed或absolute定位）
    const computedStyle = window.getComputedStyle(element);
    const isVisible = element.offsetWidth > 0 && element.offsetHeight > 0;
    const isPositioned = computedStyle.position === 'fixed' ||
                        computedStyle.position === 'absolute' ||
                        computedStyle.zIndex > 1000;

    // 生成唯一标识符避免重复处理
    const elementId = element.outerHTML.substring(0, 200) + text.substring(0, 100);

    if (processedAlerts.has(elementId)) {
      return false; // 已经处理过的警报
    }

    const isNewAlert = isPopup && hasAlertKeyword && isVisible && isPositioned;

    if (isNewAlert) {
      processedAlerts.add(elementId);
      // 清理旧的记录，避免内存泄漏
      if (processedAlerts.size > 100) {
        const firstItem = processedAlerts.values().next().value;
        processedAlerts.delete(firstItem);
      }
    }

    return isNewAlert;
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

  // DOM变化监听器 - 专门监听新出现的弹窗
  function handleDOMChanges(mutations) {
    if (!isEnabled) return;

    mutations.forEach(mutation => {
      // 只关注新增的节点（新出现的弹窗）
      mutation.addedNodes.forEach(node => {
        if (node.nodeType === Node.ELEMENT_NODE) {
          console.log('🔍 检测到新DOM节点:', node.tagName, node.className);

          // 检查节点本身是否是弹窗警报
          if (isNewPopupAlert(node)) {
            console.log('🎯 发现新弹窗警报:', node);
            const alertData = extractAlertInfo(node);
            processAlert(alertData);
            return; // 找到就不再检查子元素
          }

          // 检查节点的直接子元素中是否有弹窗警报
          popupAlertSelectors.forEach(selector => {
            try {
              const alertElements = node.querySelectorAll ? node.querySelectorAll(selector) : [];
              alertElements.forEach(element => {
                if (isNewPopupAlert(element)) {
                  console.log('🎯 在子元素中发现新弹窗警报:', element);
                  const alertData = extractAlertInfo(element);
                  processAlert(alertData);
                }
              });
            } catch (error) {
              console.warn('选择器错误:', selector, error);
            }
          });
        }
      });

      // 检查属性变化（可能是弹窗显示/隐藏状态变化）
      if (mutation.type === 'attributes') {
        const target = mutation.target;
        if (mutation.attributeName === 'style' ||
            mutation.attributeName === 'class' ||
            mutation.attributeName === 'aria-hidden') {

          // 检查是否是从隐藏变为显示的弹窗
          const isNowVisible = target.offsetWidth > 0 && target.offsetHeight > 0;
          const wasHidden = mutation.oldValue &&
                           (mutation.oldValue.includes('display: none') ||
                            mutation.oldValue.includes('visibility: hidden') ||
                            mutation.oldValue.includes('aria-hidden="true"'));

          if (isNowVisible && wasHidden && isNewPopupAlert(target)) {
            console.log('🎯 发现显示状态变化的弹窗警报:', target);
            const alertData = extractAlertInfo(target);
            processAlert(alertData);
          }
        }
      }
    });
  }

  // 启动DOM监听 - 专门监听弹窗出现
  function startDOMMonitoring() {
    console.log('🔍 启动弹窗警报监听...');

    observer = new MutationObserver(handleDOMChanges);

    // 监听配置：重点关注新增节点和属性变化
    observer.observe(document.body, {
      childList: true,        // 监听子节点变化（新弹窗出现）
      subtree: true,          // 监听所有后代节点
      attributes: true,       // 监听属性变化（显示/隐藏状态）
      attributeOldValue: true, // 记录属性旧值
      attributeFilter: ['class', 'style', 'aria-hidden', 'data-name'] // 只监听相关属性
    });

    console.log('✅ 弹窗警报监听已启动');
  }

  // 不再扫描现有元素，只监听新出现的弹窗
  // function scanExistingElements() - 已移除

  // 监听可能触发弹窗的事件
  function setupTriggerMonitoring() {
    // 监听可能触发警报弹窗的事件
    document.addEventListener('click', (event) => {
      const target = event.target;

      // 检查是否点击了可能触发警报的元素
      if (target && (
        target.textContent.includes('警报') ||
        target.textContent.includes('Alert') ||
        target.className.includes('alert') ||
        target.className.includes('notification') ||
        target.getAttribute('data-name')?.includes('alert')
      )) {
        console.log('🖱️ 检测到可能触发警报的点击:', target);
        // 不需要主动扫描，DOM监听器会自动捕获新出现的弹窗
      }
    });

    // 监听键盘事件（可能的快捷键触发）
    document.addEventListener('keydown', (event) => {
      // 一些可能触发警报的快捷键组合
      if ((event.ctrlKey || event.metaKey) && event.key === 'a') {
        console.log('🎹 检测到可能的警报快捷键');
      }
    });
  }

  // 初始化
  function initialize() {
    checkEnabled((enabled) => {
      if (!enabled) {
        console.log('⚠️ 插件已禁用，跳过弹窗监听');
        return;
      }

      console.log('🚀 初始化弹窗警报监听器...');

      // 等待页面完全加载
      if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', () => {
          setTimeout(() => {
            startDOMMonitoring();
            setupTriggerMonitoring();
          }, 1000);
        });
      } else {
        setTimeout(() => {
          startDOMMonitoring();
          setupTriggerMonitoring();
        }, 1000);
      }

      // 定期检查状态
      setInterval(() => {
        console.log(`📊 弹窗监听状态: ${alertCount} 个新警报检测到`);
        console.log(`📊 已处理警报数量: ${processedAlerts.size}`);
      }, 30000);
    });
  }

  // 页面可见性变化时不需要扫描，只需要确保监听器正常工作
  document.addEventListener('visibilitychange', () => {
    if (!document.hidden) {
      console.log('👁️ 页面重新可见，弹窗监听器继续工作...');
      // 不扫描现有元素，只等待新弹窗出现
    }
  });

  // 启动
  initialize();

  console.log('✅ TradingView 弹窗警报监听器已加载');
  console.log('🎯 只监听新出现的弹窗警报，不处理已存在的警报');
})();
