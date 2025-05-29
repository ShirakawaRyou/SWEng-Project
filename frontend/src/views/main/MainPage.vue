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
      <div class="resume-card" v-for="resume in resumes" :key="resume.id">
        <div class="thumbnail">
          <img :src="resume.thumbnail || pdfIcon" alt="Resume Thumbnail" />
        </div>
        <p class="resume-name">{{ resume.name || ('Resume ' + resume.id) }}</p>
        <div class="actions">
          <button @click.stop="downloadResume(resume.id)">下载</button>
          <button @click.stop="previewResume(resume.id)">预览</button>
          <button @click.stop="deleteResume(resume.id)">删除</button>
        </div>
      </div>
      <div class="resume-card add-new" @click="goToUpload">
        <div class="plus-icon">+</div>
        <p>添加新简历</p>
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
      error: ''
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
    async fetchResumes() {
      try {
        const resp = await axios.get('/api/v1/resumes/');
        this.resumes = resp.data;
      } catch (e) {
        console.error('无法获取简历列表', e);
        this.error = '无法加载简历';
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
    goToUpload() {
      this.$router.push('/resume/upload');
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
  flex-wrap: wrap;
  gap: 20px;
  padding: 20px;
}
.resume-card {
  width: 150px;
  border: 1px solid #d1d5da;
  border-radius: 8px;
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 10px;
  cursor: pointer;
  background: #fff;
}
.thumbnail img {
  width: 100%;
  height: 100px;
  object-fit: cover;
}
.resume-name {
  margin: 10px 0;
  font-weight: bold;
  text-align: center;
}
.actions {
  display: flex;
  gap: 5px;
}
.actions button {
  padding: 4px 8px;
  font-size: 12px;
}
.resume-card.add-new {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  color: #409eff;
  width: 150px;
  height: 180px;
  border: 1px solid #409eff;
  border-radius: 8px;
}
.plus-icon {
  font-size: 48px;
  line-height: 1;
}
</style> 