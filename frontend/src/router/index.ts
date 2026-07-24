import { createRouter, createWebHistory } from 'vue-router'

export const router = createRouter({
  history: createWebHistory(),
  routes: [
    {
      path: '/',
      name: 'trips',
      component: () => import('../views/TripListView.vue'),
    },
    {
      path: '/maletas',
      name: 'packing-templates',
      component: () => import('../views/PackingTemplatesView.vue'),
    },
    {
      path: '/viajeros',
      name: 'travelers',
      component: () => import('../views/TravelersView.vue'),
    },
    {
      path: '/settings',
      name: 'settings',
      component: () => import('../views/SettingsView.vue'),
    },
    {
      path: '/trips/:id',
      component: () => import('../views/TripDetailView.vue'),
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
          path: 'files',
          name: 'trip-files',
          component: () => import('../views/trip/FilesTab.vue'),
        },
      ],
    },
  ],
})
