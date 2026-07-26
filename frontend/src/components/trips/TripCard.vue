<script setup lang="ts">
import StatusTag from '../StatusTag.vue'
import SettledPill from '../trip/SettledPill.vue'
import CoverImage from '../ui/CoverImage.vue'
import type { Trip } from '../../api/types'
import { tripDateRange } from '../../utils/trips'
import { flagEmoji } from '../../countries'

defineProps<{ trip: Trip; image: string | null }>()
</script>

<template>
  <router-link :to="`/trips/${trip.id}/overview`" class="no-underline">
    <div class="tt-lift bg-surface rounded-card border border-line overflow-hidden h-full group">
      <div class="relative h-32 bg-surface-strong overflow-hidden">
        <CoverImage
          v-if="image"
          :src="image"
          lazy
          class="w-full h-full"
          img-class="w-full h-full object-cover group-hover:scale-105 transition-transform duration-500"
        />
        <div
          v-else
          class="w-full h-full flex items-center justify-center text-4xl bg-gradient-to-br from-media-ph-start to-media-ph-end"
        >
          <template v-if="trip.countries.length">
            {{ trip.countries.map(flagEmoji).join(' ') }}
          </template>
          <i v-else class="mdi mdi-bag-suitcase-outline text-ink-faint" />
        </div>
        <div class="absolute top-2 right-2">
          <StatusTag :status="trip.status" />
        </div>
      </div>
      <div class="p-3.5">
        <h3 class="font-semibold text-ink-heading flex items-center gap-2">
          {{ trip.name }}
          <span class="text-sm">{{ trip.countries.map(flagEmoji).join(' ') }}</span>
          <SettledPill v-if="trip.debts_settled" />
        </h3>
        <p class="text-sm text-ink-muted mt-1 flex items-center gap-1.5">
          <i class="pi pi-calendar text-xs" /> {{ tripDateRange(trip) ?? $t('trips.noDates') }}
        </p>
        <p
          v-if="trip.travelers.length"
          class="text-xs text-ink-faint mt-1.5 flex items-center gap-1"
        >
          <i class="pi pi-users" /> {{ trip.travelers.map((t) => t.name).join(', ') }}
        </p>
      </div>
    </div>
  </router-link>
</template>
