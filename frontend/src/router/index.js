import { createRouter, createWebHistory } from 'vue-router';
import IndexPage from '../views/index/IndexPage.vue';
import LoginPage from '../views/login/LoginPage.vue';
import MainPage from '../views/main/MainPage.vue';
const routes = [
  {
    path: '/login',
    name: 'Login',
    component: LoginPage
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