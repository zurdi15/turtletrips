<script setup lang="ts">
import { ref } from 'vue'
import Button from 'primevue/button'
import InputText from 'primevue/inputtext'
import RowActions from './RowActions.vue'

const props = defineProps<{
  name: string
  /** color del punto redondo; null usa el fallback */
  color?: string | null
  colorFallback?: string
}>()
const emit = defineEmits<{
  rename: [name: string]
  remove: []
  /** clic en el punto de color: el padre abre su ColorSwatchPopover */
  'pick-color': [event: Event]
}>()

const editing = ref(false)
const editName = ref('')

function startEdit() {
  editing.value = true
  editName.value = props.name
}

function confirmEdit() {
  const name = editName.value.trim()
  if (!name) return
  emit('rename', name)
  editing.value = false
}
</script>

<template>
  <li class="flex items-center gap-3 px-3 py-2 rounded-lg hover:bg-surface-hover group">
    <button
      class="w-5 h-5 rounded-full shrink-0 ring-1 ring-line hover:scale-110 transition-transform"
      :style="{ background: color ?? colorFallback }"
      v-tooltip.top="$t('common.actions.changeColor')"
      @click="$emit('pick-color', $event)"
    />
    <template v-if="editing">
      <InputText
        v-model="editName"
        class="flex-1"
        size="small"
        autofocus
        @keyup.enter="confirmEdit"
        @keyup.escape="editing = false"
      />
      <Button icon="pi pi-check" text size="small" @click="confirmEdit" />
      <Button icon="pi pi-times" text size="small" severity="secondary" @click="editing = false" />
    </template>
    <template v-else>
      <span class="flex-1 text-ink font-medium">{{ name }}</span>
      <slot />
      <RowActions @edit="startEdit" @remove="$emit('remove')" />
    </template>
  </li>
</template>
