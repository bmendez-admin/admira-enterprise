<script setup>
import { onMounted, ref } from 'vue';
import { Download, Maximize, Minimize, Monitor, Wifi, ShieldCheck, FolderKanban } from 'lucide-vue-next';
import StatCard from '../components/dashboard/StatCard.vue';
import Charts from '../components/dashboard/Charts.vue';
import Tendencia from '../components/dashboard/Tendencia.vue';
import { useDashboard } from '../composables/useDashboard';

const { kpis, iniciarDashboard, cargando } = useDashboard();
const pantallaCompleta = ref(false);

onMounted(async () => {
  await iniciarDashboard();
  
  // Escuchar si el usuario sale de pantalla completa con la tecla ESC para actualizar el ícono
  document.addEventListener('fullscreenchange', () => {
    pantallaCompleta.value = !!document.fullscreenElement;
  });
});

// Lógica de Exportación a PDF (Nativa)
// Utilizamos el motor de impresión del navegador junto con CSS (@media print) 
// para evitar conflictos con colores modernos (como oklch) y librerías obsoletas.
const exportarPDF = () => {
  window.print();
};

// Lógica de Modo TV (Pantalla Completa)
const togglePantallaCompleta = () => {
  if (!document.fullscreenElement) {
    document.documentElement.requestFullscreen();
  } else {
    if (document.exitFullscreen) {
      document.exitFullscreen();
    }
  }
};
</script>

<template>
  <div class="animate-in fade-in duration-500 w-full overflow-x-hidden pb-8 relative">

    <div class="flex flex-wrap items-center gap-3 md:gap-4 mb-6 md:mb-8 no-print">
      
      <button @click="exportarPDF" :disabled="cargando"
        class="flex items-center justify-center gap-3 px-6 py-3.5 sm:py-3 bg-white border border-gray-200 rounded-xl hover:border-admira-500 hover:text-admira-600 transition-all shadow-sm active:scale-95 disabled:opacity-50 disabled:pointer-events-none group">
        <Download class="w-5 h-5 sm:w-4 sm:h-4 text-admira-500 group-hover:text-admira-600" />
        <span class="text-sm font-bold text-slate-700 group-hover:text-admira-600">
          Exportar Reporte
        </span>
      </button>

      <button @click="togglePantallaCompleta"
        class="flex items-center justify-center gap-3 px-6 py-3.5 sm:py-3 bg-white border border-gray-200 rounded-xl hover:border-indigo-300 hover:bg-indigo-50 transition-all shadow-sm active:scale-95 group">
        <Minimize v-if="pantallaCompleta" class="w-5 h-5 sm:w-4 sm:h-4 text-indigo-500" />
        <Maximize v-else class="w-5 h-5 sm:w-4 sm:h-4 text-indigo-500" />
        <span class="text-sm font-bold text-slate-700">
          {{ pantallaCompleta ? 'Salir de Modo TV' : 'Modo TV' }}
        </span>
      </button>
      
    </div>

    <div v-if="cargando" class="absolute inset-0 top-[80px] flex items-start justify-center z-50 pt-20 no-print">
      <div class="w-12 h-12 border-4 border-admira-100 border-t-admira-600 rounded-full animate-spin shadow-lg"></div>
    </div>

    <div id="dashboard-reporte" class="p-1" :class="{ 'opacity-30 pointer-events-none blur-[2px] grayscale-[20%]': cargando, 'transition-all duration-500 ease-in-out': true }">
      
      <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 md:gap-6 mb-8 md:mb-10">
        <StatCard title="Total Players" :value="kpis.uniquePlayers" :icon="Monitor" color="admira" sub="Inventario Activo" />
        <StatCard title="% De Emisión" :value="kpis.uptime + '%'" :icon="Wifi" color="emerald" sub="Uptime promedio" />
        <StatCard title="Proyectos Activos" :value="kpis.proyectosActivos" :icon="FolderKanban" color="indigo" sub="Clientes en el periodo" />
        <StatCard title="Proyectos en SLA" :value="kpis.proyectosSLA" :icon="ShieldCheck" color="emerald" sub="Cumplimiento > 70%" />
      </div>
      
      <Charts />
      <Tendencia />
      
    </div>

  </div>
</template>

<style>
@media print {
  @page {
    size: A4 landscape;
    margin: 5mm;
  }

  /* 1. Forzamos los colores corporativos para que no salgan blancos */
  body {
    -webkit-print-color-adjust: exact !important;
    print-color-adjust: exact !important;
    background-color: white !important;
  }

  /* 2. Ocultamos la app entera visualmente */
  body * {
    visibility: hidden;
  }

  /* 3. Iluminamos de nuevo SOLO nuestro reporte */
  #dashboard-reporte, #dashboard-reporte * {
    visibility: visible;
  }

  /* 4. EL TRUCO MAESTRO: Desactivamos las clases '.relative' de Tailwind.
        Esto elimina las "paredes invisibles" del menú lateral y la cabecera 
        para que no empujen el reporte hacia abajo. */
  .relative {
    position: static !important;
  }

  /* 5. Anclamos el reporte en la esquina superior izquierda de la hoja blanca */
  #dashboard-reporte {
    position: absolute !important;
    left: 0 !important;
    top: 0 !important;
    width: 100vw !important;
    height: auto !important; /* Altura automática para que genere una página 2 si es necesario */
    margin: 0 !important;
    padding: 0 !important;
  }

  /* 6. Le decimos al navegador que NO parta las gráficas a la mitad si no caben */
  .vue-apexcharts, .grid > div {
    page-break-inside: avoid !important;
    break-inside: avoid !important;
  }

  /* 7. Escondemos la botonera y los loaders */
  .no-print {
    display: none !important;
  }
}
</style>