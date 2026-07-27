<script setup lang="ts">
import { computed, onMounted, ref, watch } from 'vue'
import { useI18n } from 'vue-i18n'
import { useRoute, useRouter } from 'vue-router'
import ProgressSpinner from 'primevue/progressspinner'
import BrandMark from '../components/BrandMark.vue'
import ClusterBtn from '../components/ui/ClusterBtn.vue'
import LoginForm from '../components/auth/LoginForm.vue'
import BootstrapForm from '../components/auth/BootstrapForm.vue'
import { useSessionStore } from '../stores/session'
import { safeRedirect } from '../utils/auth'
import { setLocale, type AppLocale } from '../i18n'

const { t, locale } = useI18n()
const route = useRoute()
const router = useRouter()
const session = useSessionStore()

onMounted(() => {
  if (session.bootstrapped === null) session.fetchStatus()
})

// el formulario a mostrar se decide UNA vez por montaje: tras el bootstrap el
// flag global pasa a true, y si el template reaccionara al cambio la
// Transition desmontaría BootstrapForm antes de que emita 'success' (Vue
// silencia los emits de componentes desmontados) — el redirect a home se
// perdería y el out-in quedaría colgado sin formulario
const mode = ref<'bootstrap' | 'login' | null>(null)
watch(
  () => session.bootstrapped,
  (v) => {
    if (mode.value === null && v !== null) mode.value = v ? 'login' : 'bootstrap'
  },
  { immediate: true },
)

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

function onSuccess() {
  router.replace(safeRedirect(route.query.redirect))
}
</script>

<template>
  <div class="min-h-[80vh] flex items-center justify-center">
    <div
      class="w-full max-w-sm bg-surface border border-line rounded-card shadow-lift p-8 flex flex-col gap-6 tt-anim-rise"
    >
      <div class="flex flex-col items-center gap-2 text-center">
        <!-- entra con un pop y se queda nadando; misma tinta que en la cabecera -->
        <BrandMark class="tt-swim w-14 h-14 text-ink-heading" />
        <h1 class="text-xl font-bold text-ink-heading">
          {{ mode === 'bootstrap' ? t('auth.bootstrap.title') : t('auth.login.title') }}
        </h1>
        <p v-if="mode !== 'bootstrap'" class="text-sm text-ink-muted">
          {{ t('auth.login.subtitle') }}
        </p>
      </div>
      <!-- el cambio spinner → formulario entra con un fade suave -->
      <Transition name="tt-fade" mode="out-in">
        <div v-if="mode === null" key="spinner" class="flex justify-center py-6">
          <ProgressSpinner class="w-10 h-10" stroke-width="4" />
        </div>
        <BootstrapForm v-else-if="mode === 'bootstrap'" key="bootstrap" @success="onSuccess" />
        <LoginForm v-else key="login" @success="onSuccess" />
      </Transition>
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
