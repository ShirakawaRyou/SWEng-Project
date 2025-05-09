// background.js

chrome.action.onClicked.addListener((tab) => {
  // 当用户点击扩展图标时执行
  if (tab.id) {
    chrome.tabs.sendMessage(tab.id, { action: "toggle_sidebar" }, (response) => {
      if (chrome.runtime.lastError) {
        // 如果发送消息失败 (例如，内容脚本尚未加载或页面不允许脚本注入)
        // 我们可以尝试注入内容脚本，然后再发送消息
        // console.warn("Could not send message, attempting to inject script:", chrome.runtime.lastError.message);
        // 对于某些特殊页面 (如Chrome商店页面，chrome:// URL等)，注入会失败
        // 在这种情况下，我们可能需要更复杂的错误处理或用户提示

        // 简单的错误处理：如果内容脚本未准备好，可以尝试注入。
        // 但因为 manifest.json 中的 sidebar_scripts 已经配置为在 <all_urls> 注入，
        // 正常情况下内容脚本应该已经存在。
        // 此处主要处理 tab.url 可能不支持脚本注入的情况。
        if (tab.url && (tab.url.startsWith("chrome://") || tab.url.startsWith("https://chrome.google.com/webstore"))) {
            console.log("Cannot inject scripts on this page:", tab.url);
        } else {
            // 尝试注入，以防万一sidebar script因为某些原因没加载
            chrome.scripting.executeScript({
                target: { tabId: tab.id },
                files: ['sidebar.js']
            }).then(() => {
                chrome.scripting.insertCSS({
                    target: {tabId: tab.id},
                    files: ['styles.css']
                });
                // 再次尝试发送消息，延迟一点确保脚本加载完成
                setTimeout(() => {
                    chrome.tabs.sendMessage(tab.id, { action: "toggle_sidebar" });
                }, 100);

            }).catch(err => console.error("Failed to inject script:", err));
        }

      } else {
        // console.log("Message sent and received:", response);
      }
    });
  } else {
    console.error("Tab ID is missing.");
  }
});