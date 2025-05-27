import { createRouter, createWebHistory } from 'vue-router';
import IndexPage from '../views/index/IndexPage.vue';
import LoginPage from '../views/login/LoginPage.vue';
import MainPage from '../views/main/MainPage.vue';
import RegisterPage from '../views/register/RegisterPage.vue';
import TermsPage from '../views/TermsPage.vue';
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
    path: '/IndexPage',
    name: 'IndexPage',
    component: IndexPage
  },
];
 
const router = createRouter({
    history: createWebHistory(),
    routes,
  });
  
// 导航守卫：已登录用户无法访问登录页，未登录用户无法访问主页面
router.beforeEach((to, from, next) => {
  const accessToken = localStorage.getItem('access_token');
  if (to.name === 'Login' && accessToken) {
    return next({ name: 'Main' });
  } else if (to.name === 'Main' && !accessToken) {
    return next({ name: 'Login' });
  }
  next();
});
  
export default router;