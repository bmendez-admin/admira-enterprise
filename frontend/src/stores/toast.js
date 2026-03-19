import { defineStore } from 'pinia'

export const useToastStore = defineStore('toast', {
  state: () => ({
    mensajes: []
  }),
  actions: {
    agregarToast({ tipo = 'success', titulo, mensaje, duracion = 4000 }) {
      const id = Date.now();
      this.mensajes.push({ id, tipo, titulo, mensaje });
      // Autodestrucción después del tiempo indicado
      setTimeout(() => {
        this.removerToast(id);
      }, duracion);
    },
    removerToast(id) {
      this.mensajes = this.mensajes.filter(t => t.id !== id);
    }
  }
})