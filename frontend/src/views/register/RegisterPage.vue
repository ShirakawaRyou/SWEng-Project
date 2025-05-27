<template>
  <div class="signup-page">
    <div class="signup-card">
      <h2>Sign up to ResumeAlign</h2>
      <form @submit.prevent="handleRegister">
        <div class="form-group">
          <label for="email">Email*</label>
          <input id="email" v-model="email" type="email" placeholder="Email" required />
        </div>
        <div class="form-group">
          <label for="password">Password*</label>
          <input id="password" v-model="password" type="password" placeholder="Password" required />
        </div>
        <div class="form-group">
          <label for="username">Username*</label>
          <input id="username" v-model="username" type="text" placeholder="Username" required />
        </div>
        <button type="submit">Continue →</button>
      </form>
      <p class="tos-note">
        By creating an account, you agree to the <router-link to="/terms">Terms of Service</router-link>.
      </p>
    </div>
    <div class="signup-footer">
      Already have an account? <router-link to="/login">Sign in →</router-link>
    </div>
  </div>
</template>

<script>
import axios from 'axios';
export default {
  name: 'RegisterPage',
  data() {
    return {
      email: '',
      password: '',
      username: '',
      errorMessage: ''
    }
  },
  methods: {
    async handleRegister() {
      this.errorMessage = '';
      try {
        // 调用后端注册接口
        await axios.post(
          '/api/v1/auth/register',
          { email: this.email, password: this.password, full_name: this.username }
        );
        // 注册成功后跳转登录页
        this.$router.push('/login');
      } catch (error) {
        console.error('Registration error', error);
        this.errorMessage = error.response?.data?.detail || 'Registration failed';
      }
    }
  }
}
</script>

<style scoped>
.signup-page {
  display: flex;
  flex-direction: column;
  justify-content: center;
  align-items: center;
  min-height: 100vh;
  margin-top: -60px;  /* 抵消 App.vue 中的 margin-top */
  background-color: #f6f8fa;
}
.signup-card {
  max-width: 400px;
  margin: 0 auto;
  background: #fff;
  border: 1px solid #e1e4e8;
  border-radius: 6px;
  padding: 2rem;
  box-shadow: 0 1px 3px rgba(27,31,35,0.12);
}
.signup-card h2 {
  margin-bottom: 1.5rem;
  color: #24292e;
  font-size: 1.5rem;
  text-align: center;
}
.form-group {
  display: flex;
  flex-direction: column;
  margin-bottom: 1rem;
}
.form-group label {
  font-weight: 600;
  margin-bottom: 0.5rem;
  color: #24292e;
  text-align: left;
}
.form-group input {
  padding: 0.5rem;
  border: 1px solid #d1d5da;
  border-radius: 4px;
  font-size: 1rem;
}
button {
  width: 100%;
  padding: 0.75rem;
  background-color: #2da44e;
  color: #fff;
  font-size: 1rem;
  border: none;
  border-radius: 6px;
  cursor: pointer;
  transition: background-color 0.2s;
}
button:hover {
  background-color: #2c974b;
}
.tos-note {
  margin-top: 1rem;
  font-size: 0.875rem;
  color: #57606a;
  text-align: center;
}
.tos-note a {
  color: #0969da;
  text-decoration: none;
}
.tos-note a:hover {
  text-decoration: underline;
}
.error {
  margin-top: 1rem;
  color: red;
  text-align: center;
}
.signup-footer {
  text-align: center;
  margin-top: 1rem;
  font-size: 0.875rem;
}
.signup-footer a {
  color: #0969da;
  text-decoration: none;
}
.signup-footer a:hover {
  text-decoration: underline;
}
</style> 