<script setup lang="ts">
import { computed, onMounted, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import ProgressSpinner from 'primevue/progressspinner'
import TripFormDialog from '../components/trips/TripFormDialog.vue'
import TabSkeleton from '../components/TabSkeleton.vue'
import TripHeader from '../components/trip/TripHeader.vue'
import TripTabsNav from '../components/trip/TripTabsNav.vue'
import { useTripsStore } from '../stores/trips'
import { useConfirmDelete } from '../composables/useConfirmDelete'
import { useCountryImage } from '../composables/useCountryImage'
import { useNotify } from '../composables/useNotify'
import { useRafDeferred } from '../composables/useRafDeferred'

const props = defineProps<{ id: string }>()
const route = useRoute()
const router = useRouter()
const confirmAction = useConfirmDelete()
const notify = useNotify()
const store = useTripsStore()

const tripId = computed(() => Number(props.id))
const showEdit = ref(false)
const notFound = ref(false)

const { imageFor } = useCountryImage()
const bannerImage = computed(() => {
  const trip = store.current
  if (!trip) return null
  return trip.cover_url ?? imageFor(trip.countries[0])
})

async function load() {
  notFound.value = false
  try {
    await store.loadTrip(tripId.value)
  } catch {
    notFound.value = true
  }
}

onMounted(load)
watch(tripId, load)

// cambio de tab en dos fases: primero se pinta la nav + skeleton (frame
// inmediato) y la tab pesada se monta en el siguiente frame — así el click
// responde al instante aunque la tab tarde en renderizar
const { pending: tabPending } = useRafDeferred(() => route.name)

interface TabSkeletonSpec {
  stats?: boolean
  main: 'table' | 'cards' | 'list'
  rows: number
}
// espejo del skeleton de primera carga de cada tab, para que recargar y
// cambiar de tab se vean igual
const TAB_SKELETON: Record<string, TabSkeletonSpec> = {
  'trip-overview': { stats: true, main: 'cards', rows: 2 },
  'trip-places': { main: 'cards', rows: 4 },
  'trip-itinerary': { main: 'cards', rows: 3 },
  'trip-bookings': { main: 'cards', rows: 3 },
  'trip-expenses': { stats: true, main: 'table', rows: 8 },
  'trip-packing': { main: 'list', rows: 8 },
  'trip-files': { main: 'table', rows: 4 },
}
const tabSkeleton = computed(
  () => TAB_SKELETON[String(route.name)] ?? { main: 'table' as const, rows: 6 },
)

function deleteTrip() {
  confirmAction({
    message: `¿Eliminar "${store.current?.name}" con todos sus datos y ficheros?`,
    header: 'Eliminar viaje',
    accept: async () => {
      await store.deleteTrip(tripId.value)
      notify.success('Viaje eliminado')
      router.push('/')
    },
  })
}
</script>

<template>
  <div>
    <div v-if="notFound" class="text-center py-20 text-ink-muted">
      Viaje no encontrado. <router-link to="/">Volver a la lista</router-link>
    </div>
    <div v-else-if="!store.current || store.current.id !== tripId" class="flex justify-center py-20">
      <ProgressSpinner style="width: 40px" />
    </div>
    <div v-else>
      <TripHeader
        :trip="store.current"
        :bannerImage="bannerImage"
        @edit="showEdit = true"
        @delete="deleteTrip"
      />

      <TripTabsNav :tripId="id" />

      <div v-if="tabPending" class="flex flex-col gap-5">
        <TabSkeleton v-if="tabSkeleton.stats" variant="stats" />
        <TabSkeleton :variant="tabSkeleton.main" :rows="tabSkeleton.rows" />
      </div>
      <!-- la clase cae en la raíz de la tab: cada tab entra con un rise suave -->
      <router-view v-else :trip="store.current" class="tt-anim-rise" />

      <TripFormDialog v-model:visible="showEdit" :trip="store.current" />
    </div>
  </div>
</template>
