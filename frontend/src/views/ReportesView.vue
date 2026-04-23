<script setup>
import {
    FileText, Trash2, FileSpreadsheet, Filter, BarChart3,
    Search, Loader2, ChevronUp, ChevronDown, ChevronLeft, ChevronRight
} from 'lucide-vue-next';
import { useDashboard } from '../composables/useDashboard';
import { useReportes } from '../composables/useReportes';
import { useToastStore } from '../stores/toast';
import { utils, writeFile } from 'xlsx';

const { filtros } = useDashboard();
const toastStore = useToastStore();
const {
    datosReporte, generandoReporte, busquedaInterna, mostrarSoloInestables,
    paginaActual, totalPaginas, statsReporte, reportePaginado, reporteFiltrado,
    generarReporteGlobal, limpiarAnalisis, toggleOrden, ordenCampo, ordenDireccion
} = useReportes(filtros);

const handleGenerar = async () => {
    try {
        await generarReporteGlobal();
        toastStore.agregarToast({ titulo: 'Análisis Finalizado', mensaje: `Se procesaron ${datosReporte.value.length} dispositivos.` });
    } catch (e) {
        toastStore.agregarToast({ tipo: 'error', titulo: 'Error', mensaje: 'No se pudo conectar con el motor de auditoría.' });
    }
};

const exportarCSV = () => {
    if (!reporteFiltrado.value.length) return;
    const headers = ['PROYECTO', 'PLAYER', 'UPTIME %', 'FALLOS', 'TOTAL REPORTES', 'ULTIMO ESTADO'];
    const filas = reporteFiltrado.value.map(d => [
        `"${d.proyecto}"`, `"${d.player}"`, `"${d.uptime}%"`, `"${d.caidas}"`, `"${d.total_reportes}"`, `"${d.ultimo_estado}"`
    ]);
    const csvContent = '\uFEFF' + [headers.join(','), ...filas.map(f => f.join(','))].join('\n');
    const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
    const link = document.createElement("a");
    link.href = URL.createObjectURL(blob);
    link.download = `Reporte_Auditoria_${filtros.fechaInicio}.csv`;
    link.click();
};

// Función auxiliar para el color de la barra
const getUptimeColor = (u) => {
    if (u >= 99) return 'bg-emerald-500';
    if (u >= 90) return 'bg-amber-500';
    return 'bg-rose-500';
};

const exportarExcelProfesional = () => {
    if (!reporteFiltrado.value.length) return;

    try {
        const fechaEmision = new Date().toLocaleString('es-MX', {
            year: 'numeric', month: '2-digit', day: '2-digit', hour: '2-digit', minute: '2-digit'
        });

        // 1. Preparamos el Lienzo de Datos (AOA - Array of Arrays)
        const datosExcel = [
            ['REPORTE CONSOLIDADO DE AUDITORÍA Y DISPONIBILIDAD (SLA)'],
            [],
            ['FICHA TÉCNICA DEL ANÁLISIS'],
            ['Proyecto:', filtros.proyecto || 'Global (Todos los Proyectos)'],
            ['Periodo Evaluado:', `${filtros.fechaInicio} al ${filtros.fechaFin}`],
            ['Fecha de Generación:', fechaEmision],
            [],
            ['RESUMEN EJECUTIVO GLOBAL'],
            ['Disponibilidad General:', `${statsReporte.value.uptimeGlobal}%`, '', 'Total Dispositivos:', statsReporte.value.total],
            ['Total de Incidencias:', statsReporte.value.fallosTotales, '', 'Estado de Red:', statsReporte.value.uptimeGlobal >= 95 ? 'ÓPTIMO' : 'REQUIERE ATENCIÓN'],
            [],
            ['DETALLE DE AUDITORÍA POR DISPOSITIVO'],
            ['NOMBRE DEL PLAYER', 'PROYECTO', 'UPTIME %', 'CAÍDAS', 'REPORTES TOTALES', 'ÚLTIMO ESTADO']
        ];

        // 2. Inyectamos las filas de la tabla (usando los datos ya filtrados y ordenados)
        reporteFiltrado.value.forEach(d => {
            datosExcel.push([
                d.player,
                d.proyecto.toUpperCase(),
                `${d.uptime}%`,
                d.caidas,
                d.total_reportes,
                d.ultimo_estado
            ]);
        });

        // 3. Crear la hoja de cálculo
        const ws = utils.aoa_to_sheet(datosExcel);

        // 4. Configuración de Diseño (Anchos de Columna)
        ws['!cols'] = [
            { wch: 35 }, // Player
            { wch: 20 }, // Proyecto
            { wch: 15 }, // Uptime
            { wch: 12 }, // Caídas
            { wch: 18 }, // Total
            { wch: 20 }  // Estado
        ];

        // 5. Fusión de Celdas (Merges) para que se vea Ejecutivo
        ws['!merges'] = [
            { s: { r: 0, c: 0 }, e: { r: 0, c: 5 } }, // Título principal
            { s: { r: 2, c: 0 }, e: { r: 2, c: 5 } }, // Ficha técnica
            { s: { r: 7, c: 0 }, e: { r: 7, c: 5 } }, // Resumen ejecutivo
            { s: { r: 11, c: 0 }, e: { r: 11, c: 5 } } // Detalle tabla
        ];

        // 6. Generar el archivo
        const wb = utils.book_new();
        utils.book_append_sheet(wb, ws, "Auditoría Consolidada");

        const nombreArchivo = `AUDITORIA_${(filtros.proyecto || 'GLOBAL').replace(/\s+/g, '_')}_${filtros.fechaInicio}.xlsx`;
        writeFile(wb, nombreArchivo);

        toastStore.agregarToast({
            titulo: 'Excel Generado',
            mensaje: 'El reporte de auditoría se ha descargado correctamente.'
        });
    } catch (e) {
        console.error("Error al exportar:", e);
        toastStore.agregarToast({
            tipo: 'error',
            titulo: 'Error de Exportación',
            mensaje: 'No se pudo generar el archivo Excel.'
        });
    }
};

</script>

<template>
    <div class="flex flex-col h-full animate-in fade-in duration-700 pb-12">

        <div class="flex flex-col md:flex-row md:justify-between md:items-end gap-4 mb-8">
            <div>
                <h2 class="text-2xl md:text-3xl font-black text-slate-800 tracking-tight">Reportes Ejecutivos</h2>
                <p class="text-xs md:text-sm text-slate-500 font-medium mt-1">Auditoría consolidada de disponibilidad de
                    red.</p>
            </div>

            <div v-if="datosReporte.length > 0" class="flex gap-3">
                <button @click="limpiarAnalisis"
                    class="p-2.5 bg-white border border-slate-200 text-slate-400 hover:text-rose-600 rounded-xl transition-all shadow-sm">
                    <Trash2 class="w-5 h-5" />
                </button>
                <button @click="exportarExcelProfesional"
                    class="flex items-center gap-2 px-6 py-2.5 bg-emerald-600 text-white rounded-xl font-bold text-xs shadow-lg shadow-emerald-200 active:scale-95 transition-all">
                    <FileSpreadsheet class="w-4 h-4" /> Exportar Excel
                </button>
            </div>
        </div>

        <div class="grid grid-cols-1 xl:grid-cols-4 gap-8">

            <div class="xl:col-span-1 space-y-6">
                <div class="bg-white p-6 rounded-[2rem] border border-slate-100 shadow-sm">
                    <div class="flex items-center gap-3 mb-6 text-admira-600">
                        <Filter class="w-5 h-5" />
                        <span class="font-bold uppercase tracking-wider text-[10px]">Parámetros</span>
                    </div>
                    <div class="space-y-5">
                        <div>
                            <label class="text-[10px] font-black text-slate-400 uppercase tracking-widest">Proyecto
                                Actual</label>
                            <div
                                class="mt-1 p-3.5 bg-admira-50/50 rounded-2xl border border-admira-100 text-xs font-extrabold text-admira-700 truncate">
                                {{ filtros.proyecto || 'Todos los Proyectos' }}
                            </div>
                        </div>
                        <div>
                            <label class="text-[10px] font-black text-slate-400 uppercase tracking-widest">Rango de
                                Fecha</label>
                            <div
                                class="mt-1 p-3.5 bg-slate-50 rounded-2xl border border-slate-100 text-[10px] font-bold text-slate-600">
                                {{ filtros.fechaInicio }} <span class="mx-1">➜</span> {{ filtros.fechaFin }}
                            </div>
                        </div>
                        <button @click="handleGenerar" :disabled="generandoReporte"
                            class="w-full py-4 bg-slate-900 text-white rounded-2xl font-bold text-sm flex items-center justify-center gap-3 active:scale-95 transition-all disabled:opacity-50">
                            <Loader2 v-if="generandoReporte" class="w-5 h-5 animate-spin" />
                            <BarChart3 v-else class="w-5 h-5 text-admira-400" />
                            Calcular Auditoría
                        </button>
                    </div>
                </div>

                <div class="bg-slate-900 p-8 rounded-[2rem] text-white shadow-2xl relative overflow-hidden group">
                    <div
                        class="absolute -right-4 -top-4 w-24 h-24 bg-white/5 rounded-full blur-2xl group-hover:bg-admira-500/10 transition-all">
                    </div>
                    <p class="text-admira-400 text-[10px] font-black uppercase tracking-widest mb-2">Disponibilidad
                        Global</p>
                    <h3 class="text-5xl font-black mb-8 tracking-tighter">
                        {{ statsReporte.uptimeGlobal }}<span class="text-xl text-admira-400/50">%</span>
                    </h3>
                    <div class="grid grid-cols-2 gap-4 border-t border-white/10 pt-6">
                        <div>
                            <p class="text-[9px] font-bold text-slate-400 uppercase mb-1">Total Equipos</p>
                            <p class="text-lg font-black">{{ statsReporte.total }}</p>
                        </div>
                        <div>
                            <p class="text-[9px] font-bold text-slate-400 uppercase mb-1">Incidencias</p>
                            <p class="text-lg font-black text-rose-400">{{ statsReporte.fallosTotales }}</p>
                        </div>
                    </div>
                </div>
            </div>

            <div class="xl:col-span-3">
                <div v-if="datosReporte.length === 0"
                    class="h-full min-h-[500px] bg-white rounded-[2.5rem] border-2 border-dashed border-slate-200 flex flex-col items-center justify-center text-center p-8">
                    <div class="w-20 h-20 bg-slate-50 rounded-full flex items-center justify-center mb-4">
                        <FileText class="w-10 h-10 text-slate-200" />
                    </div>
                    <h4 class="text-xl font-bold text-slate-800">Motor de Auditoría</h4>
                    <p class="text-slate-400 text-xs mt-2 max-w-[280px]">Configura los filtros y presiona calcular para
                        ver el análisis de SLA por dispositivo.</p>
                </div>

                <div v-else
                    class="bg-white rounded-[2rem] border border-slate-100 shadow-sm overflow-hidden flex flex-col h-full animate-in slide-in-from-right-4 duration-500">
                    <div class="p-5 border-b flex flex-col sm:flex-row items-center gap-4 bg-slate-50/30">
                        <div class="relative flex-1 w-full">
                            <Search class="absolute left-4 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400" />
                            <input v-model="busquedaInterna" type="text" placeholder="Filtrar por nombre o proyecto..."
                                class="w-full pl-11 pr-4 py-3 bg-white border border-slate-200 rounded-2xl text-xs font-bold shadow-sm focus:border-admira-400 outline-none transition-all" />
                        </div>
                        <button @click="mostrarSoloInestables = !mostrarSoloInestables"
                            :class="`w-full sm:w-auto px-6 py-3 rounded-2xl font-bold text-[10px] transition-all border ${mostrarSoloInestables ? 'bg-rose-50 text-rose-600 border-rose-200 shadow-sm shadow-rose-100' : 'bg-white text-slate-500 border-slate-200 hover:bg-slate-50'}`">
                            Solo Críticos (< 100%) </button>
                    </div>

                    <div class="overflow-x-auto flex-1">
                        <table class="w-full text-left">
                            <thead>
                                <tr class="text-[10px] font-black text-slate-400 uppercase tracking-widest border-b">
                                    <th @click="toggleOrden('player')"
                                        class="px-8 py-5 cursor-pointer hover:text-admira-600 transition-colors">
                                        <div class="flex items-center gap-2">Dispositivo
                                            <ChevronUp v-if="ordenCampo === 'player'" class="w-3 h-3"
                                                :class="ordenDireccion === 'desc' ? 'rotate-180' : ''" />
                                        </div>
                                    </th>
                                    <th @click="toggleOrden('uptime')"
                                        class="px-8 py-5 cursor-pointer hover:text-admira-600 transition-colors">
                                        <div class="flex items-center justify-center gap-2">SLA Uptime
                                            <ChevronUp v-if="ordenCampo === 'uptime'" class="w-3 h-3"
                                                :class="ordenDireccion === 'desc' ? 'rotate-180' : ''" />
                                        </div>
                                    </th>
                                    <th @click="toggleOrden('caidas')"
                                        class="px-8 py-5 text-center cursor-pointer hover:text-admira-600 transition-colors">
                                        <div class="flex items-center justify-center gap-2">Caídas
                                            <ChevronUp v-if="ordenCampo === 'caidas'" class="w-3 h-3"
                                                :class="ordenDireccion === 'desc' ? 'rotate-180' : ''" />
                                        </div>
                                    </th>
                                    <th class="px-8 py-5 text-right">Último Reporte</th>
                                </tr>
                            </thead>
                            <tbody class="divide-y divide-slate-50">
                                <tr v-for="item in reportePaginado" :key="item.player"
                                    class="hover:bg-slate-50/50 group transition-all">
                                    <td class="px-8 py-5">
                                        <div
                                            class="font-bold text-slate-800 group-hover:text-admira-600 transition-colors">
                                            {{ item.player }}</div>
                                        <div class="text-[9px] text-slate-400 font-bold uppercase tracking-tighter">{{
                                            item.proyecto }}</div>
                                    </td>
                                    <td class="px-8 py-5">
                                        <div class="flex flex-col gap-1.5 w-48 mx-auto">
                                            <div class="flex justify-between items-center text-[10px] font-black">
                                                <span
                                                    :class="item.uptime < 100 ? 'text-amber-600' : 'text-emerald-600'">{{
                                                    item.uptime }}%</span>
                                            </div>
                                            <div class="w-full h-1.5 bg-slate-100 rounded-full overflow-hidden">
                                                <div :class="`h-full rounded-full transition-all duration-1000 ${getUptimeColor(item.uptime)}`"
                                                    :style="`width: ${item.uptime}%`"></div>
                                            </div>
                                        </div>
                                    </td>
                                    <td class="px-8 py-5 text-center">
                                        <span
                                            :class="`inline-flex items-center justify-center w-8 h-8 rounded-xl font-black text-xs ${item.caidas > 0 ? 'bg-rose-50 text-rose-600 border border-rose-100' : 'bg-slate-50 text-slate-300'}`">
                                            {{ item.caidas }}
                                        </span>
                                    </td>
                                    <td class="px-8 py-5 text-right">
                                        <div
                                            class="text-[10px] font-bold text-slate-600 bg-slate-100 px-3 py-1 rounded-lg inline-block">
                                            {{ item.ultima_conexion.replace('REPORTE', '').trim() }}
                                        </div>
                                    </td>
                                </tr>
                            </tbody>
                        </table>
                    </div>

                    <div
                        class="p-6 border-t bg-slate-50/30 flex flex-col sm:flex-row items-center justify-between gap-4">
                        <p class="text-xs font-bold text-slate-400">
                            Resultados <span class="text-slate-800">{{ reporteFiltrado.length }}</span> dispositivos
                        </p>
                        <div class="flex items-center gap-2">
                            <button @click="paginaActual--" :disabled="paginaActual === 1"
                                class="p-2 bg-white border border-slate-200 rounded-xl disabled:opacity-30 hover:bg-slate-50 transition-all">
                                <ChevronLeft class="w-4 h-4" />
                            </button>
                            <div class="flex gap-1">
                                <span
                                    class="px-4 py-2 bg-slate-900 text-white rounded-xl text-xs font-bold shadow-md shadow-slate-200">
                                    {{ paginaActual }} / {{ totalPaginas }}
                                </span>
                            </div>
                            <button @click="paginaActual++" :disabled="paginaActual === totalPaginas"
                                class="p-2 bg-white border border-slate-200 rounded-xl disabled:opacity-30 hover:bg-slate-50 transition-all">
                                <ChevronRight class="w-4 h-4" />
                            </button>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    </div>
</template>