<script setup lang="ts">
import CoverImage from '../ui/CoverImage.vue'
import MemberChip from '../MemberChip.vue'
import StatusTag from '../StatusTag.vue'
import BrandMark from '../BrandMark.vue'
import type { PublicTrip } from '../../api/types'
import { countryName, flagEmoji } from '../../countries'
import { formatDate } from '../../composables/useMoney'

// Portada del viaje compartido. Los viajeros llegan como {name, color}: el
// enlace no lleva avatares ni ids, y MemberChip ya acepta esa proyección.
defineProps<{ trip: PublicTrip }>()
</script>

<template>
  <header class="relative">
    <div v-if="trip.cover_url" class="relative h-48 sm:h-72 -mx-4 sm:mx-0 sm:rounded-card overflow-hidden">
      <CoverImage
        :src="trip.cover_url"
        class="absolute inset-0"
        img-class="w-full h-full object-cover banner-fade-y"
      />
    </div>

    <div class="relative px-1 sm:px-2" :class="trip.cover_url ? '-mt-12 sm:-mt-16' : 'pt-2'">
      <div class="flex items-center gap-3 flex-wrap">
        <h1 class="text-2xl sm:text-3xl font-bold text-ink-heading">{{ trip.name }}</h1>
        <StatusTag :status="trip.status" />
      </div>

      <p class="text-ink-muted mt-1.5 flex items-center gap-3 flex-wrap text-sm">
        <span v-if="trip.countries.length" class="flex items-center gap-1.5 flex-wrap">
          <template v-for="(code, idx) in trip.countries" :key="code">
            <span class="flex items-center gap-1">
              <span class="text-base">{{ flagEmoji(code) }}</span>
              <span>{{ countryName(code) }}</span>
            </span>
            <span v-if="idx < trip.countries.length - 1" class="text-ink-disabled">·</span>
          </template>
        </span>
        <span v-if="trip.start_date" class="flex items-center gap-1">
          <i class="pi pi-calendar text-xs" />
          {{ formatDate(trip.start_date) }}
          <template v-if="trip.end_date"> → {{ formatDate(trip.end_date) }}</template>
        </span>
      </p>

      <div v-if="trip.travelers.length" class="flex flex-wrap gap-1.5 mt-3">
        <MemberChip v-for="who in trip.travelers" :key="who.name" :member="who" />
      </div>

      <p v-if="trip.notes" class="text-sm text-ink-secondary whitespace-pre-wrap mt-4">
        {{ trip.notes }}
      </p>

      <div class="flex items-center gap-3 mt-4 text-xs text-ink-faint">
        <span class="inline-flex items-center gap-1.5">
          <BrandMark class="w-4 h-4" />
          {{ $t('share.public.readOnly') }}
        </span>
        <a
          v-if="trip.album_url"
          :href="trip.album_url"
          target="_blank"
          rel="noopener noreferrer"
          class="inline-flex items-center gap-1 text-info hover:underline"
        >
          <i class="pi pi-images text-xs" />{{ $t('trips.header.album') }}
        </a>
      </div>
    </div>
  </header>
</template>
