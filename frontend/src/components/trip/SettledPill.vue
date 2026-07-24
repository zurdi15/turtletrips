<script setup lang="ts">
import Pill from '../ui/Pill.vue'
</script>

<template>
  <Pill
    color="brand"
    icon="pi pi-check-circle"
    pop-in
    v-tooltip.bottom="'Deudas saldadas entre viajeros'"
  >
    Saldado
  </Pill>
</template>
