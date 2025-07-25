// Debug script to inject into TradingView for testing
// Run this in browser console on TradingView page

console.log('=== TradingView Alert Forwarder Debug ===');

// 检查页面上所有可能的警报相关元素
function debugAlerts() {
  console.log('Scanning for alert elements...');
  
  const selectors = [
    '[data-name*="alert"]',
    '[data-name*="notification"]', 
    '[data-name*="popup"]',
    '[class*="alert"]',
    '[class*="notification"]',
    '[class*="toast"]',
    '[class*="popup"]',
    '[role="alert"]',
    '[role="notification"]',
    '.js-toast',
    '.tv-toast',
    '.tv-notification'
  ];
  
  selectors.forEach(selector => {
    const elements = document.querySelectorAll(selector);
    if (elements.length > 0) {
      console.log(`Found ${elements.length} elements for selector: ${selector}`);
      elements.forEach((el, i) => {
        console.log(`  Element ${i}:`, el.className, el.textContent?.slice(0, 50));
      });
    }
  });
  
  // 检查所有data-name属性
  const dataNameElements = document.querySelectorAll('[data-name]');
  console.log(`Found ${dataNameElements.length} elements with data-name attribute:`);
  
  const dataNames = new Set();
  dataNameElements.forEach(el => {
    dataNames.add(el.getAttribute('data-name'));
  });
  
  console.log('Unique data-name values:', Array.from(dataNames).sort());
}

// 监听DOM变化
function startDebugObserver() {
  console.log('Starting debug observer...');
  
  const observer = new MutationObserver((mutations) => {
    mutations.forEach((mutation) => {
      mutation.addedNodes.forEach((node) => {
        if (node.nodeType === Node.ELEMENT_NODE) {
          const element = node;
          
          // 检查是否包含关键词
          const text = element.textContent || '';
          const className = element.className || '';
          const dataName = element.getAttribute('data-name') || '';
          
          if (text.toLowerCase().includes('alert') || 
              className.toLowerCase().includes('alert') ||
              className.toLowerCase().includes('notification') ||
              className.toLowerCase().includes('toast') ||
              dataName.toLowerCase().includes('alert')) {
            console.log('🚨 Potential alert element added:', {
              tagName: element.tagName,
              className: className,
              dataName: dataName,
              text: text.slice(0, 100),
              element: element
            });
          }
        }
      });
    });
  });
  
  observer.observe(document.body, {
    childList: true,
    subtree: true,
    attributes: true
  });
  
  console.log('Debug observer started');
}

// 执行调试
debugAlerts();
startDebugObserver();

console.log('=== Debug script loaded ===');
console.log('Run debugAlerts() to scan for elements again');
console.log('Check console for new elements as they appear');