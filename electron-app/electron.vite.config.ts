import { resolve } from 'path'
import { defineConfig, externalizeDepsPlugin } from 'electron-vite'
import react from '@vitejs/plugin-react'
import SemiPlugin from 'vite-plugin-semi-theme'

export default defineConfig({
  main: {
    plugins: [externalizeDepsPlugin()],
  },
  preload: {
    plugins: [externalizeDepsPlugin()],
  },
  renderer: {
    resolve: {
      alias: {
        '@renderer': resolve('src/renderer/src'),
      },
    },
    plugins: [
      react({
        babel: {
          plugins: ['babel-plugin-react-compiler'],
        },
      }),
      SemiPlugin({
        theme: '@semi-bot/semi-theme-zsim',
      }),
    ],
  },
})
