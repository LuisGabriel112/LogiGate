import { sveltekit } from '@sveltejs/kit/vite';
import { defineConfig } from 'vite';
import tailwindcss from '@tailwindcss/vite';
import basicSsl from '@vitejs/plugin-basic-ssl';

export default defineConfig({
	plugins: [tailwindcss(), sveltekit(), basicSsl()],
	server: {
		host: '0.0.0.0',
		port: 5173,
		https: true,
		proxy: {
			'/api': { target: 'http://localhost:8000', changeOrigin: true },
			'/static': { target: 'http://localhost:8000', changeOrigin: true },
		},
	}
});
