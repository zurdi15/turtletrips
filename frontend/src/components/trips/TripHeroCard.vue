<script setup lang="ts">
import type { Trip } from '../../api/types'
import { daysUntil } from '../../utils/dates'
import { tripDateRange } from '../../utils/trips'
import { flagEmoji } from '../../countries'

defineProps<{ trip: Trip; image: string | null }>()
</script>

<template>
  <router-link :to="`/trips/${trip.id}/overview`" class="no-underline block">
    <div class="relative rounded-2xl overflow-hidden bg-slate-800 group">
      <!-- ajustada a los laterales (sin zoom): ancho completo y alto según la imagen -->
      <img
        v-if="image"
        :src="image"
        class="block w-full h-auto min-h-40 max-h-[26rem] object-cover group-hover:scale-105 transition-transform duration-700"
        alt=""
      />
      <div v-else class="h-56 bg-gradient-to-br from-sky-700 to-indigo-900" />
      <div
        class="absolute inset-0 bg-gradient-to-t from-slate-900/85 via-slate-900/20 to-transparent"
      />
      <div class="absolute bottom-0 left-0 right-0 p-4 sm:p-6 text-white">
        <div class="flex items-end justify-between gap-3 sm:gap-4 flex-wrap">
          <div class="min-w-0">
            <p class="text-xs font-semibold uppercase tracking-widest text-white/70 mb-1">
              <template v-if="trip.status === 'ongoing'">
                <i class="mdi mdi-airplane text-xs" /> En curso
              </template>
              <template v-else>Próximo viaje</template>
            </p>
            <h2 class="text-xl sm:text-3xl font-bold flex items-center gap-2 sm:gap-3 flex-wrap">
              {{ trip.name }}
              <span class="text-lg sm:text-2xl">
                {{ trip.countries.map(flagEmoji).join(' ') }}
              </span>
            </h2>
            <p class="text-white/80 mt-1 text-xs sm:text-sm">{{ tripDateRange(trip) }}</p>
          </div>
          <div
            v-if="daysUntil(trip.start_date)"
            class="text-center bg-white/15 backdrop-blur rounded-xl px-3 py-2 sm:px-5 sm:py-3"
          >
            <p class="text-xl sm:text-3xl font-bold leading-none">{{ daysUntil(trip.start_date) }}</p>
            <p class="text-xs text-white/80 mt-1">días para salir</p>
          </div>
        </div>
      </div>
    </div>
  </router-link>
</template>
