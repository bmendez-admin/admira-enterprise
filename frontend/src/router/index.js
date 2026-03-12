import { createRouter, createWebHistory } from 'vue-router'

// Importamos la vista principal (Dashboard)
import DashboardView from '../views/DashboardView.vue'

const routes = [
  {
    path: '/',
    name: 'Dashboard',
    component: DashboardView
  },
  {
    path: '/monitoreo',
    name: 'Monitoreo',
    // Carga perezosa (Lazy Loading) para optimizar rendimiento
    component: () => import('../views/MonitoreoView.vue')
  },
  {
    path: '/reportes',
    name: 'Reportes',
    component: () => import('../views/ReportesView.vue')
  }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

export default router