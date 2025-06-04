import { createRouter, createWebHistory } from 'vue-router';
import IndexPage from '../views/index/IndexPage.vue';
import LoginPage from '../views/login/LoginPage.vue';
import MainPage from '../views/main/MainPage.vue';
import RegisterPage from '../views/register/RegisterPage.vue';
import TermsPage from '../views/TermsPage.vue';
import ResumePage from '../views/resume/ResumePage.vue';
const routes = [
  { path: '/', redirect: { name: 'Login' } },
  {
    path: '/login',
    name: 'Login',
    component: LoginPage
  },
  {
    path: '/register',
    name: 'Register',
    component: RegisterPage
  },
  {
    path: '/terms',
    name: 'Terms',
    component: TermsPage
  },
  {
    path: '/main',
    name: 'Main',
    component: MainPage
  },
  {
    path: '/resume',
    name: 'Resume',
    component: ResumePage
  },
  {
    path: '/IndexPage',
    name: 'IndexPage',
    component: IndexPage
  },
];
 
const router = createRouter({
    history: createWebHistory(),
    routes,
  });
  
// 导航守卫：检查 token 是否存在及是否过期，并保护需要认证的路由
router.beforeEach((to, from, next) => {
  const token = localStorage.getItem('access_token');
  if (token) {
    let payload;
    try {
      payload = JSON.parse(window.atob(token.split('.')[1]));
    } catch {
      payload = null;
    }
    // 若 token 非法或已过期，清除并跳转登录
    if (!payload || payload.exp * 1000 < Date.now()) {
      localStorage.removeItem('access_token');
      localStorage.removeItem('current_user');
      return next({ name: 'Login' });
    }
  }
  // 已登录用户访问登录页则重定向
  if (to.name === 'Login' && localStorage.getItem('access_token')) {
    return next({ name: 'Main' });
  }
  // 未登录或 token 不存在，禁止访问 Main 和 Resume 页面
  if ((to.name === 'Main' || to.name === 'Resume') && !localStorage.getItem('access_token')) {
    return next({ name: 'Login' });
  }
  next();
});
  
export default router;