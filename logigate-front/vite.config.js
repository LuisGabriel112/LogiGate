import { sveltekit } from '@sveltejs/kit/vite';
import { defineConfig } from 'vite';
import tailwindcss from '@tailwindcss/vite';
import fs from 'fs';
import path from 'path';

const certPath = path.resolve('../logigate-backend/cert.pem');
const keyPath  = path.resolve('../logigate-backend/key.pem');
const hasSSL   = fs.existsSync(certPath) && fs.existsSync(keyPath);

export default defineConfig({
	plugins: [tailwindcss(), sveltekit()],
	server: {
		host: true,
		https: hasSSL
			? { cert: fs.readFileSync(certPath), key: fs.readFileSync(keyPath) }
			: undefined,
	},
});
