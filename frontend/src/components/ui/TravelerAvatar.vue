<script setup lang="ts">
// Primitiva TONTA: avatar de viajero — foto redonda si hay, si no un círculo
// con el color del viajero (iniciales a partir de tamaño sm; en xs, solo dot).
import { computed } from 'vue'
import { FALLBACK_COLOR } from '../../theme'
import { initials } from '../../utils/auth'

const props = withDefaults(
  defineProps<{
    name: string
    color?: string | null
    avatarUrl?: string | null
    size?: 'xs' | 'sm' | 'md' | 'xl'
  }>(),
  { color: null, avatarUrl: null, size: 'md' },
)

const IMG_SIZES = { xs: 'w-4 h-4', sm: 'w-6 h-6', md: 'w-8 h-8', xl: 'w-24 h-24' }
const TEXT_SIZES = { xs: '', sm: 'text-3xs', md: 'text-2xs', xl: 'text-2xl' }

const bg = computed(() => props.color ?? FALLBACK_COLOR)
</script>

<template>
  <img
    v-if="avatarUrl"
    :src="avatarUrl"
    :alt="name"
    class="rounded-full object-cover shrink-0"
    :class="IMG_SIZES[size]"
  />
  <!-- xs sin foto = el dot clásico de la app -->
  <span
    v-else-if="size === 'xs'"
    class="w-2 h-2 rounded-full inline-block shrink-0"
    :style="{ background: bg }"
    aria-hidden="true"
  />
  <span
    v-else
    class="rounded-full inline-flex items-center justify-center font-semibold text-white select-none shrink-0"
    :class="[IMG_SIZES[size], TEXT_SIZES[size]]"
    :style="{ background: bg }"
    :aria-label="name"
  >
    {{ initials(name) }}
  </span>
</template>
