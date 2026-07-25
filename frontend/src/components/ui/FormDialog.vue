<script setup lang="ts">
import { computed } from 'vue'
import { useI18n } from 'vue-i18n'
import Dialog from 'primevue/dialog'
import Button from 'primevue/button'

const props = withDefaults(
  defineProps<{
    header: string
    saving?: boolean
    saveLabel?: string
    width?: 'md' | 'lg'
  }>(),
  { saving: false, width: 'lg' },
)
const { t } = useI18n()
const saveText = computed(() => props.saveLabel ?? t('common.actions.save'))
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
        <Button :label="$t('common.actions.cancel')" severity="secondary" text @click="visible = false" />
        <Button :label="saveText" :loading="saving" @click="$emit('save')" />
      </slot>
    </template>
  </Dialog>
</template>
