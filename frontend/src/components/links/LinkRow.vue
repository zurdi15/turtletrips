<script setup lang="ts">
import CoverImage from '../ui/CoverImage.vue'
import RowActions from '../ui/RowActions.vue'
import type { TripLink } from '../../api/types'
import { linkHost } from '../../utils/links'

defineProps<{
  link: TripLink
  /** modo Ordenar: aparece el asa del drag & drop */
  reorderable?: boolean
}>()
defineEmits<{ edit: []; remove: [] }>()
</script>

<template>
  <!-- fila single-root: vive dentro del <draggable> del bloque -->
  <div class="flex items-start gap-3 px-3 py-2.5 group/item hover:bg-surface-hover">
    <i
      v-if="reorderable"
      class="pi pi-bars text-xs text-ink-faint hover:text-ink-secondary tt-drag-handle cursor-grab active:cursor-grabbing shrink-0"
      v-tooltip.top="$t('links.dragHint')"
    />
    <a
      :href="link.url"
      target="_blank"
      rel="noopener"
      class="flex-1 min-w-0 no-underline"
      v-tooltip.top="$t('links.openLink')"
    >
      <div class="min-w-0">
        <!-- en móvil nombre y dominio van SIEMPRE en filas propias (con el
             wrap, un nombre corto dejaba el dominio pegado y uno largo no) -->
        <div class="flex flex-col gap-0.5 sm:flex-row sm:items-center sm:gap-2 sm:flex-wrap">
          <span
            class="text-sm font-medium text-ink group-hover/item:text-primary transition-colors duration-200"
          >
            {{ link.title }}
          </span>
          <span
            class="inline-flex items-center gap-1 text-2xs text-ink-faint truncate max-w-full sm:max-w-[14rem]"
          >
            <i class="mdi mdi-open-in-new" />
            {{ linkHost(link.url) }}
          </span>
        </div>
        <p v-if="link.notes" class="text-xs text-ink-faint mt-0.5 whitespace-pre-line max-w-note">
          {{ link.notes }}
        </p>
      </div>
      <!-- miniatura OG (hoteles de Booking/Agoda…): la descarga el servidor.
           Va en su propia fila, debajo del texto, para que se vea de verdad -->
      <CoverImage
        v-if="link.image_url"
        :src="link.image_url"
        :alt="link.title"
        lazy
        imgClass="w-full h-full object-cover transition-transform duration-300 group-hover/item:scale-[1.03]"
        class="mt-2 w-full sm:w-80 h-40 rounded-lg bg-surface-muted"
      />
    </a>
    <RowActions always class="justify-end shrink-0" @edit="$emit('edit')" @remove="$emit('remove')" />
  </div>
</template>
