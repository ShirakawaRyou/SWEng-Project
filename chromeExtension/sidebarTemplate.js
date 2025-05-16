// sidebarTemplate.js

function getSidebarHTML() {
  return `
    <div class="my-extension-sidebar-header">
      <a id="my-extension-account-btn" href="javascript:void(0)" title="用户账号">
        <img class="my-extension-account-avatar" src="${chrome.runtime.getURL('image/default-avatar.png')}" alt="用户头像" />
      </a>
      <!-- Title area intentionally left empty -->
    </div>
    <div id="my-extension-rating-section">
      <!-- 三个评分框示例，竖向排列，默认只显示第一个 -->
      <div class="my-extension-rating-box">分数框1</div>
      <div class="my-extension-rating-box">分数框2</div>
      <div class="my-extension-rating-box">分数框3</div>
    </div>
    <div id="my-extension-jd-section" contenteditable="true">JD</div>
    <div id="my-extension-login-section">
      <form id="my-extension-login-form">
        <input type="text" id="login-username" placeholder="用户名或邮箱" required />
        <input type="password" id="login-password" placeholder="密码" required />
        <button type="submit">登录</button>
      </form>
    </div>
    <div class="my-extension-sidebar-content">
      <!-- 这里可以添加其他内容 -->
    </div>
    <button id="my-extension-collapse-btn" title="收起侧边栏">→</button>
  `;
} 