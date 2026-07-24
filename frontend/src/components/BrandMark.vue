<script setup lang="ts">
// El SVG vive en src/assets/brandmark.svg (reutilizable desde cualquier sitio).
// Se inyecta inline (?raw) en vez de <img src>: un SVG externo no hereda
// currentColor y la tinta dejaría de adaptarse al color/tema del contenedor.
import brandmark from '../assets/brandmark.svg?raw'
</script>

<template>
  <span aria-hidden="true" class="block [&>svg]:w-full [&>svg]:h-full" v-html="brandmark" />
</template>
