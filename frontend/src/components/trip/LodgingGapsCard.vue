<script setup lang="ts">
import { computed } from 'vue'
import Button from 'primevue/button'
import Pill from '../ui/Pill.vue'
import type { Booking, Trip } from '../../api/types'
import { fmtDayShort } from '../../utils/itinerary'
import { hasLodgingBookings, lodgingCoverage, type LodgingGap } from '../../utils/lodging'

// Aviso de noches sin cama. Solo aparece si el viaje TIENE alojamiento apuntado:
// en un viaje donde se duerme en casa de alguien no hay nada que avisar.
const props = defineProps<{ trip: Trip; bookings: Booking[] }>()

const coverage = computed(() => lodgingCoverage(props.trip, props.bookings))
const tracked = computed(() => hasLodgingBookings(props.bookings))

const uncovered = computed(() => coverage.value.totalNights - coverage.value.covered)
const show = computed(
  () => tracked.value && (coverage.value.gaps.length > 0 || coverage.value.overlapNights.length > 0),
)

function gapLabel(gap: LodgingGap): string {
  return gap.nights === 1 ? fmtDayShort(gap.from) : `${fmtDayShort(gap.from)} – ${fmtDayShort(gap.to)}`
}
</script>

<template>
  <div v-if="show" class="tt-pop-in bg-surface rounded-card border border-line p-4">
    <div class="flex items-start gap-3">
      <span
        class="mt-0.5 flex h-9 w-9 shrink-0 items-center justify-center rounded-full bg-warn-tint text-warn-strong"
      >
        <i class="mdi mdi-bed-empty" />
      </span>
      <div class="min-w-0 flex-1">
        <h3 v-if="uncovered" class="text-sm font-semibold text-ink-heading">
          {{ $t('trips.lodging.gapsTitle', { n: uncovered }, uncovered) }}
        </h3>
        <h3 v-else class="text-sm font-semibold text-ink-heading">
          {{ $t('trips.lodging.overlapTitle') }}
        </h3>
        <p class="text-xs text-ink-muted mt-0.5">
          {{
            $t('trips.lodging.coverage', {
              covered: coverage.covered,
              total: coverage.totalNights,
            })
          }}
        </p>
        <div v-if="coverage.gaps.length" class="flex flex-wrap gap-1.5 mt-2">
          <Pill v-for="gap in coverage.gaps" :key="gap.from" color="warn">
            {{ gapLabel(gap) }}
          </Pill>
        </div>
        <p v-if="coverage.overlapNights.length" class="text-xs text-ink-faint mt-2">
          <i class="mdi mdi-bed-double-outline" />
          {{
            $t(
              'trips.lodging.overlapHint',
              { n: coverage.overlapNights.length },
              coverage.overlapNights.length,
            )
          }}
        </p>
      </div>
      <router-link :to="{ name: 'trip-bookings', params: { id: trip.id } }" class="shrink-0">
        <Button
          :label="$t('trips.lodging.viewBookings')"
          text
          size="small"
          severity="warn"
          icon="pi pi-arrow-right"
          iconPos="right"
          class="max-sm:[&_.p-button-label]:hidden"
        />
      </router-link>
    </div>
  </div>
</template>
