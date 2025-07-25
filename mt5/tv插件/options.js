document.addEventListener('DOMContentLoaded', async () => {
  await loadConfig();
  
  document.getElementById('configForm').addEventListener('submit', saveConfig);
  document.getElementById('testBtn').addEventListener('click', testConnection);
  document.getElementById('resetBtn').addEventListener('click', resetConfig);
});

async function loadConfig() {
  const config = await getConfig();
  
  document.getElementById('webhookUrl').value = config.webhookUrl || '';
  document.getElementById('authToken').value = config.authToken || '';
  document.getElementById('customHeaders').value = config.customHeaders || '';
  document.getElementById('enabled').checked = config.enabled !== false;
}

async function saveConfig(event) {
  event.preventDefault();
  
  const webhookUrl = document.getElementById('webhookUrl').value.trim();
  const authToken = document.getElementById('authToken').value.trim();
  const customHeaders = document.getElementById('customHeaders').value.trim();
  const enabled = document.getElementById('enabled').checked;
  
  if (!webhookUrl) {
    showStatus('请输入Webhook URL', 'error');
    return;
  }
  
  if (customHeaders) {
    try {
      JSON.parse(customHeaders);
    } catch (error) {
      showStatus('自定义请求头必须是有效的JSON格式', 'error');
      return;
    }
  }
  
  try {
    await setConfig({
      webhookUrl,
      authToken,
      customHeaders,
      enabled
    });
    
    showStatus('配置已保存', 'success');
  } catch (error) {
    showStatus('保存配置失败: ' + error.message, 'error');
  }
}

async function testConnection() {
  const testBtn = document.getElementById('testBtn');
  const originalText = testBtn.textContent;
  
  testBtn.textContent = '测试中...';
  testBtn.disabled = true;
  
  try {
    const webhookUrl = document.getElementById('webhookUrl').value.trim();
    const authToken = document.getElementById('authToken').value.trim();
    const customHeaders = document.getElementById('customHeaders').value.trim();
    
    if (!webhookUrl) {
      showStatus('请先输入Webhook URL', 'error');
      return;
    }
    
    const headers = {
      'Content-Type': 'application/json'
    };
    
    if (authToken) {
      headers['Authorization'] = `Bearer ${authToken}`;
    }
    
    if (customHeaders) {
      try {
        const parsed = JSON.parse(customHeaders);
        Object.assign(headers, parsed);
      } catch (error) {
        showStatus('自定义请求头JSON格式无效', 'error');
        return;
      }
    }
    
    const testPayload = {
      test: true,
      message: '做空 XAUUSD 仓位=0.05',
      alert: {
        message: '做空 XAUUSD 仓位=0.05',
        symbol: 'XAUUSD',
        price: '2650.00',
        type: 'SELL',
        alertId: 37320364580,
        aid: 2687035109,
        fireTime: Math.floor(Date.now() / 1000),
        barTime: Math.floor(Date.now() / 1000) - 60,
        resolution: '1',
        soundEnabled: false,
        popupEnabled: true,
        name: null
      },
      timestamp: new Date().toISOString(),
      source: 'options_page_test',
      websocket: {
        alertId: 37320364580,
        aid: 2687035109,
        fireTime: Math.floor(Date.now() / 1000),
        barTime: Math.floor(Date.now() / 1000) - 60,
        resolution: '1',
        soundEnabled: false,
        popupEnabled: true
      }
    };
    
    const response = await fetch(webhookUrl, {
      method: 'POST',
      headers: headers,
      body: JSON.stringify(testPayload)
    });
    
    if (response.ok) {
      showStatus(`连接测试成功！HTTP ${response.status}`, 'success');
    } else {
      const errorText = await response.text().catch(() => 'Unknown error');
      showStatus(`连接失败: HTTP ${response.status} - ${errorText}`, 'error');
    }
    
  } catch (error) {
    showStatus(`连接错误: ${error.message}`, 'error');
  } finally {
    testBtn.textContent = originalText;
    testBtn.disabled = false;
  }
}

async function resetConfig() {
  if (confirm('确定要重置所有配置吗？')) {
    document.getElementById('webhookUrl').value = '';
    document.getElementById('authToken').value = '';
    document.getElementById('customHeaders').value = '';
    document.getElementById('enabled').checked = true;
    
    await chrome.storage.sync.clear();
    await chrome.storage.local.clear();
    
    showStatus('配置已重置', 'success');
  }
}

function showStatus(message, type) {
  const statusDiv = document.getElementById('status');
  statusDiv.textContent = message;
  statusDiv.className = `status ${type}`;
  statusDiv.style.display = 'block';
  
  setTimeout(() => {
    statusDiv.style.display = 'none';
  }, 5000);
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