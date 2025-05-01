import { createRouter, createWebHistory } from 'vue-router';
import IndexPage from '../views/index/IndexPage.vue';
const routes = [
  {
    path: '/IndexPage',
    name: 'IndexPage',
    component: IndexPage,
  },
];
 
const router = createRouter({
    history: createWebHistory(),
    routes,
  });
  
  export default router;