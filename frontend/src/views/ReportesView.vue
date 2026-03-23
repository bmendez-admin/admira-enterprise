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
  <div class="flex flex-col h-full animate-in fade-in duration-700 pb-12">
    
    <div class="flex flex-col md:flex-row md:justify-between md:items-end gap-4 mb-8">
        <div class="text-center md:text-left">
            <h2 class="text-2xl md:text-3xl font-black text-slate-800 tracking-tight">Reportes Ejecutivos</h2>
            <p class="text-xs md:text-sm text-slate-500 font-medium mt-1">Auditoría consolidada y disponibilidad histórica.</p>
        </div>
        
        <div v-if="datosReporte.length > 0" class="flex flex-wrap justify-center md:justify-end gap-2 md:gap-3">
            <button @click="limpiarAnalisis" class="p-2.5 bg-white border border-slate-200 text-slate-400 hover:text-rose-600 rounded-xl transition-all"><Trash2 class="w-5 h-5" /></button>
            <button @click="exportarExcelProfesional" class="flex items-center gap-2 px-6 py-2.5 bg-emerald-500 text-white rounded-xl font-bold text-xs shadow-lg shadow-emerald-200 active:scale-95 transition-all">
                <FileSpreadsheet class="w-4 h-4" /> Exportar CSV
            </button>
        </div>
    </div>

    <div class="grid grid-cols-1 xl:grid-cols-4 gap-6 md:gap-8">
        
        <div class="xl:col-span-1 space-y-4 md:space-y-6">
            <div class="bg-white p-6 rounded-[2rem] border border-slate-100 shadow-sm">
                <div class="flex items-center gap-3 mb-6 text-admira-600">
                    <Filter class="w-5 h-5" />
                    <span class="font-bold uppercase tracking-wider text-[10px]">Parámetros</span>
                </div>

                <div class="space-y-4 md:space-y-5">
                    <div>
                        <label class="text-[10px] font-black text-slate-400 uppercase tracking-widest">Proyecto</label>
                        <div class="mt-1 p-3.5 bg-admira-50/50 rounded-2xl border border-admira-100 text-xs font-extrabold text-admira-700 truncate">
                            {{ filtros.proyecto || 'Global' }}
                        </div>
                    </div>
                    <div>
                        <label class="text-[10px] font-black text-slate-400 uppercase tracking-widest">Periodo</label>
                        <div class="mt-1 p-3.5 bg-slate-50 rounded-2xl border border-slate-100 text-[10px] font-bold text-slate-600">
                            {{ filtros.fechaInicio }} <span class="mx-1">➜</span> {{ filtros.fechaFin }}
                        </div>
                    </div>
                    <button @click="generarReporteGlobal" :disabled="generandoReporte"
                        class="w-full py-4 bg-slate-900 text-white rounded-2xl font-bold text-sm flex items-center justify-center gap-3 active:scale-95 transition-all">
                        <Loader2 v-if="generandoReporte" class="w-5 h-5 animate-spin" />
                        <BarChart3 v-else class="w-5 h-5 text-admira-400" />
                        Calcular Auditoría
                    </button>
                </div>
            </div>

            <div v-if="datosReporte.length > 0" class="bg-slate-900 p-6 md:p-8 rounded-[2rem] text-white shadow-2xl">
                <p class="text-admira-400 text-[10px] font-black uppercase tracking-widest mb-2">Uptime Global</p>
                <h3 class="text-4xl md:text-5xl font-black mb-6 tracking-tighter">
                    {{ statsReporte.uptimeGlobal }}<span class="text-xl text-admira-400/50">%</span>
                </h3>
                <div class="grid grid-cols-2 gap-4 border-t border-white/10 pt-6">
                    <div><p class="text-[9px] font-bold text-slate-400 uppercase mb-1">Equipos</p><p class="text-base font-black">{{ statsReporte.total }}</p></div>
                    <div><p class="text-[9px] font-bold text-slate-400 uppercase mb-1">Fallos</p><p class="text-base font-black text-rose-400">{{ statsReporte.fallosTotales }}</p></div>
                </div>
            </div>
        </div>

        <div class="xl:col-span-3">
            <div v-if="datosReporte.length === 0" class="h-full min-h-[300px] md:min-h-[500px] bg-white rounded-[2.5rem] border-2 border-dashed border-slate-200 flex flex-col items-center justify-center text-center p-8">
                <FileText class="w-12 h-12 text-slate-200 mb-4" />
                <h4 class="text-xl font-bold text-slate-800">Motor de Análisis Listo</h4>
                <p class="text-slate-400 text-xs mt-2 max-w-[250px]">Presiona el botón para procesar los datos históricos.</p>
            </div>

            <div v-else class="bg-white rounded-[2rem] border border-slate-100 shadow-sm overflow-hidden flex flex-col h-full">
                <div class="p-4 md:p-6 border-b flex flex-col sm:flex-row items-center gap-3 md:gap-4 bg-slate-50/30">
                    <div class="relative flex-1 w-full">
                        <Search class="absolute left-4 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400" />
                        <input v-model="busquedaInterna" type="text" placeholder="Buscar player..." class="w-full pl-11 pr-4 py-3 bg-white border border-slate-100 rounded-2xl text-xs font-bold shadow-sm outline-none" />
                    </div>
                    <button @click="mostrarSoloInestables = !mostrarSoloInestables"
                        :class="`w-full sm:w-auto px-5 py-3 rounded-2xl font-bold text-[10px] transition-all border ${mostrarSoloInestables ? 'bg-rose-50 text-rose-600 border-rose-200' : 'bg-white text-slate-500 border-slate-200'}`">
                        Solo Inestables
                    </button>
                </div>

                <div class="overflow-x-auto">
                    <div class="min-w-[700px]">
                      <table class="w-full text-left">
                          <thead class="bg-white sticky top-0 border-b">
                              <tr class="text-[10px] font-black text-slate-400 uppercase tracking-widest">
                                  <th class="px-8 py-5">Dispositivo</th>
                                  <th class="px-8 py-5 text-center">Uptime</th>
                                  <th class="px-8 py-5 text-center">Fallos</th>
                                  <th class="px-8 py-5 text-right">Estatus</th>
                              </tr>
                          </thead>
                          <tbody class="divide-y divide-slate-50 text-xs">
                              <tr v-for="item in reporteFiltrado" :key="item.player" class="hover:bg-slate-50/50 group transition-all">
                                  <td class="px-8 py-5">
                                      <div class="font-bold text-slate-800 group-hover:text-admira-600">{{ item.player }}</div>
                                      <div class="text-[9px] text-slate-400 font-bold">{{ item.proyecto }}</div>
                                  </td>
                                  <td class="px-8 py-5 text-center font-black text-slate-800">{{ item.uptime }}%</td>
                                  <td class="px-8 py-5 text-center"><span :class="`px-2.5 py-1 rounded-lg font-bold ${item.caidas > 0 ? 'bg-rose-50 text-rose-600' : 'bg-slate-50 text-slate-400'}`">{{ item.caidas }}</span></td>
                                  <td class="px-8 py-5 text-right">
                                      <div class="inline-flex items-center gap-1.5 px-2 py-0.5 rounded border font-black uppercase text-[9px]" :class="item.alerta ? 'bg-rose-50 border-rose-100 text-rose-700' : 'bg-emerald-50 border-emerald-100 text-emerald-700'">
                                        <div :class="`w-1.5 h-1.5 rounded-full ${item.alerta ? 'bg-rose-500' : 'bg-emerald-500'}`"></div>
                                        {{ item.ultimo_estado }}
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
  </div>
</template>