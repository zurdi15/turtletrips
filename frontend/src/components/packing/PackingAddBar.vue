<script setup lang="ts">
import { ref } from 'vue'
import Button from 'primevue/button'
import InputText from 'primevue/inputtext'
import Select from 'primevue/select'

const props = withDefaults(
  defineProps<{
    placeholder: string
    categoryOptions: { value: string; label: string }[]
    defaultCategory?: string
    /** función-prop: el componente espera la promesa y limpia su estado solo
     *  si tuvo éxito (si lanza, el texto se conserva y el padre notifica) */
    onAdd: (payload: { name: string; category: string; url: string | null }) => Promise<void>
  }>(),
  { defaultCategory: 'Ropa' },
)

const name = ref('')
const category = ref(props.defaultCategory)
const url = ref('')
const showUrlField = ref(false)

async function add() {
  const trimmed = name.value.trim()
  if (!trimmed) return
  await props.onAdd({ name: trimmed, category: category.value, url: url.value.trim() || null })
  name.value = ''
  url.value = ''
  showUrlField.value = false
}
</script>

<template>
  <div class="flex flex-wrap items-center gap-2">
    <InputText v-model="name" :placeholder="placeholder" class="w-full sm:w-56" @keyup.enter="add" />
    <Select
      v-model="category"
      :options="categoryOptions"
      optionLabel="label"
      optionValue="value"
      class="flex-1 sm:flex-none sm:w-40"
    />
    <Button
      icon="pi pi-link"
      severity="secondary"
      :outlined="!showUrlField"
      v-tooltip.top="'Añadir enlace de compra'"
      @click="showUrlField = !showUrlField"
    />
    <InputText
      v-if="showUrlField"
      v-model="url"
      placeholder="https://… (enlace de compra)"
      class="w-full sm:w-56"
      @keyup.enter="add"
    />
    <Button
      label="Añadir"
      icon="pi pi-plus"
      class="shrink-0 max-sm:[&_.p-button-label]:hidden"
      @click="add"
    />
  </div>
</template>
