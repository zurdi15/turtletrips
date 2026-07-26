<script setup lang="ts">
import { useRoute } from 'vue-router'
import Toast from 'primevue/toast'
import ConfirmDialog from 'primevue/confirmdialog'
import AppNav from './components/app/AppNav.vue'

const route = useRoute()
</script>

<template>
  <div class="min-h-screen">
    <!-- las rutas "bare" (login) van a pantalla completa sin cabecera -->
    <AppNav v-if="!route.meta.bare" />
    <main class="max-w-6xl mx-auto px-4 py-6">
      <!-- cada vista entra con un rise suave al montarse (la clase cae en su raíz) -->
      <router-view class="tt-anim-rise" />
    </main>
    <Toast position="bottom-right" />
    <ConfirmDialog class="w-full max-w-md mx-4" />
  </div>
</template>
