import axios from 'axios';
import router from '../router';
import { useAuthStore } from '../stores/auth';
import { useToastStore } from '../stores/toast';

const admiraApi = axios.create({
    baseURL: import.meta.env.VITE_API_URL,
});

// INTERCEPTOR DE PETICIÓN — adjunta el access token
admiraApi.interceptors.request.use((config) => {
    const token = localStorage.getItem('token');
    if (token) {
        config.headers.Authorization = `Bearer ${token}`;
    } else {
        delete config.headers.Authorization;
    }
    return config;
}, (error) => Promise.reject(error));

// Control para evitar múltiples refreshes simultáneos
let isRefreshing = false;
let failedQueue = [];

const processQueue = (error, token = null) => {
    failedQueue.forEach(prom => {
        if (error) {
            prom.reject(error);
        } else {
            prom.resolve(token);
        }
    });
    failedQueue = [];
};

// INTERCEPTOR DE RESPUESTA — maneja 401 con refresh automático
admiraApi.interceptors.response.use(
    (response) => response,
    async (error) => {
        const originalRequest = error.config;

        if (error.response?.status === 401 && !originalRequest._retry) {
            // Si es el endpoint de refresh o login, no reintentar
            if (originalRequest.url?.includes('/auth/refresh') || originalRequest.url?.includes('/login')) {
                const authStore = useAuthStore();
                const toastStore = useToastStore();
                authStore.logout();
                if (router.currentRoute.value.name !== 'Login') {
                    toastStore.agregarToast({
                        tipo: 'error',
                        titulo: 'Sesión Expirada',
                        mensaje: 'Tu sesión ha caducado. Vuelve a entrar.'
                    });
                    router.push({ name: 'Login' });
                }
                return Promise.reject(error);
            }

            if (isRefreshing) {
                // Encolar peticiones mientras se refresca
                return new Promise((resolve, reject) => {
                    failedQueue.push({ resolve, reject });
                }).then(token => {
                    originalRequest.headers.Authorization = `Bearer ${token}`;
                    return admiraApi(originalRequest);
                }).catch(err => Promise.reject(err));
            }

            originalRequest._retry = true;
            isRefreshing = true;

            const refreshToken = localStorage.getItem('refresh_token');
            if (!refreshToken) {
                isRefreshing = false;
                const authStore = useAuthStore();
                authStore.logout();
                router.push({ name: 'Login' });
                return Promise.reject(error);
            }

            try {
                const response = await axios.post(`${import.meta.env.VITE_API_URL}/auth/refresh`, {
                    refresh_token: refreshToken
                });

                const { access_token, refresh_token: new_refresh } = response.data;
                localStorage.setItem('token', access_token);
                localStorage.setItem('refresh_token', new_refresh);

                admiraApi.defaults.headers.common['Authorization'] = `Bearer ${access_token}`;
                originalRequest.headers.Authorization = `Bearer ${access_token}`;

                processQueue(null, access_token);
                return admiraApi(originalRequest);
            } catch (refreshError) {
                processQueue(refreshError, null);
                const authStore = useAuthStore();
                const toastStore = useToastStore();
                authStore.logout();
                toastStore.agregarToast({
                    tipo: 'error',
                    titulo: 'Sesión Expirada',
                    mensaje: 'Tu sesión ha caducado. Vuelve a entrar.'
                });
                router.push({ name: 'Login' });
                return Promise.reject(refreshError);
            } finally {
                isRefreshing = false;
            }
        }

        if (error.response?.status === 403) {
            const toastStore = useToastStore();
            toastStore.agregarToast({
                tipo: 'error',
                titulo: 'Acceso Denegado',
                mensaje: 'No tienes permiso para realizar esta acción.'
            });
        }

        return Promise.reject(error);
    }
);

export default admiraApi;