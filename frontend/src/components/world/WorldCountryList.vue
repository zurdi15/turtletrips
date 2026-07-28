<script setup lang="ts">
import Button from 'primevue/button'
import Checkbox from 'primevue/checkbox'
import Tag from 'primevue/tag'
import EmptyState from '../EmptyState.vue'
import Pill from '../ui/Pill.vue'
import type { WorldPlace } from '../../api/types'
import { focusStyle } from '../../utils/imageFocus'
import { KIND_COLORS, KIND_KEYS, visitedLabel, type CountryGroup } from '../../utils/worldGrouping'

defineProps<{
  groups: CountryGroup[]
  selectedId: number | null
  empty: boolean
  noMatch: boolean
  /** países con ciudades/sitios: su entrada no se puede eliminar */
  lockedCodes: Set<string>
}>()

defineEmits<{
  'fly-to': [place: WorldPlace]
  edit: [place: WorldPlace]
  remove: [place: WorldPlace]
}>()

// selección para el borrado en bloque (solo ciudades/sitios, nunca países)
const selectedIds = defineModel<number[]>('selectedIds', { required: true })

function toggle(id: number) {
  selectedIds.value = selectedIds.value.includes(id)
    ? selectedIds.value.filter((x) => x !== id)
    : [...selectedIds.value, id]
}

function allSelected(group: CountryGroup): boolean {
  return group.children.length > 0 && group.children.every((p) => selectedIds.value.includes(p.id))
}

function toggleGroup(group: CountryGroup) {
  const ids = new Set(group.children.map((p) => p.id))
  if (allSelected(group)) {
    selectedIds.value = selectedIds.value.filter((x) => !ids.has(x))
  } else {
    selectedIds.value = [...new Set([...selectedIds.value, ...ids])]
  }
}
</script>

<template>
  <div class="tt-stagger flex flex-col gap-4">
    <EmptyState
      v-if="empty"
      icon="pi pi-globe"
      :title="$t('world.empty.title')"
      :subtitle="$t('world.empty.listHint')"
    />
    <p v-else-if="noMatch" class="text-center text-sm text-ink-faint py-10">
      {{ $t('world.list.noMatch') }}
    </p>
    <section
      v-for="group in groups"
      :key="group.code ?? 'none'"
      class="bg-surface rounded-card border border-line overflow-hidden"
    >
      <div class="px-4 py-3 bg-surface-muted border-b border-line-subtle">
        <div class="flex items-center gap-2.5 flex-wrap">
          <Checkbox
            v-if="group.children.length"
            :modelValue="allSelected(group)"
            binary
            v-tooltip.right="$t('world.list.selectGroup')"
            @update:modelValue="toggleGroup(group)"
          />
          <span class="text-xl">{{ group.flag }}</span>
          <!-- postal del país en miniatura -->
          <img
            v-if="group.entry?.photo_url"
            :src="group.entry.photo_url"
            class="h-9 w-14 object-cover rounded-md border border-line shrink-0"
            :style="{
              objectPosition: focusStyle(group.entry.photo_focus_x, group.entry.photo_focus_y),
            }"
            alt=""
          />
          <span class="font-semibold text-ink-heading">{{ group.title ?? $t('world.noCountry') }}</span>
          <Tag v-if="group.entry" :value="$t('world.list.visited')" severity="success" class="text-xs" />
          <!-- cuándo se visitó el país (retroactivo o heredado del viaje) -->
          <Pill v-if="group.entry && visitedLabel(group.entry)" color="info" icon="pi pi-calendar">
            {{ visitedLabel(group.entry) }}
          </Pill>
          <span v-if="group.entry?.origin" class="text-xs text-ink-faint">
            {{ $t('world.list.tripOrigin', { origin: group.entry.origin }) }}
          </span>
          <span class="text-xs text-ink-faint">
            {{ group.children.length ? $t('world.list.placeCount', { n: group.children.length }) : '' }}
          </span>
          <span class="flex-1" />
          <div v-if="group.entry" class="flex gap-1">
            <Button
              icon="pi pi-map-marker"
              text
              size="small"
              severity="secondary"
              v-tooltip.top="$t('world.list.viewOnMap')"
              @click="$emit('fly-to', group.entry)"
            />
            <Button
              icon="pi pi-pencil"
              text
              size="small"
              severity="secondary"
              @click="$emit('edit', group.entry)"
            />
            <!-- el span intermedio recibe el ratón cuando el botón está
                 deshabilitado: el tooltip del porqué sigue saliendo -->
            <span
              v-tooltip.top="{
                value: $t('world.list.countryLocked'),
                disabled: !(group.code && lockedCodes.has(group.code)),
              }"
            >
              <Button
                icon="pi pi-trash"
                text
                size="small"
                severity="danger"
                :disabled="!!group.code && lockedCodes.has(group.code)"
                @click="$emit('remove', group.entry)"
              />
            </span>
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
            <Checkbox
              :modelValue="selectedIds.includes(place.id)"
              binary
              @update:modelValue="toggle(place.id)"
              @click.stop
            />
            <span
              class="w-2.5 h-2.5 rounded-full shrink-0"
              :style="{ background: KIND_COLORS[place.kind] }"
              v-tooltip.left="$t(KIND_KEYS[place.kind])"
            />
            <span class="font-medium text-ink">{{ place.name }}</span>
            <span v-if="visitedLabel(place)" class="text-xs text-ink-faint whitespace-nowrap">
              <i class="pi pi-calendar text-2xs" /> {{ visitedLabel(place) }}
            </span>
            <span v-if="place.origin" class="text-xs text-ink-faint">
              {{ $t('world.list.tripOrigin', { origin: place.origin }) }}
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
