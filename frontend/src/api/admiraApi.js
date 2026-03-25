import axios from 'axios';
import router from '../router';
import { useAuthStore } from '../stores/auth';
import { useToastStore } from '../stores/toast';

// 1. EL ARREGLO ESTÁ AQUÍ: Añadimos /api a la URL base
const admiraApi = axios.create({
    // SOLUCIÓN NUCLEAR PARTE 2
    baseURL: import.meta.env.VITE_API_URL,
    headers: {
        'Bypass-Tunnel-Reminder': 'true' // Por si acaso usas Localtunnel de nuevo
    }
});

// 2. INTERCEPTOR DE PETICIÓN
admiraApi.interceptors.request.use((config) => {
  const token = localStorage.getItem('token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  } else {
    delete config.headers.Authorization;
  }
  return config;
}, (error) => {
  return Promise.reject(error);
});

// 3. INTERCEPTOR DE RESPUESTA
admiraApi.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response && (error.response.status === 401 || error.response.status === 403)) {
      if (router.currentRoute.value.name !== 'Login') {
        const authStore = useAuthStore();
        const toastStore = useToastStore();

        authStore.logout();
        
        toastStore.agregarToast({
          tipo: 'error',
          titulo: 'Sesión Expirada',
          mensaje: 'Tu sesión es inválida o ha caducado. Vuelve a entrar.'
        });

        router.push({ name: 'Login' });
      }
    }
    return Promise.reject(error);
  }
);

export default admiraApi;