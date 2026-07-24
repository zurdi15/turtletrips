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
import type { ItineraryItem, Trip } from '../../api/types'
import { useItineraryStore } from '../../stores/itinerary'
import { usePlacesStore } from '../../stores/places'
import { useBookingsStore } from '../../stores/bookings'
import { parseIsoDate, toIsoDate } from '../../composables/useMoney'

const props = defineProps<{ trip: Trip }>()
const store = useItineraryStore()
const places = usePlacesStore()
const bookings = useBookingsStore()
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
}
onMounted(() => loadAll(props.trip.id))
watch(() => props.trip.id, loadAll)

// ---- Agenda ----

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
      .map((b) => ({
        id: `b-${b.id}`,
        title: `🎫 ${b.title}`,
        start: b.start_dt!,
        end: b.end_dt ?? undefined,
        editable: false,
        backgroundColor: '#94a3b8',
        borderColor: '#94a3b8',
      })),
  ],
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
        <div class="flex items-center justify-between px-4 py-2.5 bg-slate-50 border-b border-slate-100">
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
                <span
                  v-if="element.place_id && placeName(element.place_id)"
                  class="ml-2 text-xs text-emerald-600"
                >
                  <i class="pi pi-map-marker text-[10px]" /> {{ placeName(element.place_id) }}
                </span>
                <span
                  v-if="element.booking_id && bookingTitle(element.booking_id)"
                  class="ml-2 text-xs text-violet-600"
                >
                  <i class="pi pi-ticket text-[10px]" /> {{ bookingTitle(element.booking_id) }}
                </span>
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
        <p
          v-if="!lists[day]?.length && !(continuations.get(day) ?? []).length"
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
