(function() {
  function syncStorage() {
    try {
      const token = localStorage.getItem('access_token');
      const userJson = localStorage.getItem('current_user');
      if (token) {
        chrome.storage.local.set({ accessToken: token });
      }
      if (userJson) {
        let user;
        try {
          user = JSON.parse(userJson);
        } catch (e) {
          console.error('frontStorageSync: JSON parse error', e);
        }
        if (user) {
          chrome.storage.local.set({ currentUser: user });
        }
      }
    } catch (err) {
      console.error('frontStorageSync error:', err);
    }
  }
  // 初次同步
  syncStorage();
  // 每隔 5 秒同步一次，确保用户信息及时更新
  setInterval(syncStorage, 5000);
})(); 