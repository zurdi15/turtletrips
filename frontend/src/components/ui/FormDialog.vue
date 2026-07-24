<script setup lang="ts">
import Dialog from 'primevue/dialog'
import Button from 'primevue/button'

withDefaults(
  defineProps<{
    header: string
    saving?: boolean
    saveLabel?: string
    width?: 'md' | 'lg'
  }>(),
  { saving: false, saveLabel: 'Guardar', width: 'lg' },
)
const visible = defineModel<boolean>('visible', { required: true })
defineEmits<{ save: [] }>()
</script>

<template>
  <Dialog
    v-model:visible="visible"
    modal
    :header="header"
    :class="['w-full mx-4', width === 'md' ? 'max-w-md' : 'max-w-lg']"
  >
    <div class="flex flex-col gap-4">
      <slot />
    </div>
    <template #footer>
      <!-- el fallback vive DENTRO de un #footer siempre declarado: el patrón
           v-if="$slots.footer" sobre el template es frágil en PrimeVue -->
      <slot name="footer">
        <Button label="Cancelar" severity="secondary" text @click="visible = false" />
        <Button :label="saveLabel" :loading="saving" @click="$emit('save')" />
      </slot>
    </template>
  </Dialog>
</template>
