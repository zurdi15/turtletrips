<script setup lang="ts">
import Button from 'primevue/button'
import CoverImage from '../ui/CoverImage.vue'
import MemberChip from '../MemberChip.vue'
import StatusTag from '../StatusTag.vue'
import type { PublicTrip } from '../../api/types'
import { countryName, flagEmoji } from '../../countries'
import { formatDate } from '../../composables/useMoney'

// Cabecera del viaje compartido: el MISMO layout y los mismos tamaños que la
// cabecera de la app (`trip/TripHeader.vue`), con dos diferencias — no hay
// enlace al álbum (es privado) y en su hueco va la versión imprimible.
// Los viajeros llegan como {name, color}: el enlace no lleva avatares ni ids,
// y MemberChip ya acepta esa proyección.
defineProps<{ trip: PublicTrip; printTo: string }>()
</script>

<template>
  <div>
    <!-- banner con la imagen del viaje desvanecida hacia el fondo de la página -->
    <div
      v-if="trip.cover_url"
      class="relative h-44 sm:h-60 -mt-6 sm:mt-0 -mx-4 sm:mx-0 -mb-16 sm:-mb-20 overflow-hidden sm:rounded-t-2xl"
    >
      <CoverImage
        :src="trip.cover_url"
        class="absolute inset-0"
        img-class="w-full h-full object-cover banner-fade-y"
        :focus-x="trip.cover_focus_x"
        :focus-y="trip.cover_focus_y"
      />
    </div>

    <div
      class="relative flex flex-wrap items-start justify-between gap-3 mb-1"
      :class="trip.cover_url ? 'px-3 sm:px-6' : ''"
    >
      <div>
        <div class="flex items-center gap-3 flex-wrap">
          <h1 class="text-2xl font-bold text-ink-heading">{{ trip.name }}</h1>
          <StatusTag :status="trip.status" />
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
            <MemberChip v-for="who in trip.travelers" :key="who.name" :member="who" />
          </span>
        </p>
      </div>
      <div class="flex items-center gap-2 flex-wrap max-sm:w-full">
        <div class="flex gap-1 mr-2 flex-wrap max-sm:flex-1 sm:hidden">
          <MemberChip v-for="who in trip.travelers" :key="who.name" :member="who" />
        </div>
        <!-- donde la app tiene el álbum: aquí, guardar el plan en PDF -->
        <router-link :to="printTo">
          <Button
            icon="pi pi-print"
            severity="secondary"
            outlined
            size="small"
            class="tt-banner-btn"
            :aria-label="$t('print.open')"
            v-tooltip.bottom="$t('print.open')"
          />
        </router-link>
      </div>
    </div>
  </div>
</template>
