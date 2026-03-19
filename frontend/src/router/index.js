import { createRouter, createWebHistory } from 'vue-router'
import { useAuthStore } from '../stores/auth' // <-- 1. Importamos tu almacén de seguridad

// Importamos las vistas principales
import DashboardView from '../views/DashboardView.vue'
import LoginView from '../views/LoginView.vue' // <-- 2. Importamos la nueva vista de Login

const routes = [
  {
    path: '/login',
    name: 'Login',
    component: LoginView // <-- 3. La ruta pública donde nadie necesita token
  },
  {
    path: '/',
    name: 'Dashboard',
    component: DashboardView,
    meta: { requiresAuth: true } // <-- 4. CANDADO: Exige token para entrar
  },
  {
    path: '/monitoreo',
    name: 'Monitoreo',
    // Carga perezosa (Lazy Loading) para optimizar rendimiento
    component: () => import('../views/MonitoreoView.vue'),
    meta: { requiresAuth: true } // <-- CANDADO
  },
  {
    path: '/reportes',
    name: 'Reportes',
    component: () => import('../views/ReportesView.vue'),
    meta: { requiresAuth: true } // <-- CANDADO
  },
  {
    path: '/configuracion',
    name: 'Configuracion',
    component: () => import('../views/ConfiguracionView.vue'),
    meta: { requiresAuth: true } // Protegida por el guardia
  }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

// ==========================================
// EL GUARDIA DE SEGURIDAD INTERCEPTOR
// ==========================================
router.beforeEach((to, from, next) => {
  const authStore = useAuthStore() // Abrimos la caja fuerte de Pinia
  
  // REGLA 1: Si la ruta tiene el candado (requiresAuth) y NO hay token...
  if (to.meta.requiresAuth && !authStore.isAuthenticated) {
    next({ name: 'Login' }) // ...lo rebotamos al Login.
  } 
  // REGLA 2: Si ya tiene token y trata de ir a la página de Login manualmente...
  else if (to.name === 'Login' && authStore.isAuthenticated) {
    next({ name: 'Dashboard' }) // ...lo pasamos directo a su Dashboard.
  } 
  // REGLA 3: Si todo está en orden...
  else {
    next() // ...lo dejamos pasar a donde iba.
  }
})

export default router