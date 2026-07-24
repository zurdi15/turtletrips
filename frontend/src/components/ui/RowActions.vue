<script setup lang="ts">
import Button from 'primevue/button'

// El reveal en hover depende de una clase .group (o .group/item) en el
// ANCESTRO de la fila — ver .hover-actions en style.css. Con `always` los
// botones quedan siempre visibles.
withDefaults(defineProps<{ always?: boolean }>(), { always: false })
defineEmits<{ edit: []; remove: [] }>()
</script>

<template>
  <div class="flex gap-1" :class="always ? '' : 'hover-actions'">
    <slot name="before" />
    <Button icon="pi pi-pencil" text size="small" severity="secondary" @click="$emit('edit')" />
    <Button icon="pi pi-trash" text size="small" severity="danger" @click="$emit('remove')" />
  </div>
</template>
