<script setup>
import { computed } from 'vue';
import { useDashboard } from '../../composables/useDashboard';

const { datosGraficas, kpis } = useDashboard();

const barOptions = computed(() => ({
    chart: { type: 'bar', toolbar: { show: false }, fontFamily: 'Inter, sans-serif' },
    colors: ['#689840'],
    plotOptions: {
        bar: { borderRadius: 4, horizontal: false, columnWidth: '45%', distributed: false }
    },
    xaxis: {
        categories: datosGraficas.value.barras.categorias,
        labels: { style: { fontSize: '10px', fontWeight: 500 } }
    },
    yaxis: {
        min: 0,
        max: 100,
        tickAmount: 5,
        labels: {
            formatter: (val) => `${Math.floor(val)}%`
        }
    },
    grid: { borderColor: '#f3f4f6', strokeDashArray: 4 },
    dataLabels: { enabled: false },
    tooltip: {
        theme: 'light',
        y: { formatter: (val) => `${val}% Uptime` }
    }
}));

const barSeries = computed(() => [
    { name: 'Rendimiento Promedio', data: datosGraficas.value.barras.series }
]);

const pieOptions = computed(() => ({
    labels: ['Conectados', 'Desconectados'],
    colors: ['#689840', '#F59E0B'],
    legend: { position: 'bottom', fontSize: '11px' },
    dataLabels: { enabled: false },
    plotOptions: {
        pie: {
            donut: {
                size: '75%',
                labels: {
                    show: true,
                    name: { show: true, fontSize: '11px', fontFamily: 'Inter, sans-serif', color: '#64748b' },
                    value: { show: true, fontSize: '20px', fontFamily: 'Inter, sans-serif', fontWeight: 700, color: '#1e293b' },
                    total: {
                        show: true,
                        showAlways: true,
                        label: 'Total',
                        fontSize: '11px',
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
    <div class="grid grid-cols-1 lg:grid-cols-3 gap-4 md:gap-6 mb-8 w-full">

        <div
            class="lg:col-span-2 bg-white rounded-2xl border border-gray-200 shadow-sm p-4 md:p-6 flex flex-col hover:shadow-md transition-shadow w-full overflow-hidden">
            <div class="mb-4 md:mb-6 flex flex-col sm:flex-row justify-between items-start sm:items-center gap-2">
                <div>
                    <h3 class="font-bold text-slate-800 text-sm md:text-base">Rendimiento por Franja</h3>
                    <p class="text-[10px] md:text-xs text-slate-400 mt-1">Uptime promedio histórico de emisión</p>
                </div>
            </div>
            <div class="flex-1 w-full min-h-[250px] md:min-h-[300px] overflow-x-auto overflow-y-hidden">
                <div class="min-w-[400px] lg:min-w-full h-full">
                    <apexchart type="bar" height="100%" :options="barOptions" :series="barSeries"></apexchart>
                </div>
            </div>
        </div>

        <div
            class="bg-white rounded-2xl border border-gray-200 shadow-sm p-4 md:p-6 flex flex-col hover:shadow-md transition-shadow w-full">
            <div class="mb-4 text-center sm:text-left">
                <h3 class="font-bold text-slate-800 text-sm md:text-base">Estado de Red</h3>
                <p class="text-[10px] md:text-xs text-slate-400 mt-1">Estatus del inventario activo</p>
            </div>
            <div class="flex-1 flex items-center justify-center min-h-[250px] md:min-h-[300px] w-full">
                <apexchart type="donut" width="100%" :options="pieOptions" :series="pieSeries"></apexchart>
            </div>
        </div>

    </div>
</template>