<script setup>
import { ref } from 'vue';
import { useRouter } from 'vue-router';
import {
  LayoutDashboard,
  MonitorSmartphone,
  FileText,
  Settings,
  ChevronDown,
  Globe,
  Layers,
  LogOut,
  X 
} from 'lucide-vue-next';
import { useDashboard } from '../../composables/useDashboard';
import { useAuthStore } from '../../stores/auth';

const { filtros, configInicial, recargarDashboard, menuMovilAbierto } = useDashboard();
const dropdownProyectoAbierto = ref(false);

const router = useRouter();
const authStore = useAuthStore();

const seleccionarProyecto = async (proyecto) => {
  filtros.proyecto = proyecto;
  filtros.pagina = 1;
  dropdownProyectoAbierto.value = false;
  menuMovilAbierto.value = false; // Cerramos el menú en móvil al elegir proyecto
  await recargarDashboard();
};

const cerrarSesion = () => {
  authStore.logout();
  router.push({ name: 'Login' });
};
</script>

<template>
  <div 
    v-if="menuMovilAbierto" 
    @click="menuMovilAbierto = false" 
    class="fixed inset-0 bg-slate-900/60 backdrop-blur-sm z-40 md:hidden transition-opacity"
  ></div>

  <aside 
    :class="[
      'w-72 bg-white h-screen fixed left-0 top-0 border-r border-gray-200 flex flex-col shadow-2xl md:shadow-sm z-50 transition-transform duration-300 ease-in-out',
      menuMovilAbierto ? 'translate-x-0' : '-translate-x-full md:translate-x-0'
    ]"
  >
    <div class="h-20 flex items-center justify-between px-6 border-b border-gray-100">
      <div class="flex items-center">
        <div class="w-10 h-10 bg-admira-500 rounded-xl flex items-center justify-center shadow-md shadow-admira-500/30">
          <svg class="w-6 h-6 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 10V3L4 14h7v7l9-11h-7z" />
          </svg>
        </div>
        <div class="ml-3">
          <h1 class="text-lg font-black text-slate-800 tracking-tight leading-none">ADMIRA</h1>
          <p class="text-[10px] font-bold text-slate-400 uppercase tracking-widest mt-0.5">Enterprise</p>
        </div>
      </div>
      
      <button @click="menuMovilAbierto = false" class="md:hidden p-2 text-slate-400 hover:text-rose-500 rounded-lg">
        <X class="w-6 h-6" />
      </button>
    </div>

    <div class="pt-6 px-6 flex-1 flex flex-col">
      <div class="mb-8 relative z-50">
        <label class="flex items-center text-[10px] font-bold text-slate-400 uppercase tracking-widest mb-3">
          <svg class="w-3.5 h-3.5 mr-1.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
              d="M19 11H5m14 0a2 2 0 012 2v6a2 2 0 01-2 2H5a2 2 0 01-2-2v-6a2 2 0 012-2m14 0V9a2 2 0 00-2-2M5 11V9a2 2 0 002-2m0 0V5a2 2 0 012-2h6a2 2 0 012 2v2M7 7h10">
            </path>
          </svg>
          Proyecto Activo
        </label>

        <div @click="dropdownProyectoAbierto = !dropdownProyectoAbierto"
          class="w-full bg-slate-50 border border-slate-200 hover:border-admira-300 text-slate-700 text-sm font-bold rounded-xl px-4 py-3 flex items-center justify-between transition-all cursor-pointer shadow-sm group">
          <div class="flex items-center gap-2 truncate">
            <Globe v-if="!filtros.proyecto" class="w-4 h-4 text-admira-500" />
            <Layers v-else class="w-4 h-4 text-admira-500" />
            <span class="truncate">{{ filtros.proyecto || 'Todos los Proyectos' }}</span>
          </div>
          <ChevronDown class="w-4 h-4 text-slate-400 transition-transform duration-200"
            :class="{ 'rotate-180': dropdownProyectoAbierto }" />
        </div>

        <div v-if="dropdownProyectoAbierto"
          class="absolute top-full left-0 mt-2 w-full bg-white border border-slate-100 rounded-xl shadow-xl overflow-hidden z-50 animate-in fade-in slide-in-from-top-2 duration-200 max-h-[300px] overflow-y-auto">
          <div @click="seleccionarProyecto('')"
            :class="`px-4 py-3 flex items-center gap-2 text-sm font-bold cursor-pointer transition-colors ${!filtros.proyecto ? 'bg-admira-50 text-admira-700' : 'text-slate-600 hover:bg-slate-50'}`">
            <Globe class="w-4 h-4" :class="!filtros.proyecto ? 'text-admira-600' : 'text-slate-400'" />
            Todos los Proyectos
          </div>

          <div class="h-px bg-slate-50 w-full"></div>

          <div v-for="proy in configInicial.proyectos" :key="proy" @click="seleccionarProyecto(proy)"
            :class="`px-4 py-3 flex items-center gap-2 text-sm font-bold cursor-pointer transition-colors ${filtros.proyecto === proy ? 'bg-admira-50 text-admira-700' : 'text-slate-600 hover:bg-slate-50'}`">
            <Layers class="w-4 h-4" :class="filtros.proyecto === proy ? 'text-admira-600' : 'text-slate-400'" />
            <span class="truncate">{{ proy }}</span>
          </div>
        </div>
        <div v-if="dropdownProyectoAbierto" @click="dropdownProyectoAbierto = false" class="fixed inset-0 z-40"></div>
      </div>

      <nav class="space-y-1.5 flex-1 relative z-10">
        <router-link to="/" @click="menuMovilAbierto = false"
          class="flex items-center px-4 py-3 rounded-xl transition-all group text-slate-500 hover:bg-slate-50"
          active-class="bg-admira-50 text-admira-600 font-bold"
          exact-active-class="bg-admira-50 text-admira-600 font-bold">
          <LayoutDashboard class="w-5 h-5 mr-3" />
          <span class="text-sm">Dashboard</span>
        </router-link>

        <router-link to="/monitoreo" @click="menuMovilAbierto = false"
          class="flex items-center px-4 py-3 rounded-xl text-slate-500 font-semibold hover:bg-slate-50 transition-colors group"
          active-class="bg-admira-50 text-admira-600 font-bold">
          <MonitorSmartphone class="w-5 h-5 mr-3" />
          <span class="text-sm">Monitoreo</span>
        </router-link>

        <router-link to="/reportes" @click="menuMovilAbierto = false"
          class="flex items-center px-4 py-3 rounded-xl text-slate-500 font-semibold hover:bg-slate-50 transition-colors group"
          active-class="bg-admira-50 text-admira-600 font-bold">
          <FileText class="w-5 h-5 mr-3" />
          <span class="text-sm">Reportes</span>
        </router-link>
      </nav>

      <div class="mt-auto pt-6 pb-2">
        <router-link to="/configuracion" @click="menuMovilAbierto = false" class="flex items-center px-4 py-3 rounded-xl text-slate-500 font-semibold hover:bg-slate-50 transition-colors group">
          <Settings class="w-5 h-5 mr-3 group-hover:text-admira-600 transition-colors" />
          <span class="text-sm group-hover:text-admira-600 transition-colors">Configuración</span>
        </router-link>
      </div>
    </div>

    <div class="p-6 border-t border-gray-100 flex justify-between items-center relative z-10 bg-slate-50/50">
      <div class="flex items-center gap-3 overflow-hidden">
        <div class="w-9 h-9 shrink-0 rounded-full bg-admira-100 border border-admira-200 flex items-center justify-center text-xs font-bold text-admira-700">
          {{ authStore.usuario?.nombre?.charAt(0) || 'A' }}
        </div>
        <div class="truncate">
          <p class="text-sm font-bold text-slate-800 leading-none truncate">{{ authStore.usuario?.nombre || 'Administrador' }}</p>
          <p class="text-[10px] text-slate-400 mt-1 truncate">{{ authStore.usuario?.sub || 'admin@admira.com' }}</p>
        </div>
      </div>
      <button @click="cerrarSesion" class="p-2 text-slate-400 hover:text-rose-600 transition-colors rounded-lg hover:bg-rose-50" title="Cerrar Sesión">
        <LogOut class="w-5 h-5" />
      </button>
    </div>
  </aside>
</template>