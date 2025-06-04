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
  let cachedJdText = '';
  let cachedJdId = null;
  let suggestionCache = {}; // 缓存每个简历的建议
  // 用于追踪当前打开的建议框和对应的简历ID
  let currentSuggestionBox = null;
  let currentSuggestionResumeId = null;

  // 添加简单的 Markdown 渲染函数，支持标题、加粗、斜体、换行
  function renderMarkdown(md) {
    if (!md) return '';
    return md
      .replace(/^### (.*)$/gm, '<h3>$1</h3>')
      .replace(/^## (.*)$/gm, '<h2>$1</h2>')
      .replace(/^# (.*)$/gm, '<h1>$1</h1>')
      .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
      .replace(/\*(.*?)\*/g, '<em>$1</em>')
      .replace(/\n/g, '<br>');
  }

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
      // 显示职位名称
      displayJobTitle();
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
      ratingSectionEl.innerHTML = '<p>Please open a specific job to view ratings</p>';
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
      if (!accessToken) return;
      // 1. 获取页面上的 JD 文本
      const jdText = getLinkedInJD();
      if (!jdText) return;
      // 定义获取简历列表并匹配的函数
      const fetchAndMatch = (jd_id) => {
        console.log('[Sidebar] >>> Sending fetch_resumes');
        chrome.runtime.sendMessage({ action: 'fetch_resumes', accessToken }, resumesRes => {
          console.log('[Sidebar] >>> Received fetch_resumes response');
          console.log('[Sidebar] fetch_resumes response:', resumesRes);
          if (chrome.runtime.lastError || !resumesRes || !resumesRes.success) {
            console.error('获取简历列表失败', resumesRes && resumesRes.error);
            return;
          }
          const resumeIds = resumesRes.resumes.map(r => r.id || r._id || r._id_str || r._id.toString());
          console.log('[Sidebar] resumeIds:', resumeIds);
          // placeholder: 显示rating直到实际得分加载完
          const ratingSection = document.getElementById('my-extension-rating-section');
          ratingSection.innerHTML = '';
          resumesRes.resumes.slice(0, 5).forEach(r => {
            const placeholderBox = document.createElement('div');
            placeholderBox.className = 'my-extension-rating-box';
            placeholderBox.style.position = 'relative';
            placeholderBox.setAttribute('title', 'Get suggestion');
            placeholderBox.style.cursor = 'pointer';
            placeholderBox.innerHTML = `
              <svg viewBox="0 0 36 36" class="circular-chart">
                <path class="circle-bg" d="M18 2.0845
a 15.9155 15.9155 0 1 1 0 31.831
a 15.9155 15.9155 0 1 1 0 -31.831"/>
                <path class="circle" stroke-dasharray="0,100" d="M18 2.0845
a 15.9155 15.9155 0 1 1 0 31.831
a 15.9155 15.9155 0 1 1 0 -31.831"/>
                <text x="18" y="20.35" class="percentage">rating</text>
              </svg>
              <div class="rating-title">${r.title}</div>
            `;
            ratingSection.appendChild(placeholderBox);
          });
          console.log('[Sidebar] >>> Sending match_resumes');
          chrome.runtime.sendMessage({ action: 'match_resumes', accessToken, jd_id, resume_ids: resumeIds }, matchRes => {
            console.log('[Sidebar] >>> Received match_resumes response');
            console.log('[Sidebar] match_resumes response:', matchRes);
            if (chrome.runtime.lastError || !matchRes || !matchRes.success) {
              console.error('匹配简历失败', matchRes && matchRes.error);
              return;
            }
            const results = matchRes.data.match_results;
            // 按 match_score 降序排列
            results.sort((a, b) => b.match_score - a.match_score);
            // 渲染分数框
            const ratingSection = document.getElementById('my-extension-rating-section');
            ratingSection.innerHTML = '';
            results.slice(0, 5).forEach(res => {
              const box = document.createElement('div');
              box.setAttribute('title', 'Get suggestion');
              box.style.cursor = 'pointer';
              box.className = 'my-extension-rating-box';
              box.style.position = 'relative'; // 允许子元素绝对定位
              // 圆形进度图表示匹配得分
              const score = res.match_score;
              const percent = Math.min(Math.max(score, 0), 100);
              const scoreText = score.toFixed(2);
              box.innerHTML = `
                <svg viewBox="0 0 36 36" class="circular-chart">
                  <path class="circle-bg" d="M18 2.0845
a 15.9155 15.9155 0 1 1 0 31.831
a 15.9155 15.9155 0 1 1 0 -31.831"/>
                  <path class="circle" stroke-dasharray="${percent},100" d="M18 2.0845
a 15.9155 15.9155 0 1 1 0 31.831
a 15.9155 15.9155 0 1 1 0 -31.831"/>
                  <text x="18" y="20.35" class="percentage">${scoreText}</text>
                </svg>
                <div class="rating-title">${res.resume_title}</div>
              `;
              // 点击时获取建议并显示
              box.addEventListener('click', event => {
                event.stopPropagation();
                // 切换：如果点击同一个简历，关闭现有建议框
                if (currentSuggestionResumeId === res.resume_id && currentSuggestionBox) {
                  currentSuggestionBox.remove();
                  currentSuggestionBox = null;
                  currentSuggestionResumeId = null;
                  return;
                }
                // 移除旧的建议框（如果存在）
                if (currentSuggestionBox) {
                  currentSuggestionBox.remove();
                }

                // 如果已缓存建议，直接显示并退出
                if (suggestionCache[res.resume_id]) {
                  const suggestionBox = document.createElement('div');
                  suggestionBox.className = 'my-extension-suggestion-box';
                  suggestionBox.innerHTML = renderMarkdown(suggestionCache[res.resume_id]);
                  // 计算视口内固定定位位置
                  const rect = box.getBoundingClientRect();
                  const margin = 10, desiredWidth = 350;
                  // 动态计算宽度，确保不超过可视宽度
                  const width = Math.min(desiredWidth, window.innerWidth - margin * 2);
                  // 计算水平位置，确保在可视范围内
                  const leftPos = Math.min(
                    Math.max(rect.left - width - margin, margin),
                    window.innerWidth - width - margin
                  );
                  suggestionBox.style.position = 'fixed';
                  suggestionBox.style.left = `${leftPos}px`;
                  suggestionBox.style.top = `${rect.top}px`;
                  suggestionBox.style.width = `${width}px`;
                  // 动态计算高度，确保不超出可视高度
                  const availableHeight = window.innerHeight - rect.top - margin;
                  suggestionBox.style.maxHeight = `${availableHeight}px`;
                  suggestionBox.style.overflowY = 'auto';
                  suggestionBox.style.overflowX = 'hidden';
                  suggestionBox.style.background = '#fff';
                  suggestionBox.style.border = '1px solid #ccc';
                  suggestionBox.style.padding = '10px';
                  suggestionBox.style.boxShadow = '0 2px 8px rgba(0,0,0,0.2)';
                  suggestionBox.style.borderRadius = '8px';
                  suggestionBox.style.zIndex = '1000001';
                  document.body.appendChild(suggestionBox);
                  // 记录当前打开的建议框
                  currentSuggestionBox = suggestionBox;
                  currentSuggestionResumeId = res.resume_id;
                  return;
                }

                // 占位提示：正在加载建议
                const suggestionBox = document.createElement('div');
                suggestionBox.className = 'my-extension-suggestion-box';
                suggestionBox.innerText = 'Getting suggestions. Please wait a moment';
                // 计算位置并固定
                const rect2 = box.getBoundingClientRect();
                const margin2 = 10, desiredW = 350;
                const width2 = Math.min(desiredW, window.innerWidth - margin2 * 2);
                const leftPos2 = Math.min(
                  Math.max(rect2.left - width2 - margin2, margin2),
                  window.innerWidth - width2 - margin2
                );
                suggestionBox.style.position = 'fixed';
                suggestionBox.style.left = `${leftPos2}px`;
                suggestionBox.style.top = `${rect2.top}px`;
                suggestionBox.style.width = `${width2}px`;
                const availableHeight2 = window.innerHeight - rect2.top - margin2;
                suggestionBox.style.maxHeight = `${availableHeight2}px`;
                suggestionBox.style.overflowY = 'auto';
                suggestionBox.style.overflowX = 'hidden';
                suggestionBox.style.background = '#fff';
                suggestionBox.style.border = '1px solid #ccc';
                suggestionBox.style.padding = '10px';
                suggestionBox.style.boxShadow = '0 2px 8px rgba(0,0,0,0.2)';
                suggestionBox.style.borderRadius = '8px';
                suggestionBox.style.zIndex = '1000001';
                document.body.appendChild(suggestionBox);
                // 记录当前打开的建议框
                currentSuggestionBox = suggestionBox;
                currentSuggestionResumeId = res.resume_id;
                // 调用后端建议接口
                chrome.runtime.sendMessage({
                  action: 'suggestions',
                  accessToken,
                  jd_id,
                  resume_id: res.resume_id
                }, suggestionRes => {
                  // 更新占位提示为实际建议或错误
                  if (chrome.runtime.lastError || !suggestionRes || !suggestionRes.success) {
                    console.error('获取建议失败', suggestionRes && suggestionRes.error);
                    suggestionBox.innerText = suggestionRes && suggestionRes.error ? suggestionRes.error : 'Failed to get suggestions';
                    return;
                  }
                  // 缓存结果并更新显示
                  suggestionCache[res.resume_id] = suggestionRes.suggestions;
                  suggestionBox.innerHTML = renderMarkdown(suggestionRes.suggestions);
                });
              });
              ratingSection.appendChild(box);
            });
            console.log('[Sidebar] >>> Scores rendered:', results);
          });
        });
      };
      // 如果JD未变化且已缓存，则复用缓存的jd_id
      if (cachedJdText === jdText && cachedJdId) {
        console.log('[Sidebar] >>> Using cached jd_id', cachedJdId);
        fetchAndMatch(cachedJdId);
      } else {
        console.log('[Sidebar] >>> Sending extract_jd_keywords');
        chrome.runtime.sendMessage({ action: 'extract_jd_keywords', jd_text: jdText }, extractRes => {
          if (chrome.runtime.lastError || !extractRes || !extractRes.success) {
            console.error('提取JD关键词失败', extractRes && extractRes.error);
            return;
          }
          cachedJdText = jdText;
          cachedJdId = extractRes.jd_id;
          fetchAndMatch(cachedJdId);
        });
      }
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

  // 获取 LinkedIn 页面中的职位名称
  function getLinkedInJobTitle() {
    // 优先尝试根据 h1 下带 id 的链接获取职位名称
    const linkEl = document.querySelector('h1 a[id]');
    if (linkEl && linkEl.innerText.trim()) return linkEl.innerText.trim();
    // 优先尝试未隐藏的 h1 元素
    const h1Els = document.querySelectorAll('h1');
    for (const el of h1Els) {
      const text = el.innerText.trim();
      if (text && !el.classList.contains('visually-hidden') && el.offsetParent !== null) {
        return text;
      }
    }
    // 回退到 Ember 单行链接
    const aEl = document.querySelector('a.ember-single-line-link');
    if (aEl && aEl.innerText.trim()) return aEl.innerText.trim();
    return '';
  }

  // 将职位名称显示到侧边栏头部，仅当JD存在时才获取，否则显示默认提示
  function displayJobTitle() {
    const jdText = getLinkedInJD();
    const titleEl = document.getElementById('my-extension-job-title');
    if (!titleEl) return;
    if (jdText && jdText.trim().length > 0) {
      const title = getLinkedInJobTitle();
      titleEl.innerText = title || 'cannot find job title';
    } else {
      titleEl.innerText = 'cannot find job title';
    }
  }

  // 将 JD 显示到侧边栏的 JD 区域下方，若未获取到则隐藏
  function displayJobDescription() {
    const jdText = getLinkedInJD();
    const jdSection = document.getElementById('my-extension-jd-section');
    const jdContent = document.getElementById('my-extension-jd-content');
    if (jdSection && jdContent) {
      if (jdText && jdText.length > 0) {
        jdSection.style.display = '';
        jdContent.innerText = jdText;
        jdContent.style.whiteSpace = 'pre-wrap';
      } else {
        jdSection.style.display = 'none';
      }
    }
  }
})();