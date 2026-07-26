import { computed, ref } from 'vue'
import { defineStore } from 'pinia'
import { api, ApiError } from '../api/client'
import type {
  BootstrapInput,
  Me,
  SettingsInput,
  Traveler,
} from '../api/types'
import { setThemePref } from '../composables/useTheme'
import { setLocale } from '../i18n'

const ME_KEY = 'tt-me'

export const useSessionStore = defineStore('session', () => {
  const me = ref<Me | null>(null)
  // ya se intentó cargar la sesión al menos una vez (el guard espera a esto)
  const loaded = ref(false)
  const loading = ref(false)
  // resultado de /auth/status: null = aún no consultado
  const bootstrapped = ref<boolean | null>(null)
  let inflight: Promise<void> | null = null

  const isAuthenticated = computed(() => me.value !== null)
  const isAdmin = computed(() => me.value?.user.is_admin ?? false)
  const travelerId = computed(() => me.value?.traveler.id ?? null)

  function applyUserSettings() {
    if (!me.value) return
    // tema e idioma viven en DB; localStorage queda como caché anti-flash
    setThemePref(me.value.user.theme)
    setLocale(me.value.user.language)
  }

  function setMe(value: Me) {
    me.value = value
    applyUserSettings()
    try {
      localStorage.setItem(ME_KEY, JSON.stringify(value))
    } catch {
      /* almacenamiento lleno o no disponible */
    }
  }

  function clearSession() {
    me.value = null
    localStorage.removeItem(ME_KEY)
  }

  async function fetchMe() {
    loading.value = true
    try {
      setMe(await api.get<Me>('/auth/me'))
    } catch (err) {
      if (err instanceof ApiError) {
        // 401 = sin sesión (o caducada): estado limpio, sin relanzar
        clearSession()
      } else {
        // fallo de red (PWA offline): restaurar el último snapshot conocido
        try {
          const cached = localStorage.getItem(ME_KEY)
          if (cached) me.value = JSON.parse(cached) as Me
        } catch {
          me.value = null
        }
      }
    } finally {
      loading.value = false
      loaded.value = true
    }
  }

  /** Carga única y deduplicada de la sesión (la llama el guard del router). */
  function ensureLoaded(): Promise<void> {
    if (loaded.value) return Promise.resolve()
    if (!inflight) {
      inflight = fetchMe().finally(() => {
        inflight = null
      })
    }
    return inflight
  }

  async function fetchStatus() {
    const status = await api.get<{ bootstrapped: boolean }>('/auth/status')
    bootstrapped.value = status.bootstrapped
    return status.bootstrapped
  }

  async function login(username: string, password: string) {
    setMe(await api.post<Me>('/auth/login', { username, password }))
    loaded.value = true
  }

  async function bootstrap(payload: BootstrapInput) {
    setMe(await api.post<Me>('/auth/bootstrap', payload))
    bootstrapped.value = true
    loaded.value = true
  }

  async function logout() {
    try {
      await api.post('/auth/logout')
    } catch {
      /* la sesión local se limpia igual */
    }
    clearSession()
    // sin fugas entre cuentas en el mismo navegador: fuera cachés del SW
    if ('caches' in window) {
      try {
        await caches.delete('api')
        await caches.delete('images')
      } catch {
        /* sin SW (dev) */
      }
    }
  }

  async function updateSettings(patch: SettingsInput) {
    setMe(await api.patch<Me>('/auth/me/settings', patch))
  }

  function changePassword(currentPassword: string, newPassword: string) {
    return api.post('/auth/me/password', {
      current_password: currentPassword,
      new_password: newPassword,
    })
  }

  /** Espeja en la sesión las ediciones del propio viajero (perfil). */
  function setTraveler(traveler: Traveler) {
    if (me.value && traveler.id === me.value.traveler.id) {
      setMe({ ...me.value, traveler })
    }
  }

  return {
    me,
    loaded,
    loading,
    bootstrapped,
    isAuthenticated,
    isAdmin,
    travelerId,
    ensureLoaded,
    fetchMe,
    fetchStatus,
    login,
    bootstrap,
    logout,
    clearSession,
    updateSettings,
    changePassword,
    setTraveler,
  }
})
