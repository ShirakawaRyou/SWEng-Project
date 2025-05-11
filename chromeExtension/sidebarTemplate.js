// sidebarTemplate.js

function getSidebarHTML() {
  return `
    <!-- 用户账号按钮：请将 href 替换为实际用户页面 URL -->
    <a id="my-extension-account-btn" href="http://localhost:8080/IndexPage" target="_blank" title="用户账号">账户</a>
    <div id="my-extension-rating-section">
      <!-- 评分区域占位 -->
      <p>评分区域</p>
    </div>
    <div class="my-extension-sidebar-content">
      <h1> Title </h1>
    </div>
    <button id="my-extension-collapse-btn" title="收起侧边栏">→</button>
  `;
} 