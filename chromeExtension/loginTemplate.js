// loginTemplate.js

function getLoginHTML() {
  return `
    <div class="my-extension-login-card" style="display:flex;flex-direction:column;align-items:center;justify-content:center;height:100%;padding:20px;box-sizing:border-box;">
      <h2>Sign in to RateMyResume</h2>
      <form id="my-extension-login-form">
        <div class="form-group">
          <label for="login-username">Email address</label>
          <input type="text" id="login-username" name="username" placeholder="Email address" required />
        </div>
        <div class="form-group">
          <label for="login-password">Password</label>
          <a href="#" class="forgot-password">Forgot password?</a>
          <input type="password" id="login-password" name="password" placeholder="Password" required />
        </div>
        <button type="submit" class="btn-primary">Sign in</button>
      </form>
      <div class="create-account">
        New to RateMyResume? <a href="#">Create an account</a>
      </div>
    </div>
  `;
} 