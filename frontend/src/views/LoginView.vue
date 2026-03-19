<template>
  <div class="flex min-h-screen w-full bg-admira-50 font-sans absolute top-0 left-0 z-[9999]">
    
    <div class="hidden lg:flex lg:w-1/2 bg-gradient-to-br from-admira-900 via-admira-600 to-admira-900 text-white flex-col justify-center px-16 xl:px-24 relative overflow-hidden">
      
      <div class="absolute -top-32 -left-32 w-96 h-96 bg-white opacity-10 rounded-full blur-3xl"></div>
      <div class="absolute bottom-0 right-0 w-[500px] h-[500px] bg-admira-500 opacity-20 rounded-full blur-3xl"></div>

      <div class="relative z-10">
        <div class="w-16 h-16 bg-white/10 border border-white/20 rounded-2xl flex items-center justify-center mb-8 shadow-lg backdrop-blur-sm">
          <Activity class="w-8 h-8 text-admira-50" />
        </div>
        
        <h1 class="text-5xl font-extrabold tracking-tight mb-2">
          ADMIRA
        </h1>
        <h2 class="text-3xl font-light text-admira-100 mb-6 tracking-widest">
          ENTERPRISE
        </h2>
        
        <p class="text-lg text-admira-50/80 mb-12 leading-relaxed max-w-md">
          Plataforma centralizada para el monitoreo de players, análisis de emisiones y control estratégico de proyectos.
        </p>

        <div class="inline-flex items-center gap-3 bg-admira-900/50 border border-admira-500/30 px-5 py-2.5 rounded-xl text-sm font-medium text-admira-100 backdrop-blur-md">
          <ShieldCheck class="w-5 h-5 text-admira-500" />
          Conexión Segura y Encriptada
        </div>
      </div>
    </div>

    <div class="w-full lg:w-1/2 flex items-center justify-center p-8 sm:p-12 bg-white">
      <div class="w-full max-w-md">
        
        <div class="mb-10">
          <div class="lg:hidden w-12 h-12 bg-admira-500 rounded-xl flex items-center justify-center mb-6 shadow-md">
            <Activity class="w-6 h-6 text-white" />
          </div>
          <h2 class="text-3xl font-bold text-slate-800 tracking-tight mb-2">Iniciar Sesión</h2>
          <p class="text-slate-500 text-sm">Ingresa tus credenciales de administrador para continuar.</p>
        </div>

        <div v-if="mensajeError" class="mb-6 flex items-center gap-3 bg-rose-50 border border-rose-200 text-rose-700 p-4 rounded-xl text-sm font-medium animate-in fade-in slide-in-from-top-2 duration-300">
          <AlertTriangle class="w-5 h-5 shrink-0 text-rose-600" />
          {{ mensajeError }}
        </div>

        <form @submit.prevent="procesarLogin" class="space-y-6">
          
          <div>
            <label for="email" class="block text-sm font-bold text-slate-700 mb-2">Correo Electrónico</label>
            <div class="relative group">
              <div class="absolute inset-y-0 left-0 pl-4 flex items-center pointer-events-none">
                <Mail class="h-5 w-5 text-slate-400 group-focus-within:text-admira-500 transition-colors" />
              </div>
              <input 
                type="email" 
                id="email" 
                v-model="email" 
                placeholder="admin@admira.com" 
                required
                :disabled="estaCargando"
                class="w-full pl-11 pr-4 py-3.5 bg-white border border-gray-200 rounded-xl text-slate-800 placeholder-slate-400 focus:outline-none focus:border-admira-500 focus:ring-1 focus:ring-admira-500 transition-all duration-200 disabled:bg-slate-50 disabled:text-slate-400"
              />
            </div>
          </div>

          <div>
            <label for="password" class="block text-sm font-bold text-slate-700 mb-2">Contraseña</label>
            <div class="relative group">
              <div class="absolute inset-y-0 left-0 pl-4 flex items-center pointer-events-none">
                <Lock class="h-5 w-5 text-slate-400 group-focus-within:text-admira-500 transition-colors" />
              </div>
              <input 
                type="password" 
                id="password" 
                v-model="password" 
                placeholder="••••••••" 
                required
                :disabled="estaCargando"
                class="w-full pl-11 pr-4 py-3.5 bg-white border border-gray-200 rounded-xl text-slate-800 placeholder-slate-400 focus:outline-none focus:border-admira-500 focus:ring-1 focus:ring-admira-500 transition-all duration-200 disabled:bg-slate-50 disabled:text-slate-400"
              />
            </div>
          </div>

          <button 
            type="submit" 
            :disabled="estaCargando"
            class="w-full mt-2 flex justify-center items-center gap-3 py-3.5 px-4 border border-transparent rounded-xl shadow-sm text-sm font-bold text-white bg-admira-500 hover:bg-admira-600 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-admira-500 transition-all duration-200 disabled:opacity-70 disabled:cursor-not-allowed group"
          >
            <Loader2 v-if="estaCargando" class="w-5 h-5 animate-spin text-white" />
            <span v-if="estaCargando">Verificando...</span>
            <span v-else>Acceder al Dashboard</span>
          </button>

        </form>

        <p class="mt-12 text-center text-xs text-slate-400 font-medium">
          &copy; 2026 ADMIRA Enterprise. <br class="sm:hidden" />Todos los derechos reservados.
        </p>

      </div>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '../stores/auth'
// ¡Importamos los íconos de Lucide para que coincida con tu Dashboard!
import { Mail, Lock, ShieldCheck, Activity, AlertTriangle, Loader2 } from 'lucide-vue-next'

const email = ref('')
const password = ref('')
const mensajeError = ref('')
const estaCargando = ref(false)

const router = useRouter()
const authStore = useAuthStore()

const procesarLogin = async () => {
  mensajeError.value = ''
  estaCargando.value = true

  try {
    await authStore.login(email.value, password.value)
    router.push({ name: 'Dashboard' })
  } catch (error) {
    if (error.response && error.response.status === 401) {
      mensajeError.value = "Credenciales incorrectas. Verifica tu acceso."
    } else {
      mensajeError.value = "Error de conexión. Contacta a soporte de TI."
    }
  } finally {
    estaCargando.value = false
  }
}
</script>