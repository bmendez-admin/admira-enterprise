<template>
  <Teleport to="body">
    <div v-if="player" class="fixed inset-0 z-[999] flex items-center justify-center p-2 sm:p-4 bg-slate-900/60 backdrop-blur-sm">
        <div class="bg-white rounded-3xl shadow-2xl w-full max-w-4xl flex flex-col max-h-[95vh] overflow-hidden relative">

            <div class="px-6 py-4 md:px-8 md:py-6 border-b flex justify-between items-center bg-white sticky top-0 z-10">
                <div class="flex items-center gap-4">
                    <div :class="['p-2.5 rounded-2xl hidden sm:block', player.alerta ? 'bg-rose-50 text-rose-600' : 'bg-emerald-50 text-emerald-600']">
                        <Monitor class="w-6 h-6"></Monitor>
                    </div>
                    <div>
                        <h3 class="text-lg md:text-xl font-black text-slate-800 truncate max-w-[200px] sm:max-w-md">{{ player.player }}</h3>
                        <div class="flex items-center gap-2 mt-1">
                            <span class="text-[10px] font-black text-white bg-slate-800 px-2 py-0.5 rounded uppercase">{{ player.proyecto }}</span>
                            <span :class="['text-[10px] font-black uppercase px-2 py-0.5 rounded border', player.alerta ? 'bg-rose-50 border-rose-100 text-rose-600' : 'bg-emerald-50 border-emerald-100 text-emerald-600']">
                                {{ player.alerta ? 'Sin Conexión' : 'Activo' }}
                            </span>
                        </div>
                    </div>
                </div>
                <button @click="$emit('cerrar')" class="p-2 text-slate-400 hover:text-rose-500 bg-slate-50 hover:bg-rose-50 rounded-xl transition-all">
                    <X class="w-6 h-6"></X>
                </button>
            </div>

            <div class="flex-1 overflow-y-auto p-4 md:p-8 bg-slate-50/50">

                <div v-if="cargando && historialGraficas.length === 0" class="w-full animate-pulse">
                    <div class="flex gap-3 mb-6">
                        <div class="w-48 h-10 bg-slate-200/70 rounded-xl"></div>
                        <div class="w-32 h-10 bg-slate-200/70 rounded-xl ml-auto"></div>
                    </div>
                    <div class="grid grid-cols-1 lg:grid-cols-3 gap-6">
                        <div class="bg-white p-6 rounded-2xl border border-slate-100 h-[320px] flex flex-col items-center justify-center">
                            <div class="w-40 h-40 border-[16px] border-slate-100 rounded-full"></div>
                        </div>
                        <div class="lg:col-span-2 bg-white p-6 rounded-2xl border border-slate-100 h-[320px] flex flex-col justify-end">
                            <div class="w-full h-24 bg-slate-100 rounded-sm mb-4"></div>
                        </div>
                    </div>
                </div>

                <div v-else-if="historialGraficas.length > 0">
                    <div class="flex flex-col sm:flex-row gap-3 mb-6">
                      <div class="flex bg-slate-200/50 p-1 rounded-xl">
                          <button @click="mostrarTabla = false" :class="['flex-1 sm:px-6 py-2 text-xs font-bold rounded-lg transition-all flex items-center justify-center gap-2', !mostrarTabla ? 'bg-white shadow-sm text-admira-600' : 'text-slate-500 hover:text-slate-700']">
                              <BarChart2 class="w-4 h-4"></BarChart2> Gráficas
                          </button>
                          <button @click="mostrarTabla = true" :class="['flex-1 sm:px-6 py-2 text-xs font-bold rounded-lg transition-all flex items-center justify-center gap-2', mostrarTabla ? 'bg-white shadow-sm text-admira-600' : 'text-slate-500 hover:text-slate-700']">
                              <Table class="w-4 h-4"></Table> Bitácora
                          </button>
                      </div>

                      <button @click="exportarExcel" class="flex-1 sm:flex-none flex items-center justify-center gap-2 px-5 py-2.5 ml-auto bg-white border border-slate-200 hover:border-emerald-400 text-emerald-600 hover:bg-emerald-50 text-xs font-bold rounded-xl shadow-sm transition-all group">
                        <FileSpreadsheet class="w-4 h-4 group-hover:scale-110 transition-transform"></FileSpreadsheet> Exportar Excel
                      </button>
                    </div>

                    <div v-if="!mostrarTabla" class="space-y-6 animate-in fade-in slide-in-from-bottom-2 duration-300">
                        <div class="grid grid-cols-1 lg:grid-cols-3 gap-6 items-stretch">

                          <div class="bg-white p-6 rounded-2xl border border-slate-100 shadow-sm flex flex-col items-center justify-between min-h-[320px]">
                            <h4 class="text-[11px] font-black uppercase tracking-wider text-slate-400 w-full text-center mb-0">Uptime Promedio</h4>
                            <div class="w-full flex-1 flex justify-center items-center">
                                <apexchart type="donut" width="100%" height="280" :options="pieOptions" :series="pieSeries" class="w-full"></apexchart>
                            </div>
                          </div>

                          <div class="lg:col-span-2 bg-white p-6 rounded-2xl border border-slate-100 shadow-sm flex flex-col justify-center relative min-h-[320px]">
                            <h4 class="text-[11px] font-black uppercase tracking-wider text-slate-400 mb-1">Historial de Trazabilidad</h4>
                            <p class="text-xs text-slate-400 mb-8">Muestra los últimos 100 movimientos de conexión registrados.</p>

                            <div class="flex items-center gap-[2px] w-full h-24 bg-slate-50 p-1.5 rounded-lg border border-slate-100" @mouseleave="ocultarTooltip">
                                <div v-for="(item, idx) in timelineData" :key="idx"
                                     @mousemove="mostrarTooltip($event, item)"
                                     class="flex-1 h-full rounded-[2px] hover:scale-y-110 hover:opacity-80 transition-all cursor-crosshair"
                                     :class="item.isOk ? 'bg-emerald-400' : 'bg-rose-400'">
                                </div>
                            </div>
                            <div class="flex justify-between items-center mt-3 px-1">
                                <span class="text-[9px] font-bold text-slate-400 uppercase tracking-widest text-left">Antiguo</span>
                                <span class="text-[9px] font-bold text-slate-400 uppercase tracking-widest text-right">Reciente</span>
                            </div>
                          </div>

                        </div>
                    </div>

                    <div v-else class="bg-white rounded-2xl border border-slate-100 shadow-sm overflow-hidden animate-in fade-in slide-in-from-bottom-2 duration-300 flex flex-col h-[500px]">
                        
                        <div class="flex-1 overflow-x-auto relative">
                            <div v-if="cargando" class="absolute inset-0 bg-white/70 backdrop-blur-sm z-10 flex flex-col items-center justify-center">
                                <Loader2 class="w-8 h-8 text-admira-600 animate-spin mb-2"></Loader2>
                                <span class="text-xs font-bold text-slate-500">Cargando página...</span>
                            </div>

                            <table class="w-full text-left text-xs min-h-full">
                                <thead class="bg-slate-50/50 border-b border-slate-100 font-black text-slate-400 uppercase tracking-wider sticky top-0">
                                    <tr>
                                        <th class="px-6 py-4">Fecha</th><th class="px-6 py-4">Hora</th><th class="px-6 py-4">Estado</th><th class="px-6 py-4 text-right">Origen</th>
                                    </tr>
                                </thead>
                                <tbody class="divide-y divide-slate-100">
                                    <tr v-for="(h, i) in historialPlayer" :key="i" class="hover:bg-slate-50/50 transition-colors">
                                        <td class="px-6 py-3.5 font-bold text-slate-600">{{ h.FECHA_LIMPIA }}</td>
                                        <td class="px-6 py-3.5 font-mono font-bold text-slate-500 bg-slate-50/50">{{ h.HORA_LIMPIA }}</td>
                                        <td class="px-6 py-3.5">
                                            <span :class="['px-2.5 py-1 rounded-md font-bold text-[10px] uppercase', h.ESTADO === 'Activo' || h.ESTADO === 'Emisión OK' ? 'bg-emerald-50 text-emerald-700' : 'bg-rose-50 text-rose-700']">
                                                {{ h.ESTADO }}
                                            </span>
                                        </td>
                                        <td class="px-6 py-3.5 text-right font-bold text-slate-400">{{ h.ORIGEN_LIMPIO }}</td>
                                    </tr>
                                </tbody>
                            </table>
                        </div>

                        <div class="px-6 py-4 border-t border-slate-100 flex items-center justify-between bg-slate-50/50">
                            <span class="text-xs font-bold text-slate-400">
                                Mostrando <span class="text-slate-600">{{ historialPlayer.length }}</span> de <span class="text-slate-600">{{ totalRegistros }}</span> reportes
                            </span>
                            
                            <div class="flex items-center gap-2">
                                <button @click="cambiarPagina(paginaActual - 1)" :disabled="paginaActual === 1 || cargando" 
                                        class="px-3 py-1.5 text-xs font-bold rounded-lg border border-slate-200 text-slate-500 hover:bg-white disabled:opacity-50 disabled:cursor-not-allowed transition-all">
                                    Anterior
                                </button>
                                <span class="text-xs font-black text-admira-600 bg-admira-50 px-3 py-1.5 rounded-lg border border-admira-100">
                                    {{ paginaActual }} / {{ totalPaginas }}
                                </span>
                                <button @click="cambiarPagina(paginaActual + 1)" :disabled="paginaActual === totalPaginas || cargando" 
                                        class="px-3 py-1.5 text-xs font-bold rounded-lg border border-slate-200 text-slate-500 hover:bg-white disabled:opacity-50 disabled:cursor-not-allowed transition-all">
                                    Siguiente
                                </button>
                            </div>
                        </div>

                    </div>
                </div>
            </div>
        </div>

        <div v-if="tooltipVisible"
             class="fixed z-[9999] pointer-events-none px-4 py-3 bg-slate-800 rounded-xl shadow-2xl transition-opacity duration-75 border border-slate-700"
             :style="{ top: tooltipY + 'px', left: tooltipX + 'px' }">
            <div class="flex items-center gap-2 mb-1.5">
                <span :class="['w-2.5 h-2.5 rounded-full', tooltipData.isOk ? 'bg-emerald-400' : 'bg-rose-400']"></span>
                <span class="text-[11px] font-black uppercase text-white">{{ tooltipData.estado }}</span>
            </div>
            <div class="text-[11px] text-slate-300 font-bold font-mono">{{ tooltipData.fecha }} <span class="text-slate-500">|</span> {{ tooltipData.hora }}</div>
        </div>
    </div>
  </Teleport>
</template>

<script setup>
import { ref, watch } from 'vue';
import { Monitor, X, Loader2, Table, BarChart2, FileSpreadsheet } from 'lucide-vue-next';
import { utils, writeFile } from 'xlsx';
import { useDashboard } from '../../composables/useDashboard';
import { useToastStore } from '../../stores/toast';
import admiraApi from '../../api/admiraApi';

const props = defineProps({ player: Object });
const emit = defineEmits(['cerrar']);
const { filtros } = useDashboard();
const toastStore = useToastStore();

const cargando = ref(false);
const mostrarTabla = ref(false);

const historialPlayer = ref([]); 
const historialGraficas = ref([]); 

const pieSeries = ref([]);
const timelineData = ref([]);

const paginaActual = ref(1);
const totalPaginas = ref(1);
const totalRegistros = ref(0);
const filasPorPagina = 15;

const tooltipVisible = ref(false);
const tooltipX = ref(0);
const tooltipY = ref(0);
const tooltipData = ref({});

const mostrarTooltip = (e, item) => {
    tooltipData.value = item;
    tooltipX.value = e.clientX + 15;
    tooltipY.value = e.clientY + 15;
    tooltipVisible.value = true;
};
const ocultarTooltip = () => { tooltipVisible.value = false; };

// 🌟 OPCIONES DE GRÁFICA ACTUALIZADAS PARA MAXIMIZAR TAMAÑO
const pieOptions = ref({
    chart: { 
        type: 'donut', 
        fontFamily: 'inherit', 
        animations: { speed: 400 },
        parentHeightOffset: 0 // Quita márgenes extra del contenedor padre
    },
    labels: ['Conexión OK', 'Caídas'],
    colors: ['#10b981', '#f43f5e'],
    stroke: { width: 2, colors: ['#ffffff'] },
    plotOptions: {
        pie: { 
            customScale: 1, // TRUCO: Fuerza a la gráfica a ser un 15% más grande
            expandOnClick: false, // TRUCO: Quita el espacio invisible que reserva para las animaciones de clic
            donut: { 
                size: '65%', // Rebanadas más gruesas
                labels: { 
                    show: true, 
                    name: { show: false }, 
                    value: { show: true, fontSize: '32px', fontWeight: 900, color: '#1e293b', offsetY: 8 },
                    total: { 
                        show: true, 
                        showAlways: true, 
                        formatter: function (w) {
                            const ok = w.globals.seriesTotals[0] || 0;
                            const caidas = w.globals.seriesTotals[1] || 0;
                            const total = ok + caidas;
                            return total === 0 ? '0%' : Math.round((ok / total) * 100) + '%';
                        }
                    }
                }
            } 
        }
    },
    dataLabels: { 
        enabled: true, 
        style: { fontSize: '14px', fontWeight: 'bold' }, 
        dropShadow: { enabled: false } 
    },
    legend: { 
        position: 'bottom', 
        fontSize: '12px', 
        fontWeight: 'bold', 
        markers: { radius: 12 }, 
        itemMargin: { horizontal: 15, vertical: 0 } 
    }
});

const cargarGraficas = async () => {
    const { data } = await admiraApi.get('/tabla', {
        params: { player: props.player.player, fecha_inicio: filtros.fechaInicio || null, fecha_fin: filtros.fechaFin || null, pagina: 1, filas_por_pagina: 100 }
    });

    historialGraficas.value = data.items.map(i => {
        let origenLimpio = 'SISTEMA';
        if (i.ARCHIVO_ORIGEN) { origenLimpio = i.ARCHIVO_ORIGEN.replace(/\.(xlsx|xls|csv)$/i, ''); }
        return { ...i, FECHA_LIMPIA: i.FECHA ? i.FECHA.split('T')[0] : '---', HORA_LIMPIA: i.HORARIO_LEGIBLE ? i.HORARIO_LEGIBLE.replace('REPORTE', '').trim() : '---', ORIGEN_LIMPIO: origenLimpio };
    });

    const activos = historialGraficas.value.filter(i => i.ESTADO === 'Emisión OK' || i.ESTADO === 'Activo').length;
    pieSeries.value = [activos, historialGraficas.value.filter(i => i.ESTADO === 'Sin conexión').length];
    timelineData.value = [...historialGraficas.value].reverse().map(i => ({ estado: i.ESTADO, isOk: i.ESTADO === 'Emisión OK' || i.ESTADO === 'Activo', fecha: i.FECHA_LIMPIA, hora: i.HORA_LIMPIA }));
};

const cargarTabla = async () => {
    const { data } = await admiraApi.get('/tabla', {
        params: { player: props.player.player, fecha_inicio: filtros.fechaInicio || null, fecha_fin: filtros.fechaFin || null, pagina: paginaActual.value, filas_por_pagina: filasPorPagina }
    });

    totalPaginas.value = data.total_paginas;
    totalRegistros.value = data.total_registros;

    historialPlayer.value = data.items.map(i => {
        let origenLimpio = 'SISTEMA';
        if (i.ARCHIVO_ORIGEN) { origenLimpio = i.ARCHIVO_ORIGEN.replace(/\.(xlsx|xls|csv)$/i, ''); }
        return { ...i, FECHA_LIMPIA: i.FECHA ? i.FECHA.split('T')[0] : '---', HORA_LIMPIA: i.HORARIO_LEGIBLE ? i.HORARIO_LEGIBLE.replace('REPORTE', '').trim() : '---', ORIGEN_LIMPIO: origenLimpio };
    });
};

watch(() => props.player, async (nuevoPlayer) => {
    if (!nuevoPlayer) return;
    cargando.value = true;
    mostrarTabla.value = false;
    paginaActual.value = 1;
    ocultarTooltip();

    try {
        await Promise.all([cargarGraficas(), cargarTabla()]);
    } catch (e) {
        console.error("Error", e);
        toastStore.agregarToast({ tipo: 'error', titulo: 'Fallo de conexión', mensaje: 'No se pudo cargar el historial del reproductor.' });
    } finally {
        cargando.value = false;
    }
});

const cambiarPagina = async (nuevaPagina) => {
    if (nuevaPagina >= 1 && nuevaPagina <= totalPaginas.value) {
        paginaActual.value = nuevaPagina;
        cargando.value = true; 
        try {
            await cargarTabla(); 
        } catch (e) {
            toastStore.agregarToast({ tipo: 'error', titulo: 'Error de paginación', mensaje: 'No se pudo cargar la página solicitada.' });
        } finally {
            cargando.value = false;
        }
    }
};

const exportarExcel = () => {
    if (!historialGraficas.value.length) return;

    try {
        const total = historialGraficas.value.length;
        const ok = historialGraficas.value.filter(i => i.ESTADO === 'Emisión OK' || i.ESTADO === 'Activo').length;
        const caidas = total - ok;
        const uptime = total === 0 ? 0 : Math.round((ok / total) * 100);
        const fechaEmision = new Date().toLocaleString('es-MX', { year: 'numeric', month: '2-digit', day: '2-digit', hour: '2-digit', minute: '2-digit' });

        const datosExcel = [
            ['REPORTE EJECUTIVO DE SALUD DE RED'], [], ['FICHA TÉCNICA'],
            ['Player:', props.player.player], ['Proyecto:', props.player.proyecto], ['Fecha de Emisión:', fechaEmision], [],
            ['RESUMEN OPERATIVO'], ['Total de Reportes:', total, '', 'Disponibilidad (Uptime):', `${uptime}%`],
            ['Conexiones OK:', ok, '', 'Caídas:', caidas], [],
            ['BITÁCORA DE TRAZABILIDAD (Últimos 100 reportes)'], ['FECHA', 'HORA', 'ESTADO', 'ARCHIVO ORIGEN']
        ];

        historialGraficas.value.forEach(h => { datosExcel.push([h.FECHA_LIMPIA, h.HORA_LIMPIA, h.ESTADO, h.ORIGEN_LIMPIO]); });

        const ws = utils.aoa_to_sheet(datosExcel);
        ws['!cols'] = [{ wch: 22 }, { wch: 20 }, { wch: 18 }, { wch: 38 }, { wch: 15 }];
        ws['!merges'] = [{ s: { r: 0, c: 0 }, e: { r: 0, c: 4 } }, { s: { r: 2, c: 0 }, e: { r: 2, c: 4 } }, { s: { r: 7, c: 0 }, e: { r: 7, c: 4 } }, { s: { r: 11, c: 0 }, e: { r: 11, c: 4 } }];

        const wb = utils.book_new();
        utils.book_append_sheet(wb, ws, "Reporte Salud");
        writeFile(wb, `Reporte_${props.player.player}.xlsx`);

        toastStore.agregarToast({ tipo: 'success', titulo: 'Exportación Exitosa', mensaje: 'El archivo Excel se descargó correctamente.' });
    } catch (e) {
        toastStore.agregarToast({ tipo: 'error', titulo: 'Error', mensaje: 'No se pudo generar el archivo Excel.' });
    }
};

defineExpose({ cambiarPagina });
</script>