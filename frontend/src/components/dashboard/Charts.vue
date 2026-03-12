<script setup>
import { computed } from 'vue';
import { useDashboard } from '../../composables/useDashboard';

const { datosGraficas, kpis } = useDashboard();

const barOptions = computed(() => ({
  chart: { type: 'bar', toolbar: { show: false }, fontFamily: 'Inter, sans-serif' },
  colors: ['#EF4444'], // Rojo para las fallas (Se mantiene para contraste de alerta)
  plotOptions: { 
      bar: { borderRadius: 4, horizontal: false, columnWidth: '45%', distributed: false } 
  },
  xaxis: { 
      categories: datosGraficas.value.barras.categorias,
      labels: { style: { fontSize: '11px', fontWeight: 500 } }
  },
  grid: { borderColor: '#f3f4f6', strokeDashArray: 4 },
  dataLabels: { enabled: false },
  tooltip: { 
      theme: 'light',
      y: { formatter: (val) => `${val} Equipos` } 
  }
}));

const barSeries = computed(() => [
  { name: 'Equipos Caídos', data: datosGraficas.value.barras.series }
]);

const pieOptions = computed(() => ({
    labels: ['Conectados', 'Desconectados'],
    // AQUÍ ESTÁ LA MAGIA: Tu color corporativo como principal
    colors: ['#689840', '#F59E0B'], 
    legend: { position: 'bottom', fontSize: '12px' },
    dataLabels: { enabled: false },
    plotOptions: { 
        pie: { 
            donut: { 
                size: '75%',
                labels: {
                    show: true,
                    name: { show: true, fontSize: '12px', fontFamily: 'Inter, sans-serif', color: '#64748b' },
                    value: { show: true, fontSize: '24px', fontFamily: 'Inter, sans-serif', fontWeight: 700, color: '#1e293b' },
                    total: { 
                        show: true, 
                        showAlways: true,
                        label: 'Inventario Total', 
                        fontSize: '12px', 
                        fontWeight: 600,
                        color: '#64748b',
                        formatter: function () {
                            return kpis.value.uniquePlayers;
                        }
                    }
                }
            } 
        } 
    }
}));

const pieSeries = computed(() => {
    return [kpis.value.dona_activos || 0, kpis.value.dona_caidos || 0];
});
</script>

<template>
  <div class="grid grid-cols-1 lg:grid-cols-3 gap-6 mb-8">
    
    <div class="lg:col-span-2 bg-white rounded-2xl border border-gray-200 shadow-sm p-6 flex flex-col hover:shadow-md transition-shadow">
      <div class="mb-6 flex justify-between items-center">
          <div>
              <h3 class="font-bold text-slate-800">Concentración de Caídas</h3>
              <p class="text-xs text-slate-400 mt-1">Equipos distintos caídos por franja horaria</p>
          </div>
          </div>
      <div class="flex-1 w-full min-h-[300px]">
          <apexchart type="bar" height="100%" :options="barOptions" :series="barSeries"></apexchart>
      </div>
    </div>

    <div class="bg-white rounded-2xl border border-gray-200 shadow-sm p-6 flex flex-col hover:shadow-md transition-shadow">
        <div class="mb-4 text-center sm:text-left">
            <h3 class="font-bold text-slate-800">Estado de Red</h3>
            <p class="text-xs text-slate-400 mt-1">Estatus actual del inventario activo</p>
        </div>
        <div class="flex-1 flex items-center justify-center min-h-[300px]">
            <apexchart type="donut" width="100%" :options="pieOptions" :series="pieSeries"></apexchart>
        </div>
    </div>

  </div>
</template>