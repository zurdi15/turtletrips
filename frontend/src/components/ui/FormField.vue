<script setup lang="ts">
defineProps<{ label: string; required?: boolean }>()
</script>

<template>
  <!-- tt-field: engancha las reglas de ancho de los controles (ver style.css) -->
  <div class="tt-field flex flex-col gap-1">
    <label class="text-sm font-medium">{{ label }}<template v-if="required"> *</template></label>
    <slot />
    <slot name="hint" />
  </div>
</template>
