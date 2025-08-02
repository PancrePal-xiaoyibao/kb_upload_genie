// Vite 配置文件
// 注意：在安装依赖后，TypeScript 类型声明将自动可用

export default {
  plugins: [],
  resolve: {
    alias: {
      '@': './src',
    },
  },
  server: {
    port: 3000,
    proxy: {
      '/api': {
        target: 'http://localhost:8000',
        changeOrigin: true,
      },
    },
  },
  build: {
    outDir: 'dist',
    sourcemap: true,
  },
}