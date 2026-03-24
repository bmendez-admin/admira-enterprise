import { createRouter, createWebHistory } from 'vue-router'
import { useAuthStore } from '../stores/auth'
import { useToastStore } from '../stores/toast' // Importamos las alertas

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
    meta: { 
      requiresAuth: true,
      roles: ['ADMIN', 'DIRECTIVO', 'SOPORTE', 'CLIENTE'] // Acceso universal
    }
  },
  {
    path: '/monitoreo',
    name: 'Monitoreo',
    component: () => import('../views/MonitoreoView.vue'),
    meta: { 
      requiresAuth: true,
      roles: ['ADMIN', 'DIRECTIVO', 'SOPORTE', 'CLIENTE'] // Acceso universal
    }
  },
  {
    path: '/reportes',
    name: 'Reportes',
    component: () => import('../views/ReportesView.vue'),
    meta: { 
      requiresAuth: true,
      roles: ['ADMIN', 'DIRECTIVO'] // Nivel gerencial exclusivo
    }
  },
  {
    path: '/configuracion',
    name: 'Configuracion',
    component: () => import('../views/ConfiguracionView.vue'),
    meta: { 
      requiresAuth: true,
      roles: ['ADMIN', 'DIRECTIVO', 'SOPORTE'] // Clientes excluidos
    }
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

// EL CADENERO (Interceptor de Rutas)
router.beforeEach((to, from, next) => {
  const authStore = useAuthStore()
  const estaAutenticado = authStore.isAuthenticated
  const rolUsuario = authStore.usuario?.rol?.toUpperCase() // Extraemos el rol del JWT

  // 1. Protección básica: Si requiere auth y no está logueado -> Al Login
  if (to.meta.requiresAuth && !estaAutenticado) {
    return next({ name: 'Login' })
  } 
  
  // 2. Si ya está logueado y quiere ir al Login -> Al Dashboard
  if (to.name === 'Login' && estaAutenticado) {
    return next({ name: 'Dashboard' })
  } 

  // 3. PROTECCIÓN POR ROLES (RBAC)
  if (to.meta.roles && estaAutenticado) {
    if (!to.meta.roles.includes(rolUsuario)) {
      // Instanciamos el toast aquí adentro para asegurar que Pinia ya cargó
      const toastStore = useToastStore()
      
      toastStore.agregarToast({
        tipo: 'error',
        titulo: 'Acceso Restringido',
        mensaje: 'Tu nivel de usuario no permite acceder a esta sección.'
      })
      
      // Lo regresamos a una zona segura
      return next({ name: 'Dashboard' })
    }
  }

  // 4. Si pasa todos los filtros, lo dejamos pasar
  next()
})

export default router