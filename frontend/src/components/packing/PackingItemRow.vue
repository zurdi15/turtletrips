<script setup lang="ts">
import Checkbox from 'primevue/checkbox'
import RowActions from '../ui/RowActions.vue'
import PackingQuantity from './PackingQuantity.vue'
import type { PackingItem } from '../../api/types'

defineProps<{
  item: PackingItem
  /** maleta de solo consulta: ni check ni acciones */
  editable: boolean
  /** modo Ordenar: aparece el asa del drag & drop */
  reorderable?: boolean
}>()
defineEmits<{ toggle: []; edit: []; remove: [] }>()
</script>

<template>
  <!-- fila single-root: vive dentro del <draggable> de su categoría -->
  <li
    class="flex items-center gap-3 px-4 py-2 border-b border-line-faint last:border-b-0 hover:bg-surface-hover group/item"
  >
    <i
      v-if="reorderable"
      class="pi pi-bars text-xs text-ink-faint hover:text-ink-secondary tt-drag-handle cursor-grab active:cursor-grabbing shrink-0"
      v-tooltip.top="$t('packing.dragHint')"
    />
    <Checkbox
      :modelValue="item.checked"
      binary
      :disabled="!editable"
      @update:modelValue="$emit('toggle')"
    />
    <span
      class="flex-1 transition-colors duration-200"
      :class="{ 'line-through text-ink-faint': item.checked }"
    >
      {{ item.name }}
      <PackingQuantity :quantity="item.quantity" />
      <a
        v-if="item.url"
        :href="item.url"
        target="_blank"
        rel="noopener"
        class="ml-1 text-info hover:underline text-xs"
        v-tooltip.top="$t('packing.purchaseLink')"
        @click.stop
      >
        <i class="pi pi-shopping-cart" />
      </a>
    </span>
    <RowActions v-if="editable" @edit="$emit('edit')" @remove="$emit('remove')" />
  </li>
</template>
