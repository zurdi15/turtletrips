<script setup lang="ts">
import type { PublicDayRow, RowTone } from '../../utils/publicAgenda'

// Tarjeta de un día del viaje compartido: solo lectura, sin enlaces ni acciones.
defineProps<{ title: string; sub: string; rows: PublicDayRow[] }>()

const TONE_CLASSES: Record<RowTone, string> = {
  info: 'text-info-strong bg-info-tint-strong',
  warn: 'text-warn-strong bg-warn-tint-strong',
  lodging: 'text-lodging-strong bg-lodging-tint-strong',
  plain: 'text-ink',
}
</script>

<template>
  <div class="bg-surface rounded-card border border-line overflow-hidden">
    <div
      class="flex items-baseline justify-between gap-2 px-4 py-2.5 bg-surface-muted border-b border-line-subtle"
    >
      <span class="font-semibold text-ink capitalize">{{ title }}</span>
      <span class="text-sm text-ink-faint shrink-0">{{ sub }}</span>
    </div>
    <div
      v-for="row in rows"
      :key="row.key"
      class="flex items-start gap-3 px-4 py-2 border-b border-line-faint last:border-b-0"
      :class="TONE_CLASSES[row.tone]"
    >
      <!-- el icono en su propia caja fija (vacía en las actividades): dentro de
           la columna de horas se comía el ancho y recortaba "Check-in: 15:00" -->
      <span class="w-4 shrink-0 mt-0.5 text-sm opacity-80 grid place-items-center">
        <i v-if="row.icon" :class="row.icon" />
      </span>
      <span class="w-24 sm:w-32 shrink-0 text-xs sm:text-sm opacity-80 tabular-nums truncate">
        <!-- transporte: tipo y horas (salida–llegada, +n si cruza noches) en
             dos líneas, como en la agenda de la app -->
        <template v-if="row.transport">
          {{ row.transport.kind }}
          <span v-if="row.transport.dep || row.transport.arr" class="block font-medium">
            {{ row.transport.dep ?? '' }}<span v-if="row.transport.dep && row.transport.arr" class="opacity-50">–</span>{{ row.transport.arr ?? '' }}<sup v-if="row.transport.arr && row.transport.plusDays" class="text-3xs">+{{ row.transport.plusDays }}</sup>
          </span>
        </template>
        <template v-else>{{ row.head }}</template>
      </span>
      <span class="min-w-0">
        <span class="font-medium text-sm">{{ row.title }}</span>
        <!-- una sola línea de apoyo: el sitio manda sobre la nota -->
        <span v-if="row.place ?? row.note" class="block text-xs opacity-70 whitespace-pre-line">
          {{ row.place ?? row.note }}
        </span>
      </span>
    </div>
    <p v-if="!rows.length" class="px-4 py-3 text-xs text-ink-disabled">
      {{ $t('share.public.emptyDay') }}
    </p>
  </div>
</template>
