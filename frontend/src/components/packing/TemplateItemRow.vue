<script setup lang="ts">
import { ref } from 'vue'
import Button from 'primevue/button'
import InputText from 'primevue/inputtext'
import Select from 'primevue/select'
import RowActions from '../ui/RowActions.vue'
import type { PackingTemplateItem } from '../../api/types'

const props = defineProps<{
  item: PackingTemplateItem
  categoryOptions: { value: string; label: string }[]
}>()
const emit = defineEmits<{
  save: [payload: { name: string; category: string; url: string | null }]
  remove: []
}>()

// fila con edición inline (nombre + categoría + enlace, sin diálogo)
const editing = ref(false)
const editName = ref('')
const editCategory = ref('')
const editUrl = ref('')

function startEdit() {
  editing.value = true
  editName.value = props.item.name
  editCategory.value = props.item.category
  editUrl.value = props.item.url ?? ''
}

function save() {
  if (!editName.value.trim()) return
  emit('save', {
    name: editName.value.trim(),
    category: editCategory.value,
    url: editUrl.value.trim() || null,
  })
  editing.value = false
}
</script>

<template>
  <li
    class="flex flex-wrap items-center gap-2 px-3 py-1.5 border-b border-line-faint last:border-b-0 hover:bg-surface-hover group/item text-sm"
  >
    <template v-if="editing">
      <InputText v-model="editName" size="small" class="flex-1" @keyup.enter="save" />
      <Select
        v-model="editCategory"
        :options="categoryOptions"
        optionLabel="label"
        optionValue="value"
        size="small"
        class="w-32"
      />
      <InputText v-model="editUrl" size="small" placeholder="https://…" class="w-32" />
      <Button icon="pi pi-check" text size="small" @click="save" />
      <Button icon="pi pi-times" text size="small" severity="secondary" @click="editing = false" />
    </template>
    <template v-else>
      <span class="flex-1 text-ink">
        {{ item.name }}
        <a
          v-if="item.url"
          :href="item.url"
          target="_blank"
          rel="noopener"
          class="ml-1 text-info hover:underline text-xs"
          v-tooltip.top="'Enlace de compra'"
        >
          <i class="pi pi-shopping-cart" />
        </a>
      </span>
      <RowActions @edit="startEdit" @remove="$emit('remove')" />
    </template>
  </li>
</template>
