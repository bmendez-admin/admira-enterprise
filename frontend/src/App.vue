<script setup>
import { onMounted } from 'vue';
import { useAuthStore } from './stores/auth'; // <-- Inyectamos a nuestro guardia
import Sidebar from './components/layout/Sidebar.vue';
import Header from './components/layout/Header.vue';
import { useDashboard } from './composables/useDashboard';
import Toast from './components/ui/Toast.vue';

const { cargarConfiguracion, recargarDashboard } = useDashboard();
const authStore = useAuthStore(); // Iniciamos el almacén

onMounted(async () => {
  // REGLA DE ORO: Solo intentamos descargar datos si el usuario ya tiene su pulsera VIP
  if (authStore.isAuthenticated) {
    await cargarConfiguracion();
    await recargarDashboard();
  }
});
</script>

<template>
  <div class="flex min-h-screen bg-[#F8FAFC] font-sans text-slate-900">
    <Sidebar v-if="$route.name !== 'Login'" />
    <main :class="['flex-1 w-full flex flex-col', $route.name !== 'Login' ? 'ml-72 p-8' : '']">
      <Header v-if="$route.name !== 'Login'" />
      <router-view />
    </main>
    <Toast /> 
  </div>
</template>