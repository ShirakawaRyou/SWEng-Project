// sidebar.js
(function() {
  // Remove elements with bad src/href values (invalid, recommended, or unknown protocols)
  function removeInvalidResources() {
    ['src','href'].forEach(attr => {
      document.querySelectorAll(`[${attr}]`).forEach(el => {
        const val = el.getAttribute(attr);
        if (!val) return;
        // 包含 invalid 或 recommended 开头，或协议不是 http(s) 或 chrome-extension
        if (
          val.includes('invalid') ||
          val.startsWith('recommended://') ||
          (/^[a-z]+:\/\//.test(val) && !val.startsWith('http://') && !val.startsWith('https://') && !val.startsWith('chrome-extension://'))
        ) {
          el.removeAttribute(attr);
        }
      });
    });
  }
  // 持续监测并移除后续插入的错误资源
  function observeInvalidResources() {
    const observer = new MutationObserver(removeInvalidResources);
    observer.observe(document.documentElement, { attributes: true, subtree: true, attributeFilter: ['src','href'] });
  }
  // 运行移除和监测
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', () => {
      removeInvalidResources();
      observeInvalidResources();
    }, { once: true });
  } else {
    removeInvalidResources();
    observeInvalidResources();
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
      // 通过后台脚本执行登录，以解决混合内容和 CORS 问题
      chrome.runtime.sendMessage({ action: 'do_login', username, password }, loginRes => {
        console.log('[Sidebar] do_login response:', loginRes);
        if (chrome.runtime.lastError || !loginRes) {
          console.error('Message error:', chrome.runtime.lastError);
          alert('网络错误，请稍后重试');
          return;
        }
        if (loginRes.success) {
          const token = loginRes.accessToken;
          chrome.storage.local.set({ accessToken: token }, () => {
            // 获取并缓存用户信息
            chrome.runtime.sendMessage({ action: 'get_user', accessToken: token }, userRes => {
              console.log('[Sidebar] get_user response:', userRes);
              if (chrome.runtime.lastError || !userRes) {
                console.error('Message error:', chrome.runtime.lastError);
                alert('登录成功，但无法获取用户信息');
                toggleSidebar();
                return;
              }
              if (userRes.success) {
                const user = userRes.user;
                chrome.storage.local.set({ currentUser: user }, () => {
                  console.log('登录成功', user);
                  // 渲染主侧边栏模板
                  const sidebarEl = document.getElementById('my-extension-sidebar');
                  sidebarEl.innerHTML = getSidebarHTML();
                  const ratingSection = sidebarEl.querySelector('#my-extension-rating-section');
                  if (ratingSection) initialRatingHTML = ratingSection.innerHTML;
                  const collapseBtn = sidebarEl.querySelector('#my-extension-collapse-btn');
                  if (collapseBtn) collapseBtn.addEventListener('click', e => { e.stopPropagation(); toggleSidebar(); });
                  checkLoginStatus();
                  updateSidebarMessageBasedOnURL();
                  fetchSidebarData();
                });
              } else {
                console.error('获取用户信息失败', userRes.error);
                alert('登录成功，但无法获取用户信息');
                toggleSidebar();
              }
            });
          });
        } else {
          if (loginRes.error === 'credentials') {
            alert('登录失败，请检查邮箱和密码');
          } else {
            console.error('登录请求失败', loginRes.error);
            alert('网络错误，请稍后重试');
          }
        }
      });
    });
  }

  let sidebar;
  const SIDEBAR_WIDTH_VAR = '--my-extension-sidebar-width'; // 定义CSS变量名
  let toggleButton; //新增浮于页面的按钮
  let initialRatingHTML = '';

  function createToggleButton() {
    if (document.getElementById('my-extension-sidebar-toggle')) return;

    toggleButton = document.createElement('div');
    toggleButton.id = 'my-extension-sidebar-toggle';
    toggleButton.innerHTML = `
      <svg width="24" height="24" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
        <path d="M14 18L8 12L14 6L15.4 7.4L10.8 12L15.4 16.6L14 18Z" fill="#1D1B20"/>
      </svg>
    `;
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
    // 渲染侧边栏模板
    sidebar.innerHTML = getSidebarHTML();

    // 捕获初始评分框 HTML 以便恢复
    const ratingSection = sidebar.querySelector('#my-extension-rating-section');
    if (ratingSection) {
      initialRatingHTML = ratingSection.innerHTML;
    }

    const setupDOMElements = () => {
      if (document.body) {
        document.body.insertBefore(sidebar, document.body.firstChild);
        createToggleButton();
        // 为收起按钮绑定点击事件
        const collapseBtn = document.getElementById('my-extension-collapse-btn');
        if (collapseBtn) {
          collapseBtn.addEventListener('click', e => {
            e.stopPropagation();
            toggleSidebar();
          });
        }
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
      // 展开时先同步前端 localStorage，再更新 UI 和获取数据
      try {
        chrome.runtime.sendMessage({ action: 'open_front_sync' });
      } catch (e) {
        console.error('[Sidebar] open_front_sync exception:', e);
      }
      checkLoginStatus();
      updateSidebarMessageBasedOnURL();
      // 显示页面上的职位描述
      displayJobDescription();
      // 延迟获取简历列表，确保同步完成
      setTimeout(fetchSidebarData, 1500);
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
  checkLoginStatus();
  if (!sidebar) {
    console.error("Right-side sidebar element NOT created on load.");
  }

  chrome.runtime.onMessage.addListener((request, sender, sendResponse) => {
    if (request.action === "toggle_sidebar") {
      toggleSidebar();
      sendResponse({ status: "Right sidebar toggled by sidebar script" });
      return true;
    }
  });

  // 为账户按钮添加点击事件，根据本地 token 校验后跳转（只绑定一次）
  const accountBtn = document.getElementById('my-extension-account-btn');
  if (accountBtn && !accountBtn.dataset.handlerBound) {
    accountBtn.dataset.handlerBound = 'true';
    accountBtn.addEventListener('click', (e) => {
      e.preventDefault();
      chrome.storage.local.get(['accessToken'], ({ accessToken }) => {
        if (!accessToken) {
          window.open('http://localhost:8080/login', '_blank');
          return;
        }
        chrome.runtime.sendMessage({ action: 'get_user', accessToken }, (userRes) => {
          if (chrome.runtime.lastError || !userRes) {
            console.error('Message error:', chrome.runtime.lastError);
            chrome.storage.local.remove(['accessToken']);
            window.open('http://localhost:8080/login', '_blank');
            return;
          }
          if (userRes.success) {
            window.open('http://localhost:8080/main', '_blank');
          } else {
            chrome.storage.local.remove(['accessToken']);
            window.open('http://localhost:8080/login', '_blank');
          }
        });
      });
    });
  }

  // 检查登录状态：始终显示默认头像
  function checkLoginStatus() {
    const accountBtn = document.getElementById('my-extension-account-btn');
    if (!accountBtn) return;
    const avatarUrl = chrome.runtime.getURL('image/default-avatar-icon.png');
    accountBtn.innerHTML = `<div class="my-extension-account-avatar" style="background-image:url('${avatarUrl}')"></div>`;
  }

  // 根据 URL 判断并更新侧边栏主体内容
  function updateSidebarMessageBasedOnURL() {
    const ratingSectionEl = document.getElementById('my-extension-rating-section');
    if (!ratingSectionEl) return;
    const url = window.location.href;
    // 如果不在 jobs/collections 或 jobs/search 页面，显示一行提示文字
    if (!url.startsWith('https://www.linkedin.com/jobs/collections') && !url.startsWith('https://www.linkedin.com/jobs/search')) {
      ratingSectionEl.innerHTML = '<p>请点开具体的职位以查看评分</p>';
    } else {
      // 否则恢复原始评分框内容
      ratingSectionEl.innerHTML = initialRatingHTML;
    }
  }

  // 获取侧边栏数据：用户信息、JD匹配得分等
  function fetchSidebarData() {
    console.log('[Sidebar] >>> fetchSidebarData start');
    chrome.storage.local.get(['accessToken','currentUser'], ({ accessToken, currentUser }) => {
      console.log('[Sidebar] fetchSidebarData accessToken:', accessToken, 'currentUser:', currentUser);
      if (!accessToken) {
        console.warn('未登录，跳过获取数据');
        return;
      }
      // 1. 获取页面上的 JD 文本
      const jdText = getLinkedInJD();
      console.log('[Sidebar] JD 文本：', jdText);
      if (!jdText) {
        console.error('未获取到JD文本，取消匹配');
        return;
      }
      console.log('[Sidebar] >>> Sending extract_jd_keywords');
      // 2. 提取 JD 关键词，获取 jd_id
      chrome.runtime.sendMessage({ action: 'extract_jd_keywords', jd_text: jdText }, extractRes => {
        console.log('[Sidebar] >>> Received extract_jd_keywords response');
        console.log('[Sidebar] extract_jd_keywords response:', extractRes);
        if (chrome.runtime.lastError || !extractRes || !extractRes.success) {
          console.error('提取JD关键词失败', extractRes && extractRes.error);
          return;
        }
        const jd_id = extractRes.jd_id;
        console.log('[Sidebar] >>> Sending fetch_resumes');
        // 3. 获取简历列表
        chrome.runtime.sendMessage({ action: 'fetch_resumes', accessToken }, resumesRes => {
          console.log('[Sidebar] >>> Received fetch_resumes response');
          console.log('[Sidebar] fetch_resumes response:', resumesRes);
          if (chrome.runtime.lastError || !resumesRes || !resumesRes.success) {
            console.error('获取简历列表失败', resumesRes && resumesRes.error);
            return;
          }
          const resumeIds = resumesRes.resumes.map(r => r.id || r._id || r._id_str || r._id.toString());
          console.log('[Sidebar] resumeIds:', resumeIds);
          // 4. 匹配简历得分
          console.log('[Sidebar] >>> Sending match_resumes');
          chrome.runtime.sendMessage({ action: 'match_resumes', accessToken, jd_id, resume_ids: resumeIds }, matchRes => {
            console.log('[Sidebar] >>> Received match_resumes response');
            console.log('[Sidebar] match_resumes response:', matchRes);
            if (chrome.runtime.lastError || !matchRes || !matchRes.success) {
              console.error('匹配简历失败', matchRes && matchRes.error);
              return;
            }
            const results = matchRes.data.match_results;
            // 将得分渲染到评分框
            const ratingBoxes = document.querySelectorAll('#my-extension-rating-section .my-extension-rating-box');
            ratingBoxes.forEach((box, idx) => {
              if (results[idx]) {
                box.innerText = results[idx].match_score.toFixed(2);
              } else {
                box.innerText = 'N/A';
              }
            });
            console.log('[Sidebar] >>> Scores rendered:', results);
          });
        });
      });
    });
  }

  // 注入 SPA 路由监听，确保在 pushState/replaceState/popstate 后自动初始化或重置侧边栏
  (function(history) {
    const pushState = history.pushState;
    history.pushState = function(state, title, url) {
      const ret = pushState.apply(this, arguments);
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

  // 提取 LinkedIn JD 的函数，优先使用精准选择器
  function getLinkedInJD() {
    // 精准匹配：h2.text-heading-large 紧跟 div.mt4 下的 p[dir="ltr"]
    const pElement = document.querySelector('h2.text-heading-large + div.mt4 p[dir="ltr"]');
    if (pElement) {
      console.log('[Sidebar] JD Element found with precise selector');
      return pElement.innerText.trim();
    }
    console.warn('[Sidebar] Precise JD selector did not match, falling back to broader logic');
    // 回退到原先逻辑
    const header = document.querySelector('h2.text-heading-large');
    if (!header) return '';
    const jdContainer = header.nextElementSibling;
    if (!jdContainer || !jdContainer.classList.contains('mt4')) return '';
    const p = jdContainer.querySelector('p[dir="ltr"]');
    if (p) {
      return p.innerText.trim();
    }
    const spans = jdContainer.querySelectorAll('span');
    return Array.from(spans)
      .map(s => s.textContent.trim())
      .filter(t => t.length > 0)
      .join('\n');
  }

  // 将 JD 显示到侧边栏的 JD 区域下方
  function displayJobDescription() {
    const jdText = getLinkedInJD();
    // 调试日志：获取 JD 成功或失败
    if (jdText && jdText.length > 0) {
      console.log('[Sidebar] JD 获取成功');
    } else {
      console.error('[Sidebar] JD 获取失败');
    }
    const jdContent = document.getElementById('my-extension-jd-content');
    if (jdContent) {
      jdContent.innerText = jdText || '未获取到职位描述';
      jdContent.style.whiteSpace = 'pre-wrap';
    }
  }
})();