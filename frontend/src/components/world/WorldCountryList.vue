<script setup lang="ts">
import Button from 'primevue/button'
import Tag from 'primevue/tag'
import EmptyState from '../EmptyState.vue'
import type { WorldPlace } from '../../api/types'
import { KIND_COLORS, KIND_LABELS, type CountryGroup } from '../../utils/worldGrouping'

defineProps<{
  groups: CountryGroup[]
  selectedId: number | null
  empty: boolean
  noMatch: boolean
}>()

defineEmits<{
  'fly-to': [place: WorldPlace]
  edit: [place: WorldPlace]
  remove: [place: WorldPlace]
}>()
</script>

<template>
  <div class="tt-stagger flex flex-col gap-4">
    <EmptyState
      v-if="empty"
      icon="pi pi-globe"
      title="Tu diario está vacío"
      subtitle="Marca tu primer país, busca una ciudad, o termina un viaje y aparecerá solo"
    />
    <p v-else-if="noMatch" class="text-center text-sm text-ink-faint py-10">
      Nada coincide con los filtros
    </p>
    <section
      v-for="group in groups"
      :key="group.code ?? 'none'"
      class="bg-surface rounded-card border border-line overflow-hidden"
    >
      <div class="px-4 py-3 bg-surface-muted border-b border-line-subtle">
        <div class="flex items-center gap-2.5 flex-wrap">
          <span class="text-xl">{{ group.flag }}</span>
          <span class="font-semibold text-ink-heading">{{ group.title }}</span>
          <Tag v-if="group.entry" value="visitado" severity="success" class="text-xs" />
          <span v-if="group.entry?.origin" class="text-xs text-ink-faint">
            viaje: {{ group.entry.origin }}
          </span>
          <span class="text-xs text-ink-faint">
            {{ group.children.length ? `${group.children.length} lugares` : '' }}
          </span>
          <span class="flex-1" />
          <div v-if="group.entry" class="flex gap-1">
            <Button
              icon="pi pi-map-marker"
              text
              size="small"
              severity="secondary"
              v-tooltip.top="'Ver en el mapa'"
              @click="$emit('fly-to', group.entry)"
            />
            <Button
              icon="pi pi-pencil"
              text
              size="small"
              severity="secondary"
              @click="$emit('edit', group.entry)"
            />
            <Button
              icon="pi pi-trash"
              text
              size="small"
              severity="danger"
              @click="$emit('remove', group.entry)"
            />
          </div>
        </div>
        <p v-if="group.entry?.note" class="text-sm text-ink-muted mt-1.5 whitespace-pre-wrap">
          {{ group.entry.note }}
        </p>
      </div>
      <ul v-if="group.children.length">
        <li
          v-for="place in group.children"
          :key="place.id"
          class="px-4 py-2.5 border-b border-line-faint last:border-b-0 hover:bg-surface-hover cursor-pointer group"
          :class="{ 'bg-info-tint': selectedId === place.id }"
          @click="$emit('fly-to', place)"
        >
          <div class="flex items-center gap-2.5">
            <span
              class="w-2.5 h-2.5 rounded-full shrink-0"
              :style="{ background: KIND_COLORS[place.kind] }"
              v-tooltip.left="KIND_LABELS[place.kind]"
            />
            <span class="font-medium text-ink">{{ place.name }}</span>
            <span v-if="place.origin" class="text-xs text-ink-faint">
              viaje: {{ place.origin }}
            </span>
            <span class="flex-1" />
            <div class="flex gap-1 hover-actions">
              <Button
                icon="pi pi-pencil"
                text
                size="small"
                severity="secondary"
                @click.stop="$emit('edit', place)"
              />
              <Button
                icon="pi pi-trash"
                text
                size="small"
                severity="danger"
                @click.stop="$emit('remove', place)"
              />
            </div>
          </div>
          <p v-if="place.note" class="text-sm text-ink-faint mt-1 pl-5 whitespace-pre-wrap">
            {{ place.note }}
          </p>
        </li>
      </ul>
    </section>
  </div>
</template>
