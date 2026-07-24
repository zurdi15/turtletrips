<script setup lang="ts">
import { computed } from 'vue'
import FullCalendar from '@fullcalendar/vue3'
import dayGridPlugin from '@fullcalendar/daygrid'
import timeGridPlugin from '@fullcalendar/timegrid'
import interactionPlugin from '@fullcalendar/interaction'
import esLocale from '@fullcalendar/core/locales/es'
import type { CalendarOptions, EventDropArg } from '@fullcalendar/core'
import type { Booking, ItineraryItem, Trip } from '../../api/types'
import { BOOKING_TYPE_ICONS, isTransport } from '../../constants'
import { useItineraryStore } from '../../stores/itinerary'
import { parseIsoDate, toIsoDate } from '../../composables/useMoney'
import { rangeNights, transportLabel } from '../../utils/itinerary'

const props = defineProps<{ trip: Trip; bookings: Booking[] }>()
const emit = defineEmits<{ edit: [item: ItineraryItem] }>()

const store = useItineraryStore()

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
    ...props.bookings
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
        const transport = isTransport(b.type)
        const color = b.type === 'hotel' ? '#7c3aed' : transport ? '#0284c7' : '#94a3b8'
        return {
          id: `b-${b.id}`,
          title: transport ? transportLabel({ b, arrival: false }) : b.title,
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
    if (item) emit('edit', item)
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
  <FullCalendar :options="calendarOptions" />
</template>
