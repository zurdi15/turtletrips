<script setup lang="ts">
import { computed, onMounted, reactive, ref, watch } from 'vue'
import Button from 'primevue/button'
import SelectButton from 'primevue/selectbutton'
import { useConfirm } from 'primevue/useconfirm'
import draggable from 'vuedraggable'
import FullCalendar from '@fullcalendar/vue3'
import dayGridPlugin from '@fullcalendar/daygrid'
import timeGridPlugin from '@fullcalendar/timegrid'
import interactionPlugin from '@fullcalendar/interaction'
import esLocale from '@fullcalendar/core/locales/es'
import type { CalendarOptions, EventDropArg } from '@fullcalendar/core'
import ItineraryFormDialog from '../../components/ItineraryFormDialog.vue'
import EmptyState from '../../components/EmptyState.vue'
import TabSkeleton from '../../components/TabSkeleton.vue'
import { API_BASE } from '../../api/client'
import type { Booking, BookingType, ItineraryItem, Trip } from '../../api/types'
import { BOOKING_TYPE_ICONS, BOOKING_TYPE_LABELS } from '../../constants'
import { useItineraryStore } from '../../stores/itinerary'
import { usePlacesStore } from '../../stores/places'
import { useBookingsStore } from '../../stores/bookings'
import { useExpensesStore } from '../../stores/expenses'
import { parseIsoDate, toIsoDate } from '../../composables/useMoney'

const props = defineProps<{ trip: Trip }>()
const store = useItineraryStore()
const places = usePlacesStore()
const bookings = useBookingsStore()
const expenses = useExpensesStore()
const confirm = useConfirm()

const view = ref<'agenda' | 'calendar'>('agenda')
const viewOptions = [
  { value: 'agenda', label: 'Agenda', icon: 'pi pi-list' },
  { value: 'calendar', label: 'Calendario', icon: 'pi pi-calendar' },
]

const showForm = ref(false)
const editing = ref<ItineraryItem | null>(null)
const presetDay = ref<string | null>(null)

const icsUrl = computed(() => `${API_BASE}/trips/${props.trip.id}/calendar.ics`)

function loadAll(tripId: number) {
  store.load(tripId)
  places.load(tripId)
  bookings.load(tripId)
  expenses.load(tripId)
}
onMounted(() => loadAll(props.trip.id))
watch(() => props.trip.id, loadAll)

// ---- Agenda ----

// reservas con hueco propio en la agenda: transportes el día de salida y
// alojamiento en cada noche (check-in → noche anterior al check-out)
const TRANSPORT_TYPES: BookingType[] = ['flight', 'train', 'bus', 'ferry']

// gasto generado por cada reserva (enlace directo con highlight)
const expenseByBooking = computed(() => {
  const map = new Map<number, number>()
  for (const e of expenses.items) if (e.booking_id != null) map.set(e.booking_id, e.id)
  return map
})


// salida el día de inicio y, si llega en OTRO día (vuelo nocturno), también
// una entrada de "Llegada" en el día de destino
interface TransportEntry {
  b: Booking
  arrival: boolean
}
function transportDt(e: TransportEntry): string {
  return e.arrival ? e.b.end_dt! : e.b.start_dt!
}

const transportsByDay = computed(() => {
  const map = new Map<string, TransportEntry[]>()
  const add = (day: string, e: TransportEntry) => map.set(day, [...(map.get(day) ?? []), e])
  for (const b of bookings.items) {
    if (!TRANSPORT_TYPES.includes(b.type) || !b.start_dt) continue
    add(b.start_dt.slice(0, 10), { b, arrival: false })
    if (b.end_dt && b.end_dt.slice(0, 10) > b.start_dt.slice(0, 10)) {
      add(b.end_dt.slice(0, 10), { b, arrival: true })
    }
  }
  for (const list of map.values()) {
    list.sort((a, b) => transportDt(a).localeCompare(transportDt(b)))
  }
  return map
})

// resto de reservas con fecha (actividades, coche, otros): aparecen en su día
const otherBookingsByDay = computed(() => {
  const map = new Map<string, Booking[]>()
  for (const b of bookings.items) {
    if (b.type === 'hotel' || TRANSPORT_TYPES.includes(b.type) || !b.start_dt) continue
    const day = b.start_dt.slice(0, 10)
    map.set(day, [...(map.get(day) ?? []), b])
  }
  for (const list of map.values()) {
    list.sort((a, b) => a.start_dt!.localeCompare(b.start_dt!))
  }
  return map
})

// noches del check-in a la víspera del check-out, más el día del check-out
const lodgingByDay = computed(() => {
  const map = new Map<string, Booking[]>()
  const add = (day: string, b: Booking) => map.set(day, [...(map.get(day) ?? []), b])
  for (const b of bookings.items) {
    if (b.type !== 'hotel' || !b.start_dt) continue
    const checkin = b.start_dt.slice(0, 10)
    const checkout = b.end_dt ? b.end_dt.slice(0, 10) : null
    if (!checkout || checkout <= checkin) {
      add(checkin, b)
      continue
    }
    const cursor = parseIsoDate(checkin)
    while (toIsoDate(cursor) <= checkout) {
      add(toIsoDate(cursor), b)
      cursor.setDate(cursor.getDate() + 1)
    }
  }
  return map
})

type LodgingKind = 'checkin' | 'noche' | 'checkout'
function lodgingKind(b: Booking, day: string): LodgingKind {
  if (b.start_dt && b.start_dt.slice(0, 10) === day) return 'checkin'
  if (b.end_dt && b.end_dt.slice(0, 10) === day) return 'checkout'
  return 'noche'
}

// filas en tres columnas: hora | tipo (Vuelo/Llegada/Check-in…) | ruta o nombre
function lodgingTime(b: Booking, day: string): string {
  const kind = lodgingKind(b, day)
  if (kind === 'noche') return ''
  const dt = kind === 'checkout' ? b.end_dt! : b.start_dt!
  const t = dt.slice(11, 16)
  return t !== '00:00' ? t : ''
}

function lodgingKindLabel(b: Booking, day: string): string {
  const kind = lodgingKind(b, day)
  if (kind === 'checkin') return 'Check-in'
  if (kind === 'checkout') return 'Check-out'
  return 'noche'
}

function transportTime(e: TransportEntry): string {
  const t = transportDt(e).slice(11, 16)
  return t !== '00:00' ? t : ''
}

function transportKind(e: TransportEntry): string {
  return e.arrival ? 'Llegada' : BOOKING_TYPE_LABELS[e.b.type]
}

function transportLabel(e: TransportEntry): string {
  const b = e.b
  return b.origin || b.destination ? `${b.origin ?? '?'} → ${b.destination ?? '?'}` : b.title
}

function bookingTime(b: Booking): string {
  const t = b.start_dt ? b.start_dt.slice(11, 16) : ''
  return t && t !== '00:00' ? t : ''
}

// cabecera de columna izquierda: "Check-in: 15:00", "Vuelo: 07:30", "noche"…
function transportHead(e: TransportEntry): string {
  const t = transportTime(e)
  return t ? `${transportKind(e)}: ${t}` : transportKind(e)
}

function lodgingHead(b: Booking, day: string): string {
  const kind = lodgingKindLabel(b, day)
  const t = lodgingTime(b, day)
  return t ? `${kind}: ${t}` : kind
}

function bookingHead(b: Booking): string {
  const t = bookingTime(b)
  return t ? `${BOOKING_TYPE_LABELS[b.type]}: ${t}` : BOOKING_TYPE_LABELS[b.type]
}

const days = computed<string[]>(() => {
  const set = new Set<string>()
  const addRange = (from: string, to: string) => {
    const cursor = parseIsoDate(from)
    const end = parseIsoDate(to)
    while (cursor <= end) {
      set.add(toIsoDate(cursor))
      cursor.setDate(cursor.getDate() + 1)
    }
  }
  if (props.trip.start_date && props.trip.end_date) {
    addRange(props.trip.start_date, props.trip.end_date)
  }
  for (const item of store.items) {
    if (item.end_day && item.end_day > item.day) addRange(item.day, item.end_day)
    else set.add(item.day)
  }
  for (const day of transportsByDay.value.keys()) set.add(day)
  for (const day of lodgingByDay.value.keys()) set.add(day)
  for (const day of otherBookingsByDay.value.keys()) set.add(day)
  return [...set].sort()
})

// items de varios días que "continúan" en un día dado (no arrastrables)
const continuations = computed(() => {
  const map = new Map<string, ItineraryItem[]>()
  for (const item of store.items) {
    if (!item.end_day || item.end_day <= item.day) continue
    const cursor = parseIsoDate(item.day)
    cursor.setDate(cursor.getDate() + 1)
    const end = parseIsoDate(item.end_day)
    while (cursor <= end) {
      const key = toIsoDate(cursor)
      map.set(key, [...(map.get(key) ?? []), item])
      cursor.setDate(cursor.getDate() + 1)
    }
  }
  return map
})

function rangeNights(item: ItineraryItem): number {
  if (!item.end_day) return 0
  return Math.round(
    (parseIsoDate(item.end_day).getTime() - parseIsoDate(item.day).getTime()) / 86400000,
  )
}

const lists = reactive<Record<string, ItineraryItem[]>>({})

watch(
  [() => store.items, days],
  () => {
    for (const key of Object.keys(lists)) delete lists[key]
    for (const day of days.value) {
      lists[day] = (store.byDay.get(day) ?? []).slice()
    }
  },
  { immediate: true, deep: true },
)

function persistOrder() {
  const entries: { id: number; day: string; order_index: number }[] = []
  for (const [day, items] of Object.entries(lists)) {
    items.forEach((item, idx) => entries.push({ id: item.id, day, order_index: idx }))
  }
  store.reorder(entries)
}

function dayLabel(iso: string): { title: string; sub: string } {
  const d = parseIsoDate(iso)
  const sub = d.toLocaleDateString('es-ES', { weekday: 'long', day: 'numeric', month: 'long' })
  if (props.trip.start_date) {
    const diff =
      Math.round((d.getTime() - parseIsoDate(props.trip.start_date).getTime()) / 86400000) + 1
    if (diff >= 1) return { title: `Día ${diff}`, sub }
  }
  return { title: sub, sub: '' }
}

function fmtTime(t: string | null): string {
  return t ? t.slice(0, 5) : ''
}

function fmtDayShort(iso: string): string {
  return parseIsoDate(iso).toLocaleDateString('es-ES', { day: 'numeric', month: 'short' })
}

function placeName(id: number | null): string | null {
  return id == null ? null : (places.items.find((p) => p.id === id)?.name ?? null)
}
function bookingTitle(id: number | null): string | null {
  return id == null ? null : (bookings.items.find((b) => b.id === id)?.title ?? null)
}

function openNew(day?: string) {
  editing.value = null
  presetDay.value = day ?? null
  showForm.value = true
}
function openEdit(item: ItineraryItem) {
  editing.value = item
  showForm.value = true
}
function removeItem(item: ItineraryItem) {
  confirm.require({
    message: `¿Eliminar "${item.title}" del itinerario?`,
    header: 'Eliminar actividad',
    icon: 'pi pi-exclamation-triangle',
    rejectProps: { label: 'Cancelar', severity: 'secondary', outlined: true },
    acceptProps: { label: 'Eliminar', severity: 'danger' },
    accept: () => store.remove(item.id),
  })
}

// ---- Calendario ----

const calendarOptions = computed<CalendarOptions>(() => ({
  plugins: [dayGridPlugin, timeGridPlugin, interactionPlugin],
  initialView: 'dayGridMonth',
  initialDate: props.trip.start_date ?? undefined,
  locale: esLocale,
  firstDay: 1,
  headerToolbar: { left: 'prev,next today', center: 'title', right: 'dayGridMonth,timeGridWeek' },
  height: 'auto',
  editable: true,
  events: [
    ...store.items.map((item) => {
      // items de varios días: evento all-day con fin exclusivo (día siguiente al último)
      if (item.end_day && item.end_day > item.day) {
        const endExclusive = parseIsoDate(item.end_day)
        endExclusive.setDate(endExclusive.getDate() + 1)
        return {
          id: `i-${item.id}`,
          title: item.title,
          start: item.day,
          end: toIsoDate(endExclusive),
          allDay: true,
          backgroundColor: '#0f766e',
          borderColor: '#0f766e',
        }
      }
      return {
        id: `i-${item.id}`,
        title: item.title,
        start: item.start_time ? `${item.day}T${item.start_time}` : item.day,
        end: item.start_time && item.end_time ? `${item.day}T${item.end_time}` : undefined,
        allDay: !item.start_time,
        backgroundColor: 'var(--p-primary-color)',
        borderColor: 'var(--p-primary-color)',
      }
    }),
    ...bookings.items
      .filter((b) => b.start_dt)
      .map((b) => {
        // hoteles: banda all-day del check-in al check-out
        if (b.type === 'hotel' && b.end_dt && b.end_dt.slice(0, 10) > b.start_dt!.slice(0, 10)) {
          const endExclusive = parseIsoDate(b.end_dt.slice(0, 10))
          endExclusive.setDate(endExclusive.getDate() + 1)
          return {
            id: `b-${b.id}`,
            title: b.title,
            start: b.start_dt!.slice(0, 10),
            end: toIsoDate(endExclusive),
            allDay: true,
            editable: false,
            backgroundColor: '#7c3aed',
            borderColor: '#7c3aed',
            extendedProps: { icon: BOOKING_TYPE_ICONS[b.type] },
          }
        }
        const isTransport = TRANSPORT_TYPES.includes(b.type)
        const color = b.type === 'hotel' ? '#7c3aed' : isTransport ? '#0284c7' : '#94a3b8'
        return {
          id: `b-${b.id}`,
          title: isTransport ? transportLabel({ b, arrival: false }) : b.title,
          start: b.start_dt!,
          end: b.end_dt ?? undefined,
          editable: false,
          backgroundColor: color,
          borderColor: color,
          extendedProps: { icon: BOOKING_TYPE_ICONS[b.type] },
        }
      }),
  ],
  // icono (mdi/pi) delante del título — los eventos de reservas lo declaran
  // en extendedProps.icon; los de itinerario se renderizan igual pero sin él
  eventContent: (arg) => {
    const icon = arg.event.extendedProps.icon as string | undefined
    const wrap = document.createElement('div')
    wrap.className = 'flex items-center gap-1 overflow-hidden px-0.5'
    if (icon) {
      const i = document.createElement('i')
      i.className = `${icon} text-[11px] shrink-0`
      wrap.append(i)
    }
    const text = document.createElement('span')
    text.className = 'truncate'
    text.textContent = arg.timeText ? `${arg.timeText} ${arg.event.title}` : arg.event.title
    wrap.append(text)
    return { domNodes: [wrap] }
  },
  eventDrop: onEventDrop,
  eventClick: (info) => {
    if (!info.event.id.startsWith('i-')) return
    const item = store.items.find((i) => i.id === Number(info.event.id.slice(2)))
    if (item) openEdit(item)
  },
}))

function onEventDrop(info: EventDropArg) {
  if (!info.event.id.startsWith('i-') || !info.event.start) {
    info.revert()
    return
  }
  const id = Number(info.event.id.slice(2))
  const item = store.items.find((i) => i.id === id)
  const start = info.event.start
  const newDay = toIsoDate(start)
  const payload: { day: string; end_day?: string | null; start_time?: string | null } = {
    day: newDay,
  }
  // desplazar también el fin del rango manteniendo la duración
  if (item?.end_day && item.end_day > item.day) {
    const shifted = parseIsoDate(newDay)
    shifted.setDate(shifted.getDate() + rangeNights(item))
    payload.end_day = toIsoDate(shifted)
  }
  if (!info.event.allDay) {
    payload.start_time = `${String(start.getHours()).padStart(2, '0')}:${String(
      start.getMinutes(),
    ).padStart(2, '0')}:00`
  }
  store.update(id, payload).catch(() => info.revert())
}
</script>

<template>
  <div>
    <div class="flex flex-wrap items-center gap-2 mb-4">
      <Button label="Nueva actividad" icon="pi pi-plus" @click="openNew()" />
      <a :href="icsUrl" download>
        <Button
          label="Exportar"
          icon="pi pi-calendar-plus"
          severity="secondary"
          outlined
          v-tooltip.bottom="'Descargar calendario (.ics)'"
          class="max-sm:[&_.p-button-label]:hidden"
        />
      </a>
      <span class="flex-1" />
      <SelectButton
        v-model="view"
        :options="viewOptions"
        optionLabel="label"
        optionValue="value"
        :allowEmpty="false"
      />
    </div>

    <TabSkeleton
      v-if="store.loading && !store.items.length && !days.length"
      variant="cards"
      :rows="3"
    />

    <EmptyState
      v-else-if="!store.loading && !store.items.length && !days.length"
      icon="pi pi-calendar"
      title="Sin itinerario"
      subtitle="Define las fechas del viaje o añade una actividad para empezar"
    >
      <Button label="Nueva actividad" icon="pi pi-plus" @click="openNew()" />
    </EmptyState>

    <div v-else-if="view === 'agenda'" class="tt-stagger flex flex-col gap-4">
      <div
        v-for="day in days"
        :key="day"
        class="bg-white rounded-xl border border-slate-200 overflow-hidden"
      >
        <div class="flex items-center justify-between px-4 py-2.5 bg-slate-100 border-b border-slate-100">
          <div class="flex items-baseline gap-2">
            <span class="font-semibold text-slate-700">{{ dayLabel(day).title }}</span>
            <span class="text-sm text-slate-400 capitalize">{{ dayLabel(day).sub }}</span>
          </div>
          <Button
            icon="pi pi-plus"
            text
            size="small"
            severity="secondary"
            v-tooltip.left="'Añadir a este día'"
            @click="openNew(day)"
          />
        </div>
        <!-- transportes del día: sección propia con cabecera -->
        <div
          v-if="(transportsByDay.get(day) ?? []).length"
          class="bg-sky-100 border-b border-slate-100 py-1.5"
        >
          <p
            class="px-4 pb-0.5 text-[11px] font-semibold uppercase tracking-wide text-sky-600 flex items-center gap-1.5"
          >
            <i class="mdi mdi-plane-train" /> Transporte
          </p>
          <div
            v-for="e in transportsByDay.get(day) ?? []"
            :key="`t-${e.b.id}-${e.arrival ? 'a' : 's'}`"
            class="flex items-center gap-3 px-4 py-1 text-sky-700"
          >
            <span class="text-xs sm:text-sm w-24 sm:w-28 shrink-0 opacity-80 truncate">
              {{ transportHead(e) }}
            </span>
            <router-link
              :to="{ name: 'trip-bookings', params: { id: trip.id }, query: { booking: e.b.id } }"
              class="font-medium text-sm truncate text-inherit no-underline hover:underline"
            >
              {{ transportLabel(e) }}
            </router-link>
            <span class="ml-auto flex items-center gap-2.5 shrink-0">
              <router-link
                v-if="e.b.place_id"
                :to="{ name: 'trip-places', params: { id: trip.id }, query: { place: e.b.place_id } }"
                class="text-emerald-600"
                v-tooltip.top="'Ver sitio'"
              >
                <i class="pi pi-map-marker text-[11px]" />
              </router-link>
              <router-link
                v-if="expenseByBooking.get(e.b.id)"
                :to="{ name: 'trip-expenses', params: { id: trip.id }, query: { expense: expenseByBooking.get(e.b.id) } }"
                class="text-amber-600"
                v-tooltip.top="'Ver gasto'"
              >
                <i class="pi pi-wallet text-[11px]" />
              </router-link>
              <router-link
                :to="{ name: 'trip-bookings', params: { id: trip.id }, query: { booking: e.b.id } }"
                class="text-inherit opacity-50 hover:opacity-100"
                v-tooltip.top="'Ver reserva'"
              >
                <i class="pi pi-ticket text-[11px]" />
              </router-link>
            </span>
          </div>
        </div>

        <!-- otras reservas del día (actividades, coche…) -->
        <div
          v-if="(otherBookingsByDay.get(day) ?? []).length"
          class="bg-amber-100 border-b border-slate-100 py-1.5"
        >
          <p
            class="px-4 pb-0.5 text-[11px] font-semibold uppercase tracking-wide text-amber-600 flex items-center gap-1.5"
          >
            <i class="mdi mdi-ticket-outline" /> Reservas
          </p>
          <div
            v-for="b in otherBookingsByDay.get(day) ?? []"
            :key="`o-${b.id}`"
            class="flex items-center gap-3 px-4 py-1 text-amber-700"
          >
            <span class="text-xs sm:text-sm w-24 sm:w-28 shrink-0 opacity-80 truncate">
              {{ bookingHead(b) }}
            </span>
            <router-link
              :to="{ name: 'trip-bookings', params: { id: trip.id }, query: { booking: b.id } }"
              class="font-medium text-sm truncate text-inherit no-underline hover:underline"
            >
              {{ b.title }}
            </router-link>
            <span class="ml-auto flex items-center gap-2.5 shrink-0">
              <router-link
                v-if="b.place_id"
                :to="{ name: 'trip-places', params: { id: trip.id }, query: { place: b.place_id } }"
                class="text-emerald-600"
                v-tooltip.top="'Ver sitio'"
              >
                <i class="pi pi-map-marker text-[11px]" />
              </router-link>
              <router-link
                v-if="expenseByBooking.get(b.id)"
                :to="{ name: 'trip-expenses', params: { id: trip.id }, query: { expense: expenseByBooking.get(b.id) } }"
                class="text-inherit"
                v-tooltip.top="'Ver gasto'"
              >
                <i class="pi pi-wallet text-[11px]" />
              </router-link>
              <router-link
                :to="{ name: 'trip-bookings', params: { id: trip.id }, query: { booking: b.id } }"
                class="text-inherit opacity-50 hover:opacity-100"
                v-tooltip.top="'Ver reserva'"
              >
                <i class="pi pi-ticket text-[11px]" />
              </router-link>
            </span>
          </div>
        </div>

        <draggable
          :list="lists[day]"
          group="itinerary"
          item-key="id"
          handle=".drag-handle"
          class="min-h-[2.5rem]"
          @end="persistOrder"
        >
          <template #item="{ element }">
            <div
              class="flex items-center gap-3 px-4 py-2.5 border-b border-slate-50 last:border-b-0 hover:bg-slate-50 group"
            >
              <i class="pi pi-bars drag-handle cursor-grab text-slate-300 group-hover:text-slate-400" />
              <span class="text-xs sm:text-sm font-mono text-slate-400 w-16 sm:w-24 shrink-0">
                <template v-if="element.start_time">
                  {{ fmtTime(element.start_time) }}<template v-if="element.end_time">–{{ fmtTime(element.end_time) }}</template>
                </template>
                <template v-else>—</template>
              </span>
              <div class="flex-1 min-w-0">
                <span class="font-medium text-slate-700">{{ element.title }}</span>
                <span
                  v-if="element.end_day && element.end_day > element.day"
                  class="ml-2 text-xs px-1.5 py-0.5 rounded bg-teal-50 text-teal-700"
                >
                  {{ rangeNights(element) + 1 }} días · hasta el {{ fmtDayShort(element.end_day) }}
                </span>
                <!-- enlaces compactos: solo icono, el detalle vive en el tooltip -->
                <router-link
                  v-if="element.place_id && placeName(element.place_id)"
                  :to="{ name: 'trip-places', params: { id: trip.id }, query: { place: element.place_id } }"
                  class="ml-2 text-emerald-600 no-underline"
                  v-tooltip.top="`Sitio: ${placeName(element.place_id)}`"
                >
                  <i class="pi pi-map-marker text-xs" />
                </router-link>
                <router-link
                  v-if="element.booking_id && bookingTitle(element.booking_id)"
                  :to="{ name: 'trip-bookings', params: { id: trip.id }, query: { booking: element.booking_id } }"
                  class="ml-2 text-violet-600 no-underline"
                  v-tooltip.top="`Reserva: ${bookingTitle(element.booking_id)}`"
                >
                  <i class="pi pi-ticket text-xs" />
                </router-link>
                <router-link
                  v-if="element.booking_id && expenseByBooking.get(element.booking_id)"
                  :to="{
                    name: 'trip-expenses',
                    params: { id: trip.id },
                    query: { expense: expenseByBooking.get(element.booking_id) },
                  }"
                  class="ml-2 text-amber-600 no-underline"
                  v-tooltip.top="'Ver gasto'"
                >
                  <i class="pi pi-wallet text-xs" />
                </router-link>
                <p v-if="element.notes" class="text-xs text-slate-400 truncate">{{ element.notes }}</p>
              </div>
              <div class="flex gap-1 hover-actions">
                <Button icon="pi pi-pencil" text size="small" severity="secondary" @click="openEdit(element)" />
                <Button icon="pi pi-trash" text size="small" severity="danger" @click="removeItem(element)" />
              </div>
            </div>
          </template>
        </draggable>
        <div
          v-for="cont in continuations.get(day) ?? []"
          :key="`cont-${cont.id}`"
          class="flex items-center gap-3 px-4 py-1.5 border-b border-slate-50 last:border-b-0 text-sm text-teal-700/70 cursor-pointer hover:bg-teal-50/50"
          @click="openEdit(cont)"
        >
          <i class="pi pi-arrow-down-right text-xs w-4 text-center" />
          <span class="w-24 shrink-0 text-xs">sigue</span>
          <span class="italic">{{ cont.title }}</span>
        </div>
        <!-- dónde se duerme esa noche: sección propia al pie del día -->
        <div
          v-if="(lodgingByDay.get(day) ?? []).length"
          class="bg-violet-100 border-t border-slate-100 py-1.5"
        >
          <p
            class="px-4 pb-0.5 text-[11px] font-semibold uppercase tracking-wide text-violet-600 flex items-center gap-1.5"
          >
            <i class="mdi mdi-bed" /> Alojamiento
          </p>
          <div
            v-for="b in lodgingByDay.get(day) ?? []"
            :key="`l-${b.id}`"
            class="flex items-center gap-3 px-4 py-1 text-violet-700"
          >
            <span class="text-xs sm:text-sm w-24 sm:w-28 shrink-0 opacity-80 truncate">
              {{ lodgingHead(b, day) }}
            </span>
            <router-link
              :to="{ name: 'trip-bookings', params: { id: trip.id }, query: { booking: b.id } }"
              class="font-medium text-sm truncate text-inherit no-underline hover:underline"
            >
              {{ b.title }}
            </router-link>
            <span class="ml-auto flex items-center gap-2.5 shrink-0">
              <router-link
                v-if="b.place_id"
                :to="{ name: 'trip-places', params: { id: trip.id }, query: { place: b.place_id } }"
                class="text-emerald-600"
                v-tooltip.top="'Ver sitio'"
              >
                <i class="pi pi-map-marker text-[11px]" />
              </router-link>
              <router-link
                v-if="expenseByBooking.get(b.id)"
                :to="{ name: 'trip-expenses', params: { id: trip.id }, query: { expense: expenseByBooking.get(b.id) } }"
                class="text-amber-600"
                v-tooltip.top="'Ver gasto'"
              >
                <i class="pi pi-wallet text-[11px]" />
              </router-link>
              <router-link
                :to="{ name: 'trip-bookings', params: { id: trip.id }, query: { booking: b.id } }"
                class="text-inherit opacity-50 hover:opacity-100"
                v-tooltip.top="'Ver reserva'"
              >
                <i class="pi pi-ticket text-[11px]" />
              </router-link>
            </span>
          </div>
        </div>
        <p
          v-if="
            !lists[day]?.length &&
            !(continuations.get(day) ?? []).length &&
            !(transportsByDay.get(day) ?? []).length &&
            !(otherBookingsByDay.get(day) ?? []).length &&
            !(lodgingByDay.get(day) ?? []).length
          "
          class="px-4 pb-3 pt-1 text-xs text-slate-300"
        >
          Sin actividades
        </p>
      </div>
    </div>

    <div v-else class="bg-white rounded-xl border border-slate-200 p-4">
      <FullCalendar :options="calendarOptions" />
    </div>

    <ItineraryFormDialog v-model:visible="showForm" :item="editing" :presetDay="presetDay" />
  </div>
</template>
