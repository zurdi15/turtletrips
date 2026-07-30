<script setup lang="ts">
import { computed } from 'vue'
import { useI18n } from 'vue-i18n'
import BrandMark from '../BrandMark.vue'
import ClusterBtn from '../ui/ClusterBtn.vue'
import { setLocale, type AppLocale } from '../../i18n'

// Marco de las pantallas sin sesión (login, alta del admin, recuperación):
// tortuga, título y el selector de idioma pre-sesión.
defineProps<{ title: string; subtitle?: string }>()

const { t, locale } = useI18n()

// pre-sesión: la elección vive en localStorage; tras el login manda la de la
// cuenta (y el bootstrap crea la cuenta con el idioma elegido aquí)
const language = computed<AppLocale>({
  get: () => locale.value as AppLocale,
  set: (v) => setLocale(v),
})
// endónimos: el nombre de cada idioma no se traduce
const languageOptions = [
  { value: 'es', label: 'Español' },
  { value: 'en', label: 'English' },
] as const
</script>

<template>
  <div class="min-h-[80vh] flex items-center justify-center">
    <div
      class="w-full max-w-sm bg-surface border border-line rounded-card shadow-lift p-8 flex flex-col gap-6 tt-anim-rise"
    >
      <div class="flex flex-col items-center gap-2 text-center">
        <!-- entra con un pop y se queda nadando; misma tinta que en la cabecera -->
        <BrandMark class="tt-swim w-14 h-14 text-ink-heading" />
        <h1 class="text-xl font-bold text-ink-heading">{{ title }}</h1>
        <p v-if="subtitle" class="text-sm text-ink-muted">{{ subtitle }}</p>
      </div>
      <slot />
      <div class="flex justify-center">
        <ClusterBtn
          v-model="language"
          :options="languageOptions"
          size="small"
          :aria-label="t('settings.language.title')"
        />
      </div>
    </div>
  </div>
</template>
