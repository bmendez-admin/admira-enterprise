<template>
  <div class="bg-white p-6 rounded-2xl border border-gray-100 shadow-sm relative overflow-hidden">
    <div class="flex items-center justify-between mb-6">
      <div>
        <h3 class="font-bold text-slate-800 text-base md:text-lg">Evolución del Servicio</h3>
        <p class="text-xs text-slate-400 mt-1">Tendencia de Uptime global a lo largo del tiempo</p>
      </div>
    </div>

    <div v-if="!datosTendencia?.series?.length && !cargando" class="flex flex-col items-center justify-center py-20 text-slate-400 gap-4 border-2 border-dashed border-gray-100 rounded-xl bg-slate-50/50">
        <p class="text-sm font-medium">No hay suficientes datos históricos en este rango.</p>
    </div>

    <div v-show="datosTendencia?.series?.length > 0">
      <apexchart type="area" height="350" :options="chartOptions" :series="chartSeries" />
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue';
import { useDashboard } from '../../composables/useDashboard';

const { datosTendencia, cargando } = useDashboard();

const chartSeries = computed(() => [
  { name: 'Uptime Promedio', data: datosTendencia.value.series || [] }
]);

const chartOptions = computed(() => ({
  chart: {
    type: 'area',
    height: 350,
    toolbar: { show: false },
    fontFamily: 'Inter, sans-serif',
    animations: { enabled: true, easing: 'easeinout', speed: 800 }
  },
  colors: ['#689840'], // Verde Corporativo
  fill: {
    type: 'gradient',
    gradient: { shadeIntensity: 1, opacityFrom: 0.4, opacityTo: 0.05, stops: [0, 100] }
  },
  dataLabels: { enabled: false },
  stroke: { curve: 'smooth', width: 3 }, // Curva elegante
  xaxis: {
    categories: datosTendencia.value.categorias || [],
    labels: { style: { fontSize: '10px', colors: '#64748b' } },
    tooltip: { enabled: false },
    axisBorder: { show: false },
    axisTicks: { show: false }
  },
  yaxis: {
    min: 0,
    max: 100, // Fijamos al 100% para evitar saltos locos
    tickAmount: 5,
    labels: { style: { fontSize: '11px', fontWeight: 600, colors: '#1e293b' }, formatter: (val) => `${Math.floor(val)}%` }
  },
  grid: { borderColor: '#f1f5f9', strokeDashArray: 4 },
  tooltip: {
    theme: 'light',
    y: { formatter: (val) => `${val}% Uptime` }
  }
}));
</script>