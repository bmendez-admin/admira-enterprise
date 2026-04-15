import { ref, computed } from 'vue';
import admiraApi from '../api/admiraApi';

export function useReportes(filtros) {
    const datosReporte = ref([]);
    const generandoReporte = ref(false);
    const busquedaInterna = ref('');
    const mostrarSoloInestables = ref(false);
    
    // Paginación en cliente
    const paginaActual = ref(1);
    const filasPorPagina = 12;

    // Ordenamiento dinámico
    const ordenCampo = ref('uptime'); 
    const ordenDireccion = ref('asc'); // 'asc' o 'desc'

    const generarReporteGlobal = async () => {
        generandoReporte.value = true;
        try {
            const params = {
                proyecto: (filtros.proyecto && filtros.proyecto !== 'Todos los Proyectos') ? filtros.proyecto : null,
                fecha_inicio: filtros.fechaInicio || null,
                fecha_fin: filtros.fechaFin || null
            };
            const { data } = await admiraApi.get('/reporte/consolidado', { params });
            datosReporte.value = data;
            paginaActual.value = 1; // Reiniciar al cargar nuevos datos
        } catch (error) {
            console.error("Error al generar reporte:", error);
            throw error;
        } finally {
            generandoReporte.value = false;
        }
    };

    const limpiarAnalisis = () => {
        datosReporte.value = [];
        busquedaInterna.value = '';
        mostrarSoloInestables.value = false;
        paginaActual.value = 1;
    };

    // Estadísticas globales (Layout estable)
    const statsReporte = computed(() => {
        const total = datosReporte.value.length;
        const fallosTotales = datosReporte.value.reduce((acc, curr) => acc + curr.caidas, 0);
        const reportesTotales = datosReporte.value.reduce((acc, curr) => acc + curr.total_reportes, 0);
        const uptimeGlobal = reportesTotales > 0 
            ? (((reportesTotales - fallosTotales) / reportesTotales) * 100).toFixed(1) 
            : "0.0";
        
        return { total, fallosTotales, uptimeGlobal };
    });

    // Procesamiento de datos (Filtros + Ordenamiento)
    const reporteFiltrado = computed(() => {
        let filtrados = [...datosReporte.value];

        if (mostrarSoloInestables.value) {
            filtrados = filtrados.filter(d => d.uptime < 100);
        }

        if (busquedaInterna.value) {
            const term = busquedaInterna.value.toLowerCase();
            filtrados = filtrados.filter(d => 
                d.player.toLowerCase().includes(term) || 
                (d.proyecto && d.proyecto.toLowerCase().includes(term))
            );
        }

        // Lógica de Ordenamiento
        filtrados.sort((a, b) => {
            let valA = a[ordenCampo.value];
            let valB = b[ordenCampo.value];
            
            if (typeof valA === 'string') {
                valA = valA.toLowerCase();
                valB = valB.toLowerCase();
            }

            if (ordenDireccion.value === 'asc') return valA > valB ? 1 : -1;
            return valA < valB ? 1 : -1;
        });

        return filtrados;
    });

    // Segmento para la página actual
    const reportePaginado = computed(() => {
        const inicio = (paginaActual.value - 1) * filasPorPagina;
        return reporteFiltrado.value.slice(inicio, inicio + filasPorPagina);
    });

    const totalPaginas = computed(() => Math.ceil(reporteFiltrado.value.length / filasPorPagina) || 1);

    const toggleOrden = (campo) => {
        if (ordenCampo.value === campo) {
            ordenDireccion.value = ordenDireccion.value === 'asc' ? 'desc' : 'asc';
        } else {
            ordenCampo.value = campo;
            ordenDireccion.value = 'desc'; // Por defecto los peores arriba al cambiar
        }
    };

    return {
        datosReporte, generandoReporte, busquedaInterna, mostrarSoloInestables,
        paginaActual, totalPaginas, statsReporte, reportePaginado, reporteFiltrado,
        generarReporteGlobal, limpiarAnalisis, toggleOrden, ordenCampo, ordenDireccion
    };
}