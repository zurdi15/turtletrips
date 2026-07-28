import { computed, ref, watch } from 'vue'
import { useRoute } from 'vue-router'
import { useI18n } from 'vue-i18n'
import { useSessionStore } from '../stores/session'

export interface NavItem {
  to: string
  label: string
  icon: string
  match: (path: string) => boolean
}

/**
 * Secciones de la navegación principal y cuál está activa. Lo comparten la
 * cabecera (desktop) y la barra flotante inferior (móvil), que nunca están
 * montadas a la vez.
 */
export function useNavItems() {
  const { t } = useI18n()
  const route = useRoute()
  const session = useSessionStore()

  const items = computed<NavItem[]>(() => [
    // solo la lista: dentro del detalle de un viaje (/trips/:id) ninguna
    // sección de la nav queda marcada como activa
    { to: '/', label: t('common.nav.trips'), icon: 'pi pi-compass', match: (p) => p === '/' },
    { to: '/map', label: t('common.nav.map'), icon: 'pi pi-globe', match: (p) => p.startsWith('/map') },
    {
      to: '/packing',
      label: t('common.nav.packing'),
      icon: 'pi pi-briefcase',
      match: (p) => p.startsWith('/packing'),
    },
    // el hub de viajeros/familias/cuentas es gestión: solo lo ve el admin
    ...(session.isAdmin
      ? [
          {
            to: '/travelers',
            label: t('common.nav.travelers'),
            icon: 'pi pi-users',
            match: (p: string) => p.startsWith('/travelers'),
          },
        ]
      : []),
  ])

  // la sección clicada se marca activa al momento (optimista), sin esperar al router
  const pendingTo = ref<string | null>(null)
  const activePath = computed(() => pendingTo.value ?? route.path)
  watch(
    () => route.path,
    () => (pendingTo.value = null),
  )
  const activeIndex = computed(() => items.value.findIndex((item) => item.match(activePath.value)))

  return { items, activeIndex, pendingTo }
}
