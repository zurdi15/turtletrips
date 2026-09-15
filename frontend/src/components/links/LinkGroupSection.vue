<script setup lang="ts">
import { useI18n } from 'vue-i18n'
import draggable from 'vuedraggable'
import Button from 'primevue/button'
import LinkRow from './LinkRow.vue'
import type { LinkGroup, TripLink } from '../../api/types'
import { LINK_GROUP_ICONS } from '../../constants'

defineProps<{
  /** null = enlaces sin bloque */
  group: LinkGroup | null
  /** espejo local del padre: el <draggable> lo reordena en sitio */
  links: TripLink[]
  /** sin cabecera (único cubo cuando aún no hay bloques) */
  bare?: boolean
  /** modo Ordenar: asas visibles y drag & drop activo */
  reorderable?: boolean
}>()
defineEmits<{
  edit: []
  remove: []
  add: []
  editLink: [link: TripLink]
  removeLink: [link: TripLink]
  /** fin de un arrastre de enlaces (el padre persiste la disposición entera) */
  reorder: []
}>()
const { t } = useI18n()
const DEFAULT_ICON = LINK_GROUP_ICONS[0]
</script>

<template>
  <section class="bg-surface rounded-card border border-line overflow-hidden">
    <header
      v-if="!bare"
      class="flex items-center gap-2 px-3 py-2 border-b border-line-subtle bg-surface-soft"
    >
      <!-- asa del drag & drop de BLOQUES (el <draggable> exterior vive en la pestaña) -->
      <i
        v-if="group && reorderable"
        class="pi pi-bars text-xs text-ink-faint hover:text-ink-secondary tt-group-handle cursor-grab active:cursor-grabbing"
        v-tooltip.top="t('links.dragHint')"
      />
      <i
        :class="group ? `mdi mdi-${group.icon ?? DEFAULT_ICON}` : 'mdi mdi-tray'"
        class="text-lg text-ink-muted leading-none"
      />
      <h3 class="flex-1 font-semibold text-ink truncate text-sm">
        {{ group?.name ?? t('links.noGroup') }}
      </h3>
      <span class="text-2xs text-ink-faint whitespace-nowrap">
        {{ t('links.count', links.length) }}
      </span>
      <Button
        icon="pi pi-plus"
        text
        size="small"
        severity="secondary"
        v-tooltip.top="t('links.addHere')"
        @click="$emit('add')"
      />
      <div v-if="group" class="flex gap-1">
        <Button icon="pi pi-pencil" text size="small" severity="secondary" @click="$emit('edit')" />
        <Button icon="pi pi-trash" text size="small" severity="danger" @click="$emit('remove')" />
      </div>
    </header>

    <!-- alto mínimo: un bloque vacío sigue siendo destino del arrastre, y la
         pista se pinta encima (absoluta) para no ser hija del <draggable> -->
    <div class="relative">
      <draggable
        :list="links"
        group="links"
        item-key="id"
        handle=".tt-drag-handle"
        :disabled="!reorderable"
        ghost-class="opacity-40"
        tag="div"
        class="tt-stagger divide-y divide-line-subtle min-h-[2.75rem]"
        @end="$emit('reorder')"
      >
        <template #item="{ element }">
          <LinkRow
            :link="element"
            :reorderable="reorderable"
            @edit="$emit('editLink', element)"
            @remove="$emit('removeLink', element)"
          />
        </template>
      </draggable>
      <p
        v-if="!links.length"
        class="absolute inset-0 flex items-center px-4 text-xs text-ink-faint pointer-events-none"
      >
        {{ t('links.groupEmpty') }}
      </p>
    </div>
  </section>
</template>
