<script setup lang="ts">
import Toast from 'primevue/toast'
import ConfirmDialog from 'primevue/confirmdialog'
import AppNav from './components/app/AppNav.vue'
</script>

<template>
  <div class="min-h-screen">
    <AppNav />
    <main class="max-w-6xl mx-auto px-4 py-6">
      <!-- cada vista entra con un rise suave al montarse (la clase cae en su raíz) -->
      <router-view class="tt-anim-rise" />
    </main>
    <Toast position="bottom-right" />
    <ConfirmDialog class="w-full max-w-md mx-4" />
  </div>
</template>
