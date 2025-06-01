// sidebarTemplate.js

function getSidebarHTML() {
  return `
    <div class="my-extension-sidebar-header">
      <a id="my-extension-account-btn" href="javascript:void(0)" title="User Account">
        Login
      </a>
      <div id="my-extension-job-title" class="my-extension-job-title">
        Job Title Loading...
      </div>
      <button id="my-extension-collapse-btn" title="Collapse sidebar">
        <svg width="24" height="24" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
          <path d="M12.6 12L8 7.4L9.4 6L15.4 12L9.4 18L8 16.6L12.6 12Z" fill="#1D1B20"/>
        </svg>
      </button>
    </div>
    <div id="my-extension-rating-section">
    </div>
    <div class="my-extension-sidebar-content">
      <div id="my-extension-jd-section">
        <h3 class="my-extension-jd-title">Job Description</h3>
        <div id="my-extension-jd-content" contenteditable="true"></div>
      </div>
    </div>
  `;
} 