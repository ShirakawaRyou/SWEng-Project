// sidebarTemplate.js

function getSidebarHTML() {
  return `
    <div class="my-extension-sidebar-header">
      <a id="my-extension-account-btn" href="javascript:void(0)" title="用户账号">
        登录
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
    <div class="my-extension-sidebar-content">
      <!-- 这里可以添加其他内容 -->
    </div>
    <button id="my-extension-collapse-btn" title="收起侧边栏">
      <svg width="24" height="24" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
        <path d="M12.6 12L8 7.4L9.4 6L15.4 12L9.4 18L8 16.6L12.6 12Z" fill="#1D1B20"/>
      </svg>
    </button>
  `;
} 