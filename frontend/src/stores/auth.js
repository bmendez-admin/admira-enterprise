import { defineStore } from 'pinia';
import axios from 'axios';

export const useAuthStore = defineStore('auth', {
  state: () => ({
    // Intentamos recuperar los datos del "bolsillo" (LocalStorage) nada más empezar
    token: localStorage.getItem('token') || null,
    usuario: JSON.parse(localStorage.getItem('usuario')) || null,
  }),

  getters: {
    // Si hay token y no es null/undefined, estamos autenticados
    isAuthenticated: (state) => !!state.token,
  },

  actions: {
    // Esta función es vital: se asegura de que Axios siempre tenga el token listo
    rehidratarSesion() {
      if (this.token) {
        axios.defaults.headers.common['Authorization'] = `Bearer ${this.token}`;
      }
    },

    async login(email, password) {
      try {
        const response = await axios.post('/login', { email, password });

        this.token = response.data.access_token;
        this.usuario = response.data.usuario;

        localStorage.setItem('token', this.token);
        localStorage.setItem('usuario', JSON.stringify(this.usuario));

        // Ponemos el token en la "frente" de todas las peticiones futuras
        axios.defaults.headers.common['Authorization'] = `Bearer ${this.token}`;

        return true;
      } catch (error) {
        console.error("Error en el login:", error);
        throw error;
      }
    },

    logout() {
      this.token = null;
      this.usuario = null;
      localStorage.removeItem('token');
      localStorage.removeItem('usuario');
      delete axios.defaults.headers.common['Authorization'];
    }
  }
});