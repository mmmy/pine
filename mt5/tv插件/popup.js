document.addEventListener('DOMContentLoaded', async () => {
  await loadStatus();
  await loadStats();
  
  document.getElementById('configBtn').addEventListener('click', () => {
    chrome.runtime.openOptionsPage();
  });
  
  document.getElementById('testBtn').addEventListener('click', testConnection);
  document.getElementById('toggleSwitch').addEventListener('click', toggleEnabled);
});

async function loadStatus() {
  const config = await getConfig();
  const statusDiv = document.getElementById('status');
  const statusText = document.getElementById('statusText');
  const toggleSwitch = document.getElementById('toggleSwitch');
  
  // 更新开关状态
  if (config.enabled) {
    toggleSwitch.classList.add('enabled');
  } else {
    toggleSwitch.classList.remove('enabled');
  }
  
  // 更新状态显示
  if (config.webhookUrl && config.enabled) {
    statusDiv.className = 'status enabled';
    statusText.textContent = '插件已启用';
  } else if (config.webhookUrl && !config.enabled) {
    statusDiv.className = 'status disabled';
    statusText.textContent = '插件已禁用';
  } else {
    statusDiv.className = 'status disabled';
    statusText.textContent = '未配置URL';
  }
}

async function loadStats() {
  const stats = await getStats();
  
  document.getElementById('totalAlerts').textContent = stats.totalAlerts || 0;
  
  if (stats.lastAlert) {
    const date = new Date(stats.lastAlert);
    document.getElementById('lastAlert').textContent = date.toLocaleString('zh-CN');
  } else {
    document.getElementById('lastAlert').textContent = '无';
  }
}

async function testConnection() {
  const testBtn = document.getElementById('testBtn');
  const originalText = testBtn.textContent;
  
  testBtn.textContent = '测试中...';
  testBtn.disabled = true;
  
  try {
    const config = await getConfig();
    
    if (!config.webhookUrl) {
      alert('请先配置Webhook URL');
      return;
    }
    
    const testPayload = {
      test: true,
      message: '做空 XAUUSD 仓位=0.05',
      alert: {
        message: '做空 XAUUSD 仓位=0.05',
        symbol: 'XAUUSD',
        price: '2650.00',
        type: 'SELL'
      },
      timestamp: new Date().toISOString(),
      source: 'popup_test'
    };
    
    const response = await fetch(config.webhookUrl, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        ...getCustomHeaders(config)
      },
      body: JSON.stringify(testPayload)
    });
    
    if (response.ok) {
      alert('连接测试成功！');
    } else {
      alert(`连接失败: ${response.status} ${response.statusText}`);
    }
    
  } catch (error) {
    alert(`连接错误: ${error.message}`);
  } finally {
    testBtn.textContent = originalText;
    testBtn.disabled = false;
  }
}

function getCustomHeaders(config) {
  const headers = {};
  
  if (config.customHeaders) {
    try {
      const customHeaders = JSON.parse(config.customHeaders);
      Object.assign(headers, customHeaders);
    } catch (error) {
      console.error('Invalid custom headers JSON:', error);
    }
  }
  
  if (config.authToken) {
    headers['Authorization'] = `Bearer ${config.authToken}`;
  }
  
  return headers;
}

async function getConfig() {
  return new Promise((resolve) => {
    chrome.storage.sync.get({
      webhookUrl: 'http://localhost:5000/webhook',
      customHeaders: '',
      authToken: '',
      enabled: true
    }, resolve);
  });
}

async function toggleEnabled() {
  try {
    const config = await getConfig();
    const newEnabled = !config.enabled;
    
    await setConfig({
      ...config,
      enabled: newEnabled
    });
    
    await loadStatus();
    
    console.log('Extension enabled status changed to:', newEnabled);
  } catch (error) {
    console.error('Error toggling enabled status:', error);
  }
}

async function setConfig(config) {
  return new Promise((resolve, reject) => {
    chrome.storage.sync.set(config, () => {
      if (chrome.runtime.lastError) {
        reject(new Error(chrome.runtime.lastError.message));
      } else {
        resolve();
      }
    });
  });
}

async function getStats() {
  return new Promise((resolve) => {
    chrome.storage.local.get({
      stats: {
        totalAlerts: 0,
        lastAlert: null
      }
    }, (result) => resolve(result.stats));
  });
}