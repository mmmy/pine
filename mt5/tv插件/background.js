chrome.runtime.onMessage.addListener((message, sender, sendResponse) => {
  if (message.type === 'TRADINGVIEW_ALERT') {
    handleAlert(message.data, message.timestamp, message.url, message)
      .then(() => {
        sendResponse({success: true, message: 'Alert processed'});
      })
      .catch((error) => {
        console.error('Alert handling error:', error);
        sendResponse({success: false, error: error.message});
      });
  }
  
  return true;
});

async function handleAlert(alertData, timestamp, sourceUrl, message) {
  try {
    const config = await getConfig();
    
    if (!config.webhookUrl || !config.enabled) {
      return;
    }

    const payload = {
      message: alertData.message,
      alert: alertData,
      timestamp: timestamp,
      source: sourceUrl,
      extension: 'TradingView Alert Forwarder v1.0',
      // 如果是WebSocket数据，包含额外信息
      ...(message.source === 'websocket' && {
        websocket: {
          alertId: alertData.alertId,
          aid: alertData.aid,
          fireTime: alertData.fireTime,
          barTime: alertData.barTime,
          resolution: alertData.resolution,
          soundEnabled: alertData.soundEnabled,
          popupEnabled: alertData.popupEnabled
        }
      })
    };

    await sendToWebhook(config.webhookUrl, payload, config);
    await updateStats();
    
  } catch (error) {
    console.error('Error handling alert:', error);
  }
}

async function sendToWebhook(url, payload, config) {
  const options = {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      ...getCustomHeaders(config)
    },
    body: JSON.stringify(payload)
  };

  const response = await fetch(url, options);
  
  if (!response.ok) {
    throw new Error(`HTTP ${response.status}: ${response.statusText}`);
  }
  
  return response;
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

async function updateStats() {
  const stats = await getStats();
  stats.totalAlerts = (stats.totalAlerts || 0) + 1;
  stats.lastAlert = new Date().toISOString();
  
  chrome.storage.local.set({ stats });
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

chrome.runtime.onInstalled.addListener(() => {
  console.log('TradingView Alert Forwarder installed');
});