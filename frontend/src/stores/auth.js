import { defineStore } from 'pinia';
import axios from 'axios';

export const useAuthStore = defineStore('auth', {
  // 1. EL ESTADO: ¿Qué estamos guardando?
  state: () => ({
    // Buscamos si ya hay un token guardado en el navegador de visitas anteriores
    token: localStorage.getItem('token') || null,
    usuario: JSON.parse(localStorage.getItem('usuario')) || null,
  }),

  // 2. GETTERS: Preguntas rápidas al almacén
  getters: {
    // Si hay un token, significa que el usuario está autenticado (true/false)
    isAuthenticated: (state) => !!state.token,
  },

  // 3. ACCIONES: Las funciones que cambian las cosas
  actions: {
    async login(email, password) {
      try {
        // Le tocamos la puerta al backend que hicimos ayer
        const response = await axios.post('http://127.0.0.1:8000/api/login', {
          email: email,
          password: password
        });

        // Si el backend nos deja pasar, guardamos el Token VIP y los datos
        this.token = response.data.access_token;
        this.usuario = response.data.usuario;

        // Lo guardamos en el 'localStorage' del navegador para que no se borre al recargar la página (F5)
        localStorage.setItem('token', this.token);
        localStorage.setItem('usuario', JSON.stringify(this.usuario));

        // Le pegamos el token al "Cartero" (Axios) para que todas las peticiones futuras vayan con la pulsera VIP puesta
        axios.defaults.headers.common['Authorization'] = `Bearer ${this.token}`;

        return true; // Éxito
      } catch (error) {
        console.error("Error en el login:", error);
        throw error; // Rebotamos el error para que la pantalla visual muestre una alerta
      }
    },

    // Función para cerrar sesión y destruir la pulsera VIP
    logout() {
      this.token = null;
      this.usuario = null;
      localStorage.removeItem('token');
      localStorage.removeItem('usuario');
      delete axios.defaults.headers.common['Authorization'];
    }
  }
});