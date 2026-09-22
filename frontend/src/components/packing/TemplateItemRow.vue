<script setup lang="ts">
import { ref } from 'vue'
import Button from 'primevue/button'
import InputText from 'primevue/inputtext'
import QuantityStepper from '../ui/QuantityStepper.vue'
import RowActions from '../ui/RowActions.vue'
import PackingCategorySelect from './PackingCategorySelect.vue'
import PackingQuantity from './PackingQuantity.vue'
import type { PackingTemplateItem } from '../../api/types'
import type { PackingAddPayload } from './PackingAddBar.vue'

const props = defineProps<{
  item: PackingTemplateItem
  /** plantilla de otro viajero: fila de solo consulta */
  readonly?: boolean
}>()
const emit = defineEmits<{
  save: [payload: PackingAddPayload]
  remove: []
}>()

// fila con edición inline (nombre + cantidad + categoría + enlace, sin diálogo)
const editing = ref(false)
const editName = ref('')
const editQuantity = ref(1)
const editCategory = ref('')
const editUrl = ref('')

function startEdit() {
  editing.value = true
  editName.value = props.item.name
  editQuantity.value = props.item.quantity
  editCategory.value = props.item.category
  editUrl.value = props.item.url ?? ''
}

function save() {
  if (!editName.value.trim()) return
  emit('save', {
    name: editName.value.trim(),
    category: editCategory.value,
    url: editUrl.value.trim() || null,
    quantity: editQuantity.value,
  })
  editing.value = false
}
</script>

<template>
  <li
    class="flex flex-wrap items-center gap-2 px-3 py-1.5 border-b border-line-faint last:border-b-0 hover:bg-surface-hover group/item text-sm"
  >
    <template v-if="editing">
      <InputText v-model="editName" size="small" class="flex-1 min-w-32" @keyup.enter="save" />
      <QuantityStepper v-model="editQuantity" :label="$t('packing.quantity')" size="small" />
      <PackingCategorySelect v-model="editCategory" size="small" class="w-36" />
      <InputText v-model="editUrl" size="small" placeholder="https://…" class="w-32" />
      <Button icon="pi pi-check" text size="small" @click="save" />
      <Button icon="pi pi-times" text size="small" severity="secondary" @click="editing = false" />
    </template>
    <template v-else>
      <span class="flex-1 text-ink">
        {{ item.name }}
        <PackingQuantity :quantity="item.quantity" />
        <a
          v-if="item.url"
          :href="item.url"
          target="_blank"
          rel="noopener"
          class="ml-1 text-info hover:underline text-xs"
          v-tooltip.top="$t('packing.purchaseLink')"
        >
          <i class="pi pi-shopping-cart" />
        </a>
      </span>
      <RowActions v-if="!readonly" @edit="startEdit" @remove="$emit('remove')" />
    </template>
  </li>
</template>
