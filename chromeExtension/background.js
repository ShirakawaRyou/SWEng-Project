// background.js

// 拦截所有包含 /invalid/ 的网络请求，避免资源加载错误
// chrome.webRequest.onBeforeRequest.addListener(
//   details => {
//     if (details.url.includes('/invalid/')) {
//       return { cancel: true };
//     }
//   },
//   { urls: ['<all_urls>'] },
//   ['blocking']
// );

chrome.action.onClicked.addListener((tab) => {
  if (!tab.id) {
    console.error("Tab ID is missing.");
    return;
  }
  // 每次点击先注入模板、脚本和样式，确保内容脚本可用
  chrome.scripting.insertCSS({ target: { tabId: tab.id }, files: ['styles.css','sidebar.css'] })
    .catch(err => console.error('注入 CSS 失败', err));
  chrome.scripting.executeScript({ target: { tabId: tab.id }, files: ['sidebarTemplate.js','sidebar.js'] })
    .then(() => {
      // 脚本注入后再发送消息展开/收起侧边栏
      chrome.tabs.sendMessage(tab.id, { action: 'toggle_sidebar' });
    })
    .catch(err => console.error('注入脚本失败', err));
});

// 扩展安装或更新时，自动向所有已打开的 LinkedIn 标签注入侧边栏脚本和样式
chrome.runtime.onInstalled.addListener(() => {
  chrome.tabs.query({ url: ["*://*.linkedin.com/*", "*://linkedin.com/*"] }, tabs => {
    for (const tab of tabs) {
      if (tab.id) {
        chrome.scripting.insertCSS({ target: { tabId: tab.id }, files: ['styles.css','sidebar.css'] });
        chrome.scripting.executeScript({ target: { tabId: tab.id }, files: ['sidebarTemplate.js','sidebar.js'] });
      }
    }
  });
});

// 标签加载完成后，如果是 LinkedIn 页面，自动注入侧边栏脚本和样式
chrome.tabs.onUpdated.addListener((tabId, changeInfo, tab) => {
  if (changeInfo.status === 'complete' && tab.url && /https?:\/\/(www\.)?linkedin\.com/.test(tab.url)) {
    chrome.scripting.insertCSS({ target: { tabId }, files: ['styles.css','sidebar.css'] });
    chrome.scripting.executeScript({ target: { tabId }, files: ['sidebarTemplate.js','sidebar.js'] });
  }
});

// 监听来自内容脚本的 API 请求消息
chrome.runtime.onMessage.addListener((msg, sender, sendResponse) => {
  console.log('[Background] Received message:', msg);
  if (msg.action === 'do_login') {
    console.log('[Background] Action: do_login, username:', msg.username);
    const params = new URLSearchParams();
    params.append('username', msg.username);
    params.append('password', msg.password);
    fetch('http://localhost:8000/api/v1/auth/login', {
      method: 'POST',
      headers: {'Content-Type': 'application/x-www-form-urlencoded'},
      body: params
    })
      .then(res => {
        console.log('[Background] do_login raw response status:', res.status);
        return res.json();
      })
      .then(data => {
        console.log('[Background] do_login data:', data);
        if (data.access_token) {
          sendResponse({success: true, accessToken: data.access_token});
        } else {
          sendResponse({success: false, error: data.detail || '登录失败'});
        }
      })
      .catch(err => {
        console.error('[Background] do_login error:', err);
        sendResponse({success: false, error: err.message});
      });
    return true;
  } else if (msg.action === 'get_user') {
    console.log('[Background] Action: get_user, token:', msg.accessToken);
    fetch('http://localhost:8000/api/v1/auth/users/me', {
      headers: {'Authorization': `Bearer ${msg.accessToken}`}
    })
      .then(res => {
        console.log('[Background] get_user raw response status:', res.status);
        if (!res.ok) {
          return res.json().then(errorData => { throw new Error(errorData.detail || `HTTP error! status: ${res.status}`); }).catch(() => { throw new Error(`HTTP error! status: ${res.status}`); });
        }
        return res.json();
      })
      .then(data => {
        console.log('[Background] get_user data:', data);
        sendResponse({success: true, user: data});
      })
      .catch(err => {
        console.error('[Background] get_user error:', err);
        sendResponse({success: false, error: err.message});
      });
    return true;
  } else if (msg.action === 'fetch_resumes') {
    console.log('[Background] Action: fetch_resumes, token:', msg.accessToken);
    fetch('http://localhost:8000/api/v1/resumes', {
      headers: {'Authorization': `Bearer ${msg.accessToken}`}
    })
      .then(res => {
        console.log('[Background] fetch_resumes raw response status:', res.status);
        return res.json();
      })
      .then(data => {
        console.log('[Background] fetch_resumes data:', data);
        sendResponse({success: true, resumes: data});
      })
      .catch(err => {
        console.error('[Background] fetch_resumes error:', err);
        sendResponse({success: false, error: err.message});
      });
    return true;
  } else if (msg.action === 'extract_jd_keywords') {
    console.log('[Background] Action: extract_jd_keywords, text length:', msg.jd_text ? msg.jd_text.length : 0);
    fetch('http://localhost:8000/api/v1/matching/extract-jd-keywords', {
      method: 'POST',
      headers: {'Content-Type': 'application/json'},
      body: JSON.stringify({ jd_text: msg.jd_text })
    })
      .then(res => {
        console.log('[Background] extract_jd_keywords raw status:', res.status);
        return res.json();
      })
      .then(data => {
        console.log('[Background] extract_jd_keywords data:', data);
        sendResponse({success: true, jd_id: data.jd_id, keywords: data.keywords});
      })
      .catch(err => {
        console.error('[Background] extract_jd_keywords error:', err);
        sendResponse({success: false, error: err.message});
      });
    return true;
  } else if (msg.action === 'match_resumes') {
    console.log('[Background] Action: match_resumes, token:', msg.accessToken, 'jd_id:', msg.jd_id, 'resume_ids:', msg.resume_ids);
    fetch('http://localhost:8000/api/v1/matching/match-resumes', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${msg.accessToken}`
      },
      body: JSON.stringify({ jd_id: msg.jd_id, resume_ids: msg.resume_ids })
    })
      .then(res => {
        console.log('[Background] match_resumes raw status:', res.status);
        return res.json();
      })
      .then(data => {
        console.log('[Background] match_resumes data:', data);
        sendResponse({success: true, data});
      })
      .catch(err => {
        console.error('[Background] match_resumes error:', err);
        sendResponse({success: false, error: err.message});
      });
    return true;
  }
  // 新增：处理建议请求
  else if (msg.action === 'suggestions') {
    console.log('[Background] Action: suggestions, token:', msg.accessToken, 'jd_id:', msg.jd_id, 'resume_id:', msg.resume_id);
    fetch('http://localhost:8000/api/v1/matching/suggestions', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${msg.accessToken}`
      },
      body: JSON.stringify({ jd_id: msg.jd_id, resume_id: msg.resume_id })
    })
      .then(res => {
        console.log('[Background] suggestions raw status:', res.status);
        return res.json();
      })
      .then(data => {
        console.log('[Background] suggestions data:', data);
        sendResponse({ success: true, ...data });
      })
      .catch(err => {
        console.error('[Background] suggestions error:', err);
        sendResponse({ success: false, error: err.message });
      });
    return true;
  }
  else if (msg.action === 'open_front_sync') {
    // 在后台打开前端页面以触发 frontStorageSync，同步 localStorage
    chrome.tabs.create({ url: 'http://localhost:8080', active: false }, (tab) => {
      const tabId = tab.id;
      function handleUpdate(updatedTabId, changeInfo) {
        if (updatedTabId === tabId && changeInfo.status === 'complete') {
          // 等待脚本运行完成后关闭标签页
          setTimeout(() => {
            chrome.tabs.remove(tabId);
          }, 1000);
          chrome.tabs.onUpdated.removeListener(handleUpdate);
        }
      }
      chrome.tabs.onUpdated.addListener(handleUpdate);
    });
    return false;
  }
});