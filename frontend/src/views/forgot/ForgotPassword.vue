<template>
  <div class="forgot-password-page">
    <div class="forgot-password-card">
      <label class="desc-label">
        Enter your user account's verified email address and we will send you a password reset link.
      </label>
      <input class="email-input" type="email" v-model="email" placeholder="Enter your email address" />
      <div class="verify-section">
        <label class="verify-label">Please enter the verification code sent to your email</label>
        <div class="verify-box code-section">
          <input v-model="verificationCode" type="text" class="code-input" placeholder="Please enter the verification code" />
          <button class="send-code-btn" :disabled="!email || codeSent" @click="sendVerificationCode">
            {{ codeSent ? 'Resend in ' + countdown + 's' : 'Send verification code' }}
          </button>
        </div>
        <button class="verify-btn" :disabled="!verificationCode" @click="verifyCode">Verify Code</button>
      </div>
      <button class="send-btn" :disabled="!email">Send password reset email</button>
    </div>
  </div>
</template>

<script>
export default {
  name: 'ForgotPassword',
  data() {
    return {
      email: '',
      verificationCode: '',
      codeSent: false,
      countdown: 60
    }
  },
  methods: {
    async sendVerificationCode() {
      this.codeSent = true;
      this.countdown = 60;
      // TODO: 调用后端接口发送验证码
      const timer = setInterval(() => {
        this.countdown--;
        if (this.countdown <= 0) {
          clearInterval(timer);
          this.codeSent = false;
        }
      }, 1000);
    },
    verifyCode() {
      // TODO: 验证验证码逻辑，例如调用后端验证接口
      console.log('Verifying code:', this.verificationCode);
    }
  }
}
</script>

<style scoped>
.forgot-password-page {
  display: flex;
  justify-content: center;
  align-items: center;
  min-height: 100vh;
  background: #fafbfc;
}
.forgot-password-card {
  width: 100%;
  max-width: 500px;
  background: #fff;
  padding: 2rem;
  border-radius: 8px;
  box-shadow: 0 2px 8px rgba(0,0,0,0.08);
  display: flex;
  flex-direction: column;
  gap: 1.2rem;
}
.desc-label {
  font-size: 1rem;
  color: #222;
  margin-bottom: 0.5rem;
}
.email-input {
  width: 100%;
  padding: 0.5rem;
  border: 1px solid #d1d5da;
  border-radius: 4px;
  font-size: 1rem;
  margin-bottom: 0.5rem;
}
.verify-section {
  margin-top: 0.5rem;
}
.verify-title {
  font-weight: bold;
  margin-bottom: 0.5rem;
}
.verify-box {
  background: #fafbfc;
  border: 1px solid #e1e4e8;
  border-radius: 6px;
  min-height: 180px;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  position: relative;
  margin-bottom: 0.5rem;
}
.verify-content {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 1rem;
}
.verify-tip {
  color: #888;
  margin-bottom: 1rem;
}
.verify-btn {
  padding: 0.5rem 1.5rem;
  border: 1px solid #409eff;
  background: #fff;
  color: #409eff;
  border-radius: 4px;
  cursor: pointer;
  font-size: 1rem;
}
.audio-btn {
  display: flex;
  flex-direction: column;
  align-items: center;
  position: absolute;
  bottom: 10px;
  left: 50%;
  transform: translateX(-50%);
}
.audio-icon {
  font-size: 2rem;
}
.audio-text {
  font-size: 0.9rem;
  color: #222;
}
.send-btn {
  width: 100%;
  padding: 0.75rem;
  background-color: #a5d6a7;
  color: #fff;
  font-size: 1rem;
  border: none;
  border-radius: 4px;
  cursor: pointer;
  transition: background-color 0.3s;
}
.send-btn:disabled {
  background-color: #e0e0e0;
  color: #aaa;
  cursor: not-allowed;
}
/* 验证码输入区样式 */
.verify-label {
  font-weight: 600;
  margin-top: 1rem;
  color: #24292e;
}
.code-input {
  width: 60%;
  padding: 0.5rem;
  border: 1px solid #d1d5da;
  border-radius: 4px;
  font-size: 1rem;
  margin-right: 0.5rem;
}
.send-code-btn {
  padding: 0.5rem 1rem;
  background-color: #409eff;
  color: #fff;
  border: none;
  border-radius: 4px;
  cursor: pointer;
  transition: background-color 0.3s;
}
.send-code-btn:disabled {
  background-color: #e0e0e0;
  color: #aaa;
  cursor: not-allowed;
}
</style> 