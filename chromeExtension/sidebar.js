// sidebar.js
(function() {
  // 动态注入侧边栏样式表和通用样式
  const styleLink1 = document.createElement('link');
  styleLink1.rel = 'stylesheet';
  styleLink1.href = chrome.runtime.getURL('sidebar.css');
  document.head.appendChild(styleLink1);
  const styleLink2 = document.createElement('link');
  styleLink2.rel = 'stylesheet';
  styleLink2.href = chrome.runtime.getURL('styles.css');
  document.head.appendChild(styleLink2);
  // 动态注入 Material Icons 字体
  const iconFontLink = document.createElement('link');
  iconFontLink.rel = 'stylesheet';
  iconFontLink.href = 'https://fonts.googleapis.com/icon?family=Material+Icons';
  document.head.appendChild(iconFontLink);

  // Remove elements that wrongly try to load 'invalid/' to suppress repeated errors
  function removeInvalidResources() {
    ['src','href'].forEach(attr => {
      document.querySelectorAll('[' + attr + '="invalid/"]').forEach(el => {
        el.removeAttribute(attr);
      });
    });
  }
  // Run removal once DOM is ready
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', removeInvalidResources, { once: true });
  } else {
    removeInvalidResources();
  }

  // 设置登录表单提交处理
  function setupLoginForm() {
    const form = document.getElementById('my-extension-login-form');
    if (!form) return;
    form.addEventListener('submit', e => {
      e.preventDefault();
      const username = document.getElementById('login-username').value;
      const password = document.getElementById('login-password').value;
      const params = new URLSearchParams();
      params.append('username', username);
      params.append('password', password);
      fetch('http://localhost:8000/api/v1/auth/login/token', {
        method: 'POST',
        headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
        body: params
      }).then(response => {
        if (response.ok) {
          response.json().then(data => {
            const token = data.access_token;
            // 缓存 accessToken
            chrome.storage.local.set({ accessToken: token }, () => {
              // 获取并缓存用户信息
              fetch('http://localhost:8000/api/v1/auth/users/me', {
                headers: { 'Authorization': `Bearer ${token}` }
              })
              .then(res => res.json())
              .then(user => {
                chrome.storage.local.set({ currentUser: user }, () => {
                  alert('登录成功');
                  toggleSidebar();
                });
              })
              .catch(err => {
                console.error('获取用户信息失败', err);
                alert('登录成功，但无法获取用户信息');
                toggleSidebar();
              });
            });
          });
        } else {
          alert('登录失败，请检查用户名和密码');
        }
      }).catch(err => {
        console.error('登录请求失败', err);
        alert('网络错误，请稍后重试');
      });
    });
  }

  let sidebar;
  const SIDEBAR_WIDTH_VAR = '--my-extension-sidebar-width'; // 定义CSS变量名
  let toggleButton; //新增浮于页面的按钮

  function createToggleButton() {
    if (document.getElementById('my-extension-sidebar-toggle')) return;

    toggleButton = document.createElement('div');
    toggleButton.id = 'my-extension-sidebar-toggle';
    // 确保 material-icons 字体样式可用
    if (!document.getElementById('my-extension-material-icons-style')) {
      const style = document.createElement('style');
      style.id = 'my-extension-material-icons-style';
      style.textContent = `
        @font-face {
          font-family: 'Material Icons';
          font-style: normal;
          font-weight: 400;
          src: url(data:font/woff2;base64,d09GMgABAAAAAAWcABAAAAAA...) format('woff2'); /* 这里请替换为完整的base64字体 */
        }
        .material-icons {
          font-family: 'Material Icons', sans-serif;
          font-weight: normal;
          font-style: normal;
          font-size: 24px;
          line-height: 1;
          letter-spacing: normal;
          text-transform: none;
          display: inline-block;
          white-space: nowrap;
          direction: ltr;
          -webkit-font-feature-settings: 'liga';
          -webkit-font-smoothing: antialiased;
        }
      `;
      document.head.appendChild(style);
    }
    toggleButton.innerHTML = '<span class="material-icons">navigate_before</span>';
    toggleButton.title = '打开侧边栏';

    // 将按钮直接添加到 body
    const insertLogic = () => {
      if (document.body) {
        document.body.appendChild(toggleButton);
      } else {
        document.addEventListener('DOMContentLoaded', insertLogic);
      }
    };
    insertLogic();

    // 点击事件
    toggleButton.addEventListener('click', (e) => {
      e.stopPropagation();
      toggleButton.title = sidebar.classList.contains('my-extension-sidebar-expanded') ? '打开侧边栏' : '关闭侧边栏';
      toggleSidebar();
    });
    // 支持用户拖动 expand 切换按钮
    let isDraggingToggle = false;
    let dragStartX, dragStartY, toggleStartLeft, toggleStartTop;
    toggleButton.addEventListener('mousedown', (e) => {
      isDraggingToggle = true;
      const rect = toggleButton.getBoundingClientRect();
      dragStartX = e.clientX;
      dragStartY = e.clientY;
      toggleStartLeft = rect.left;
      toggleStartTop = rect.top;
      toggleButton.style.cursor = 'grabbing';
      // 清除固定 right/bottom
      toggleButton.style.right = 'auto';
      toggleButton.style.bottom = 'auto';
      toggleButton.style.left = toggleStartLeft + 'px';
      toggleButton.style.top = toggleStartTop + 'px';
      e.preventDefault();
    });
    document.addEventListener('mousemove', (e) => {
      if (!isDraggingToggle) return;
      const dx = e.clientX - dragStartX;
      const dy = e.clientY - dragStartY;
      toggleButton.style.left = (toggleStartLeft + dx) + 'px';
      toggleButton.style.top = (toggleStartTop + dy) + 'px';
    });
    document.addEventListener('mouseup', () => {
      if (isDraggingToggle) {
        isDraggingToggle = false;
        toggleButton.style.cursor = 'grab';
      }
    });
  }

  function createSidebar() {
    let existingSidebar = document.getElementById('my-extension-sidebar');
    if (existingSidebar) {
      sidebar = existingSidebar;
      // 确保CSS变量存在并初始化
      if (!document.documentElement.style.getPropertyValue(SIDEBAR_WIDTH_VAR)) {
        document.documentElement.style.setProperty(SIDEBAR_WIDTH_VAR, `0px`);
      }
      if (!document.getElementById('my-extension-sidebar-toggle')) {
        createToggleButton();
      }
      return sidebar;
    }

    sidebar = document.createElement('div');
    sidebar.id = 'my-extension-sidebar';
    // 使用 sidebarTemplate.js 中的模板
    sidebar.innerHTML = getSidebarHTML();

    const setupDOMElements = () => {
      if (document.body) {
        document.body.insertBefore(sidebar, document.body.firstChild);
        createToggleButton();
        setupLoginForm();  // 初始化登录表单事件
      } else {
        document.addEventListener('DOMContentLoaded', setupDOMElements, { once: true });
      }
    };
    setupDOMElements();

    document.documentElement.style.setProperty(SIDEBAR_WIDTH_VAR, `0px`);
    return sidebar;
  }
    

  function toggleSidebar() {
    if (!sidebar) {
      console.warn("Sidebar element not found, creating it now.");
      createSidebar();
      if (!sidebar) {
        console.error("Failed to create sidebar.");
        return;
      }
    }

    sidebar.classList.toggle('my-extension-sidebar-expanded');
    if (sidebar.classList.contains('my-extension-sidebar-expanded')) {
      checkLoginStatus();
    }
    
    // 直接控制按钮的显示和隐藏
    if (toggleButton) {
      if (sidebar.classList.contains('my-extension-sidebar-expanded')) {
        toggleButton.style.display = 'none';
        // 添加点击事件监听器
        setTimeout(() => {
          document.addEventListener('click', handleClickOutside);
        }, 100);
      } else {
        toggleButton.style.display = 'flex';
        document.removeEventListener('click', handleClickOutside);
      }
    }
  }

  // 处理点击侧边栏外部的事件
  function handleClickOutside(event) {
    // 如果点击的不是侧边栏内部元素
    if (!sidebar.contains(event.target)) {
      sidebar.classList.remove('my-extension-sidebar-expanded');
      if (toggleButton) {
        toggleButton.style.display = 'flex';
      }
      document.removeEventListener('click', handleClickOutside);
    }
  }

  // 脚本加载时立即尝试创建（隐藏的）侧边栏
  sidebar = createSidebar();
  // 初始化时检查登录状态，显示合适的图标或文字
  checkLoginStatus();
  // 新增：为收起按钮添加点击事件
  const collapseBtn = document.getElementById('my-extension-collapse-btn');
  if (collapseBtn) {
    collapseBtn.addEventListener('click', (e) => {
      e.stopPropagation();
      toggleSidebar();
    });
  }
  // 添加日志确认
  if (sidebar) {
    console.log("Right-side sidebar element created on load.");
  } else {
    console.error("Right-side sidebar element NOT created on load.");
  }

  chrome.runtime.onMessage.addListener((request, sender, sendResponse) => {
    if (request.action === "toggle_sidebar") {
      toggleSidebar();
      sendResponse({ status: "Right sidebar toggled by sidebar script" });
      return true;
    }
  });

  // 为账户按钮添加点击事件，根据本地 token 校验后跳转
  const accountBtn = document.getElementById('my-extension-account-btn');
  if (accountBtn) {
    accountBtn.addEventListener('click', (e) => {
      e.preventDefault();
      chrome.storage.local.get(['accessToken'], ({ accessToken }) => {
        if (!accessToken) {
          window.open('http://localhost:8080/login', '_blank');
          return;
        }
        fetch('http://localhost:8000/api/v1/auth/users/me', {
          headers: { 'Authorization': `Bearer ${accessToken}` }
        })
        .then(res => {
          if (res.ok) {
            window.open('http://localhost:8080/main', '_blank');
          } else {
            chrome.storage.local.remove(['accessToken']);
            window.open('http://localhost:8080/login', '_blank');
          }
        })
        .catch(err => {
          console.error('检查登录状态失败', err);
          window.open('http://localhost:8080/login', '_blank');
        });
      });
    });
  }

  // 简化：检查登录状态，仅切换按钮文本
  function checkLoginStatus() {
    const accountBtn = document.getElementById('my-extension-account-btn');
    // 优先从 localStorage 获取 token，保证网页端登录后侧边栏能同步
    const token = window.localStorage.getItem('access_token');
    if (token) {
      accountBtn.textContent = 'Account';
    } else {
      // 若 localStorage 没有，再查扩展存储
      chrome.storage.local.get(['accessToken'], ({ accessToken }) => {
        accountBtn.textContent = accessToken ? 'Account' : 'Login';
      });
    }
  }

  // 注入 SPA 路由监听，确保在 pushState/replaceState/popstate 后自动初始化或重置侧边栏
  (function(history) {
    const pushState = history.pushState;
    history.pushState = function(state, title, url) {
      const ret = pushState.apply(this, arguments);
      window.dispatchEvent(new Event('locationchange'));
      return ret;
    };
    const replaceState = history.replaceState;
    history.replaceState = function(state, title, url) {
      const ret = replaceState.apply(this, arguments);
      window.dispatchEvent(new Event('locationchange'));
      return ret;
    };
  })(window);
  window.addEventListener('popstate', () => window.dispatchEvent(new Event('locationchange')));
  window.addEventListener('locationchange', () => {
    // 路由变化时，如果未注入则创建，否则重置为折叠状态
    if (!document.getElementById('my-extension-sidebar')) {
      createSidebar();
    } else {
      sidebar.classList.remove('my-extension-sidebar-expanded');
      if (toggleButton) toggleButton.style.display = 'flex';
    }
  });

})();