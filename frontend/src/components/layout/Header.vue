<script setup>
import { Calendar, RefreshCcw, Database } from 'lucide-vue-next';
import { useDashboard } from '../../composables/useDashboard';
import {VueDatePicker} from '@vuepic/vue-datepicker';
import '@vuepic/vue-datepicker/dist/main.css';


const { filtros, cargando, recargarDashboard, sincronizarBaseDeDatos, resetFiltros } = useDashboard();

const actualizarFechas = async () => {
    filtros.pagina = 1; 
    await recargarDashboard();
};
</script>

<template>
  <header class="flex flex-col md:flex-row justify-between items-start md:items-end mb-8 gap-4 bg-white p-6 rounded-2xl border border-gray-200 shadow-sm relative z-50">
    
    <div>
      <div class="flex items-center gap-2 mb-1.5">
        <span class="relative flex h-2 w-2">
          <span class="animate-ping absolute inline-flex h-full w-full rounded-full bg-admira-400 opacity-75"></span>
          <span class="relative inline-flex rounded-full h-2 w-2 bg-admira-500"></span>
        </span>
        <p class="text-[11px] font-bold text-slate-400 uppercase tracking-widest">Sistema Operativo</p>
      </div>
      <h2 class="text-2xl font-extrabold text-slate-800 tracking-tight">Centro de Control</h2>
      
      <div class="flex items-center gap-2 mt-2">
        <span class="text-sm text-slate-500">Proyecto:</span>
        <span class="px-2.5 py-0.5 rounded-md bg-admira-50 text-admira-600 text-xs font-bold uppercase border border-admira-100">
          {{ filtros.proyecto || 'Global' }}
        </span>
        <span v-if="filtros.estado" class="px-2.5 py-0.5 rounded-md bg-rose-50 text-rose-700 text-xs font-bold uppercase border border-rose-100">
          Filtro: Caídos
        </span>
      </div>
    </div>
    
    <div class="flex items-center gap-3">
      
      <div class="flex items-center bg-slate-50 border border-gray-200 rounded-xl px-4 py-2 hover:bg-white hover:border-admira-300 transition-all shadow-sm h-[42px]">
          <Calendar class="w-4 h-4 text-admira-500 mr-2" />
          
          <VueDatePicker 
              v-model="filtros.fechaInicio" 
              model-type="yyyy-MM-dd"
              :enable-time-picker="false"
              auto-apply
              :clearable="false"
              @update:model-value="actualizarFechas"
          >
              <template #trigger>
                  <button class="text-xs font-bold text-slate-700 hover:text-admira-600 transition-colors outline-none tracking-wide">
                      {{ filtros.fechaInicio }}
                  </button>
              </template>
          </VueDatePicker>

          <span class="text-slate-300 mx-3 text-[10px]">➜</span>

          <VueDatePicker 
              v-model="filtros.fechaFin" 
              model-type="yyyy-MM-dd"
              :enable-time-picker="false"
              auto-apply
              :clearable="false"
              @update:model-value="actualizarFechas"
          >
              <template #trigger>
                  <button class="text-xs font-bold text-slate-700 hover:text-admira-600 transition-colors outline-none tracking-wide">
                      {{ filtros.fechaFin }}
                  </button>
              </template>
          </VueDatePicker>
      </div>
      
      <button 
        @click="resetFiltros"
        class="p-2.5 bg-white border border-gray-200 rounded-xl text-slate-500 hover:text-admira-600 hover:border-admira-300 hover:bg-admira-50 transition-all shadow-sm active:scale-95 flex items-center justify-center h-[42px] w-[42px]"
        title="Restaurar a fechas por defecto"
        :disabled="cargando"
      >
        <RefreshCcw class="w-4 h-4" :class="{ 'animate-spin text-admira-600': cargando }" />
      </button>
      
      <button 
        @click="sincronizarBaseDeDatos" 
        class="px-4 py-2 bg-admira-500 text-white rounded-xl font-bold text-xs hover:bg-admira-600 transition-colors shadow-sm shadow-admira-500/30 flex items-center gap-2 disabled:opacity-50 active:scale-95 h-[42px]"
        title="Forzar lectura de nuevos Excels"
        :disabled="cargando"
      >
        <Database class="w-4 h-4" :class="{ 'animate-pulse': cargando }" />
        Sincronizar
      </button>

    </div>
  </header>
</template>

<style>
/* Variables CSS de VueDatePicker alineadas al Verde ADMIRA */
.dp__theme_light {
   --dp-background-color: #ffffff;
   --dp-text-color: #1e293b;
   --dp-hover-color: #e5eedd; /* admira-100 */
   --dp-hover-text-color: #507731; /* admira-600 */
   --dp-primary-color: #689840; /* admira-500 */
   --dp-primary-text-color: #ffffff;
   --dp-secondary-color: #94a3b8;
   --dp-border-color: #e2e8f0;
   --dp-menu-border-color: #f1f5f9;
   --dp-border-radius: 12px;
   --dp-font-family: 'Inter', system-ui, sans-serif;
}
.dp__menu {
    box-shadow: 0 10px 25px -5px rgb(0 0 0 / 0.1), 0 8px 10px -6px rgb(0 0 0 / 0.1) !important;
    border: 1px solid #f1f5f9 !important;
    padding: 8px !important;
}
.dp__action_buttons { display: none !important; }
</style>