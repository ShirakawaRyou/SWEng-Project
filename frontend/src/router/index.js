import { createRouter, createWebHistory } from 'vue-router';
import IndexPage from '../views/index/IndexPage.vue';
import LoginPage from '../views/login/LoginPage.vue';
import MainPage from '../views/main/MainPage.vue';
import RegisterPage from '../views/register/RegisterPage.vue';
import TermsPage from '../views/TermsPage.vue';
const routes = [
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
  
  export default router;