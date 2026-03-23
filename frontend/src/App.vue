<script setup>
import { onMounted } from 'vue';
import { useAuthStore } from './stores/auth';
import Sidebar from './components/layout/Sidebar.vue';
import Header from './components/layout/Header.vue';
import { useDashboard } from './composables/useDashboard';
import Toast from './components/ui/Toast.vue';

const { cargarConfiguracion, recargarDashboard } = useDashboard();
const authStore = useAuthStore();

onMounted(async () => {
  if (authStore.isAuthenticated) {
    await cargarConfiguracion();
    await recargarDashboard();
  }
});
</script>

<template>
  <div class="flex min-h-screen bg-[#F8FAFC] font-sans text-slate-900 overflow-x-hidden">
    <Sidebar v-if="$route.name !== 'Login'" />
    <main :class="['flex-1 w-full flex flex-col min-w-0 transition-all duration-300', $route.name !== 'Login' ? 'md:ml-72 p-4 md:p-8' : '']">
      <Header v-if="$route.name !== 'Login'" />
      <router-view />
    </main>
    <Toast /> 
  </div>
</template>