// background.js

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