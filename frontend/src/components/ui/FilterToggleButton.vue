<script setup lang="ts">
import Button from 'primevue/button'

defineProps<{ count: number }>()
const open = defineModel<boolean>({ required: true })
</script>

<template>
  <Button
    :label="$t('common.actions.filters')"
    :icon="open ? 'pi pi-chevron-up' : 'pi pi-sliders-h'"
    severity="secondary"
    :outlined="!open && !count"
    :badge="count ? String(count) : undefined"
    @click="open = !open"
  />
</template>
