import { createApp } from 'vue'
import './style.css'
import App from './App.vue'
import VueApexCharts from "vue3-apexcharts";
import router from './router' 

const app = createApp(App);

app.use(VueApexCharts);
app.use(router);

app.mount('#app');