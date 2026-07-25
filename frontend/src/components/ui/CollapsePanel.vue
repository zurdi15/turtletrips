<script setup lang="ts">
// Colapso suave de altura (grid-template-rows 0fr→1fr, sin medir): el
// contenido de debajo se desplaza con la animación en vez de saltar.
// `inert` desactiva foco e interacción mientras está cerrado (sigue montado).
defineProps<{ open: boolean }>()
</script>

<template>
  <div class="tt-collapse" :class="open && 'tt-collapse-open'" :inert="!open">
    <div class="tt-collapse-clip">
      <slot />
    </div>
  </div>
</template>
