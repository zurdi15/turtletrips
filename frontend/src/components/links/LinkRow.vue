<script setup lang="ts">
import RowActions from '../ui/RowActions.vue'
import type { TripLink } from '../../api/types'
import { linkHost } from '../../utils/links'

defineProps<{ link: TripLink }>()
defineEmits<{ edit: []; remove: [] }>()
</script>

<template>
  <!-- fila single-root: vive dentro del <draggable> del bloque -->
  <div class="flex items-start gap-3 px-3 py-2.5 group/item hover:bg-surface-hover">
    <i
      class="pi pi-bars text-xs text-ink-faint hover:text-ink-secondary tt-drag-handle cursor-grab active:cursor-grabbing mt-1 shrink-0"
      v-tooltip.top="$t('links.dragHint')"
    />
    <a
      :href="link.url"
      target="_blank"
      rel="noopener"
      class="flex-1 min-w-0 no-underline"
      v-tooltip.top="$t('links.openLink')"
    >
      <div class="flex items-center gap-2 flex-wrap">
        <span class="text-sm font-medium text-ink group-hover/item:text-primary transition-colors duration-200">
          {{ link.title }}
        </span>
        <span class="inline-flex items-center gap-1 text-2xs text-ink-faint truncate max-w-[14rem]">
          <i class="mdi mdi-open-in-new" />
          {{ linkHost(link.url) }}
        </span>
      </div>
      <p v-if="link.notes" class="text-xs text-ink-faint mt-0.5 whitespace-pre-line max-w-note">
        {{ link.notes }}
      </p>
    </a>
    <RowActions class="justify-end shrink-0" @edit="$emit('edit')" @remove="$emit('remove')" />
  </div>
</template>
