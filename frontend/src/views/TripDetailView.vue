<script setup lang="ts">
import { computed, onMounted, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import Button from 'primevue/button'
import ProgressSpinner from 'primevue/progressspinner'
import StatusTag from '../components/StatusTag.vue'
import MemberChip from '../components/MemberChip.vue'
import SettledPill from '../components/trip/SettledPill.vue'
import TripFormDialog from '../components/TripFormDialog.vue'
import TabSkeleton from '../components/TabSkeleton.vue'
import { useTripsStore } from '../stores/trips'
import { formatDate } from '../composables/useMoney'
import { useConfirmDelete } from '../composables/useConfirmDelete'
import { useCountryImage } from '../composables/useCountryImage'
import { useNotify } from '../composables/useNotify'
import { countryName, flagEmoji } from '../countries'

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

const tabs = [
  { name: 'trip-overview', label: 'Resumen', icon: 'pi pi-home' },
  { name: 'trip-places', label: 'Sitios', icon: 'pi pi-map-marker' },
  { name: 'trip-itinerary', label: 'Itinerario', icon: 'pi pi-calendar' },
  { name: 'trip-bookings', label: 'Reservas', icon: 'pi pi-ticket' },
  { name: 'trip-expenses', label: 'Gastos', icon: 'pi pi-wallet' },
  { name: 'trip-packing', label: 'Maleta', icon: 'pi pi-briefcase' },
  { name: 'trip-files', label: 'Ficheros', icon: 'pi pi-paperclip' },
]

// cambio de tab en dos fases: primero se pinta la nav + skeleton (frame
// inmediato) y la tab pesada se monta en el siguiente frame — así el click
// responde al instante aunque la tab tarde en renderizar
const tabReady = ref(true)
// la tab clicada se marca activa al momento (optimista), sin esperar al router
const pendingTab = ref<string | null>(null)
const activeTab = computed(() => pendingTab.value ?? String(route.name))
watch(
  () => route.name,
  () => {
    pendingTab.value = null
    tabReady.value = false
    requestAnimationFrame(() => {
      requestAnimationFrame(() => {
        tabReady.value = true
      })
    })
  },
)

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
    <div v-if="notFound" class="text-center py-20 text-slate-500">
      Viaje no encontrado. <router-link to="/">Volver a la lista</router-link>
    </div>
    <div v-else-if="!store.current || store.current.id !== tripId" class="flex justify-center py-20">
      <ProgressSpinner style="width: 40px" />
    </div>
    <div v-else>
      <!-- banner con la imagen del viaje desvanecida hacia el fondo de la página -->
      <div
        v-if="bannerImage"
        class="relative h-44 sm:h-60 -mt-6 sm:mt-0 -mx-4 sm:mx-0 -mb-16 sm:-mb-20 overflow-hidden sm:rounded-t-2xl"
      >
        <img
          :src="bannerImage"
          class="absolute inset-0 w-full h-full object-cover banner-fade-y"
          alt=""
        />
      </div>

      <div
        class="relative flex flex-wrap items-start justify-between gap-3 mb-1"
        :class="bannerImage ? 'px-3 sm:px-6' : ''"
      >
        <div>
          <div class="flex items-center gap-3 flex-wrap">
            <h1 class="text-2xl font-bold text-slate-800">{{ store.current.name }}</h1>
            <StatusTag :status="store.current.status" />
            <SettledPill v-if="store.current.debts_settled" />
          </div>
          <p class="text-slate-500 mt-1 flex items-center gap-3 flex-wrap text-sm">
            <!-- cada bandera junto al nombre de su país -->
            <span v-if="store.current.countries.length" class="flex items-center gap-1.5 flex-wrap">
              <template v-for="(code, idx) in store.current.countries" :key="code">
                <span class="flex items-center gap-1">
                  <span class="text-base">{{ flagEmoji(code) }}</span>
                  <span>{{ countryName(code) }}</span>
                </span>
                <span v-if="idx < store.current.countries.length - 1" class="text-slate-300">·</span>
              </template>
            </span>
            <span v-if="store.current.start_date" class="flex items-center gap-1">
              <i class="pi pi-calendar text-xs" />
              {{ formatDate(store.current.start_date) }}
              <template v-if="store.current.end_date">→ {{ formatDate(store.current.end_date) }}</template>
            </span>
          </p>
        </div>
        <div class="flex items-center gap-2 flex-wrap max-sm:w-full">
          <div class="flex gap-1 mr-2 flex-wrap max-sm:flex-1">
            <MemberChip v-for="t in store.current.travelers" :key="t.id" :member="t" />
          </div>
          <Button
            v-if="store.current.album_url"
            as="a"
            :href="store.current.album_url"
            target="_blank"
            rel="noopener"
            icon="pi pi-images"
            severity="secondary"
            outlined
            size="small"
            class="tt-banner-btn"
            v-tooltip.bottom="'Álbum de fotos'"
          />
          <Button
            icon="pi pi-pencil"
            severity="secondary"
            outlined
            size="small"
            class="tt-banner-btn"
            v-tooltip.bottom="'Editar viaje'"
            @click="showEdit = true"
          />
          <Button
            icon="pi pi-trash"
            severity="danger"
            outlined
            size="small"
            class="tt-banner-btn"
            v-tooltip.bottom="'Eliminar viaje'"
            @click="deleteTrip"
          />
        </div>
      </div>

      <nav class="flex gap-1 border-b border-slate-200 mb-6 mt-4 overflow-x-auto no-scrollbar">
        <!-- el color activo se aplica SIN transición (una transición de color se
             congela si el hilo principal está montando la tab) y el subrayado
             crece con transform, que anima en el compositor -->
        <router-link
          v-for="tab in tabs"
          :key="tab.name"
          :to="{ name: tab.name, params: { id } }"
          class="tt-tab px-3 py-2 text-sm font-medium no-underline whitespace-nowrap"
          :class="
            activeTab === tab.name
              ? 'tt-tab-active text-[var(--p-primary-color)]'
              : 'text-slate-500 hover:text-slate-700'
          "
          @click="pendingTab = tab.name"
        >
          <i :class="tab.icon" class="mr-1.5 text-xs" />{{ tab.label }}
        </router-link>
      </nav>

      <div v-if="!tabReady" class="flex flex-col gap-5">
        <TabSkeleton v-if="tabSkeleton.stats" variant="stats" />
        <TabSkeleton :variant="tabSkeleton.main" :rows="tabSkeleton.rows" />
      </div>
      <!-- la clase cae en la raíz de la tab: cada tab entra con un rise suave -->
      <router-view v-else :trip="store.current" class="tt-anim-rise" />

      <TripFormDialog v-model:visible="showEdit" :trip="store.current" />
    </div>
  </div>
</template>

<style scoped>
/* reduced-motion lo cubre el guard global de style.css */
.tt-tab {
  position: relative;
}
.tt-tab::after {
  content: '';
  position: absolute;
  left: 0.6rem;
  right: 0.6rem;
  bottom: 0;
  height: 2px;
  border-radius: theme('borderRadius.full');
  background: var(--p-primary-color);
  transform: scaleX(0);
  transition: transform var(--tt-dur-180) ease;
}
.tt-tab-active::after {
  transform: scaleX(1);
}
</style>
