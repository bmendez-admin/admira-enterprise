import { ref, reactive } from 'vue';
import admiraApi from '../api/admiraApi';

// ESTADO GLOBAL: Compartido entre todos los componentes
const filtros = reactive({
    proyecto: '',
    fechaInicio: '',
    fechaFin: '',
    estado: '',
    pagina: 1,
    filasPorPagina: 10
});

const menuMovilAbierto = ref(false); 
const configInicial = ref({ proyectos: [], fecha_inicio_sugerida: '', fecha_fin_sugerida: '' });
const kpis = ref({ uptime: 0, off: 0, uniquePlayers: 0, totalRegistros: 0, crit: 0 });
const datosTabla = ref({ items: [], total_registros: 0, total_paginas: 1, pagina_actual: 1 });
const datosGraficas = ref({ barras: { categorias: [], series: [] } });
const cargando = ref(false);
const dispositivosMonitoreo = ref([]);

// NUEVO: Bandera para saber si ya tenemos las fechas por defecto
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
            configuracionLista.value = true; // Avisamos que las fechas ya están listas
        } catch (error) {
            console.error("Error cargando configuración", error);
            configuracionLista.value = true; // Para no bloquear la app si falla
        }
    };

    // 2. Cargar KPIs
    const cargarKpis = async () => {
        try {
            const params = {
                proyecto: filtros.proyecto || null,
                fecha_inicio: filtros.fechaInicio || null,
                fecha_fin: filtros.fechaFin || null
            };
            const { data } = await admiraApi.get('/kpis', { params });
            kpis.value = data;
        } catch (error) {
            console.error("Error cargando KPIs", error);
        }
    };

    // 3. Cargar Bitácora (Tabla)
    const cargarTabla = async () => {
        cargando.value = true;
        try {
            const params = {
                proyecto: filtros.proyecto || null,
                fecha_inicio: filtros.fechaInicio || null,
                fecha_fin: filtros.fechaFin || null,
                estado: filtros.estado || null,
                pagina: filtros.pagina,
                filas_por_pagina: filtros.filasPorPagina
            };
            const { data } = await admiraApi.get('/tabla', { params });
            datosTabla.value = data;
        } catch (error) {
            console.error("Error cargando tabla", error);
        } finally {
            cargando.value = false;
        }
    };

    // 4. Cargar Gráficas
    const cargarGraficas = async () => {
        try {
            const params = {
                proyecto: filtros.proyecto || null,
                fecha_inicio: filtros.fechaInicio || null,
                fecha_fin: filtros.fechaFin || null
            };
            const { data } = await admiraApi.get('/graficas/barras', { params });
            datosGraficas.value.barras = data;
        } catch (error) {
            console.error("Error cargando gráficas", error);
        }
    };

    // 5. SINCRONIZAR BASE DE DATOS
    const sincronizarBaseDeDatos = async () => {
        cargando.value = true;
        try {
            await admiraApi.post('/sincronizar');
            console.log("Sincronización en proceso...");
            setTimeout(async () => {
                await recargarDashboard();
            }, 5000);
        } catch (error) {
            console.error("Error al sincronizar", error);
            alert("Hubo un error al intentar sincronizar.");
            cargando.value = false;
        }
    };

    const recargarDashboard = async () => {
        cargando.value = true;
        await Promise.all([cargarKpis(), cargarGraficas(), cargarTabla()]);
        cargando.value = false;
    };

    // NUEVO: Función de arranque coordinado (Evita la carrera de tiempo)
    const iniciarDashboard = async () => {
        if (!configuracionLista.value) {
            await cargarConfiguracion(); // Primero obligamos a obtener las fechas
        }
        await recargarDashboard(); // Luego ya pintamos lo demás
    };

    const resetFiltros = () => {
        filtros.proyecto = '';
        filtros.estado = '';
        filtros.fechaInicio = configInicial.value.fecha_inicio_sugerida;
        filtros.fechaFin = configInicial.value.fecha_fin_sugerida;
        filtros.pagina = 1;
        recargarDashboard();
    };

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

    return {
        filtros,
        configInicial,
        kpis,
        datosTabla,
        datosGraficas,
        cargando,
        dispositivosMonitoreo,
        menuMovilAbierto,
        configuracionLista, // Exportamos para que los componentes sepan si ya está listo
        cargarConfiguracion,
        recargarDashboard,
        iniciarDashboard, // Exportamos la nueva función maestra
        cargarTabla,
        resetFiltros,
        sincronizarBaseDeDatos,
        cargarMonitoreo
    };
}