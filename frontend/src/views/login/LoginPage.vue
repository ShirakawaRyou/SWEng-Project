<template>
  <div class="login-page">
    <div class="login-card">
      <img src="@/assets/logo.png" alt="Logo" class="login-logo" />
      <h2 class="title">Sign in to ResumeAlign</h2>
      <p v-if="currentUser" class="current-user-info">已登录为：{{ currentUser.full_name || currentUser.email }}</p>
      <form @submit.prevent="handleLogin">
        <div class="form-group">
          <label for="username">Username or email address</label>
          <input id="username" v-model="username" type="text" placeholder="Username or email address" required />
        </div>
        <div class="form-group password-group">
          <label for="password">
            <span>Password</span>
          </label>
          <input id="password" v-model="password" type="password" placeholder="Password" required />
        </div>
        <button type="submit">Sign in</button>
      </form>
      <p v-if="errorMessage" class="error">{{ errorMessage }}</p>
      <div class="secondary-card">
        <p>New to ResumeAlign? <router-link to="/register">Create an account</router-link></p>
      </div>
    </div>
  </div>
</template>

<script>
import axios from 'axios'
export default {
  name: 'LoginPage',
  data() {
    return {
      username: '',
      password: '',
      errorMessage: '',
      currentUser: null
    }
  },
  mounted() {
    const userJson = localStorage.getItem('current_user')
    if (userJson) {
      this.currentUser = JSON.parse(userJson)
    }
  },
  methods: {
    async handleLogin() {
      this.errorMessage = ''
      try {
        // 使用 OAuth2 Token 接口登录
        const params = new URLSearchParams()
        params.append('username', this.username)
        params.append('password', this.password)
        const tokenResp = await axios.post(
          '/api/v1/auth/login/token',
          params,
          { headers: { 'Content-Type': 'application/x-www-form-urlencoded' } }
        )
        const accessToken = tokenResp.data.access_token
        // 设置默认请求头
        axios.defaults.headers.common['Authorization'] = `Bearer ${accessToken}`
        // 本地存储 Token
        localStorage.setItem('access_token', accessToken)

        // 获取当前用户信息
        const userResp = await axios.get('/api/v1/auth/users/me')
        // 存储用户信息
        localStorage.setItem('current_user', JSON.stringify(userResp.data))

        // 登录成功，跳转主页面
        this.$router.push('/main')
      } catch (error) {
        console.error('Login error', error)
        if (error.response && error.response.status === 401) {
          this.errorMessage = 'Incorrect username or password'
        } else {
          this.errorMessage = 'Login request failed'
        }
      }
    }
  }
}
</script>

<style scoped>
.login-page {
  display: flex;
  justify-content: center;
  align-items: center;
  min-height: 100vh;
  margin-top: -60px;
  background-color: #f0f2f5;
}
.login-card {
  width: 100%;
  max-width: 400px;
  background: #fff;
  padding: 2rem;
  border-radius: 8px;
  box-shadow: 0 2px 8px rgba(0,0,0,0.1);
}
.login-logo {
  display: block;
  width: 72px;
  margin: 0 auto 1rem;
}
.title {
  text-align: center;
  margin-bottom: 1.5rem;
  font-size: 1.5rem;
  color: #333;
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
  width: 100%;
  padding: 0.5rem;
  border: 1px solid #d1d5da;
  border-radius: 4px;
  font-size: 1rem;
}
.password-group label {
  display: flex;
  justify-content: space-between;
  align-items: center;
}
.forgot-link {
  font-size: 0.875rem;
  color: #0366d6;
  text-decoration: none;
}
.forgot-link:hover {
  text-decoration: underline;
}
.secondary-card {
  margin-top: 1rem;
  padding: 1rem;
  background: #f6f8fa;
  border: 1px solid #e1e4e8;
  border-radius: 6px;
  text-align: center;
}
button {
  width: 100%;
  padding: 0.75rem;
  background-color: #409eff;
  color: #fff;
  font-size: 1rem;
  border: none;
  border-radius: 4px;
  cursor: pointer;
  transition: background-color 0.3s;
}
button:hover {
  background-color: #66b1ff;
}
.error {
  margin-top: 1rem;
  color: red;
  text-align: center;
}
</style> 