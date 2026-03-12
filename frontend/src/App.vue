<script setup>
import { onMounted } from 'vue';
import Sidebar from './components/layout/Sidebar.vue';
import Header from './components/layout/Header.vue';
import { useDashboard } from './composables/useDashboard';

const { cargarConfiguracion, recargarDashboard } = useDashboard();

onMounted(async () => {
  await cargarConfiguracion();
  await recargarDashboard();
});
</script>

<template>
  <div class="flex min-h-screen bg-[#F8FAFC] font-sans text-slate-900">
    <Sidebar />
    <main class="flex-1 ml-72 p-8 w-full flex flex-col">
      <Header />
      <router-view />
    </main>
  </div>
</template>