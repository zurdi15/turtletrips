<script setup lang="ts">
import { ref } from 'vue'
import Button from 'primevue/button'

withDefaults(
  defineProps<{
    label?: string
    icon?: string
    accept?: string
    loading?: boolean
    severity?: string
    outlined?: boolean
    size?: 'small' | 'large'
  }>(),
  { icon: 'pi pi-upload', loading: false, outlined: false },
)
const emit = defineEmits<{ file: [file: File] }>()

const input = ref<HTMLInputElement>()

function onChange(event: Event) {
  const target = event.target as HTMLInputElement
  const file = target.files?.[0]
  // reset para poder volver a elegir el mismo fichero
  target.value = ''
  if (file) emit('file', file)
}
</script>

<template>
  <span>
    <input ref="input" type="file" :accept="accept" class="hidden" @change="onChange" />
    <Button
      :label="label"
      :icon="icon"
      :severity="severity"
      :outlined="outlined"
      :size="size"
      :loading="loading"
      @click="input?.click()"
    />
  </span>
</template>
