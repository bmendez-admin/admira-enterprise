import { createRouter, createWebHistory } from 'vue-router'
import { useAuthStore } from '../stores/auth'

import LoginView from '../views/LoginView.vue'
import DashboardView from '../views/DashboardView.vue'

const routes = [
  {
    path: '/',
    name: 'Login',
    component: LoginView,
    meta: { requiresAuth: false } 
  },
  {
    path: '/dashboard',
    name: 'Dashboard',
    component: DashboardView,
    meta: { requiresAuth: true }
  },
  {
    path: '/monitoreo',
    name: 'Monitoreo',
    component: () => import('../views/MonitoreoView.vue'),
    meta: { requiresAuth: true }
  },
  {
    path: '/reportes',
    name: 'Reportes',
    component: () => import('../views/ReportesView.vue'),
    meta: { requiresAuth: true }
  },
  {
    path: '/configuracion',
    name: 'Configuracion',
    component: () => import('../views/ConfiguracionView.vue'),
    meta: { requiresAuth: true }
  },
  {
    path: '/:pathMatch(.*)*',
    redirect: { name: 'Login' }
  }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

router.beforeEach((to, from, next) => {
  const authStore = useAuthStore()
  const estaAutenticado = authStore.isAuthenticated

  if (to.meta.requiresAuth && !estaAutenticado) {
    next({ name: 'Login' })
  } 
  else if (to.name === 'Login' && estaAutenticado) {
    next({ name: 'Dashboard' })
  } 
  else {
    next()
  }
})

export default router