<script setup lang="ts">
import { computed, onMounted, ref, watch } from 'vue'
import { useI18n } from 'vue-i18n'
import { useRoute, useRouter } from 'vue-router'
import ProgressSpinner from 'primevue/progressspinner'
import AuthCard from '../components/auth/AuthCard.vue'
import LoginForm from '../components/auth/LoginForm.vue'
import BootstrapForm from '../components/auth/BootstrapForm.vue'
import { useSessionStore } from '../stores/session'
import { safeRedirect } from '../utils/auth'

const { t } = useI18n()
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

const title = computed(() =>
  mode.value === 'bootstrap' ? t('auth.bootstrap.title') : t('auth.login.title'),
)
const subtitle = computed(() =>
  mode.value === 'bootstrap' ? undefined : t('auth.login.subtitle'),
)

function onSuccess() {
  router.replace(safeRedirect(route.query.redirect))
}
</script>

<template>
  <AuthCard :title="title" :subtitle="subtitle">
    <!-- el cambio spinner → formulario entra con un fade suave -->
    <Transition name="tt-fade" mode="out-in">
      <div v-if="mode === null" key="spinner" class="flex justify-center py-6">
        <ProgressSpinner class="w-10 h-10" stroke-width="4" />
      </div>
      <BootstrapForm v-else-if="mode === 'bootstrap'" key="bootstrap" @success="onSuccess" />
      <LoginForm v-else key="login" @success="onSuccess" />
    </Transition>
  </AuthCard>
</template>
