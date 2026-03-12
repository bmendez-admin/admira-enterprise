<script setup>
import { Calendar, ChevronLeft, ChevronRight } from 'lucide-vue-next';
import { useDashboard } from '../../composables/useDashboard';

const { datosTabla, filtros, cargarTabla, cargando } = useDashboard();

const getStatusColor = (status) => {
    const map = {
        'Activo': 'bg-emerald-50 text-emerald-700 border-emerald-200',
        'Sin conexión': 'bg-rose-50 text-rose-700 border-rose-200',
        'Desconocido': 'bg-slate-50 text-slate-600 border-slate-200'
    };
    return map[status] || 'bg-slate-50 text-slate-600 border-slate-200';
};

const paginaAnterior = async () => {
    if (filtros.pagina > 1) {
        filtros.pagina--;
        await cargarTabla();
    }
};

const paginaSiguiente = async () => {
    if (filtros.pagina < datosTabla.value.total_paginas) {
        filtros.pagina++;
        await cargarTabla();
    }
};
</script>

<template>
  <div class="bg-white rounded-2xl border border-gray-200 shadow-sm overflow-hidden flex flex-col relative hover:shadow-md transition-shadow">
     
     <div v-if="cargando" class="absolute inset-0 bg-white/60 backdrop-blur-sm z-10 flex items-center justify-center">
         <div class="animate-spin rounded-full h-8 w-8 border-b-2 border-admira-500"></div>
     </div>

     <div class="px-6 py-5 border-b border-gray-100 flex justify-between items-center bg-slate-50/50">
        <h3 class="font-bold text-slate-800 text-sm flex items-center gap-2">
            <Calendar class="w-4 h-4 text-admira-500"/>
            Bitácora de Reportes
        </h3>
        <div class="flex items-center gap-2 text-xs font-bold text-slate-400 bg-white px-3 py-1 rounded-full border border-gray-200 shadow-sm">
            {{ datosTabla.total_registros.toLocaleString() }} registros encontrados
        </div>
     </div>
     
     <div class="overflow-x-auto min-h-[450px]">
        <table class="w-full text-left text-sm text-slate-600">
           <thead class="bg-slate-50 text-[10px] uppercase font-bold text-slate-400 tracking-wider">
              <tr>
                 <th class="px-6 py-4">Dispositivo</th>
                 <th class="px-6 py-4">Fecha y Hora</th>
                 <th class="px-6 py-4">Estado</th>
                 <th class="px-6 py-4 text-right">Archivo Origen</th>
              </tr>
           </thead>
           <tbody class="divide-y divide-gray-100">
              <tr v-if="datosTabla.items.length === 0">
                  <td colspan="4" class="text-center py-10 text-slate-400 font-medium">
                      No se encontraron reportes con estos filtros.
                  </td>
              </tr>

              <tr v-for="(f, i) in datosTabla.items" :key="i" class="hover:bg-admira-50/50 transition-colors group">
                 <td class="px-6 py-3.5">
                    <div class="flex items-center gap-3">
                       <div :class="`w-8 h-8 rounded-xl flex items-center justify-center font-bold text-[10px] shadow-sm border ${f.ESTADO === 'Activo' ? 'bg-emerald-50 text-emerald-700 border-emerald-100' : 'bg-rose-50 text-rose-700 border-rose-100'}`">
                          {{ f.PLAYER ? f.PLAYER.substring(0,2).toUpperCase() : '--' }}
                       </div>
                       <span class="font-bold text-xs text-slate-700 group-hover:text-admira-600 transition-colors">{{ f.PLAYER }}</span>
                    </div>
                 </td>
                 <td class="px-6 py-3.5 font-mono text-[11px] text-slate-500 font-medium">
                    {{ f.FECHA }} <span class="text-slate-300 mx-1">|</span> {{ f.HORARIO_LEGIBLE }}
                 </td>
                 <td class="px-6 py-3.5">
                    <span :class="['inline-flex items-center px-2.5 py-1 rounded-md text-[10px] font-bold border', getStatusColor(f.ESTADO)]">
                       <div :class="`w-1.5 h-1.5 rounded-full mr-1.5 ${f.ESTADO==='Activo'?'bg-emerald-500':'bg-rose-500'}`"></div>
                       {{ f.ESTADO }}
                    </span>
                 </td>
                 <td class="px-6 py-3.5 text-right text-[10px] text-slate-400 font-mono truncate max-w-[150px]" :title="f.ARCHIVO_ORIGEN">
                    {{ (f.ARCHIVO_ORIGEN || '').replace('.xlsx', '').replace('.csv', '') || '---' }}
                 </td>
              </tr>
           </tbody>
        </table>
     </div>
     
     <div class="px-6 py-4 border-t border-gray-100 flex justify-between items-center bg-slate-50/50">
         <span class="text-xs font-bold text-slate-500">
            Página {{ datosTabla.pagina_actual }} de {{ datosTabla.total_paginas.toLocaleString() }}
         </span>
         <div class="flex gap-2">
             <button 
                @click="paginaAnterior" 
                :disabled="filtros.pagina === 1 || cargando" 
                class="p-2 rounded-xl bg-white border border-gray-200 shadow-sm hover:bg-admira-50 hover:border-admira-500 hover:text-admira-600 disabled:opacity-50 disabled:cursor-not-allowed transition-all"
             >
                <ChevronLeft class="w-4 h-4"/>
             </button>
             <button 
                @click="paginaSiguiente" 
                :disabled="filtros.pagina === datosTabla.total_paginas || cargando" 
                class="p-2 rounded-xl bg-white border border-gray-200 shadow-sm hover:bg-admira-50 hover:border-admira-500 hover:text-admira-600 disabled:opacity-50 disabled:cursor-not-allowed transition-all"
             >
                <ChevronRight class="w-4 h-4"/>
             </button>
         </div>
     </div>
  </div>
</template>