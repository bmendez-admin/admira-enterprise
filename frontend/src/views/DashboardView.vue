<script setup>
import { onMounted } from 'vue';
import { FileSpreadsheet, WifiOff, RefreshCcw, Monitor, Wifi, AlertTriangle, Filter } from 'lucide-vue-next';
import StatCard from '../components/dashboard/StatCard.vue';
import Charts from '../components/dashboard/Charts.vue';
import Bitacora from '../components/dashboard/Bitacora.vue';
import { useDashboard } from '../composables/useDashboard';

const { kpis, filtros, resetFiltros, datosTabla, recargarDashboard, iniciarDashboard } = useDashboard();

onMounted(async () => {
  await iniciarDashboard();
});

const exportarCSV = () => {
  if (!datosTabla.value.items.length) return alert("No hay datos");
  const headers = ['FECHA', 'HORA', 'PLAYER', 'ESTADO', 'PROYECTO'];
  const filas = datosTabla.value.items.map(d => `${d.FECHA},${d.HORARIO_LEGIBLE},${d.PLAYER},${d.ESTADO},${d.PROYECTO}`);
  // El \uFEFF soluciona los acentos
  const blob = new Blob(['\uFEFF' + [headers.join(','), ...filas].join('\n')], { type: 'text/csv;charset=utf-8;' });
  const url = URL.createObjectURL(blob);
  const link = document.createElement("a");
  link.href = url;
  link.download = `Bitacora_Admira.csv`;
  link.click();
};

const filtrarCaidos = async () => {
  filtros.estado = 'Sin conexión';
  filtros.pagina = 1;
  await recargarDashboard();
};
</script>

<template>
  <div class="animate-in fade-in duration-500 w-full overflow-x-hidden pb-8">
    
    <div class="grid grid-cols-1 sm:grid-cols-3 gap-3 md:gap-4 mb-6 md:mb-8">
      <button @click="exportarCSV" class="flex items-center justify-center gap-3 px-6 py-3.5 sm:py-3 bg-white border border-gray-200 rounded-xl hover:border-admira-500 hover:text-admira-600 transition-all shadow-sm active:scale-95 group">
        <FileSpreadsheet class="w-5 h-5 sm:w-4 sm:h-4 text-admira-500 group-hover:text-admira-600"/>
        <span class="text-sm font-bold text-slate-700 group-hover:text-admira-600">Exportar CSV</span>
      </button>
      <button @click="filtrarCaidos" class="flex items-center justify-center gap-3 px-6 py-3.5 sm:py-3 bg-white border border-gray-200 rounded-xl hover:border-rose-300 hover:bg-rose-50 transition-all shadow-sm active:scale-95 group">
        <WifiOff class="w-5 h-5 sm:w-4 sm:h-4 text-rose-500"/>
        <span class="text-sm font-bold text-slate-700">Filtrar Caídos</span>
      </button>
      <button @click="resetFiltros" class="flex items-center justify-center gap-3 px-6 py-3.5 sm:py-3 bg-white border border-gray-200 rounded-xl hover:border-emerald-300 hover:bg-emerald-50 transition-all shadow-sm active:scale-95 group">
        <RefreshCcw class="w-5 h-5 sm:w-4 sm:h-4 text-emerald-500"/>
        <span class="text-sm font-bold text-slate-700">Limpiar Filtros</span>
      </button>
    </div>

    <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 md:gap-6 mb-8 md:mb-10">
      <StatCard title="Total Players" :value="kpis.uniquePlayers" :icon="Monitor" color="admira" sub="Inventario Activo" />
      <StatCard title="% De Emisiones" :value="kpis.uptime + '%'" :icon="Wifi" color="emerald" sub="Uptime promedio" />
      <StatCard title="Equipos Afectados" :value="kpis.off" :icon="AlertTriangle" color="red" sub="Con al menos 1 fallo" />
      <StatCard title="Inestables" :value="kpis.crit" :icon="Filter" color="amber" sub="Fallos recurrentes" />
    </div>

    <Charts />
    <Bitacora />
  </div>
</template>