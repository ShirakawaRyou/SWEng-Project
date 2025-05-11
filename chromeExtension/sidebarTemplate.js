// sidebarTemplate.js

function getSidebarHTML() {
  return `
    <!-- 用户账号按钮：点击后由脚本根据登录状态动态跳转 -->
    <a id="my-extension-account-btn" href="javascript:void(0)" title="用户账号">账户</a>
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