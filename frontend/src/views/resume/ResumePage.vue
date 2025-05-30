<template>
  <div class="resume-page">
    <h2>用户简历列表</h2>
    <div class="resume-container">
      <div class="resume-card" v-for="resume in resumes" :key="resume.id">
        <div class="thumbnail">
          <img :src="resume.thumbnail || pdfIcon" alt="Resume Thumbnail" />
        </div>
        <p class="resume-name">{{ resume.name || ('Resume ' + resume.id) }}</p>
        <div class="actions">
          <button @click.stop="downloadResume(resume.id)">下载</button>
          <button @click.stop="previewResume(resume.id)">预览</button>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import axios from 'axios';
import pdfIcon from '@/assets/pdf-icon.png';

export default {
  name: 'ResumePage',
  data() {
    return {
      resumes: [],
      error: '',
      pdfIcon: pdfIcon
    };
  },
  mounted() {
    const token = localStorage.getItem('access_token');
    if (!token) {
      this.$router.push({ name: 'Login' });
      return;
    }
    axios.defaults.headers.common['Authorization'] = `Bearer ${token}`;
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
    }
  }
};
</script>

<style scoped>
.resume-page {
  padding: 20px;
}
.resume-container {
  display: flex;
  flex-wrap: wrap;
  gap: 20px;
}
.resume-card {
  width: 150px;
  border: 1px solid #d1d5da;
  border-radius: 8px;
  padding: 10px;
  background: #fff;
  display: flex;
  flex-direction: column;
  align-items: center;
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
</style> 