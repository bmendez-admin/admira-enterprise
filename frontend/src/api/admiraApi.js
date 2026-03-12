import axios from 'axios';

// Instancia centralizada para conectarnos a tu FastAPI
const admiraApi = axios.create({
    baseURL: 'http://127.0.0.1:8000/api',
    headers: {
        'Content-Type': 'application/json'
    }
});

// Interceptor para atrapar errores en la consola y no romper la app
admiraApi.interceptors.response.use(
    response => response,
    error => {
        console.error('Error en la API:', error.response?.data || error.message);
        return Promise.reject(error);
    }
);

export default admiraApi;