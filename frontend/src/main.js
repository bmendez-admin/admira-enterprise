import { createApp } from 'vue'
import './style.css'
import { createPinia } from 'pinia'
import App from './App.vue'
import VueApexCharts from "vue3-apexcharts";
import router from './router'
import axios from 'axios'

// 1. Inicialización Base
const app = createApp(App);
const pinia = createPinia();

app.use(pinia);
app.use(VueApexCharts);
app.use(router);

// Importamos los Stores DESPUÉS de haber inicializado Pinia
import { useAuthStore } from './stores/auth';
import { useToastStore } from './stores/toast';

const authStore = useAuthStore(pinia);
const toastStore = useToastStore(pinia);

// 2. SOLUCIÓN NUCLEAR: Configuración de Axios FORZADA
// Ignoramos el .env y clavamos la URL de Cloudflare directamente
axios.defaults.baseURL = import.meta.env.VITE_API_URL;

app.mount('#app');