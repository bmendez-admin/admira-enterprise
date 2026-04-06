<script setup>
import { ref, computed, onMounted } from 'vue';
import axios from 'axios';
import { useAuthStore } from '../stores/auth';
import { useToastStore } from '../stores/toast';
import { User, Edit3, Lock, Users, UserPlus, Search, Shield, X } from 'lucide-vue-next';

const authStore = useAuthStore();
const toastStore = useToastStore();
const usuarioActual = computed(() => authStore.usuario || {});

// CONTROL DE PERMISOS INTERNO
const esAdmin = computed(() => {
  const rol = usuarioActual.value.rol?.toUpperCase();
  return rol === 'ADMIN' || rol === 'DIRECTIVO';
});

const estadisticasUsuarios = ref({
  total: 0,
  activos: 0,
  roles: 0
});

const modalActivo = ref(null);
const tituloModal = ref('');
const listaUsuarios = ref([]);

const formPerfil = ref({
  nombre: '',
  email: ''
});

const formPassword = ref({
  actual: '',
  nueva: ''
});

const formNuevoUsuario = ref({
  nombre: '',
  email: '',
  password: '',
  rol: 'SOPORTE'
});

const cargarUsuarios = async () => {
  try {
    const response = await axios.get('/usuarios', {
      headers: { Authorization: `Bearer ${authStore.token}` }
    });
    listaUsuarios.value = response.data;
  } catch (error) {
    console.error("Error al obtener lista de usuarios:", error);
  }
};

const toggleEstatus = async (user) => {
  try {
    await axios.put(`/usuarios/${user.id}`, {
      activo: !user.activo
    }, {
      headers: { Authorization: `Bearer ${authStore.token}` }
    });

    toastStore.agregarToast({
      tipo: 'success',
      titulo: 'Estado Actualizado',
      mensaje: `El usuario ${user.nombre_completo} ha sido ${!user.activo ? 'activado' : 'suspendido'}.`
    });

    await cargarUsuarios();
    await cargarEstadisticas();
  } catch (error) {
    toastStore.agregarToast({ tipo: 'error', titulo: 'Error', mensaje: 'No se pudo cambiar el estado del usuario.' });
  }
};

const cambiarPassword = async () => {
  if (!formPassword.value.actual || !formPassword.value.nueva) {
    toastStore.agregarToast({ tipo: 'error', titulo: 'Campos vacíos', mensaje: 'Debes ingresar ambas contraseñas.' });
    return;
  }

  try {
    await axios.put('/usuarios/password', {
      password_actual: formPassword.value.actual,
      password_nueva: formPassword.value.nueva
    }, {
      headers: { Authorization: `Bearer ${authStore.token}` }
    });

    toastStore.agregarToast({
      tipo: 'success',
      titulo: 'Seguridad',
      mensaje: 'Tu contraseña ha sido actualizada con éxito.'
    });

    formPassword.value.actual = '';
    formPassword.value.nueva = '';
    cerrarModal();
  } catch (error) {
    const mensajeError = error.response?.data?.detail || 'No se pudo cambiar la contraseña.';
    toastStore.agregarToast({ tipo: 'error', titulo: 'Error de Seguridad', mensaje: mensajeError });
  }
};

const crearUsuario = async () => {
  if (!formNuevoUsuario.value.nombre || !formNuevoUsuario.value.email || !formNuevoUsuario.value.password) {
    toastStore.agregarToast({ tipo: 'error', titulo: 'Campos vacíos', mensaje: 'Debes llenar todos los datos.' });
    return;
  }

  try {
    await axios.post('/usuarios', {
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
      mensaje: `${formNuevoUsuario.value.nombre} ha sido registrado.`
    });

    formNuevoUsuario.value = { nombre: '', email: '', password: '', rol: 'SOPORTE' };
    await cargarEstadisticas();
    cerrarModal();
  } catch (error) {
    const mensajeError = error.response?.data?.detail || 'Error al registrar al usuario.';
    toastStore.agregarToast({ tipo: 'error', titulo: 'Error', mensaje: mensajeError });
  }
};

const filtroBusqueda = ref('');
const usuarioEditando = ref(null); 

const usuariosFiltrados = computed(() => {
  return listaUsuarios.value.filter(u =>
    u.nombre_completo.toLowerCase().includes(filtroBusqueda.value.toLowerCase()) ||
    u.email.toLowerCase().includes(filtroBusqueda.value.toLowerCase())
  );
});

const prepararEdicion = (user) => {
  usuarioEditando.value = { ...user }; 
};

const guardarEdicionUsuario = async () => {
  try {
    await axios.patch(`/usuarios/${usuarioEditando.value.id}`, {
      nombre_completo: usuarioEditando.value.nombre_completo,
      rol: usuarioEditando.value.rol,
    }, {
      headers: { Authorization: `Bearer ${authStore.token}` }
    });

    toastStore.agregarToast({ tipo: 'success', titulo: 'Actualizado', mensaje: 'Usuario modificado con éxito.' });
    usuarioEditando.value = null; 
    cargarUsuarios(); 
  } catch (error) {
    toastStore.agregarToast({ tipo: 'error', titulo: 'Error', mensaje: 'No se pudo actualizar el usuario.' });
  }
};

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
  if (accion === 'buscarUsuario') {
    cargarUsuarios();
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

const cargarEstadisticas = async () => {
  if (esAdmin.value) {
    try {
      const respuesta = await axios.get('/usuarios/estadisticas', {
        headers: { Authorization: `Bearer ${authStore.token}` }
      });
      estadisticasUsuarios.value = respuesta.data;
    } catch (error) {
      console.error("Error cargando estadísticas:", error);
    }
  }
};

const guardarCambios = async () => {
  try {
    await axios.put('/usuarios/perfil', { nombre: formPerfil.value.nombre }, {
      headers: { Authorization: `Bearer ${authStore.token}` }
    });
    authStore.usuario.nombre = formPerfil.value.nombre;
    toastStore.agregarToast({
      tipo: 'success',
      titulo: 'Perfil Actualizado',
      mensaje: 'Tus datos se han guardado correctamente.'
    });
    cerrarModal();
  } catch (error) {
    toastStore.agregarToast({ tipo: 'error', titulo: 'Error', mensaje: 'No se pudo guardar la información.' });
  }
};

onMounted(() => {
  cargarEstadisticas();
});
</script>

<template>
  <div class="animate-in fade-in duration-500 w-full pb-12">
    <div class="mb-8 md:mb-10 text-center md:text-left">
      <h1 class="text-2xl md:text-3xl font-bold text-slate-800 tracking-tight">Configuración del Sistema</h1>
      <p class="text-slate-500 text-sm md:text-base mt-2">Administra tus credenciales y accesos de equipo en la plataforma.</p>
    </div>

    <div :class="['grid gap-6 md:gap-8 items-stretch', esAdmin ? 'grid-cols-1 lg:grid-cols-2' : 'grid-cols-1 max-w-3xl mx-auto']">
      
      <div class="bg-white border border-slate-200 rounded-2xl shadow-sm overflow-hidden flex flex-col h-full min-w-0">
        <div class="bg-slate-50 px-6 md:px-8 py-5 flex items-center gap-4 border-b border-slate-200">
          <User class="w-6 h-6 text-slate-700 shrink-0" />
          <h2 class="font-bold text-slate-800 text-lg md:text-xl m-0">Mi Perfil</h2>
        </div>

        <div class="p-6 md:p-8 lg:p-10 flex flex-col flex-1">
          <div class="flex flex-col sm:flex-row items-center sm:items-start gap-4 sm:gap-6 mb-8 pb-8 border-b border-slate-100 text-center sm:text-left">
            <div
              class="w-20 h-20 rounded-2xl bg-slate-50 border border-slate-200 flex items-center justify-center text-3xl font-black text-slate-600 shrink-0 shadow-sm mt-1">
              {{ usuarioActual.nombre?.charAt(0) || 'A' }}
            </div>
            <div class="flex-1 space-y-4 overflow-hidden w-full">
              <div>
                <p class="text-[11px] font-bold text-slate-400 uppercase tracking-widest mb-0.5">Nombre Completo</p>
                <p class="font-bold text-slate-800 text-sm md:text-base truncate">{{ usuarioActual.nombre }}</p>
              </div>
              <div>
                <p class="text-[11px] font-bold text-slate-400 uppercase tracking-widest mb-0.5">Correo Electrónico</p>
                <p class="font-medium text-slate-600 text-sm md:text-base truncate">{{ usuarioActual.sub }}</p>
              </div>
              <div>
                <p class="text-[11px] font-bold text-slate-400 uppercase tracking-widest mb-1.5">Rol de Acceso</p>
                <span
                  class="inline-flex items-center px-3 py-1 bg-admira-50 text-admira-700 text-xs font-bold uppercase tracking-widest rounded-md border border-admira-200">
                  {{ usuarioActual.rol }}
                </span>
              </div>
            </div>
          </div>

          <div class="mt-auto">
            <h3 class="text-xs md:text-sm font-bold text-slate-400 tracking-widest uppercase mb-4 md:mb-5 text-center sm:text-left">Acciones Rápidas</h3>
            <div class="space-y-3 md:space-y-5">
              <button @click="abrirModal('editarPerfil')"
                class="w-full flex items-center justify-center sm:justify-start gap-3 md:gap-4 px-4 md:px-6 py-3 md:py-4 bg-white border border-slate-200 rounded-xl hover:border-admira-400 hover:bg-admira-50 text-slate-700 transition-all text-sm md:text-base font-bold shadow-sm group">
                <Edit3 class="w-5 h-5 text-admira-600 group-hover:scale-110 transition-transform shrink-0" />
                <span>Editar Información</span>
              </button>
              <button @click="abrirModal('cambiarPassword')"
                class="w-full flex items-center justify-center sm:justify-start gap-3 md:gap-4 px-4 md:px-6 py-3 md:py-4 bg-white border border-slate-200 rounded-xl hover:border-admira-400 hover:bg-admira-50 text-slate-700 transition-all text-sm md:text-base font-bold shadow-sm group">
                <Lock class="w-5 h-5 text-slate-400 group-hover:text-admira-600 transition-colors shrink-0" />
                <span>Cambiar Contraseña</span>
              </button>
            </div>
          </div>
        </div>
      </div>

      <div v-if="esAdmin"
        class="bg-white border border-slate-200 rounded-2xl shadow-sm overflow-hidden flex flex-col h-full min-w-0">
        <div class="bg-slate-50 px-6 md:px-8 py-5 flex items-center gap-4 border-b border-slate-200">
          <Users class="w-6 h-6 text-slate-700 shrink-0" />
          <h2 class="font-bold text-slate-800 text-lg md:text-xl m-0">Gestión de Usuarios</h2>
        </div>

        <div class="p-6 md:p-8 lg:p-10 flex flex-col flex-1">
          <div class="space-y-5 md:space-y-6 mb-8 pb-8 border-b border-slate-100">
            <div class="flex justify-between items-center text-sm md:text-base">
              <span class="text-slate-600 font-medium">Total de Usuarios</span>
              <span class="font-bold text-slate-800 text-lg">{{ estadisticasUsuarios.total }}</span>
            </div>
            <div class="flex justify-between items-center text-sm md:text-base">
              <span class="text-slate-600 font-medium">Usuarios Activos</span>
              <span class="font-bold text-emerald-600 text-lg">{{ estadisticasUsuarios.activos }}</span>
            </div>
            <div class="flex justify-between items-center text-sm md:text-base">
              <span class="text-slate-600 font-medium">Roles Configurados</span>
              <span class="font-bold text-slate-800 text-lg">{{ estadisticasUsuarios.roles }}</span>
            </div>
          </div>

          <div class="mt-auto">
            <h3 class="text-xs md:text-sm font-bold text-slate-400 tracking-widest uppercase mb-4 md:mb-5 text-center sm:text-left">Acciones Rápidas</h3>
            <div class="space-y-3 md:space-y-5">
              <button @click="abrirModal('crearUsuario')"
                class="w-full flex items-center justify-center sm:justify-start gap-3 md:gap-4 px-4 md:px-6 py-3 md:py-4 bg-white border border-slate-200 rounded-xl hover:border-admira-400 hover:bg-admira-50 text-slate-700 transition-all text-sm md:text-base font-bold shadow-sm group">
                <UserPlus class="w-5 h-5 text-slate-400 group-hover:text-admira-600 transition-colors shrink-0" />
                <span>Crear Nuevo Usuario</span>
              </button>
              <button @click="abrirModal('buscarUsuario')"
                class="w-full flex items-center justify-center sm:justify-start gap-3 md:gap-4 px-4 md:px-6 py-3 md:py-4 bg-white border border-slate-200 rounded-xl hover:border-admira-400 hover:bg-admira-50 text-slate-700 transition-all text-sm md:text-base font-bold shadow-sm group">
                <Search class="w-5 h-5 text-slate-400 group-hover:text-admira-600 transition-colors shrink-0" />
                <span>Buscar y Editar Usuario</span>
              </button>
              <button @click="abrirModal('gestionarPermisos')"
                class="w-full flex items-center justify-center sm:justify-start gap-3 md:gap-4 px-4 md:px-6 py-3 md:py-4 bg-white border border-slate-200 rounded-xl hover:border-admira-400 hover:bg-admira-50 text-slate-700 transition-all text-sm md:text-base font-bold shadow-sm group">
                <Shield class="w-5 h-5 text-slate-400 group-hover:text-admira-600 transition-colors shrink-0" />
                <span>Gestionar Permisos</span>
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>

    <Teleport to="body">
      <div v-if="modalActivo" class="fixed inset-0 z-[999999] flex items-center justify-center p-4 md:p-6">
        <div class="absolute inset-0 bg-slate-900/60 backdrop-blur-sm" @click="cerrarModal"></div>

        <div class="bg-white rounded-2xl shadow-2xl w-full max-w-2xl relative z-10 overflow-hidden flex flex-col max-h-full">
          <div class="px-5 md:px-6 py-4 border-b border-slate-100 flex justify-between items-center bg-slate-50 shrink-0">
            <h3 class="font-bold text-slate-800 text-sm md:text-base">{{ tituloModal }}</h3>
            <button @click="cerrarModal" class="text-slate-400 hover:text-rose-500 transition-colors p-1">
              <X class="w-5 h-5" />
            </button>
          </div>

          <div class="p-5 md:p-6 overflow-y-auto">
            <div v-if="modalActivo === 'editarPerfil'">
              <label class="block text-xs font-bold text-slate-700 mb-1">Nombre Completo</label>
              <input type="text" v-model="formPerfil.nombre"
                class="w-full mb-4 px-4 py-2.5 border border-slate-300 rounded-lg text-sm focus:ring-2 focus:ring-admira-500 outline-none transition-all" />
              <label class="block text-xs font-bold text-slate-700 mb-1">Correo Electrónico (Solo Lectura)</label>
              <input type="email" :value="usuarioActual.sub"
                class="w-full px-4 py-2.5 border border-slate-200 rounded-lg text-sm bg-slate-50 text-slate-500 cursor-not-allowed"
                disabled />
            </div>

            <div v-else-if="modalActivo === 'cambiarPassword'">
              <input type="password" v-model="formPassword.actual"
                class="w-full mb-4 px-4 py-2.5 border border-slate-300 rounded-lg text-sm focus:ring-2 focus:ring-admira-500 outline-none transition-all"
                placeholder="Contraseña Actual" />
              <input type="password" v-model="formPassword.nueva"
                class="w-full px-4 py-2.5 border border-slate-300 rounded-lg text-sm focus:ring-2 focus:ring-admira-500 outline-none transition-all"
                placeholder="Nueva Contraseña" />
            </div>

            <div v-else-if="modalActivo === 'crearUsuario'">
              <div class="space-y-4">
                <input type="text" v-model="formNuevoUsuario.nombre"
                  class="w-full px-4 py-2.5 border border-slate-300 rounded-lg text-sm focus:ring-2 focus:ring-admira-500 outline-none transition-all"
                  placeholder="Nombre Completo" />
                <input type="email" v-model="formNuevoUsuario.email"
                  class="w-full px-4 py-2.5 border border-slate-300 rounded-lg text-sm focus:ring-2 focus:ring-admira-500 outline-none transition-all"
                  placeholder="Correo Electrónico" />
                <div class="grid grid-cols-1 sm:grid-cols-2 gap-4">
                  <input type="password" v-model="formNuevoUsuario.password"
                    class="w-full px-4 py-2.5 border border-slate-300 rounded-lg text-sm focus:ring-2 focus:ring-admira-500 outline-none transition-all"
                    placeholder="Contraseña" />
                  <select v-model="formNuevoUsuario.rol"
                    class="w-full px-4 py-2.5 border border-slate-300 rounded-lg text-sm focus:ring-2 focus:ring-admira-500 outline-none bg-white">
                    <option value="ADMIN">Administrador</option>
                    <option value="DIRECTIVO">Directivo</option>
                    <option value="SOPORTE">Soporte</option>
                    <option value="CLIENTE">Cliente</option>
                  </select>
                </div>
              </div>
            </div>

            <div v-else-if="modalActivo === 'buscarUsuario'">
              <div class="flex flex-col sm:flex-row sm:items-center gap-3 md:gap-4 mb-6">
                <div v-if="!usuarioEditando" class="relative flex-1">
                  <Search class="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400" />
                  <input type="text" v-model="filtroBusqueda" placeholder="Buscar por nombre o correo..."
                    class="w-full pl-10 pr-4 py-2 bg-slate-50 border border-slate-200 rounded-xl text-sm outline-none focus:ring-2 focus:ring-admira-500" />
                </div>
                <button v-else @click="usuarioEditando = null"
                  class="text-admira-600 font-bold text-sm flex items-center gap-2 self-start sm:self-auto">
                  ← Volver a la lista
                </button>
              </div>

              <div v-if="!usuarioEditando" class="overflow-x-auto max-h-[400px] border border-slate-100 rounded-xl">
                <table class="w-full text-sm text-left text-slate-500 min-w-[500px]">
                  <thead class="text-xs text-slate-700 uppercase bg-slate-50 sticky top-0 shadow-sm z-10">
                    <tr>
                      <th class="px-4 py-3">Nombre</th>
                      <th class="px-4 py-3">Rol</th>
                      <th class="px-4 py-3 text-center">Acciones</th>
                    </tr>
                  </thead>
                  <tbody>
                    <tr v-for="user in usuariosFiltrados" :key="user.id"
                      class="border-b hover:bg-slate-50 transition-colors">
                      <td class="px-4 py-3">
                        <p class="font-bold text-slate-900 leading-tight">{{ user.nombre_completo }}</p>
                        <p class="text-xs text-slate-400">{{ user.email }}</p>
                      </td>
                      <td class="px-4 py-3">
                        <span
                          class="text-[10px] font-black px-2 py-0.5 rounded bg-slate-100 border border-slate-200 uppercase">
                          {{ user.rol }}
                        </span>
                      </td>
                      <td class="px-4 py-3">
                        <div class="flex items-center justify-center gap-2">
                          <button @click="prepararEdicion(user)"
                            class="p-1.5 hover:bg-admira-50 text-admira-600 rounded-lg transition-colors"
                            title="Editar datos">
                            <Edit3 class="w-4 h-4" />
                          </button>
                          <button @click="toggleEstatus(user)" class="p-1.5 rounded-lg transition-colors"
                            :class="user.activo ? 'text-emerald-500 hover:bg-emerald-50' : 'text-rose-500 hover:bg-rose-50'">
                            <Shield class="w-4 h-4" />
                          </button>
                        </div>
                      </td>
                    </tr>
                  </tbody>
                </table>
              </div>

              <div v-else class="space-y-4 animate-in slide-in-from-right-4 duration-300">
                <div class="bg-admira-50 p-4 rounded-xl border border-admira-100 mb-4">
                  <p class="text-xs font-bold text-admira-700 uppercase mb-1">Editando a:</p>
                  <p class="text-sm font-bold text-slate-800 break-all">{{ usuarioEditando.email }}</p>
                </div>

                <div>
                  <label class="block text-xs font-bold text-slate-700 mb-1">Nombre Completo</label>
                  <input type="text" v-model="usuarioEditando.nombre_completo"
                    class="w-full px-4 py-2 border border-slate-300 rounded-lg text-sm" />
                </div>

                <div>
                  <label class="block text-xs font-bold text-slate-700 mb-1">Rol de Acceso</label>
                  <select v-model="usuarioEditando.rol"
                    class="w-full px-4 py-2 border border-slate-300 rounded-lg text-sm bg-white">
                    <option value="ADMIN">Administrador</option>
                    <option value="DIRECTIVO">Directivo</option>
                    <option value="SOPORTE">Soporte</option>
                    <option value="CLIENTE">Cliente</option>
                  </select>
                </div>

                <button @click="guardarEdicionUsuario"
                  class="w-full py-3 bg-admira-600 text-white font-bold rounded-xl hover:bg-admira-700 shadow-lg shadow-admira-200 transition-all mt-2">
                  Actualizar Datos
                </button>
              </div>
            </div>

            <div v-if="modalActivo !== 'buscarUsuario'"
              class="flex flex-col sm:flex-row justify-end gap-3 mt-8 pt-4 border-t border-slate-100 shrink-0">
              <button @click="cerrarModal"
                class="px-5 py-2.5 w-full sm:w-auto text-sm font-bold text-slate-700 bg-slate-100 hover:bg-slate-200 rounded-xl transition-colors order-2 sm:order-1">
                Cancelar
              </button>
              <button @click="ejecutarAccionModal"
                class="px-5 py-2.5 w-full sm:w-auto text-sm font-bold text-white bg-admira-600 hover:bg-admira-700 rounded-xl transition-colors shadow-md order-1 sm:order-2">
                Guardar Cambios
              </button>
            </div>
          </div>
        </div>
      </div>
    </Teleport>
  </div>
</template>