import { ref, reactive } from 'vue';
import admiraApi from '../api/admiraApi';

// ESTADO GLOBAL: Compartido entre todos los componentes
const filtros = reactive({
    proyecto: '',
    fechaInicio: '',
    fechaFin: '',
    estado: '',
    pagina: 1,
    filasPorPagina: 1000 // Aumentamos para que el CSV exporte todo de un golpe
});

const menuMovilAbierto = ref(false);
const configInicial = ref({ proyectos: [], fecha_inicio_sugerida: '', fecha_fin_sugerida: '' });
const kpis = ref({
    uptime: 0,
    uniquePlayers: 0,
    proyectosActivos: 0,
    proyectosSLA: 0,
    dona_activos: 0,
    dona_caidos: 0
});

const datosTendencia = ref({ categorias: [], series: [] });
const datosGraficas = ref({ barras: { categorias: [], series: [] } });
const cargando = ref(false);
const dispositivosMonitoreo = ref([]);

// Bandera para saber si ya tenemos las fechas por defecto
const configuracionLista = ref(false);

export function useDashboard() {

    // 1. Cargar Configuración Inicial
    const cargarConfiguracion = async () => {
        try {
            const { data } = await admiraApi.get('/configuracion');
            configInicial.value = data;
            if (!filtros.fechaInicio && data.fecha_inicio_sugerida) {
                filtros.fechaInicio = data.fecha_inicio_sugerida;
                filtros.fechaFin = data.fecha_fin_sugerida;
            }
            configuracionLista.value = true;
        } catch (error) {
            console.error("Error cargando configuración", error);
            configuracionLista.value = true;
        }
    };

    // 2. Cargar KPIs
    const cargarKpis = async () => {
        try {
            const params = { proyecto: filtros.proyecto || null, fecha_inicio: filtros.fechaInicio || null, fecha_fin: filtros.fechaFin || null };
            const { data } = await admiraApi.get('/kpis', { params });
            kpis.value = data;
        } catch (error) { console.error("Error cargando KPIs", error); }
    };

    // 3. Cargar Gráficas de Barras
    const cargarGraficas = async () => {
        try {
            const params = { proyecto: filtros.proyecto || null, fecha_inicio: filtros.fechaInicio || null, fecha_fin: filtros.fechaFin || null };
            const { data } = await admiraApi.get('/graficas/barras', { params });
            datosGraficas.value.barras = data;
        } catch (error) { console.error("Error cargando gráficas", error); }
    };

    // 4. Cargar Heatmap (NUEVO)
    const cargarTendencia = async () => {
        try {
            const params = { proyecto: filtros.proyecto || null, fecha_inicio: filtros.fechaInicio || null, fecha_fin: filtros.fechaFin || null };
            const { data } = await admiraApi.get('/graficas/tendencia', { params });
            datosTendencia.value = data;
        } catch (error) { console.error("Error cargando Tendencia", error); }
    };


    // 6. SINCRONIZAR BASE DE DATOS
    const sincronizarBaseDeDatos = async () => {
        cargando.value = true;
        try {
            await admiraApi.post('/sincronizar');
            setTimeout(async () => { await recargarDashboard(); }, 5000);
        } catch (error) {
            console.error("Error al sincronizar", error);
            alert("Hubo un error al intentar sincronizar.");
            cargando.value = false;
        }
    };

    // 7. Cargar Monitoreo (Para la pestaña de Monitoreo)
    const cargarMonitoreo = async () => {
        cargando.value = true;
        try {
            const params = {
                proyecto: filtros.proyecto || null,
                fecha_inicio: filtros.fechaInicio || null,
                fecha_fin: filtros.fechaFin || null
            };
            const { data } = await admiraApi.get('/monitoreo/status', { params });
            dispositivosMonitoreo.value = data;
        } catch (error) {
            console.error("Error en monitoreo", error);
        } finally {
            cargando.value = false;
        }
    };

    // Recargar todo el Dashboard en paralelo
    const recargarDashboard = async () => {
        cargando.value = true;
        await Promise.all([cargarKpis(), cargarGraficas(), cargarTendencia()]);
        cargando.value = false;
    };

    // Función de arranque coordinado
    const iniciarDashboard = async () => {
        if (!configuracionLista.value) {
            await cargarConfiguracion();
        }
        await recargarDashboard();
    };

    const resetFiltros = () => {
        filtros.proyecto = '';
        filtros.estado = '';
        filtros.fechaInicio = configInicial.value.fecha_inicio_sugerida;
        filtros.fechaFin = configInicial.value.fecha_fin_sugerida;
        filtros.pagina = 1;
        recargarDashboard();
    };

    return {
        filtros,
        configInicial,
        kpis,
        datosTendencia,
        datosGraficas,
        cargando,
        dispositivosMonitoreo,
        menuMovilAbierto,
        configuracionLista,
        cargarConfiguracion,
        recargarDashboard,
        iniciarDashboard,
        resetFiltros,
        sincronizarBaseDeDatos,
        cargarMonitoreo
    };
}