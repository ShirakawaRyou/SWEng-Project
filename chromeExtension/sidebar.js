// sidebar.js
(function() {
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
      fetch('http://localhost:8000/api/v1/auth/login', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        credentials: 'include',
        body: JSON.stringify({ username, password })
      }).then(response => {
        if (response.ok) {
          alert('登录成功');
          // 可在此关闭侧边栏或更新状态
          toggleSidebar();
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
    toggleButton.innerHTML = '⚡'; // 使用闪电图标，你也可以换成其他图标
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

    //点击事件
    toggleButton.addEventListener('click', (e) => {
      e.stopPropagation(); // 阻止事件冒泡
      toggleButton.title = sidebar.classList.contains('my-extension-sidebar-expanded') ? '打开侧边栏' : '关闭侧边栏';
      toggleSidebar();
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

  // 为账户按钮添加点击事件，根据登录状态动态跳转
  const accountBtn = document.getElementById('my-extension-account-btn');
  if (accountBtn) {
    accountBtn.addEventListener('click', (e) => {
      console.log("点击了账户按钮");
      e.preventDefault();
      // 检查登录状态：已登录跳转到主页面 /main，未登录跳转到登录页 /login
      fetch('http://localhost:8000/api/v1/auth/users/me', { credentials: 'include' })
        .then(response => {
          if (response.ok) {
            window.open('http://localhost:8080/main', '_blank');
          } else {
            window.open('http://localhost:8080/login', '_blank');
          }
        })
        .catch(error => console.error('检查登录状态失败', error));
    });
  }

})();