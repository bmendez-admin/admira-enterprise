<script setup>
import { ref, computed, onMounted, watch } from 'vue';
import { Search, Monitor, RefreshCw, XCircle, ArrowDownAZ, ChevronDown, FileSpreadsheet, Loader2 } from 'lucide-vue-next';
import { utils, writeFile } from 'xlsx';
import { useDashboard } from '../composables/useDashboard';
import { useToastStore } from '../stores/toast';
import admiraApi from '../api/admiraApi';
import PlayerModal from '../components/monitoreo/PlayerModal.vue';

const { dispositivosMonitoreo, cargarMonitoreo, cargando, filtros } = useDashboard();
const toastStore = useToastStore();

const busqueda = ref('');
const filtroEstado = ref('todos'); 
const orden = ref('estado'); 
const dropdownAbierto = ref(false);
const playerSeleccionado = ref(null); 

// LÓGICA DE SELECCIÓN MÚLTIPLE
const seleccionados = ref([]);
const exportandoMasivo = ref(false);

const toggleSeleccion = (player) => {
    const index = seleccionados.value.findIndex(p => p.player === player.player);
    if (index === -1) {
        seleccionados.value.push(player);
    } else {
        seleccionados.value.splice(index, 1);
    }
};

const exportarSeleccionadosExcel = async () => {
    if (seleccionados.value.length === 0) return;
    
    exportandoMasivo.value = true;
    toastStore.agregarToast({ 
        tipo: 'success', 
        titulo: 'Generando Reporte', 
        mensaje: `Obteniendo historial de ${seleccionados.value.length} reproductores. Esto puede tomar unos segundos...`, 
        duracion: 3000 
    });

    try {
        const wb = utils.book_new();
        const fechaEmision = new Date().toLocaleString('es-MX', { year: 'numeric', month: '2-digit', day: '2-digit', hour: '2-digit', minute: '2-digit' });

        const promesas = seleccionados.value.map(async (dev) => {
            try {
                const { data } = await admiraApi.get('/tabla', {
                    params: { player: dev.player, fecha_inicio: filtros.fechaInicio || null, fecha_fin: filtros.fechaFin || null, filas_por_pagina: 100 }
                });

                const historial = data.items.map(i => {
                    let origenLimpio = 'SISTEMA';
                    if (i.ARCHIVO_ORIGEN) origenLimpio = i.ARCHIVO_ORIGEN.replace(/\.(xlsx|xls|csv)$/i, '');
                    return { 
                        ...i, 
                        FECHA_LIMPIA: i.FECHA ? i.FECHA.split('T')[0] : '---', 
                        HORA_LIMPIA: i.HORARIO_LEGIBLE ? i.HORARIO_LEGIBLE.replace('REPORTE', '').trim() : '---', 
                        ORIGEN_LIMPIO: origenLimpio 
                    };
                });

                const total = historial.length;
                const ok = historial.filter(i => i.ESTADO === 'Emisión OK' || i.ESTADO === 'Activo').length;
                const caidas = total - ok;
                const uptime = total === 0 ? 0 : Math.round((ok / total) * 100);

                const datosExcel = [
                    ['REPORTE EJECUTIVO DE SALUD DE RED'], [], ['FICHA TÉCNICA'], 
                    ['Player:', dev.player], ['Proyecto:', dev.proyecto], ['Fecha de Emisión:', fechaEmision], [], 
                    ['RESUMEN OPERATIVO'], ['Total de Reportes:', total, '', 'Disponibilidad (Uptime):', `${uptime}%`], 
                    ['Conexiones OK:', ok, '', 'Caídas:', caidas], [], 
                    ['BITÁCORA DE TRAZABILIDAD'], ['FECHA', 'HORA', 'ESTADO', 'ARCHIVO ORIGEN']
                ];

                historial.forEach(h => { datosExcel.push([h.FECHA_LIMPIA, h.HORA_LIMPIA, h.ESTADO, h.ORIGEN_LIMPIO]); });

                const ws = utils.aoa_to_sheet(datosExcel);
                ws['!cols'] = [{ wch: 22 }, { wch: 20 }, { wch: 18 }, { wch: 38 }, { wch: 15 }];
                ws['!merges'] = [{ s: { r: 0, c: 0 }, e: { r: 0, c: 4 } }, { s: { r: 2, c: 0 }, e: { r: 2, c: 4 } }, { s: { r: 7, c: 0 }, e: { r: 7, c: 4 } }, { s: { r: 11, c: 0 }, e: { r: 11, c: 4 } }];

                let sheetName = dev.player.replace(/[\[\]\*\\\/\?]/g, '').substring(0, 31);
                utils.book_append_sheet(wb, ws, sheetName);
            } catch (e) {
                console.error(`Error al procesar ${dev.player}`, e);
            }
        });

        await Promise.all(promesas);

        writeFile(wb, `Consolidado_Monitoreo_${new Date().getTime()}.xlsx`);
        toastStore.agregarToast({ tipo: 'success', titulo: 'Completado', mensaje: 'El reporte consolidado se ha descargado correctamente.' });
        seleccionados.value = []; 
    } catch (e) {
        toastStore.agregarToast({ tipo: 'error', titulo: 'Error', mensaje: 'Hubo un error al generar el archivo múltiple.' });
    } finally {
        exportandoMasivo.value = false;
    }
};

const opcionesOrden = [
    { id: 'estado', label: 'Prioridad (Caídos primero)' },
    { id: 'alfabetico', label: 'Alfabético (A-Z)' },
    { id: 'reciente', label: 'Más recientes' }
];

const ordenSeleccionado = computed(() => opcionesOrden.find(o => o.id === orden.value));
const seleccionarOrden = (id) => { orden.value = id; dropdownAbierto.value = false; };

onMounted(() => { cargarMonitoreo(); });
watch([() => filtros.proyecto, () => filtros.fechaInicio, () => filtros.fechaFin], () => { cargarMonitoreo(); });

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

const stats = computed(() => ({
    total: dispositivosMonitoreo.value.length,
    activos: dispositivosMonitoreo.value.filter(d => !d.alerta).length,
    caidos: dispositivosMonitoreo.value.filter(d => d.alerta).length
}));
</script>

<template>
  <div class="flex flex-col h-full animate-in fade-in duration-500 relative pb-10">
    
    <div class="flex flex-col lg:flex-row items-stretch gap-4 mb-8 bg-white p-4 rounded-2xl border border-gray-100 shadow-sm z-30">
        <div class="relative flex-1">
            <Search class="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400"></Search>
            <input v-model="busqueda" type="text" placeholder="Buscar player..." class="w-full pl-10 pr-10 py-3 bg-slate-50 rounded-xl text-sm outline-none border border-transparent focus:border-admira-300 focus:bg-white transition-all">
            <button v-if="busqueda" @click="busqueda = ''" class="absolute right-3 top-1/2 -translate-y-1/2 text-slate-300 hover:text-slate-500">
                <XCircle class="w-5 h-5"></XCircle>
            </button>
        </div>

        <div class="flex flex-wrap sm:flex-nowrap gap-3">
            <div class="relative flex-1 sm:flex-none sm:min-w-[220px]">
                <div @click="dropdownAbierto = !dropdownAbierto" class="flex items-center justify-between bg-slate-50 rounded-xl px-4 h-[44px] border border-slate-100 cursor-pointer hover:bg-slate-100 transition-all">
                    <div class="flex items-center text-xs font-bold text-slate-600">
                        <ArrowDownAZ class="w-4 h-4 text-admira-500 mr-2"></ArrowDownAZ>
                        {{ ordenSeleccionado.label }}
                    </div>
                    <ChevronDown class="w-4 h-4 text-slate-400"></ChevronDown>
                </div>
                <div v-if="dropdownAbierto" class="absolute top-full left-0 mt-2 w-full bg-white border border-gray-100 rounded-xl shadow-xl z-50 overflow-hidden">
                    <div v-for="opcion in opcionesOrden" :key="opcion.id" @click="seleccionarOrden(opcion.id)" class="px-4 py-3 text-xs font-bold hover:bg-slate-50 cursor-pointer text-slate-700">
                        {{ opcion.label }}
                    </div>
                </div>
                <div v-if="dropdownAbierto" @click="dropdownAbierto = false" class="fixed inset-0 z-40"></div>
            </div>

            <button @click="cargarMonitoreo" class="flex items-center justify-center p-3 bg-admira-50 text-admira-600 rounded-xl hover:bg-admira-100 transition-all h-[44px] w-[44px] border border-admira-100">
                <RefreshCw class="w-5 h-5" :class="{'animate-spin': cargando}"></RefreshCw>
            </button>
        </div>

        <div class="flex flex-wrap bg-slate-100 p-1 rounded-xl border border-slate-100">
            <button v-for="st in [['todos', 'Todos', stats.total], ['activo', 'OK', stats.activos], ['caido', 'Caídos', stats.caidos]]" 
                :key="st[0]" @click="filtroEstado = st[0]" 
                :class="['flex-1 flex items-center justify-center gap-1.5 px-3 py-2 text-[10px] font-black uppercase rounded-lg transition-all', filtroEstado === st[0] ? 'bg-white shadow-sm text-admira-600 border border-slate-200' : 'text-slate-500 hover:bg-slate-200/50']">
                {{ st[1] }} ({{ st[2] }})
            </button>
        </div>
    </div>

    <div v-if="cargando" class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 2xl:grid-cols-5 gap-3">
        <div v-for="i in 15" :key="i" class="bg-white p-3 rounded-xl border border-gray-100 shadow-sm flex items-center gap-3 animate-pulse">
            <div class="w-10 h-10 bg-slate-200 rounded-lg shrink-0"></div>
            <div class="flex-1">
                <div class="h-3.5 bg-slate-200 rounded w-2/3 mb-2"></div>
                <div class="flex gap-2">
                    <div class="h-2 bg-slate-100 rounded w-12"></div>
                    <div class="h-2 bg-slate-100 rounded w-16"></div>
                </div>
            </div>
        </div>
    </div>

    <div v-else-if="dispositivosProcesados.length > 0" class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 2xl:grid-cols-5 gap-3">
        <div v-for="dev in dispositivosProcesados" :key="dev.player" @click="playerSeleccionado = dev"
            class="bg-white p-3 rounded-xl border border-gray-200 shadow-sm hover:border-admira-400 hover:shadow-md transition-all cursor-pointer flex items-center gap-3 group relative overflow-hidden">
            
            <div :class="['absolute left-0 top-0 w-1 h-full', dev.alerta ? 'bg-rose-500' : 'bg-emerald-400']"></div>

            <div :class="['relative flex-shrink-0 w-10 h-10 flex items-center justify-center rounded-lg ml-1', dev.alerta ? 'bg-rose-50 text-rose-600' : 'bg-emerald-50 text-emerald-600']">
                <Monitor class="w-5 h-5"></Monitor>
                <span v-if="dev.alerta" class="absolute -top-1 -right-1 flex h-3 w-3">
                    <span class="animate-ping absolute inline-flex h-full w-full rounded-full bg-rose-400 opacity-75"></span>
                    <span class="relative inline-flex rounded-full h-3 w-3 bg-rose-500"></span>
                </span>
            </div>

            <div class="flex-1 min-w-0 flex flex-col justify-center">
                <h3 class="font-extrabold text-slate-800 truncate text-xs md:text-sm mb-0.5 group-hover:text-admira-600" :title="dev.player">
                    {{ dev.player }}
                </h3>
                <div class="flex items-center gap-1.5 mt-0.5">
                    <span class="text-[9px] font-black uppercase text-slate-500 bg-slate-100 border border-slate-200 px-1.5 py-0.5 rounded-md truncate max-w-[80px]" :title="dev.proyecto">
                        {{ dev.proyecto }}
                    </span>
                    <span class="text-[9px] font-bold text-slate-400 truncate">
                        {{ dev.ultima_conexion.replace('REPORTE', '').trim() }}
                    </span>
                </div>
            </div>

            <div class="absolute top-2 right-2 z-10" @click.stop="toggleSeleccion(dev)">
                <input type="checkbox" :checked="seleccionados.some(s => s.player === dev.player)" 
                       class="w-4 h-4 text-admira-600 rounded border-gray-300 focus:ring-admira-500 cursor-pointer shadow-sm transition-all">
            </div>
        </div>
    </div>

    <div v-else class="flex flex-col items-center justify-center py-20 text-slate-400 bg-white rounded-2xl border border-dashed border-gray-200">
        <Monitor class="w-12 h-12 text-slate-200 mb-3"></Monitor>
        <p class="text-sm font-bold text-slate-500">No se encontraron dispositivos</p>
        <p class="text-xs text-slate-400 mt-1">Intenta con otro término de búsqueda o cambia los filtros</p>
    </div>

    <PlayerModal :player="playerSeleccionado" @cerrar="playerSeleccionado = null"></PlayerModal>

    <div v-if="seleccionados.length > 0" class="fixed bottom-6 left-1/2 -translate-x-1/2 bg-slate-800 text-white px-6 py-4 rounded-2xl shadow-2xl z-[100] flex items-center gap-6 animate-in slide-in-from-bottom-5 fade-in">
         <div class="flex items-center gap-3">
             <span class="bg-emerald-500 text-white text-xs font-black px-2 py-1 rounded-md">{{ seleccionados.length }}</span>
             <span class="text-sm font-bold text-slate-200">seleccionados</span>
         </div>
         <div class="w-px h-8 bg-slate-600"></div>
         <div class="flex gap-2">
             <button @click="seleccionados = []" class="text-xs font-bold text-slate-300 hover:text-white px-3 py-2 transition-colors">Cancelar</button>
             <button @click="exportarSeleccionadosExcel" :disabled="exportandoMasivo" class="flex items-center gap-2 bg-emerald-500 hover:bg-emerald-400 text-white px-4 py-2 rounded-xl text-xs font-bold transition-all disabled:opacity-50 disabled:cursor-not-allowed">
                 <Loader2 v-if="exportandoMasivo" class="w-4 h-4 animate-spin"></Loader2>
                 <FileSpreadsheet v-else class="w-4 h-4"></FileSpreadsheet>
                 {{ exportandoMasivo ? 'Generando...' : 'Exportar Consolidado' }}
             </button>
         </div>
    </div>

  </div>
</template>