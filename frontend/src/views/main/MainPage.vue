<template>
  <div class="main-page">
    <h2>欢迎来到主页面</h2>
    <div v-if="currentUser">
      <p class="current-user-info">账号名称：{{ currentUser.full_name || currentUser.email.split('@')[0] }}</p>
      <p class="current-user-info">邮箱：{{ currentUser.email }}</p>
      <button class="logout-button" @click="handleLogout">退出登录</button>
      <div class="users-list-container">
        <h2>用户列表</h2>
        <table>
          <thead>
            <tr><th>Email</th><th>Full Name</th><th>Active</th></tr>
          </thead>
          <tbody>
            <tr v-for="user in paginatedUsers" :key="user.id">
              <td>{{ user.email }}</td>
              <td>{{ user.full_name }}</td>
              <td>{{ user.is_active }}</td>
            </tr>
          </tbody>
        </table>
        <div class="pagination">
          <button @click="prevPage" :disabled="currentPage === 1">Previous</button>
          <span>Page {{ currentPage }} / {{ totalPages }}</span>
          <button @click="nextPage" :disabled="currentPage === totalPages">Next</button>
        </div>
        <p v-if="error" class="error">{{ error }}</p>
      </div>
    </div>
    <p v-else>未检测到登录用户。</p>
  </div>
</template>

<script>
import axios from 'axios';
export default {
  name: 'MainPage',
  data() {
    return {
      currentUser: null,
      users: [],
      currentPage: 1,
      pageSize: 10,
      error: ''
    }
  },
  mounted() {
    const userJson = localStorage.getItem('current_user');
    if (userJson) {
      this.currentUser = JSON.parse(userJson);
    }
    if (this.currentUser) {
      this.fetchUsers();
    }
  },
  computed: {
    paginatedUsers() {
      const start = (this.currentPage - 1) * this.pageSize;
      return this.users.slice(start, start + this.pageSize);
    },
    totalPages() {
      return Math.max(Math.ceil(this.users.length / this.pageSize), 1);
    }
  },
  methods: {
    handleLogout() {
      localStorage.removeItem('access_token');
      localStorage.removeItem('current_user');
      this.$router.push({ name: 'Login' });
    },
    prevPage() {
      if (this.currentPage > 1) this.currentPage--;
    },
    nextPage() {
      if (this.currentPage < this.totalPages) this.currentPage++;
    },
    async fetchUsers() {
      const token = localStorage.getItem('access_token');
      if (token) {
        axios.defaults.headers.common['Authorization'] = `Bearer ${token}`;
      } else {
        this.error = '请先登录';
        return;
      }
      try {
        const resp = await axios.get('/api/v1/auth/users');
        this.users = resp.data;
      } catch (e) {
        console.error('Failed to fetch users', e);
        this.error = '无法加载用户列表';
      }
    }
  }
}
</script>

<style scoped>
.main-page {
  padding: 20px;
}

.current-user-info {
  margin: 5px 0;
  font-weight: bold;
}

.logout-button {
  margin-top: 10px;
  padding: 0.5rem 1rem;
  border: none;
  background-color: #f56c6c;
  color: white;
  border-radius: 4px;
  cursor: pointer;
}

.logout-button:hover {
  background-color: #dd6161;
}

.users-list-container {
  margin-top: 20px;
  background: #fff;
  padding: 1rem;
  border-radius: 8px;
  box-shadow: 0 2px 8px rgba(0,0,0,0.1);
}

.users-list-container h2 {
  margin-bottom: 1rem;
  color: #24292e;
}

table {
  width: 100%;
  border-collapse: collapse;
  margin-bottom: 1rem;
}

thead th {
  text-align: left;
  border-bottom: 2px solid #e1e4e8;
  padding: 0.5rem;
  color: #0366d6;
}

tbody td {
  border-bottom: 1px solid #e1e4e8;
  padding: 0.5rem;
  color: #24292e;
}

.pagination {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.pagination button {
  padding: 0.5rem 1rem;
  background: #0366d6;
  color: #fff;
  border: none;
  border-radius: 4px;
  cursor: pointer;
}

.pagination button:disabled {
  background: #a0a0a0;
  cursor: not-allowed;
}

.pagination span {
  color: #24292e;
}

.error {
  margin-top: 1rem;
  color: red;
  text-align: center;
}
</style> 