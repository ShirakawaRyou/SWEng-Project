<template>
  <div class="login-page">
    <h2>登录</h2>
    <form @submit.prevent="handleLogin">
      <div>
        <label for="username">用户名:</label>
        <input id="username" v-model="username" type="text" required />
      </div>
      <div>
        <label for="password">密码:</label>
        <input id="password" v-model="password" type="password" required />
      </div>
      <button type="submit">登录</button>
    </form>
    <p v-if="errorMessage" class="error">{{ errorMessage }}</p>
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
      errorMessage: ''
    }
  },
  methods: {
    async handleLogin() {
      try {
        // TODO: 替换为实际登录 API URL
        const response = await axios.post('LOGIN_API_URL', {
          username: this.username,
          password: this.password
        }, { withCredentials: true })
        if (response.data.success) {
          this.$router.push('/main')
        } else {
          this.errorMessage = response.data.message || '登录失败'
        }
      } catch (error) {
        console.error('登录出错', error)
        this.errorMessage = '登录请求失败'
      }
    }
  }
}
</script>

<style scoped>
.login-page {
  padding: 20px;
}
.error {
  color: red;
}
</style> 