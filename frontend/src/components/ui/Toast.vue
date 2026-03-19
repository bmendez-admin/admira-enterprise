<script setup>
import { useToastStore } from '../../stores/toast';

const toastStore = useToastStore();
</script>

<template>
  <div class="fixed top-5 right-5 z-[999999] flex flex-col gap-3 pointer-events-none">
    <div 
      v-for="toast in toastStore.mensajes" 
      :key="toast.id"
      class="animate-in slide-in-from-top-2 fade-in duration-300 pointer-events-auto flex items-start gap-3 w-80 p-4 bg-white border rounded-xl shadow-lg"
      :class="toast.tipo === 'error' ? 'border-rose-200' : 'border-emerald-200'"
    >
      <div :class="toast.tipo === 'error' ? 'text-rose-500' : 'text-emerald-500'">
        <svg v-if="toast.tipo === 'success'" class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z"></path></svg>
        <svg v-if="toast.tipo === 'error'" class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"></path></svg>
      </div>
      <div class="flex-1 mt-0.5">
        <h4 class="text-sm font-bold text-slate-800 leading-tight">{{ toast.titulo }}</h4>
        <p class="text-[13px] text-slate-500 mt-1 leading-snug">{{ toast.mensaje }}</p>
      </div>
      <button @click="toastStore.removerToast(toast.id)" class="text-slate-400 hover:text-slate-600 transition-colors p-1 -mt-1 -mr-1">
        <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"></path></svg>
      </button>
    </div>
  </div>
</template>