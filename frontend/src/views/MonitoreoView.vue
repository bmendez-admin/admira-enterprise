<script setup>
import { ref, computed, onMounted, watch } from 'vue';
import { 
  Search, Monitor, RefreshCw, XCircle, Activity, WifiOff, LayoutGrid, ArrowDownAZ, X, Loader2, ChevronDown, Table, BarChart2, FileSpreadsheet
} from 'lucide-vue-next';
import { useDashboard } from '../composables/useDashboard';
import admiraApi from '../api/admiraApi';

const { dispositivosMonitoreo, cargarMonitoreo, cargando, filtros } = useDashboard();

// Estados de filtrado y orden
const busqueda = ref('');
const filtroEstado = ref('todos'); 
const orden = ref('estado'); 
const dropdownAbierto = ref(false);

const opcionesOrden = [
    { id: 'estado', label: 'Prioridad (Caídos primero)' },
    { id: 'alfabetico', label: 'Alfabético (A-Z)' },
    { id: 'reciente', label: 'Más recientes' }
];

const ordenSeleccionado = computed(() => opcionesOrden.find(o => o.id === orden.value));
const seleccionarOrden = (id) => { orden.value = id; dropdownAbierto.value = false; };

// Estados del Modal
const playerSeleccionado = ref(null);
const historialPlayer = ref([]);
const cargandoHistorial = ref(false);
const mostrarTabla = ref(false);

// Datos para gráficas
const pieSeries = ref([]);
const areaSeries = ref([]);

const pieOptions = {
    chart: { type: 'donut', fontFamily: 'inherit' },
    labels: ['Conexión OK', 'Caídas'],
    colors: ['#10b981', '#f43f5e'],
    plotOptions: { pie: { donut: { size: '70%' } } },
    dataLabels: { enabled: false },
    legend: { position: 'bottom', fontSize: '12px', fontWeight: 'bold' }
};

const areaOptions = ref({
    chart: { type: 'area', toolbar: { show: false }, zoom: { enabled: false } },
    colors: ['#689840'], // Color Verde ADMIRA para la gráfica de área
    dataLabels: { enabled: false },
    stroke: { curve: 'stepline', width: 2 },
    fill: { type: 'gradient', gradient: { shadeIntensity: 1, opacityFrom: 0.4, opacityTo: 0, stops: [0, 100] } },
    xaxis: { categories: [], labels: { show: false }, axisBorder: { show: false }, axisTicks: { show: false } },
    yaxis: { show: false, min: 0, max: 1 },
    grid: { show: false },
    tooltip: { x: { format: 'dd MMM HH:mm' } }
});

onMounted(() => { cargarMonitoreo(); });
watch([() => filtros.proyecto, () => filtros.fechaInicio, () => filtros.fechaFin], () => { cargarMonitoreo(); });
const limpiarBusqueda = () => busqueda.value = '';

const dispositivosProcesados = computed(() => {
  let filtrados = dispositivosMonitoreo.value.filter(d => {
    const coincideTexto = d.player.toLowerCase().includes(busqueda.value.toLowerCase()) || d.proyecto.toLowerCase().includes(busqueda.value.toLowerCase());
    const coincideEstado = filtroEstado.value === 'todos' || (filtroEstado.value === 'activo' && !d.alerta) || (filtroEstado.value === 'caido' && d.alerta);
    return coincideTexto && coincideEstado;
  });

  return filtrados.sort((a, b) => {
    if (orden.value === 'alfabetico') return a.player.localeCompare(b.player);
    if (orden.value === 'reciente') return b.ultima_conexion.localeCompare(a.ultima_conexion);
    if (orden.value === 'estado') {
        if (a.alerta === b.alerta) return a.player.localeCompare(b.player);
        return a.alerta ? -1 : 1;
    }
    return 0;
  });
});

const stats = computed(() => {
  return {
      total: dispositivosMonitoreo.value.length,
      activos: dispositivosMonitoreo.value.filter(d => !d.alerta).length,
      caidos: dispositivosMonitoreo.value.filter(d => d.alerta).length
  };
});

const abrirHistorial = async (dispositivo) => {
    playerSeleccionado.value = dispositivo;
    cargandoHistorial.value = true;
    historialPlayer.value = [];
    mostrarTabla.value = false; 
    
    try {
        const params = {
            player: dispositivo.player,
            fecha_inicio: filtros.fechaInicio || null,
            fecha_fin: filtros.fechaFin || null,
            filas_por_pagina: 100
        };
        const { data } = await admiraApi.get('/tabla', { params });
        historialPlayer.value = data.items;

        const activos = data.items.filter(i => i.ESTADO === 'Emisión OK' || i.ESTADO === 'Activo').length;
        const caidos = data.items.filter(i => i.ESTADO === 'Sin conexión').length;
        pieSeries.value = [activos, caidos];

        const chronData = [...data.items].reverse();
        
        areaOptions.value = {
            ...areaOptions.value,
            xaxis: { categories: chronData.map(i => `${i.FECHA} | ${i.HORARIO_LEGIBLE}`) }
        };
        
        areaSeries.value = [{
            name: 'Estado de Red',
            data: chronData.map(i => (i.ESTADO === 'Emisión OK' || i.ESTADO === 'Activo' ? 1 : 0))
        }];

    } catch (error) {
        console.error("Error cargando historial", error);
    } finally {
        cargandoHistorial.value = false;
    }
};

const cerrarModal = () => { playerSeleccionado.value = null; };

const exportarHistorialCSV = () => {
    if (!historialPlayer.value.length) return;
    
    const headers = ['FECHA', 'HORA', 'ESTADO', 'ARCHIVO ORIGEN'];
    const filas = historialPlayer.value.map(h => {
        const fecha = h.FECHA ? h.FECHA.replace('T', ' ') : '---';
        const hora = h.HORARIO_LEGIBLE || '---';
        const estado = h.ESTADO || '---';
        const archivo = h.ARCHIVO_ORIGEN ? h.ARCHIVO_ORIGEN.replace('.xlsx','').replace('.csv','') : '---';
        return `${fecha},${hora},${estado},${archivo}`;
    });

    const csvContent = '\uFEFF' + [headers.join(','), ...filas].join('\n');

    const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
    const url = URL.createObjectURL(blob);
    const link = document.createElement("a");
    link.href = url;
    link.download = `Historial_${playerSeleccionado.value.player.replace(/\s+/g, '_')}.csv`;
    link.click();
};
</script>

<template>
  <div class="flex flex-col h-full animate-in fade-in duration-500 relative pb-10">
    
    <div class="flex flex-col lg:flex-row items-stretch gap-4 mb-8 bg-white p-4 rounded-2xl border border-gray-100 shadow-sm z-30">
        <div class="relative flex-1">
            <Search class="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400" />
            <input v-model="busqueda" type="text" placeholder="Buscar player..." class="w-full pl-10 pr-10 py-3 bg-slate-50 rounded-xl text-sm outline-none" />
            <button v-if="busqueda" @click="busqueda = ''" class="absolute right-3 top-1/2 -translate-y-1/2 text-slate-300 hover:text-slate-500"><XCircle class="w-5 h-5" /></button>
        </div>

        <div class="flex flex-wrap sm:flex-nowrap gap-3">
            <div class="relative flex-1 sm:flex-none sm:min-w-[220px]">
                <div @click="dropdownAbierto = !dropdownAbierto" class="flex items-center justify-between bg-slate-50 rounded-xl px-4 h-[44px] border border-slate-100 cursor-pointer">
                    <div class="flex items-center text-xs font-bold text-slate-600">
                        <ArrowDownAZ class="w-4 h-4 text-admira-500 mr-2" />
                        {{ ordenSeleccionado.label }}
                    </div>
                    <ChevronDown class="w-4 h-4 text-slate-400" />
                </div>
                <div v-if="dropdownAbierto" class="absolute top-full left-0 mt-2 w-full bg-white border border-gray-100 rounded-xl shadow-xl z-50">
                    <div v-for="opcion in opcionesOrden" :key="opcion.id" @click="seleccionarOrden(opcion.id)" class="px-4 py-3 text-xs font-bold hover:bg-slate-50 cursor-pointer">
                        {{ opcion.label }}
                    </div>
                </div>
                <div v-if="dropdownAbierto" @click="dropdownAbierto = false" class="fixed inset-0 z-40"></div>
            </div>

            <button @click="cargarMonitoreo" class="flex items-center justify-center p-3 bg-admira-50 text-admira-600 rounded-xl hover:bg-admira-100 transition-all h-[44px] w-[44px]">
                <RefreshCw class="w-5 h-5" :class="{'animate-spin': cargando}" />
            </button>
        </div>

        <div class="flex flex-wrap bg-slate-100 p-1 rounded-xl">
            <button v-for="st in [['todos', 'Todos', stats.total], ['activo', 'OK', stats.activos], ['caido', 'Caídos', stats.caidos]]" 
                :key="st[0]" @click="filtroEstado = st[0]" 
                :class="['flex-1 flex items-center justify-center gap-1.5 px-3 py-2 text-[10px] font-black uppercase rounded-lg transition-all', filtroEstado === st[0] ? 'bg-white shadow-sm text-admira-600' : 'text-slate-500']">
                {{ st[1] }} ({{ st[2] }})
            </button>
        </div>
    </div>

    <div v-if="dispositivosProcesados.length > 0" class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4 md:gap-5">
        <div v-for="dev in dispositivosProcesados" :key="dev.player" @click="abrirHistorial(dev)"
            class="bg-white p-5 md:p-6 rounded-2xl border border-gray-100 shadow-sm hover:shadow-lg transition-all cursor-pointer relative overflow-hidden group">
            <div :class="`absolute top-0 left-0 w-1.5 h-full ${dev.alerta ? 'bg-rose-500' : 'bg-emerald-500'}`"></div>
            <div class="flex items-start justify-between mb-4">
                <div :class="`p-2.5 rounded-xl ${dev.alerta ? 'bg-rose-50 text-rose-600' : 'bg-emerald-50 text-emerald-600'}`">
                    <Monitor class="w-5 h-5" />
                </div>
                <span :class="`text-[9px] font-black uppercase px-2 py-1 rounded border ${dev.alerta ? 'bg-rose-50 border-rose-100 text-rose-700' : 'bg-emerald-50 border-emerald-100 text-emerald-700'}`">
                  {{ dev.estado }}
                </span>
            </div>
            <h3 class="font-extrabold text-slate-800 truncate text-base md:text-lg mb-0.5 group-hover:text-admira-600">{{ dev.player }}</h3>
            <p class="text-[10px] text-slate-400 font-bold uppercase mb-4">{{ dev.proyecto }}</p>
            <div class="pt-3 border-t border-slate-50">
                <p class="text-[9px] text-slate-400 font-bold uppercase mb-1">Último reporte:</p>
                <div class="text-[10px] font-mono font-bold text-slate-600 bg-slate-50 p-2 rounded-lg text-center">{{ dev.ultima_conexion }}</div>
            </div>
        </div>
    </div>

    <Teleport to="body">
      <div v-if="playerSeleccionado" class="fixed inset-0 z-[999] flex items-center justify-center p-2 sm:p-4 bg-slate-900/60 backdrop-blur-sm">
          <div class="bg-white rounded-3xl shadow-2xl w-full max-w-4xl flex flex-col max-h-[95vh] overflow-hidden">
              <div class="px-6 py-4 md:px-8 md:py-6 border-b flex justify-between items-center bg-white sticky top-0 z-10">
                  <div class="flex items-center gap-4">
                      <div :class="`p-2.5 rounded-xl hidden sm:block ${playerSeleccionado.alerta ? 'bg-rose-50 text-rose-600' : 'bg-emerald-50 text-emerald-600'}`">
                          <Monitor class="w-6 h-6" />
                      </div>
                      <div>
                          <h3 class="text-lg md:text-xl font-black text-slate-800 truncate max-w-[200px] sm:max-w-md">{{ playerSeleccionado.player }}</h3>
                          <p class="text-[10px] text-slate-400 font-bold uppercase">{{ playerSeleccionado.proyecto }}</p>
                      </div>
                  </div>
                  <button @click="cerrarModal" class="p-2 text-slate-400 hover:text-rose-500 bg-slate-50 rounded-xl transition-all"><X class="w-6 h-6" /></button>
              </div>
              
              <div class="flex-1 overflow-y-auto p-4 md:p-8 bg-slate-50/30">
                  <div v-if="cargandoHistorial" class="flex flex-col items-center py-20">
                      <Loader2 class="w-10 h-10 text-admira-600 animate-spin mb-4" />
                      <p class="text-slate-500 font-bold text-sm">Analizando...</p>
                  </div>
                  
                  <div v-else-if="historialPlayer.length > 0">
                      <div class="flex flex-col sm:flex-row gap-3 mb-6">
                        <button @click="mostrarTabla = !mostrarTabla" class="flex-1 sm:flex-none flex items-center justify-center gap-2 px-4 py-2.5 bg-white border border-slate-200 text-xs font-bold rounded-xl shadow-sm">
                          <component :is="mostrarTabla ? BarChart2 : Table" class="w-4 h-4" />
                          {{ mostrarTabla ? 'Gráficas' : 'Tabla' }}
                        </button>
                        <button @click="exportarHistorialCSV" class="flex-1 sm:flex-none flex items-center justify-center gap-2 px-4 py-2.5 bg-admira-500 text-white text-xs font-bold rounded-xl shadow-lg shadow-admira-200">
                          <FileSpreadsheet class="w-4 h-4" /> Excel
                        </button>
                      </div>

                      <div v-if="!mostrarTabla" class="space-y-6">
                          <div class="grid grid-cols-1 md:grid-cols-3 gap-6">
                            <div class="bg-white p-6 rounded-2xl border flex flex-col items-center">
                              <h4 class="text-[10px] font-black uppercase text-slate-400 mb-4">Disponibilidad</h4>
                              <apexchart type="donut" height="200" :options="pieOptions" :series="pieSeries" class="w-full"></apexchart>
                            </div>
                            <div class="md:col-span-2 bg-white p-6 rounded-2xl border">
                              <h4 class="text-[10px] font-black uppercase text-slate-400 mb-4">Línea de Estabilidad</h4>
                              <apexchart type="area" height="200" :options="areaOptions" :series="areaSeries" class="w-full"></apexchart>
                            </div>
                          </div>
                      </div>

                      <div v-else class="bg-white rounded-2xl border overflow-x-auto">
                          <table class="w-full text-left text-xs">
                              <thead class="bg-slate-50 font-black text-slate-400 uppercase">
                                  <tr><th class="px-6 py-4">Fecha</th><th class="px-6 py-4">Estado</th><th class="px-6 py-4 text-right">Origen</th></tr>
                              </thead>
                              <tbody class="divide-y">
                                  <tr v-for="(h, i) in historialPlayer" :key="i">
                                      <td class="px-6 py-3.5 font-mono">{{ h.FECHA }} | {{ h.HORARIO_LEGIBLE }}</td>
                                      <td class="px-6 py-3.5"><span :class="`px-2 py-0.5 rounded-md font-bold ${h.ESTADO === 'Activo' ? 'bg-emerald-50 text-emerald-700' : 'bg-rose-50 text-rose-700'}`">{{ h.ESTADO }}</span></td>
                                      <td class="px-6 py-3.5 text-right opacity-50">{{ (h.ARCHIVO_ORIGEN || '').substring(0,10) }}</td>
                                  </tr>
                              </tbody>
                          </table>
                      </div>
                  </div>
              </div>
          </div>
      </div>
    </Teleport>
  </div>
</template>