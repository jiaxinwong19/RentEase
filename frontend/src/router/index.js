// 📁 src/router/index.js
import { createRouter, createWebHistory } from 'vue-router';
import Login from '../pages/Login.vue'
import Signup from '../pages/Signup.vue'
import RentalStore from '../pages/RentalStore.vue';
import DamageReportPage from '../pages/DamageReportPage.vue'
import Orders from '../pages/Orders.vue'
import UserOrders from '../pages/UserOrders.vue'
import ProfilePage from '../pages/ProfilePage.vue';

const routes = [
  {
    path: '/',
    redirect: '/rental-store'
  },
  {
    path: '/login',
    name: 'Login',
    component: Login,
    meta: { requiresAuth: false }
  },
  {
    path: '/signup',
    name: 'Signup',
    component: Signup,
    meta: { requiresAuth: false }
  },
  {
    path: '/rental-store',
    name: 'RentalStore',
    component: RentalStore,
    meta: { requiresAuth: true }
  },
  {
    path: '/damage-report',
    name: 'DamageReport',
    component: DamageReportPage,
    meta: { requiresAuth: true }
  },
  {
    path: '/orders',
    name: 'Orders',
    component: Orders,
    meta: { requiresAuth: true }
  },
  {
    path: '/user-orders',
    name: 'UserOrders',
    component: UserOrders,
    meta: { requiresAuth: true }
  },
  {
  path: '/profile',
  name: 'Profile',
  component: ProfilePage,
  meta: { requiresAuth: true }
}
];

const router = createRouter({
  history: createWebHistory(),
  routes,
});

// Navigation guard
router.beforeEach((to, from, next) => {
  const isAuthenticated = localStorage.getItem('isAuthenticated') === 'true'
  
  if (to.meta.requiresAuth && !isAuthenticated) {
    next('/login')
  } else if (!to.meta.requiresAuth && isAuthenticated && (to.path === '/login' || to.path === '/signup')) {
    next('/rental-store')
  } else {
    next()
  }
})

export default router;
