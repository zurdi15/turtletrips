import { createApp, watch } from 'vue'
import { createPinia } from 'pinia'
import PrimeVue from 'primevue/config'
import Aura from '@primeuix/themes/aura'
import ToastService from 'primevue/toastservice'
import ConfirmationService from 'primevue/confirmationservice'
import Tooltip from 'primevue/tooltip'

import 'primeicons/primeicons.css'
import '@mdi/font/css/materialdesignicons.min.css'
import 'leaflet/dist/leaflet.css'
import './style.css'

import App from './App.vue'
import { router } from './router'
import { primevueEs } from './locale/es'
import { primevueEn } from './locale/en'
import { i18n, initLocale, type AppLocale } from './i18n'
import { initTheme } from './composables/useTheme'
import { setUnauthorizedHandler } from './api/client'
import { useSessionStore } from './stores/session'

// anti-flash: el último tema/idioma conocidos (localStorage) hasta que
// /auth/me aplique los guardados en DB (antes del primer paint, ver isReady)
initTheme()
initLocale()

const PRIMEVUE_LOCALES: Record<AppLocale, typeof primevueEs> = {
  es: primevueEs,
  en: primevueEn,
}

const app = createApp(App)
app.use(createPinia())
app.use(router)
app.use(i18n)
app.use(PrimeVue, {
  theme: {
    preset: Aura,
    options: { darkModeSelector: '.tt-dark' },
  },
  locale: PRIMEVUE_LOCALES[i18n.global.locale.value as AppLocale],
})
app.use(ToastService)
app.use(ConfirmationService)
app.directive('tooltip', Tooltip)

// PrimeVue no es reactivo al idioma por sí solo: se le espeja el cambio
watch(i18n.global.locale, (locale) => {
  app.config.globalProperties.$primevue.config.locale = PRIMEVUE_LOCALES[locale as AppLocale]
})

// sesión caducada en cualquier llamada → limpiar y volver al login
setUnauthorizedHandler(() => {
  const session = useSessionStore()
  session.clearSession()
  const current = router.currentRoute.value
  if (current.name !== 'login') {
    router.push({ name: 'login', query: { redirect: current.fullPath } })
  }
})

// la navegación inicial (y su fetchMe en el guard) termina antes del primer
// paint: sin flash de tema/idioma ni de UI protegida
router.isReady().then(() => app.mount('#app'))
