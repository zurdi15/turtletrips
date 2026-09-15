<script setup lang="ts">
import ToggleSwitch from 'primevue/toggleswitch'

// Switch con etiqueta al lado (tonto: solo modelo + label). El switch NO
// encoge: su contenido es absoluto, así que como flex item su mínimo es cero y
// una etiqueta larga lo aplastaba hasta dejar el fondo sin dibujar. El texto
// es el que se adapta al ancho que sobra.
defineProps<{ label: string; disabled?: boolean }>()
const model = defineModel<boolean>({ required: true })
</script>

<template>
  <label class="flex items-center gap-3 text-sm cursor-pointer">
    <ToggleSwitch v-model="model" :disabled="disabled" class="shrink-0" />
    <span class="min-w-0 flex-1">
      {{ label }}
      <slot name="hint" />
    </span>
  </label>
</template>
