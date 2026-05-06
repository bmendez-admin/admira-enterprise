import { defineStore } from 'pinia';
import axios from 'axios';

export const useAuthStore = defineStore('auth', {
    state: () => ({
        token: localStorage.getItem('token') || null,
        refreshToken: localStorage.getItem('refresh_token') || null,
        usuario: JSON.parse(localStorage.getItem('usuario')) || null,
    }),

    getters: {
        isAuthenticated: (state) => !!state.token,
    },

    actions: {
        rehidratarSesion() {
            if (this.token) {
                axios.defaults.headers.common['Authorization'] = `Bearer ${this.token}`;
            }
        },

        async login(email, password) {
            try {
                const response = await axios.post(
                    `${import.meta.env.VITE_API_URL}/login`,
                    { email, password }
                );

                this.token = response.data.access_token;
                this.refreshToken = response.data.refresh_token;
                this.usuario = response.data.usuario;

                localStorage.setItem('token', this.token);
                localStorage.setItem('refresh_token', this.refreshToken);
                localStorage.setItem('usuario', JSON.stringify(this.usuario));

                axios.defaults.headers.common['Authorization'] = `Bearer ${this.token}`;
                return true;
            } catch (error) {
                throw error;
            }
        },

        logout() {
            this.token = null;
            this.refreshToken = null;
            this.usuario = null;
            localStorage.removeItem('token');
            localStorage.removeItem('refresh_token');
            localStorage.removeItem('usuario');
            delete axios.defaults.headers.common['Authorization'];
        }
    }
});