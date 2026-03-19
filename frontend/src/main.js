import { createApp } from 'vue'
import './style.css'
import { createPinia } from 'pinia'
import App from './App.vue'
import VueApexCharts from "vue3-apexcharts";
import router from './router'
import axios from 'axios' // <-- 1. Importamos a nuestro mensajero

// ==========================================
// CONFIGURACIÓN GLOBAL DE SEGURIDAD (AXIOS)
// ==========================================

// Le decimos a Axios dónde vive tu Backend para no tener que escribir la URL completa cada vez
axios.defaults.baseURL = 'http://127.0.0.1:8000';

// EL INTERCEPTOR "ANTI-AMNESIA"
// Antes de que Vue mande cualquier petición a FastAPI, este policía la revisa.
// Si encuentra el Token en la memoria del navegador, se lo pega a la mochila (Headers).
axios.interceptors.request.use((config) => {
  const token = localStorage.getItem('token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
}, (error) => {
  return Promise.reject(error);
});

// ==========================================
// INICIALIZACIÓN DE VUE
// ==========================================
const app = createApp(App);

app.use(createPinia());
app.use(VueApexCharts); // Tus gráficas siguen intactas y funcionando
app.use(router);

app.mount('#app');