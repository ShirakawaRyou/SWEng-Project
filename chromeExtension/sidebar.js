// sidebar.js
(function() {
  let sidebar;
  const SIDEBAR_WIDTH_VAR = '--my-extension-sidebar-width'; // 定义CSS变量名
  let toggleButton; //新增浮于页面的按钮

  function createToggleButton() {
    if (document.getElementById('my-extension-sidebar-toggle')) return;

    toggleButton = document.createElement('div');
    toggleButton.id = 'my-extension-sidebar-toggle';
    toggleButton.innerHTML = '☰';
    toggleButton.title = '这是一个按钮';
    
    // 将按钮添加到侧边栏中
    if (sidebar) {
      sidebar.appendChild(toggleButton);
    }

    //点击事件
    toggleButton.addEventListener('click', (e) => {
        e.stopPropagation(); // 阻止事件冒泡
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
    sidebar.innerHTML = `
      <div class="my-extension-sidebar-content">
        <h2>侧边栏</h2>
        <p>这是从右侧滑出的侧边栏。</p>
        <p>你可以添加任何 HTML 元素。</p>
      </div>
    `;

    const setupDOMElements = () => {
        if (document.body) {
            document.body.insertBefore(sidebar, document.body.firstChild);
            createToggleButton();
        } else {
            document.addEventListener('DOMContentLoaded', setupDOMElements, { once: true} );
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
  // (可选) 添加日志确认
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

})();