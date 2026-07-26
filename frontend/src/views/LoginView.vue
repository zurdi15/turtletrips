<script setup lang="ts">
import { onMounted } from 'vue'
import { useI18n } from 'vue-i18n'
import { useRoute, useRouter } from 'vue-router'
import ProgressSpinner from 'primevue/progressspinner'
import BrandMark from '../components/BrandMark.vue'
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
        <BrandMark class="w-14 h-14 text-brand" />
        <h1 class="text-xl font-bold text-ink-heading">
          {{ session.bootstrapped === false ? t('auth.bootstrap.title') : t('auth.login.title') }}
        </h1>
        <p v-if="session.bootstrapped !== false" class="text-sm text-ink-muted">
          {{ t('auth.login.subtitle') }}
        </p>
      </div>
      <div v-if="session.bootstrapped === null" class="flex justify-center py-6">
        <ProgressSpinner class="w-10 h-10" stroke-width="4" />
      </div>
      <BootstrapForm v-else-if="session.bootstrapped === false" @success="onSuccess" />
      <LoginForm v-else @success="onSuccess" />
    </div>
  </div>
</template>
