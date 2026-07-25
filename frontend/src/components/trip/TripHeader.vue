<script setup lang="ts">
import Button from 'primevue/button'
import StatusTag from '../StatusTag.vue'
import MemberChip from '../MemberChip.vue'
import SettledPill from './SettledPill.vue'
import type { Trip } from '../../api/types'
import { formatDate } from '../../composables/useMoney'
import { countryName, flagEmoji } from '../../countries'

defineProps<{ trip: Trip; bannerImage: string | null }>()
</script>

<template>
  <div>
    <!-- banner con la imagen del viaje desvanecida hacia el fondo de la página -->
    <div
      v-if="bannerImage"
      class="relative h-44 sm:h-60 -mt-6 sm:mt-0 -mx-4 sm:mx-0 -mb-16 sm:-mb-20 overflow-hidden sm:rounded-t-2xl"
    >
      <img
        :src="bannerImage"
        class="absolute inset-0 w-full h-full object-cover banner-fade-y"
        alt=""
      />
    </div>

    <div
      class="relative flex flex-wrap items-start justify-between gap-3 mb-1"
      :class="bannerImage ? 'px-3 sm:px-6' : ''"
    >
      <div>
        <div class="flex items-center gap-3 flex-wrap">
          <h1 class="text-2xl font-bold text-ink-heading">{{ trip.name }}</h1>
          <StatusTag :status="trip.status" />
          <SettledPill v-if="trip.debts_settled" />
        </div>
        <p class="text-ink-muted mt-1 flex items-center gap-3 flex-wrap text-sm">
          <!-- cada bandera junto al nombre de su país -->
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
            <template v-if="trip.end_date">→ {{ formatDate(trip.end_date) }}</template>
          </span>
          <!-- en desktop los chips acompañan a países y fechas; en móvil van al bloque de abajo -->
          <span class="hidden sm:flex gap-1 flex-wrap">
            <MemberChip v-for="t in trip.travelers" :key="t.id" :member="t" />
          </span>
        </p>
      </div>
      <div class="flex items-center gap-2 flex-wrap max-sm:w-full">
        <div class="flex gap-1 mr-2 flex-wrap max-sm:flex-1 sm:hidden">
          <MemberChip v-for="t in trip.travelers" :key="t.id" :member="t" />
        </div>
        <Button
          v-if="trip.album_url"
          as="a"
          :href="trip.album_url"
          target="_blank"
          rel="noopener"
          icon="pi pi-images"
          severity="secondary"
          outlined
          size="small"
          class="tt-banner-btn"
          v-tooltip.bottom="'Álbum de fotos'"
        />
      </div>
    </div>
  </div>
</template>
