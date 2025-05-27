<template>
  <div class="terms-page">
    <div class="users-list-container">
      <h2>User List</h2>
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
</template>

<script>
import axios from 'axios';
export default {
  name: 'TermsPage',
  data() {
    return {
      users: [],
      currentPage: 1,
      pageSize: 10,
      error: ''
    };
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
  async created() {
    // 从 localStorage 获取 token 并设置请求头
    const token = localStorage.getItem('access_token');
    if (token) {
      axios.defaults.headers.common['Authorization'] = `Bearer ${token}`;
    } else {
      this.error = 'Please login first';
      return;
    }
    try {
      const resp = await axios.get('/api/v1/auth/users');
      this.users = resp.data;
    } catch (e) {
      console.error('Failed to fetch users', e);
      this.error = 'Failed to load user list';
    }
  },
  methods: {
    prevPage() {
      if (this.currentPage > 1) this.currentPage--;
    },
    nextPage() {
      if (this.currentPage < this.totalPages) this.currentPage++;
    }
  }
};
</script>

<style scoped>
.terms-page {
  display: flex;
  flex-direction: column;
  justify-content: center;
  align-items: center;
  min-height: 100vh;
  margin-top: -60px;
  background-color: #f6f8fa;
}
.users-list-container {
  width: 90%;
  max-width: 600px;
  background: #fff;
  padding: 2rem;
  border-radius: 8px;
  box-shadow: 0 2px 8px rgba(0,0,0,0.1);
}
.users-list-container h2 {
  margin-bottom: 1rem;
  text-align: center;
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