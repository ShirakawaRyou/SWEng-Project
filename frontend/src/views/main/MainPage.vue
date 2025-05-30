<template>
  <div class="main-page">
    <div class="sidebar">
      <div class="personal-info" v-if="currentUser">
        <h3>个人信息</h3>
        <p>账号名称：{{ currentUser.full_name || currentUser.email }}</p>
        <p>邮箱：{{ currentUser.email }}</p>
      </div>
    </div>
    <div class="resume-container">
      <!-- 顶部栏 -->
      <div class="resume-header">
        <h2>Resume Library</h2>
        <span class="menu-icon" @click="toggleHeaderMenu">⋮</span>
        <div v-if="showHeaderMenu" class="header-menu">
          <div class="menu-item" @click="startMultiSelect">多选</div>
        </div>
      </div>
      <!-- 网格布局 -->
      <div class="resume-grid">
        <input type="file" ref="fileInput" style="display:none" @change="handleFileChange" />
        <div class="resume-item" v-for="resume in resumes" :key="resume.id">
          <div class="resume-card">
            <img :src="getThumbnail(resume.thumbnail)" alt="Resume Thumbnail" />
          </div>
          <p class="resume-title">{{ resume.title }}</p>
          <div class="actions">
            <span class="download-icon" @click.stop="downloadResume(resume.id)" data-tooltip="download">
              <svg width="24" height="24" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                <path d="M12 16L7 11L8.4 9.55L11 12.15V4H13V12.15L15.6 9.55L17 11L12 16ZM6 20C5.45 20 4.97917 19.8042 4.5875 19.4125C4.19583 19.0208 4 18.55 4 18V15H6V18H18V15H20V18C20 18.55 19.8042 19.0208 19.4125 19.4125C19.0208 19.8042 18.55 20 18 20H6Z" fill="#1D1B20"/>
              </svg>
            </span>
            <span class="preview-icon" @click.stop="previewResume(resume.id)" data-tooltip="preview">
              <svg width="24" height="24" viewBox="0 0 48 48" fill="none" xmlns="http://www.w3.org/2000/svg">
                <path d="M24 32V24M24 16H24.02M44 24C44 35.0457 35.0457 44 24 44C12.9543 44 4 35.0457 4 24C4 12.9543 12.9543 4 24 4C35.0457 4 44 12.9543 44 24Z" stroke="#1E1E1E" stroke-width="4" stroke-linecap="round" stroke-linejoin="round"/>
              </svg>
            </span>
            <span class="delete-icon" @click.stop="deleteResume(resume.id)" data-tooltip="delete">
              <svg width="24" height="24" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                <path d="M7 21C6.45 21 5.97917 20.8042 5.5875 20.4125C5.19583 20.0208 5 19.55 5 19V6H4V4H9V3H15V4H20V6H19V19C19 19.55 18.8042 20.0208 18.4125 20.4125C18.0208 20.8042 17.55 21 17 21H7ZM17 6H7V19H17V6ZM9 17H11V8H9V17ZM13 17H15V8H13V17Z" fill="#1D1B20"/>
              </svg>
            </span>
          </div>
        </div>
        <div class="resume-item add-new-item" @click="triggerFileUpload">
          <div class="resume-card add-new">
            <div class="plus-icon">+</div>
          </div>
          <p class="resume-title add-new-text">添加新简历</p>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import axios from 'axios';
// eslint-disable-next-line no-unused-vars
import pdfIcon from '@/assets/pdf-icon.png';
export default {
  name: 'MainPage',
  data() {
    return {
      currentUser: null,
      resumes: [],
      error: '',
      showHeaderMenu: false,
      multiSelectMode: false
    };
  },
  mounted() {
    // 设置认证头~
    const token = localStorage.getItem('access_token');
    if (!token) {
      this.error = '请先登录';
      this.$router.push({ name: 'Login' });
      return;
    }
    axios.defaults.headers.common['Authorization'] = `Bearer ${token}`;
    // 获取当前用户信息
    const userJson = localStorage.getItem('current_user');
    if (userJson) this.currentUser = JSON.parse(userJson);
    // 获取简历列表
    this.fetchResumes();
  },
  methods: {
    toggleHeaderMenu() {
      this.showHeaderMenu = !this.showHeaderMenu;
    },
    startMultiSelect() {
      this.multiSelectMode = true;
      this.showHeaderMenu = false;
    },
    triggerFileUpload() {
      this.$refs.fileInput.click();
    },
    formatRelativeTime(timestamp) {
      if (!timestamp) return '';
      const diff = Date.now() - new Date(timestamp).getTime();
      const days = Math.floor(diff / (1000 * 60 * 60 * 24));
      if (days === 0) return 'today';
      if (days === 1) return 'yesterday';
      return days + ' days ago';
    },
    async fetchResumes() {
      try {
        const resp = await axios.get('/api/v1/resumes/');
        this.resumes = resp.data;
      } catch (e) {
        console.error('无法获取简历列表', e);
        this.error = '无法加载简历';
      }
    },
    async handleFileChange(event) {
      const file = event.target.files[0];
      if (!file) return;
      const formData = new FormData();
      formData.append('file', file);
      try {
        const resp = await axios.post('/api/v1/resumes/upload', formData, {
          headers: { 'Content-Type': 'multipart/form-data' }
        });
        this.resumes.push(resp.data);
      } catch (e) {
        console.error('上传失败', e);
      } finally {
        event.target.value = '';
      }
    },
    downloadResume(id) {
      axios.get(`/api/v1/resumes/${id}`, { responseType: 'blob' })
        .then(res => {
          const url = window.URL.createObjectURL(new Blob([res.data]));
          const link = document.createElement('a');
          link.href = url;
          link.setAttribute('download', `${id}.pdf`);
          document.body.appendChild(link);
          link.click();
          link.remove();
        });
    },
    previewResume(id) {
      window.open(`/api/v1/resumes/${id}`, '_blank');
    },
    async deleteResume(id) {
      try {
        await axios.delete(`/api/v1/resumes/${id}`);
        this.resumes = this.resumes.filter(r => r.id !== id);
      } catch (e) {
        console.error('删除失败', e);
      }
    },
    getThumbnail(src) {
      return src || pdfIcon;
    }
  }
};
</script>

<style scoped>
.main-page {
  display: flex;
  width: 100%;
  min-height: 100vh;
}
.sidebar {
  width: 20%;
  border-right: 1px solid #e1e4e8;
  padding: 20px;
}
.personal-info h3 {
  margin-bottom: 10px;
}
.resume-container {
  width: 80%;
  display: flex;
  flex-direction: column;
  background: #fff;
}
.resume-header {
  position: relative;
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 20px;
  border-bottom: 1px solid #e1e4e8;
}
.resume-header h2 {
  margin: 0;
  font-size: 24px;
}
.menu-icon {
  font-size: 20px;
  cursor: pointer;
}
.header-menu {
  position: absolute;
  top: 100%;
  right: 0;
  background: #fff;
  border: 1px solid #d1d5da;
  border-radius: 4px;
  box-shadow: 0 2px 8px rgba(0,0,0,0.1);
  overflow: hidden;
}
.header-menu .menu-item {
  padding: 8px 16px;
  cursor: pointer;
}
.header-menu .menu-item:hover {
  background: #f5f5f5;
}
.resume-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(165px, 1fr));
  gap: 20px;
  padding: 20px;
}
.resume-item {
  display: flex;
  flex-direction: column;
  align-items: center;
}
.resume-card {
  width: 165px;
  height: 220px;
  border-radius: 8px;
  background: none;
  display: flex;
  align-items: center;
  justify-content: center;
  overflow: hidden;
}
.resume-card img {
  width: 100%;
  height: 100%;
  object-fit: contain;
}
.resume-title {
  margin: 8px 0 4px;
  font-weight: bold;
  width: 100%;
  text-align: center;
}
.resume-updated {
  margin: 0;
  font-size: 12px;
  color: #666;
}
.add-new-item .resume-card {
  background: #fff;
  border: 1px solid #409eff;
}
.add-new-text {
  color: #409eff;
}
.actions {
  display: flex;
  justify-content: space-between;
  align-items: center;
  width: 120px;
  margin: 8px auto 0;
}
.actions button {
  padding: 4px 8px;
  font-size: 12px;
  cursor: pointer;
}
.actions span { position: relative; }
.actions span[data-tooltip]:hover::after {
  content: attr(data-tooltip);
  position: absolute;
  bottom: calc(100% + 4px);
  left: 50%;
  transform: translateX(-50%);
  background: rgba(0,0,0,0.75);
  color: #fff;
  padding: 4px 8px;
  border-radius: 4px;
  font-size: 12px;
  white-space: nowrap;
  z-index: 10;
}
.download-icon {
  position: relative;
  width: 24px;
  height: 24px;
  cursor: pointer;
}
.preview-icon {
  position: relative;
  width: 24px;
  height: 24px;
  cursor: pointer;
  display: inline-block;
}
.delete-icon {
  position: relative;
  width: 24px;
  height: 24px;
  cursor: pointer;
  display: inline-block;
}
</style> 