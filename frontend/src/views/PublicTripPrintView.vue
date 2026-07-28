<script setup lang="ts">
import { computed, onMounted, watch } from 'vue'
import { useI18n } from 'vue-i18n'
import Button from 'primevue/button'
import TabSkeleton from '../components/TabSkeleton.vue'
import EmptyState from '../components/EmptyState.vue'
import PrintToolbar from '../components/print/PrintToolbar.vue'
import TripPrintDocument from '../components/print/TripPrintDocument.vue'
import { applyVisitorLocale } from '../i18n'
import { usePublicTrip } from '../composables/usePublicTrip'
import { usePrintPage } from '../composables/usePrintPage'
import { usePrintTripData } from '../composables/usePrintTripData'
import { printDocumentTitle } from '../utils/print'

// Versión imprimible del viaje COMPARTIDO. Sin gastos, y no por omisión: el
// enlace público no los trae, y `allowExpenses: false` cierra también la puerta
// de `?expenses=1`.
const props = defineProps<{ token: string }>()

const { t } = useI18n()
const { trip, loading, gone, failed, load, retry, bookings, places, items } = usePublicTrip()
const { options, print, setTitle } = usePrintPage(false)

onMounted(() => {
  applyVisitorLocale()
  load(props.token)
})

const doc = usePrintTripData({
  trip: () =>
    trip.value && {
      name: trip.value.name,
      countries: trip.value.countries,
      start_date: trip.value.start_date,
      end_date: trip.value.end_date,
      notes: trip.value.notes,
      cover_url: trip.value.cover_url,
      cover_focus_x: trip.value.cover_focus_x,
      cover_focus_y: trip.value.cover_focus_y,
      travelers: trip.value.travelers,
    },
  // lo que el enlace no comparta llega vacío y su sección desaparece sola
  places: () => places.value,
  items: () => items.value,
  bookings: () => bookings.value,
  hasExpenses: () => false,
  options,
  t,
})

watch(
  () => trip.value?.name,
  (name) => name && setTitle(printDocumentTitle(name, trip.value?.start_date ?? null)),
)

const ready = computed(() => !loading.value && !!trip.value)
</script>

<template>
  <div class="min-h-screen -mt-6 bg-page">
    <PrintToolbar
      v-if="ready"
      v-model:options="options"
      :backTo="`/s/${token}`"
      :allowExpenses="false"
      @print="print"
    />
    <div class="max-w-4xl mx-auto py-6">
      <TabSkeleton v-if="loading" variant="cards" :rows="3" />
      <EmptyState
        v-else-if="failed"
        icon="pi pi-exclamation-triangle"
        :title="t('share.public.errorTitle')"
        :subtitle="t('share.public.errorSubtitle')"
      >
        <Button :label="t('share.public.retry')" icon="pi pi-refresh" outlined @click="retry" />
      </EmptyState>

      <EmptyState
        v-else-if="gone || !trip"
        icon="pi pi-link"
        :title="t('share.public.goneTitle')"
        :subtitle="t('share.public.goneSubtitle')"
      />
      <TripPrintDocument
        v-else-if="doc.trip.value"
        :trip="doc.trip.value"
        :days="doc.days.value"
        :places="places"
        :bookings="bookings"
        :route="doc.route.value"
        :options="options"
        :sections="doc.sections.value"
      />
    </div>
  </div>
</template>
