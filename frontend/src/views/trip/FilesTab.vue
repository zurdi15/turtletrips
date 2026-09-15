<script setup lang="ts">
import { computed, ref } from 'vue'
import { useI18n } from 'vue-i18n'
import { useRoute } from 'vue-router'
import AttachmentList from '../../components/AttachmentList.vue'
import EmptyState from '../../components/EmptyState.vue'
import FilesSection from '../../components/files/FilesSection.vue'
import TabSkeleton from '../../components/TabSkeleton.vue'
import type { Trip } from '../../api/types'
import { useAttachmentsStore } from '../../stores/attachments'
import { useBookingsStore } from '../../stores/bookings'
import { useExpensesStore } from '../../stores/expenses'
import { useConfirmDelete } from '../../composables/useConfirmDelete'
import { useRowFlash } from '../../composables/useRowFlash'
import { useTripTabData } from '../../composables/useTripTabData'

const props = defineProps<{ trip: Trip }>()
const { t } = useI18n()
const store = useAttachmentsStore()
const bookings = useBookingsStore()
const expenses = useExpensesStore()
const confirmAction = useConfirmDelete()

const route = useRoute()
// llegar desde un gasto (?attachment=id) enciende ese adjunto
const highlightId = ref<number | null>(null)

useTripTabData(() => props.trip, {
  load(tripId) {
    store.load(tripId)
    bookings.load(tripId)
    expenses.load(tripId)
  },
  afterFirstLoad() {
    const fromQuery = Number(route.query.attachment)
    if (fromQuery) {
      highlightId.value = fromQuery
      setTimeout(() => (highlightId.value = null), 4000)
    }
  },
})

const rootEl = ref<HTMLElement | null>(null)
// sin paginación en estas tablas: pageRows alto deja el salto de página en no-op
const first = ref(0)
const pageRows = ref(10000)
// solo por el scroll hasta el adjunto encendido; la clase la pone cada sección
useRowFlash({
  rows: () => store.items,
  highlightId: () => highlightId.value,
  first,
  pageRows,
  root: () => rootEl.value,
})

const bookingTitle = computed(() => new Map(bookings.items.map((b) => [b.id, b.title])))
const expenseDesc = computed(() => new Map(expenses.items.map((e) => [e.id, e.description])))

// los recibos de gastos van en su propia sección (conceptualmente aparte
// de la documentación del viaje: billetes, visados…)
const receipts = computed(() => store.items.filter((a) => a.expense_id != null))
const tripFiles = computed(() => store.items.filter((a) => a.expense_id == null))

function remove(id: number, name: string) {
  confirmAction({
    message: t('bookings.files.confirmDelete.message', { name }),
    header: t('bookings.files.confirmDelete.header'),
    accept: () => store.remove(id),
  })
}
</script>

<template>
  <div ref="rootEl">
    <TabSkeleton v-if="store.loading && !store.items.length" variant="table" :rows="4" />

    <!-- vacío: un único mensaje con el botón de añadir como acción -->
    <EmptyState
      v-else-if="!store.items.length"
      icon="pi pi-paperclip"
      :title="$t('bookings.files.empty.title')"
      :subtitle="$t('bookings.files.empty.subtitle')"
    >
      <AttachmentList :show-list="false" :label="$t('bookings.files.add')" />
    </EmptyState>

    <template v-else>
      <div class="mb-4">
        <AttachmentList :show-list="false" :label="$t('bookings.files.add')" />
      </div>

      <!-- documentación del viaje (billetes, visados, adjuntos de reservas…) -->
      <h3
        v-if="tripFiles.length && receipts.length"
        class="text-sm font-semibold text-ink-secondary mb-2"
      >
        {{ $t('bookings.files.sections.trip') }}
      </h3>
      <FilesSection
        v-if="tripFiles.length"
        :items="tripFiles"
        kind="trip"
        :tripId="trip.id"
        :bookingTitle="bookingTitle"
        :expenseDesc="expenseDesc"
        :highlightId="highlightId"
        @remove="remove"
      />

      <!-- recibos de gastos: sección propia, con enlace al gasto -->
      <template v-if="receipts.length">
        <h3
          class="text-sm font-semibold text-ink-secondary mb-2"
          :class="tripFiles.length ? 'mt-5' : ''"
        >
          {{ $t('bookings.files.sections.receipts') }}
        </h3>
        <FilesSection
          :items="receipts"
          kind="receipts"
          :tripId="trip.id"
          :bookingTitle="bookingTitle"
          :expenseDesc="expenseDesc"
          :highlightId="highlightId"
          @remove="remove"
        />
      </template>
    </template>
  </div>
</template>
