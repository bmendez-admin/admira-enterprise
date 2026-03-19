<script setup>
import { ref, computed, onMounted } from 'vue';
import axios from 'axios';
import { useAuthStore } from '../stores/auth';
import { useToastStore } from '../stores/toast';
import { User, Edit3, Lock, Users, UserPlus, Search, Shield, X } from 'lucide-vue-next';

const authStore = useAuthStore();
const toastStore = useToastStore();
const usuarioActual = computed(() => authStore.usuario || {});

const esAdmin = computed(() => {
  const rol = usuarioActual.value.rol?.toUpperCase();
  return rol === 'ADMIN' || rol === 'DIRECTIVO';
});

const estadisticasUsuarios = ref({
  total: 0,
  activos: 0,
  roles: 0
});

// CONTROL DEL MODAL
const modalActivo = ref(null);
const tituloModal = ref('');

// COPIA DE TRABAJO (Formulario real)
const formPerfil = ref({
  nombre: '',
  email: ''
});

// COPIA DE TRABAJO PARA CONTRASEÑA
const formPassword = ref({
  actual: '',
  nueva: ''
});

// FUNCIÓN PARA CAMBIAR CONTRASEÑA
const cambiarPassword = async () => {
  // Validación rápida en Frontend
  if (!formPassword.value.actual || !formPassword.value.nueva) {
    toastStore.agregarToast({ tipo: 'error', titulo: 'Campos vacíos', mensaje: 'Debes ingresar ambas contraseñas.' });
    return;
  }

  try {
    await axios.put('/api/usuarios/password', {
      password_actual: formPassword.value.actual,
      password_nueva: formPassword.value.nueva
    }, {
      headers: { Authorization: `Bearer ${authStore.token}` }
    });

    toastStore.agregarToast({
      tipo: 'success',
      titulo: 'Seguridad',
      mensaje: 'Tu contraseña ha sido actualizada y encriptada con éxito.'
    });

    // Limpiamos los campos por seguridad y cerramos
    formPassword.value.actual = '';
    formPassword.value.nueva = '';
    cerrarModal();

  } catch (error) {
    // Si la contraseña actual es incorrecta, FastAPI mandará el mensaje aquí
    const mensajeError = error.response?.data?.detail || 'No se pudo cambiar la contraseña.';
    toastStore.agregarToast({ tipo: 'error', titulo: 'Error de Seguridad', mensaje: mensajeError });
  }
};

// COPIA DE TRABAJO PARA NUEVO USUARIO
const formNuevoUsuario = ref({
  nombre: '',
  email: '',
  password: '',
  rol: 'SOPORTE' // Rol por defecto
});

// FUNCIÓN PARA CREAR USUARIO EN MYSQL
const crearUsuario = async () => {
  if (!formNuevoUsuario.value.nombre || !formNuevoUsuario.value.email || !formNuevoUsuario.value.password) {
    toastStore.agregarToast({ tipo: 'error', titulo: 'Campos vacíos', mensaje: 'Debes llenar todos los datos del usuario.' });
    return;
  }

  try {
    await axios.post('/api/usuarios', {
      nombre_completo: formNuevoUsuario.value.nombre,
      email: formNuevoUsuario.value.email,
      password: formNuevoUsuario.value.password,
      rol: formNuevoUsuario.value.rol
    }, {
      headers: { Authorization: `Bearer ${authStore.token}` }
    });

    toastStore.agregarToast({
      tipo: 'success',
      titulo: 'Usuario Creado',
      mensaje: `${formNuevoUsuario.value.nombre} ha sido registrado exitosamente.`
    });

    // Limpiamos el formulario para el siguiente
    formNuevoUsuario.value = { nombre: '', email: '', password: '', rol: 'SOPORTE' };
    
    // ¡Actualizamos las estadísticas reales en pantalla!
    cargarEstadisticas();
    cerrarModal();

  } catch (error) {
    const mensajeError = error.response?.data?.detail || 'Hubo un error al registrar al usuario.';
    toastStore.agregarToast({ tipo: 'error', titulo: 'Error al crear', mensaje: mensajeError });
  }
};

// ENRUTADOR DEL BOTÓN "GUARDAR CAMBIOS"
const ejecutarAccionModal = () => {
  if (modalActivo.value === 'editarPerfil') {
    guardarCambios();
  } else if (modalActivo.value === 'cambiarPassword') {
    cambiarPassword();
  } else if (modalActivo.value === 'crearUsuario') {
    crearUsuario();
  }
};

const abrirModal = (accion) => {
  modalActivo.value = accion;
  
  if (accion === 'editarPerfil') {
    formPerfil.value.nombre = usuarioActual.value.nombre;
    formPerfil.value.email = usuarioActual.value.sub;
  }

  const titulos = {
    editarPerfil: 'Editar Mi Perfil',
    cambiarPassword: 'Cambiar Contraseña',
    crearUsuario: 'Crear Nuevo Usuario',
    buscarUsuario: 'Buscar Usuarios',
    gestionarPermisos: 'Gestionar Permisos'
  };
  tituloModal.value = titulos[accion] || 'Configuración';
};

const cerrarModal = () => {
  modalActivo.value = null;
};

// ==========================================
// FUNCIONES REALES HACIA EL BACKEND
// ==========================================
const cargarEstadisticas = async () => {
  if (esAdmin.value) {
    try {
      const respuesta = await axios.get('/api/usuarios/estadisticas', {
        headers: { Authorization: `Bearer ${authStore.token}` }
      });
      estadisticasUsuarios.value = respuesta.data;
    } catch (error) {
      console.error("Error cargando estadísticas reales:", error);
    }
  }
};

const guardarCambios = async () => {
  try {
    // 1. PETICIÓN REAL A FASTAPI
    await axios.put('/api/usuarios/perfil', { nombre: formPerfil.value.nombre }, {
      headers: { Authorization: `Bearer ${authStore.token}` }
    });

    // 2. ACTUALIZACIÓN EN LA BÓVEDA (PINIA)
    authStore.usuario.nombre = formPerfil.value.nombre;

    // 3. TOAST PROFESIONAL (ÉXITO)
    toastStore.agregarToast({
      tipo: 'success',
      titulo: 'Perfil Actualizado',
      mensaje: 'Tus datos se han guardado correctamente en la base de datos.'
    });

    cerrarModal();

  } catch (error) {
    toastStore.agregarToast({
      tipo: 'error',
      titulo: 'Error de conexión',
      mensaje: 'No se pudo guardar la información en el servidor.'
    });
  }
};

onMounted(() => {
  cargarEstadisticas();
});
</script>

<template>
  <div class="animate-in fade-in duration-500 w-full pb-12">
    
    <div class="mb-10">
      <h1 class="text-3xl font-bold text-slate-800 tracking-tight">Configuración del Sistema</h1>
      <p class="text-slate-500 text-base mt-2">Administra tus credenciales y accesos de equipo en la plataforma.</p>
    </div>

    <div class="grid grid-cols-2 gap-8 items-stretch">
      
      <div class="bg-white border border-slate-200 rounded-2xl shadow-sm overflow-hidden flex flex-col h-full min-w-0">
        
        <div class="bg-slate-50 px-8 py-5 flex items-center gap-4 border-b border-slate-200">
          <User class="w-6 h-6 text-slate-700" />
          <h2 class="font-bold text-slate-800 text-xl m-0">Mi Perfil</h2>
        </div>
        
        <div class="p-8 sm:p-10 flex flex-col flex-1">
          <div class="flex items-start gap-6 mb-8 pb-8 border-b border-slate-100">
            <div class="w-20 h-20 rounded-2xl bg-slate-50 border border-slate-200 flex items-center justify-center text-3xl font-black text-slate-600 shrink-0 shadow-sm mt-1">
              {{ usuarioActual.nombre?.charAt(0) || 'A' }}
            </div>
            <div class="flex-1 space-y-4 overflow-hidden">
              <div>
                <p class="text-[11px] font-bold text-slate-400 uppercase tracking-widest mb-0.5">Nombre Completo</p>
                <p class="font-bold text-slate-800 text-base truncate">{{ usuarioActual.nombre }}</p>
              </div>
              <div>
                <p class="text-[11px] font-bold text-slate-400 uppercase tracking-widest mb-0.5">Correo Electrónico</p>
                <p class="font-medium text-slate-600 text-base truncate">{{ usuarioActual.sub }}</p>
              </div>
              <div>
                <p class="text-[11px] font-bold text-slate-400 uppercase tracking-widest mb-1.5">Rol de Acceso</p>
                <span class="inline-flex items-center px-3 py-1 bg-admira-50 text-admira-700 text-xs font-bold uppercase tracking-widest rounded-md border border-admira-200">
                  {{ usuarioActual.rol }}
                </span>
              </div>
            </div>
          </div>

          <div class="mt-auto">
            <h3 class="text-sm font-bold text-slate-400 tracking-widest uppercase mb-5">Acciones Rápidas</h3>
            <div class="space-y-5">
              <button @click="abrirModal('editarPerfil')" class="w-full flex items-center gap-4 px-6 py-4 bg-white border border-slate-200 rounded-xl hover:border-admira-400 hover:bg-admira-50 text-slate-700 transition-all text-base font-bold shadow-sm group">
                <Edit3 class="w-5 h-5 text-admira-600 group-hover:scale-110 transition-transform" />
                Editar Información
              </button>
              <button @click="abrirModal('cambiarPassword')" class="w-full flex items-center gap-4 px-6 py-4 bg-white border border-slate-200 rounded-xl hover:border-admira-400 hover:bg-admira-50 text-slate-700 transition-all text-base font-bold shadow-sm group">
                <Lock class="w-5 h-5 text-slate-400 group-hover:text-admira-600 transition-colors" />
                Cambiar Contraseña
              </button>
            </div>
          </div>
        </div>
      </div>

      <div v-if="esAdmin" class="bg-white border border-slate-200 rounded-2xl shadow-sm overflow-hidden flex flex-col h-full min-w-0">
        
        <div class="bg-slate-50 px-8 py-5 flex items-center gap-4 border-b border-slate-200">
          <Users class="w-6 h-6 text-slate-700" />
          <h2 class="font-bold text-slate-800 text-xl m-0">Gestión de Usuarios</h2>
        </div>
        
        <div class="p-8 sm:p-10 flex flex-col flex-1">
          <div class="space-y-6 mb-8 pb-8 border-b border-slate-100">
            <div class="flex justify-between items-center text-base ">
              <span class="text-slate-600 font-medium">Total de Usuarios</span>
              <span class="font-bold text-slate-800 text-lg">{{ estadisticasUsuarios.total }}</span>
            </div>
            <div class="flex justify-between items-center text-base ">
              <span class="text-slate-600 font-medium">Usuarios Activos</span>
              <span class="font-bold text-emerald-600 text-lg">{{ estadisticasUsuarios.activos }}</span>
            </div>
            <div class="flex justify-between items-center text-base ">
              <span class="text-slate-600 font-medium">Roles Configurados</span>
              <span class="font-bold text-slate-800 text-lg">{{ estadisticasUsuarios.roles }}</span>
            </div>
          </div>

          <div class="mt-auto">
            <h3 class="text-sm font-bold text-slate-400 tracking-widest uppercase mb-5">Acciones Rápidas</h3>
            <div class="space-y-5">
              <button @click="abrirModal('crearUsuario')" class="w-full flex items-center gap-4 px-6 py-4 bg-white border border-slate-200 rounded-xl hover:border-admira-400 hover:bg-admira-50 text-slate-700 transition-all text-base font-bold shadow-sm group">
                <UserPlus class="w-5 h-5 text-slate-400 group-hover:text-admira-600 transition-colors" />
                Crear Nuevo Usuario
              </button>
              <button @click="abrirModal('buscarUsuario')" class="w-full flex items-center gap-4 px-6 py-4 bg-white border border-slate-200 rounded-xl hover:border-admira-400 hover:bg-admira-50 text-slate-700 transition-all text-base font-bold shadow-sm group">
                <Search class="w-5 h-5 text-slate-400 group-hover:text-admira-600 transition-colors" />
                Buscar y Editar Usuario
              </button>
              <button @click="abrirModal('gestionarPermisos')" class="w-full flex items-center gap-4 px-6 py-4 bg-white border border-slate-200 rounded-xl hover:border-admira-400 hover:bg-admira-50 text-slate-700 transition-all text-base font-bold shadow-sm group">
                <Shield class="w-5 h-5 text-slate-400 group-hover:text-admira-600 transition-colors" />
                Gestionar Permisos
              </button>
            </div>
          </div>
        </div>
      </div>

    </div>

    <Teleport to="body">
      <div v-if="modalActivo" class="fixed inset-0 z-[999999] flex items-center justify-center p-4">
        <div class="absolute inset-0 bg-slate-900/60 backdrop-blur-sm" @click="cerrarModal"></div>
        
        <div class="bg-white rounded-2xl shadow-2xl w-full max-w-md relative z-10 overflow-hidden flex flex-col">
          
          <div class="px-6 py-4 border-b border-slate-100 flex justify-between items-center bg-slate-50">
            <h3 class="font-bold text-slate-800">{{ tituloModal }}</h3>
            <button @click="cerrarModal" class="text-slate-400 hover:text-rose-500 transition-colors p-1">
              <X class="w-5 h-5" />
            </button>
          </div>

          <div class="p-6">
            
            <div v-if="modalActivo === 'editarPerfil'">
              <p class="text-sm text-slate-500 mb-5">Actualiza tu información personal.</p>
              <label class="block text-xs font-bold text-slate-700 mb-1">Nombre Completo</label>
              <input type="text" v-model="formPerfil.nombre" class="w-full mb-4 px-4 py-2.5 border border-slate-300 rounded-lg text-sm focus:ring-2 focus:ring-admira-500 outline-none transition-all" />
              
              <label class="block text-xs font-bold text-slate-700 mb-1">Correo Electrónico (Solo Lectura)</label>
              <input type="email" :value="usuarioActual.sub" class="w-full mb-2 px-4 py-2.5 border border-slate-200 rounded-lg text-sm bg-slate-50 text-slate-500 cursor-not-allowed" disabled />
            </div>

            <div v-else-if="modalActivo === 'cambiarPassword'">
              <p class="text-sm text-slate-500 mb-5">Ingresa tu nueva contraseña segura.</p>
              <input type="password" v-model="formPassword.actual" class="w-full mb-4 px-4 py-2.5 border border-slate-300 rounded-lg text-sm focus:ring-2 focus:ring-admira-500 outline-none transition-all" placeholder="Contraseña Actual" />
              <input type="password" v-model="formPassword.nueva" class="w-full mb-2 px-4 py-2.5 border border-slate-300 rounded-lg text-sm focus:ring-2 focus:ring-admira-500 outline-none transition-all" placeholder="Nueva Contraseña" />
            </div>

            <div v-else-if="modalActivo === 'crearUsuario'">
              <p class="text-sm text-slate-500 mb-5">Registra a un nuevo integrante en la plataforma.</p>
              
              <div class="space-y-4">
                <div>
                  <label class="block text-xs font-bold text-slate-700 mb-1">Nombre Completo</label>
                  <input type="text" v-model="formNuevoUsuario.nombre" class="w-full px-4 py-2.5 border border-slate-300 rounded-lg text-sm focus:ring-2 focus:ring-admira-500 outline-none transition-all" placeholder="Ej. Roberto Sánchez" />
                </div>
                
                <div>
                  <label class="block text-xs font-bold text-slate-700 mb-1">Correo Electrónico</label>
                  <input type="email" v-model="formNuevoUsuario.email" class="w-full px-4 py-2.5 border border-slate-300 rounded-lg text-sm focus:ring-2 focus:ring-admira-500 outline-none transition-all" placeholder="usuario@admira.com" />
                </div>

                <div class="grid grid-cols-2 gap-4">
                  <div>
                    <label class="block text-xs font-bold text-slate-700 mb-1">Contraseña Temporal</label>
                    <input type="password" v-model="formNuevoUsuario.password" class="w-full px-4 py-2.5 border border-slate-300 rounded-lg text-sm focus:ring-2 focus:ring-admira-500 outline-none transition-all" placeholder="••••••••" />
                  </div>
                  <div>
                    <label class="block text-xs font-bold text-slate-700 mb-1">Rol de Acceso</label>
                    <select v-model="formNuevoUsuario.rol" class="w-full px-4 py-2.5 border border-slate-300 rounded-lg text-sm focus:ring-2 focus:ring-admira-500 outline-none transition-all bg-white cursor-pointer">
                      <option value="ADMIN">Administrador</option>
                      <option value="DIRECTIVO">Directivo</option>
                      <option value="SOPORTE">Soporte</option>
                      <option value="CLIENTE">Cliente</option>
                    </select>
                  </div>
                </div>
              </div>
            </div>

            <div v-else class="text-center py-8">
              <h4 class="text-slate-800 font-bold mb-1">Módulo en construcción</h4>
              <p class="text-sm text-slate-500">Esta función estará lista en la siguiente etapa.</p>
            </div>

            <div class="flex justify-end gap-3 mt-8 pt-4 border-t border-slate-100">
              <button @click="cerrarModal" class="px-5 py-2.5 text-sm font-bold text-slate-700 bg-slate-100 hover:bg-slate-200 rounded-xl transition-colors">
                Cancelar
              </button>
              <button @click="ejecutarAccionModal" class="px-5 py-2.5 text-sm font-bold text-white bg-admira-600 hover:bg-admira-700 rounded-xl transition-colors shadow-md">
                Guardar Cambios
              </button>
            </div>
          </div>
        </div>
      </div>
    </Teleport>

  </div>
</template>