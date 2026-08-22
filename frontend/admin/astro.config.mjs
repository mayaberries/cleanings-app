import { defineConfig } from 'astro/config';
import node from '@astrojs/node';
import tailwindcss from '@tailwindcss/vite';

import vue from '@astrojs/vue';

export default defineConfig({
  output: 'server',
  adapter: node({ mode: 'standalone' }),

  vite: {
    plugins: [tailwindcss()],
  },

  integrations: [vue()],
});