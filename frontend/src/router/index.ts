import { createRouter, createWebHistory } from 'vue-router'
import { useSessionStore } from '../stores/session'

declare module 'vue-router' {
  interface RouteMeta {
    /** accesible sin sesión (login) */
    public?: boolean
    /** sin cabecera de la app (pantalla completa) */
    bare?: boolean
    /** solo administradores */
    admin?: boolean
  }
}

export const router = createRouter({
  history: createWebHistory(),
  routes: [
    {
      path: '/login',
      name: 'login',
      component: () => import('../views/LoginView.vue'),
      meta: { public: true, bare: true },
    },
    {
      // viaje compartido en solo lectura: quien abre el enlace puede no tener
      // cuenta en la instancia, así que ni sesión ni cabecera de la app
      path: '/s/:token',
      name: 'public-trip',
      component: () => import('../views/PublicTripView.vue'),
      props: true,
      meta: { public: true, bare: true },
    },
    {
      // el mismo viaje compartido, listo para el "Guardar como PDF" del navegador
      path: '/s/:token/print',
      name: 'public-trip-print',
      component: () => import('../views/PublicTripPrintView.vue'),
      props: true,
      meta: { public: true, bare: true },
    },
    {
      path: '/trips/:id/print',
      name: 'trip-print',
      component: () => import('../views/TripPrintView.vue'),
      props: true,
      meta: { bare: true },
    },
    {
      path: '/profile',
      name: 'profile',
      component: () => import('../views/ProfileView.vue'),
    },
    {
      path: '/',
      name: 'trips',
      component: () => import('../views/TripListView.vue'),
    },
    {
      path: '/map',
      name: 'world-map',
      component: () => import('../views/WorldMapView.vue'),
    },
    {
      path: '/packing',
      name: 'packing-templates',
      component: () => import('../views/PackingTemplatesView.vue'),
    },
    {
      path: '/travelers',
      name: 'travelers',
      component: () => import('../views/TravelersView.vue'),
      // hub de gestión de personas (familias, cuentas): solo admin
      meta: { admin: true },
    },
    {
      path: '/settings',
      name: 'settings',
      component: () => import('../views/SettingsView.vue'),
    },
    {
      path: '/trips/:id',
      // layout del viaje: cabecera + tabs; las vistas hijas van dentro
      component: () => import('../layouts/TripLayout.vue'),
      props: true,
      children: [
        { path: '', redirect: { name: 'trip-overview' } },
        {
          path: 'overview',
          name: 'trip-overview',
          component: () => import('../views/trip/OverviewTab.vue'),
        },
        {
          path: 'places',
          name: 'trip-places',
          component: () => import('../views/trip/PlacesTab.vue'),
        },
        {
          path: 'itinerary',
          name: 'trip-itinerary',
          component: () => import('../views/trip/ItineraryTab.vue'),
        },
        {
          path: 'bookings',
          name: 'trip-bookings',
          component: () => import('../views/trip/BookingsTab.vue'),
        },
        {
          path: 'expenses',
          name: 'trip-expenses',
          component: () => import('../views/trip/ExpensesTab.vue'),
        },
        {
          path: 'packing',
          name: 'trip-packing',
          component: () => import('../views/trip/PackingTab.vue'),
        },
        {
          path: 'checklist',
          name: 'trip-checklist',
          component: () => import('../views/trip/ChecklistTab.vue'),
        },
        {
          path: 'files',
          name: 'trip-files',
          component: () => import('../views/trip/FilesTab.vue'),
        },
        {
          path: 'settings',
          name: 'trip-settings',
          component: () => import('../views/trip/SettingsTab.vue'),
        },
      ],
    },
  ],
})

// guard de sesión: espera a conocer al usuario (una única carga deduplicada)
// antes de resolver cualquier navegación. Requiere pinia instalada antes que
// el router en main.ts.
router.beforeEach(async (to) => {
  const session = useSessionStore()
  await session.ensureLoaded()
  if (to.meta.public) {
    // ya logueado, el login no pinta nada útil
    if (to.name === 'login' && session.isAuthenticated) return { path: '/' }
    return true
  }
  if (!session.isAuthenticated) {
    return { name: 'login', query: { redirect: to.fullPath } }
  }
  if (to.meta.admin && !session.isAdmin) return { path: '/' }
  return true
})
