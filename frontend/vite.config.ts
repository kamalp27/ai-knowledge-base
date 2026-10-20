/// <reference types="vitest" />
import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';

declare const process: {
  env: Record<string, string | undefined>;
};

// GitHub Pages deploys the project under '/ai-knowledge-base/'.
// In GitHub Actions (GITHUB_ACTIONS=true) or when VITE_BASE_PATH is provided,
// use the repository subpath. For Railway and local development, default to root '/'.
const isGitHubPages =
  process.env.GITHUB_ACTIONS === 'true' ||
  process.env.GITHUB_PAGES === 'true';

const basePath = process.env.VITE_BASE_PATH || (isGitHubPages ? '/ai-knowledge-base/' : '/');

// https://vitejs.dev/config/
export default defineConfig({
  base: basePath,
  plugins: [react()],
  server: {
    port: 5173,
    proxy: {
      '/api': {
        target: 'http://localhost:8000',
        changeOrigin: true,
      },
      '/health': {
        target: 'http://localhost:8000',
        changeOrigin: true,
      },
      '/ready': {
        target: 'http://localhost:8000',
        changeOrigin: true,
      },
    },
  },
  test: {
    globals: true,
    environment: 'jsdom',
    setupFiles: './src/test/setup.ts',
  },
});
