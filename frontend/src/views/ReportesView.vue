<script setup>
import { ref, computed, watch } from 'vue';
import { 
  FileText, Download, Filter, BarChart3, AlertTriangle, CheckCircle2, 
  LayoutList, Loader2, Trash2, Search, FileSpreadsheet, Activity
} from 'lucide-vue-next';
import { useDashboard } from '../composables/useDashboard';
import admiraApi from '../api/admiraApi';

const { filtros } = useDashboard();
const generandoReporte = ref(false);
const datosReporte = ref([]);
const busquedaInterna = ref('');
const mostrarSoloInestables = ref(false);

watch([() => filtros.proyecto, () => filtros.fechaInicio, () => filtros.fechaFin], () => {
    datosReporte.value = []; 
    busquedaInterna.value = '';
});

const generarReporteGlobal = async () => {
    generandoReporte.value = true;
    try {
        const params = {
            proyecto: (filtros.proyecto && filtros.proyecto !== 'Todos los Proyectos') ? filtros.proyecto : null,
            fecha_inicio: filtros.fechaInicio,
            fecha_fin: filtros.fechaFin
        };
        
        const { data } = await admiraApi.get('/reporte/consolidado', { params });
        datosReporte.value = data;
    } catch (error) {
        console.error("Error al generar reporte:", error);
        alert("Hubo un problema al conectar con el servidor.");
    } finally {
        generandoReporte.value = false;
    }
};

const limpiarAnalisis = () => {
    datosReporte.value = [];
    busquedaInterna.value = '';
    mostrarSoloInestables.value = false;
};

const reporteFiltrado = computed(() => {
    let filtrado = datosReporte.value;
    
    if (mostrarSoloInestables.value) {
        filtrado = filtrado.filter(d => d.uptime < 100);
    }
    
    if (busquedaInterna.value) {
        filtrado = filtrado.filter(d => d.player.toLowerCase().includes(busquedaInterna.value.toLowerCase()));
    }
    
    return filtrado;
});

const statsReporte = computed(() => {
    const total = datosReporte.value.length;
    const fallosTotales = datosReporte.value.reduce((acc, curr) => acc + curr.caidas, 0);
    const reportesTotales = datosReporte.value.reduce((acc, curr) => acc + curr.total_reportes, 0);
    const uptimeGlobal = reportesTotales > 0 ? (((reportesTotales - fallosTotales) / reportesTotales) * 100).toFixed(1) : 0;
    
    return { total, fallosTotales, uptimeGlobal };
});

const exportarExcelProfesional = () => {
    if (!datosReporte.value.length) return;
    
    const headers = ['PROYECTO', 'NOMBRE DEL PLAYER', 'DISPONIBILIDAD (UPTIME)', 'INCIDENCIAS', 'TOTAL REPORTES EVALUADOS', 'ESTADO AL FINALIZAR RANGO', 'ÚLTIMA CONEXIÓN'];
    
    const filas = reporteFiltrado.value.map(d => [
        `"${d.proyecto.toUpperCase()}"`,
        `"${d.player}"`,
        `"${d.uptime}%"`,
        `"${d.caidas}"`,
        `"${d.total_reportes}"`,
        `"${d.ultimo_estado}"`,
        `"${d.ultima_conexion}"`
    ]);
    
    const csvContent = '\uFEFF' + [headers.join(','), ...filas.map(f => f.join(','))].join('\n');
    const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
    const url = URL.createObjectURL(blob);
    const link = document.createElement("a");
    link.href = url;
    link.download = `AUDITORIA_CONSOLIDADA_${filtros.proyecto.replace(/\s+/g, '_')}_${filtros.fechaInicio}.csv`;
    link.click();
};
</script>

<template>
  <div class="flex flex-col h-full animate-in fade-in duration-700">
    
    <div class="flex flex-col md:flex-row md:justify-between md:items-end gap-4 mb-8">
        <div>
            <h2 class="text-3xl font-black text-slate-800 tracking-tight">Reportes Ejecutivos</h2>
            <p class="text-slate-500 font-medium">Auditoría consolidada y cálculo de disponibilidad histórica.</p>
        </div>
        
        <div v-if="datosReporte.length > 0" class="flex flex-wrap gap-3">
            <button @click="limpiarAnalisis" class="flex items-center gap-2 px-4 py-2 bg-slate-100 text-slate-500 hover:bg-rose-50 hover:text-rose-600 rounded-xl font-bold text-xs transition-colors">
                <Trash2 class="w-4 h-4" /> Limpiar
            </button>
            <button @click="exportarExcelProfesional" class="flex items-center gap-2 px-6 py-2.5 bg-emerald-500 text-white rounded-xl font-bold text-xs shadow-lg shadow-emerald-200 hover:bg-emerald-600 transition-all active:scale-95">
                <FileSpreadsheet class="w-4 h-4" /> Exportar Consolidado
            </button>
        </div>
    </div>

    <div class="grid grid-cols-1 xl:grid-cols-4 gap-8">
        
        <div class="xl:col-span-1 space-y-6">
            <div class="bg-white p-6 rounded-[2rem] border border-slate-100 shadow-sm relative overflow-hidden">
                <div class="absolute top-0 right-0 p-4 opacity-5">
                    <BarChart3 class="w-20 h-20 text-admira-900" />
                </div>
                
                <div class="flex items-center gap-3 mb-6 text-admira-600 relative z-10">
                    <Filter class="w-5 h-5" />
                    <span class="font-bold uppercase tracking-wider text-xs">Parámetros de Cruce</span>
                </div>

                <div class="space-y-5 relative z-10">
                    <div>
                        <label class="text-[10px] font-black text-slate-400 uppercase ml-1 tracking-widest">Proyecto</label>
                        <div class="mt-1 p-3.5 bg-admira-50/50 rounded-2xl border border-admira-100 text-sm font-extrabold text-admira-700 flex items-center gap-2">
                            <div class="w-2 h-2 rounded-full bg-admira-500"></div>
                            {{ filtros.proyecto || 'Global' }}
                        </div>
                    </div>

                    <div>
                        <label class="text-[10px] font-black text-slate-400 uppercase ml-1 tracking-widest">Periodo de Análisis</label>
                        <div class="mt-1 p-3.5 bg-slate-50 rounded-2xl border border-slate-100 text-xs font-bold text-slate-600">
                            {{ filtros.fechaInicio }} <span class="mx-1 text-slate-300">|</span> {{ filtros.fechaFin }}
                        </div>
                    </div>

                    <button 
                        @click="generarReporteGlobal"
                        :disabled="generandoReporte"
                        class="w-full py-4 bg-slate-900 text-white rounded-2xl font-bold text-sm hover:bg-admira-600 transition-all flex items-center justify-center gap-3 shadow-xl shadow-slate-200 disabled:opacity-50 active:scale-95"
                    >
                        <Loader2 v-if="generandoReporte" class="w-5 h-5 animate-spin" />
                        <BarChart3 v-else class="w-5 h-5 text-admira-400" />
                        Calcular Auditoría
                    </button>
                </div>
            </div>

            <div v-if="datosReporte.length > 0" class="bg-slate-900 p-8 rounded-[2rem] text-white relative overflow-hidden shadow-2xl animate-in zoom-in-95 duration-500">
                <div class="absolute -right-4 -bottom-4 opacity-10">
                    <Activity class="w-40 h-40 text-admira-100" />
                </div>
                <div class="relative z-10">
                    <p class="text-admira-400 text-[10px] font-black uppercase tracking-[0.2em] mb-2">Uptime del Periodo</p>
                    <h3 class="text-5xl font-black mb-6 tracking-tighter">
                        {{ statsReporte.uptimeGlobal }}<span class="text-xl text-admira-400/50">%</span>
                    </h3>
                    
                    <div class="grid grid-cols-2 gap-4 border-t border-white/10 pt-6">
                        <div>
                            <p class="text-[9px] font-bold text-slate-400 uppercase mb-1">Total Equipos</p>
                            <p class="text-lg font-black">{{ statsReporte.total }}</p>
                        </div>
                        <div>
                            <p class="text-[9px] font-bold text-slate-400 uppercase mb-1">Fallos Detectados</p>
                            <p class="text-lg font-black text-rose-400">{{ statsReporte.fallosTotales }}</p>
                        </div>
                    </div>
                </div>
            </div>
        </div>

        <div class="xl:col-span-3">
            <div v-if="datosReporte.length === 0" class="h-full min-h-[500px] bg-white rounded-[3rem] border-2 border-dashed border-slate-200 flex flex-col items-center justify-center text-center p-12 transition-all">
                <div class="w-24 h-24 bg-slate-50 rounded-full flex items-center justify-center mb-6">
                    <FileText class="w-10 h-10 text-slate-300" />
                </div>
                <h4 class="text-2xl font-black text-slate-800 mb-2">Motor Analítico Listo</h4>
                <p class="text-slate-400 max-w-sm text-sm font-medium">Presiona el botón "Calcular Auditoría" para procesar el histórico de conexiones.</p>
            </div>

            <div v-else class="bg-white rounded-[2.5rem] border border-slate-100 shadow-sm overflow-hidden flex flex-col h-full animate-in slide-in-from-bottom-4 duration-500">
                
                <div class="p-6 border-b border-slate-50 bg-slate-50/30 flex flex-col md:flex-row items-center gap-4">
                    <div class="relative flex-1 w-full">
                        <Search class="absolute left-4 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400" />
                        <input 
                            v-model="busquedaInterna"
                            type="text" 
                            placeholder="Buscar player en los resultados..." 
                            class="w-full pl-12 pr-4 py-3 bg-white border border-slate-100 rounded-2xl text-sm font-bold focus:ring-2 focus:ring-admira-500/20 outline-none shadow-sm"
                        />
                    </div>
                    
                    <button 
                        @click="mostrarSoloInestables = !mostrarSoloInestables"
                        :class="`flex items-center gap-2 px-5 py-3 rounded-2xl font-bold text-xs transition-all border ${mostrarSoloInestables ? 'bg-rose-50 text-rose-600 border-rose-200 shadow-sm' : 'bg-white text-slate-500 border-slate-200 hover:bg-slate-50'}`"
                    >
                        <AlertTriangle class="w-4 h-4" />
                        Solo equipos inestables
                    </button>
                </div>

                <div class="overflow-auto max-h-[600px]">
                    <table class="w-full text-left">
                        <thead class="sticky top-0 bg-white/95 backdrop-blur-md z-10 shadow-sm">
                            <tr>
                                <th class="px-8 py-5 text-[10px] font-black text-slate-400 uppercase tracking-widest">Dispositivo</th>
                                <th class="px-8 py-5 text-[10px] font-black text-slate-400 uppercase tracking-widest text-center">Uptime</th>
                                <th class="px-8 py-5 text-[10px] font-black text-slate-400 uppercase tracking-widest text-center">Incidencias</th>
                                <th class="px-8 py-5 text-[10px] font-black text-slate-400 uppercase tracking-widest text-right">Último Estado</th>
                            </tr>
                        </thead>
                        <tbody class="divide-y divide-slate-50">
                            <tr v-if="reporteFiltrado.length === 0">
                                <td colspan="4" class="text-center py-10 text-slate-400 font-medium text-sm">No hay registros que coincidan.</td>
                            </tr>
                            <tr v-for="item in reporteFiltrado" :key="item.player" class="hover:bg-admira-50/30 transition-colors group">
                                <td class="px-8 py-5">
                                    <div class="font-black text-slate-700 text-sm group-hover:text-admira-600 transition-colors">{{ item.player }}</div>
                                    <div class="text-[10px] text-slate-400 font-bold uppercase tracking-tight">{{ item.proyecto }}</div>
                                </td>
                                <td class="px-8 py-5 text-center">
                                    <span :class="`text-xs font-black ${item.uptime === 100 ? 'text-admira-500' : item.uptime > 80 ? 'text-amber-500' : 'text-rose-500'}`">
                                        {{ item.uptime }}%
                                    </span>
                                </td>
                                <td class="px-8 py-5 text-center">
                                    <span :class="`px-3 py-1 rounded-lg text-xs font-bold ${item.caidas > 0 ? 'bg-rose-50 text-rose-600' : 'bg-slate-50 text-slate-400'}`">
                                        {{ item.caidas }} fallos
                                    </span>
                                </td>
                                <td class="px-8 py-5 text-right">
                                    <div class="flex flex-col items-end">
                                        <span :class="`inline-flex items-center gap-1.5 px-3 py-1 rounded-lg text-[9px] font-black uppercase border mb-1 ${item.alerta ? 'bg-rose-50 text-rose-600 border-rose-100' : 'bg-admira-50 text-admira-600 border-admira-100'}`">
                                            <div :class="`w-1.5 h-1.5 rounded-full ${item.alerta ? 'bg-rose-500' : 'bg-admira-500'}`"></div>
                                            {{ item.ultimo_estado }}
                                        </span>
                                        <span class="text-[10px] font-mono font-bold text-slate-400">{{ item.ultima_conexion }}</span>
                                    </div>
                                </td>
                            </tr>
                        </tbody>
                    </table>
                </div>
            </div>
        </div>
    </div>
  </div>
</template>