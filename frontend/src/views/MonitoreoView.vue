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
  <div class="flex flex-col h-full animate-in fade-in duration-500 relative">
    
    <div class="flex flex-col xl:flex-row items-stretch xl:items-center gap-4 mb-8 bg-white p-4 rounded-2xl border border-gray-100 shadow-sm relative z-20">
        
        <div class="relative flex-1 min-w-[250px]">
            <Search class="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400" />
            <input v-model="busqueda" type="text" placeholder="Buscar player..." class="w-full pl-10 pr-10 py-3 bg-slate-50 border-none rounded-xl focus:ring-2 focus:ring-admira-500/20 outline-none text-sm transition-all" />
            <button v-if="busqueda" @click="limpiarBusqueda" class="absolute right-3 top-1/2 -translate-y-1/2 text-slate-300 hover:text-slate-500"><XCircle class="w-5 h-5" /></button>
        </div>

        <div class="relative">
            <div @click="dropdownAbierto = !dropdownAbierto" class="flex items-center justify-between bg-slate-50 hover:bg-slate-100 transition-colors rounded-xl px-4 h-[44px] border border-slate-100 cursor-pointer min-w-[220px]">
                <div class="flex items-center text-xs font-bold text-slate-600">
                    <ArrowDownAZ class="w-4 h-4 text-admira-500 mr-2" />
                    {{ ordenSeleccionado.label }}
                </div>
                <ChevronDown class="w-4 h-4 text-slate-400" />
            </div>
            <div v-if="dropdownAbierto" class="absolute top-full left-0 mt-2 w-full bg-white border border-gray-100 rounded-xl shadow-lg overflow-hidden z-50 animate-in fade-in slide-in-from-top-2 duration-200">
                <div v-for="opcion in opcionesOrden" :key="opcion.id" @click="seleccionarOrden(opcion.id)" :class="`px-4 py-3 text-xs font-bold cursor-pointer transition-colors ${orden === opcion.id ? 'bg-admira-50 text-admira-700' : 'text-slate-600 hover:bg-slate-50'}`">
                    {{ opcion.label }}
                </div>
            </div>
            <div v-if="dropdownAbierto" @click="dropdownAbierto = false" class="fixed inset-0 z-40"></div>
        </div>

        <div class="flex bg-slate-100 p-1.5 rounded-xl self-start xl:self-center">
            <button @click="filtroEstado = 'todos'" :class="`flex items-center gap-2 px-3 py-1.5 text-xs font-bold rounded-lg transition-all ${filtroEstado === 'todos' ? 'bg-white shadow-sm text-admira-600' : 'text-slate-500 hover:text-slate-700'}`"><LayoutGrid class="w-3.5 h-3.5" /> Todos ({{ stats.total }})</button>
            <button @click="filtroEstado = 'activo'" :class="`flex items-center gap-2 px-3 py-1.5 text-xs font-bold rounded-lg transition-all ${filtroEstado === 'activo' ? 'bg-emerald-500 text-white shadow-sm' : 'text-slate-500 hover:text-emerald-600'}`"><Activity class="w-3.5 h-3.5" /> Activos ({{ stats.activos }})</button>
            <button @click="filtroEstado = 'caido'" :class="`flex items-center gap-2 px-3 py-1.5 text-xs font-bold rounded-lg transition-all ${filtroEstado === 'caido' ? 'bg-rose-500 text-white shadow-sm' : 'text-slate-500 hover:text-rose-600'}`"><WifiOff class="w-3.5 h-3.5" /> Caídos ({{ stats.caidos }})</button>
        </div>

        <button @click="cargarMonitoreo" class="flex items-center justify-center p-3 bg-admira-50 text-admira-600 rounded-xl hover:bg-admira-100 transition-all active:scale-95" title="Actualizar">
            <RefreshCw class="w-5 h-5" :class="{'animate-spin': cargando}" />
        </button>
    </div>

    <div v-if="dispositivosProcesados.length > 0" class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-5 relative z-10">
        <div v-for="dev in dispositivosProcesados" :key="dev.player" @click="abrirHistorial(dev)"
            class="bg-white p-6 rounded-2xl border border-gray-100 shadow-sm hover:shadow-xl hover:-translate-y-1 hover:border-admira-200 cursor-pointer transition-all group overflow-hidden relative">
            <div :class="`absolute top-0 left-0 w-1.5 h-full ${dev.alerta ? 'bg-rose-500' : 'bg-emerald-500'}`"></div>
            <div class="flex items-start justify-between mb-5">
                <div :class="`p-2.5 rounded-xl transition-colors ${dev.alerta ? 'bg-rose-50 text-rose-600 group-hover:bg-rose-100' : 'bg-emerald-50 text-emerald-600 group-hover:bg-emerald-100'}`">
                    <Monitor class="w-5 h-5" />
                </div>
                <div class="flex flex-col items-end">
                  <span :class="`text-[10px] font-black uppercase px-2 py-1 rounded-md border ${dev.alerta ? 'bg-rose-50 border-rose-100 text-rose-700' : 'bg-emerald-50 border-emerald-100 text-emerald-700'}`">{{ dev.estado }}</span>
                </div>
            </div>
            <h3 class="font-extrabold text-slate-800 truncate mb-1 text-lg group-hover:text-admira-600 transition-colors" :title="dev.player">{{ dev.player }}</h3>
            <p class="text-[11px] text-slate-400 font-bold uppercase tracking-widest mb-6">{{ dev.proyecto }}</p>
            <div class="pt-4 border-t border-gray-50 flex flex-col gap-1">
                <span class="text-[10px] text-slate-400 font-semibold uppercase tracking-tighter">Último registro:</span>
                <span class="text-xs font-mono font-bold text-slate-600 bg-slate-50 p-1.5 rounded-lg border border-slate-100 text-center">{{ dev.ultima_conexion }}</span>
            </div>
        </div>
    </div>

    <div v-else class="flex-1 flex flex-col items-center justify-center py-24 bg-white rounded-[2rem] border-2 border-dashed border-slate-200">
        <div class="p-6 bg-slate-50 rounded-full mb-6"><Monitor class="w-12 h-12 text-slate-300" /></div>
        <h3 class="text-xl font-bold text-slate-800 mb-2">Sin resultados</h3>
        <p class="text-slate-400 text-sm">No hay reportes para los filtros seleccionados.</p>
    </div>

    <div v-if="playerSeleccionado" class="fixed inset-0 z-[100] flex items-center justify-center p-4 bg-slate-900/60 backdrop-blur-sm transition-all duration-300">
        <div class="bg-white rounded-[2rem] shadow-2xl w-full max-w-4xl flex flex-col max-h-[90vh] overflow-hidden animate-in zoom-in-95 duration-200 border border-slate-100">
            
            <div class="px-8 py-6 border-b border-gray-100 flex justify-between items-center bg-white relative">
                <div class="flex items-center gap-5">
                    <div :class="`p-3.5 rounded-2xl ${playerSeleccionado.alerta ? 'bg-rose-50 text-rose-600' : 'bg-emerald-50 text-emerald-600'}`">
                        <Monitor class="w-7 h-7" />
                    </div>
                    <div>
                        <div class="flex items-center gap-3 mb-1">
                            <h3 class="text-2xl font-black text-slate-800">{{ playerSeleccionado.player }}</h3>
                            <span :class="`text-[10px] font-black uppercase px-2.5 py-1 rounded-md border ${playerSeleccionado.alerta ? 'bg-rose-50 border-rose-100 text-rose-700' : 'bg-emerald-50 border-emerald-100 text-emerald-700'}`">
                                {{ playerSeleccionado.estado }}
                            </span>
                        </div>
                        <p class="text-xs text-slate-400 font-bold uppercase tracking-wider">
                            PROYECTO: <span class="text-slate-600">{{ playerSeleccionado.proyecto }}</span>
                        </p>
                    </div>
                </div>
                <button @click="cerrarModal" class="p-2.5 text-slate-400 hover:text-rose-600 hover:bg-rose-50 rounded-xl transition-all absolute top-6 right-6">
                    <X class="w-6 h-6" />
                </button>
            </div>
            
            <div class="flex-1 overflow-auto bg-slate-50/50 p-8 pt-6">
                
                <div v-if="historialPlayer.length > 0 && !cargandoHistorial" class="flex flex-wrap items-center justify-between gap-4 mb-6">
                    <button 
                        @click="mostrarTabla = !mostrarTabla" 
                        class="flex items-center gap-2 px-5 py-2.5 bg-white border border-gray-200 text-slate-600 text-xs font-bold rounded-xl hover:border-admira-300 hover:text-admira-600 shadow-sm transition-all active:scale-95"
                    >
                        <component :is="mostrarTabla ? BarChart2 : Table" class="w-4 h-4" />
                        {{ mostrarTabla ? 'Volver a Vista Gráfica' : 'Ver Historial en Tabla' }}
                    </button>

                    <button 
                        @click="exportarHistorialCSV" 
                        class="flex items-center gap-2 px-5 py-2.5 bg-admira-50 border border-admira-100 text-admira-700 text-xs font-bold rounded-xl hover:bg-admira-100 shadow-sm transition-all active:scale-95"
                    >
                        <FileSpreadsheet class="w-4 h-4" />
                        Descargar Excel
                    </button>
                </div>

                <div v-if="cargandoHistorial" class="flex flex-col items-center justify-center py-20">
                    <Loader2 class="w-10 h-10 text-admira-600 animate-spin mb-4" />
                    <p class="text-slate-500 font-bold text-sm">Analizando historial de conexiones...</p>
                </div>
                
                <div v-else-if="historialPlayer.length > 0" class="space-y-6">
                    
                    <div v-if="!mostrarTabla" class="grid grid-cols-1 md:grid-cols-3 gap-6 animate-in fade-in slide-in-from-bottom-4 duration-500">
                        <div class="bg-white p-6 rounded-3xl border border-gray-100 shadow-sm flex flex-col items-center justify-center">
                            <h4 class="text-xs font-bold uppercase tracking-widest text-slate-400 mb-4 w-full text-center">Salud del Periodo</h4>
                            <apexchart type="donut" height="200" :options="pieOptions" :series="pieSeries"></apexchart>
                        </div>

                        <div class="md:col-span-2 bg-white p-6 rounded-3xl border border-gray-100 shadow-sm">
                            <h4 class="text-xs font-bold uppercase tracking-widest text-slate-400 mb-2">Línea de Tiempo de Estabilidad</h4>
                            <p class="text-[10px] text-slate-400 mb-4 font-medium">(Nivel alto = Conectado, Nivel bajo = Desconectado)</p>
                            <apexchart type="area" height="180" :options="areaOptions" :series="areaSeries"></apexchart>
                        </div>
                    </div>

                    <div v-else class="bg-white rounded-3xl border border-gray-100 shadow-sm overflow-hidden animate-in fade-in slide-in-from-bottom-4 duration-500">
                        <table class="w-full text-left text-sm text-slate-600">
                            <thead class="bg-slate-50 sticky top-0 text-[10px] uppercase font-bold text-slate-400 tracking-wider">
                                <tr>
                                    <th class="px-6 py-4">Fecha y Hora</th>
                                    <th class="px-6 py-4">Estado</th>
                                    <th class="px-6 py-4 text-right">Archivo Origen</th>
                                </tr>
                            </thead>
                            <tbody class="divide-y divide-gray-50">
                                <tr v-for="(h, i) in historialPlayer" :key="i" class="hover:bg-slate-50 transition-colors">
                                    <td class="px-6 py-3.5 font-mono text-xs font-medium text-slate-600">
                                        {{ h.FECHA ? h.FECHA.replace('T', ' ') : '---' }} <span class="text-slate-300 mx-2">|</span> {{ h.HORARIO_LEGIBLE }}
                                    </td>
                                    <td class="px-6 py-3.5">
                                        <span :class="`px-2.5 py-1 rounded-md text-[10px] font-black uppercase border ${h.ESTADO === 'Emisión OK' || h.ESTADO === 'Activo' ? 'bg-emerald-50 text-emerald-700 border-emerald-100' : 'bg-rose-50 text-rose-700 border-rose-100'}`">
                                            {{ h.ESTADO }}
                                        </span>
                                    </td>
                                    <td class="px-6 py-3.5 font-mono text-[10px] text-slate-400 text-right">
                                        {{ h.ARCHIVO_ORIGEN ? h.ARCHIVO_ORIGEN.replace('.xlsx','').replace('.csv','') : '---' }}
                                    </td>
                                </tr>
                            </tbody>
                        </table>
                    </div>

                </div>
                
                <div v-else class="py-24 text-center flex flex-col items-center">
                    <Activity class="w-12 h-12 text-slate-200 mb-4"/>
                    <p class="text-slate-500 font-bold text-lg">Historial no disponible</p>
                    <p class="text-slate-400 text-sm mt-1">Este equipo no reportó en el rango de fechas seleccionado en el Header.</p>
                </div>
            </div>
            
        </div>
    </div>

  </div>
</template>