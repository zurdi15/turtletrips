<script setup lang="ts">
import { computed, onBeforeUnmount, onMounted, ref } from 'vue'
import { useI18n } from 'vue-i18n'
import DatePicker from 'primevue/datepicker'
import Popover from 'primevue/popover'
import Button from 'primevue/button'
import { intlLocale } from '../i18n'
import { parseIsoDate } from '../composables/useMoney'
import { spanClasses, tripSpanClass, type CalendarDay } from '../utils/tripCalendar'

const props = defineProps<{
  startLabel?: string
  endLabel?: string
  clearable?: boolean
  /** fechas del viaje: se pintan como franja de fondo para situar la selección */
  tripStart?: string | null
  tripEnd?: string | null
}>()

const { t } = useI18n()
const startText = computed(() => props.startLabel ?? t('common.dateRange.start'))
const endText = computed(() => props.endLabel ?? t('common.dateRange.end'))

const start = defineModel<Date | null>('start', { default: null })
const end = defineModel<Date | null>('end', { default: null })

const op = ref<InstanceType<typeof Popover> | null>(null)
const wrapEl = ref<HTMLElement | null>(null)
const active = ref<'start' | 'end'>('start')
const open = ref(false)
const hoverKey = ref<number | null>(null)

// el calendario solo refleja el inicio para abrirse en su mes; la selección la
// gestionamos aquí. Sin fecha elegida se abre en el mes del VIAJE: si no,
// aterrizas en el mes actual y la franja del viaje no se ve por ningún lado
// (la selección interna del DatePicker va neutralizada por CSS, así que ese
// día no aparece marcado)
const calModel = computed({
  get: () => start.value ?? (props.tripStart ? parseIsoDate(props.tripStart) : null),
  set: () => {},
})

// dos meses a lo Skyscanner en escritorio, uno en móvil
const months = ref(typeof window !== 'undefined' && window.innerWidth >= 640 ? 2 : 1)
function onResize() {
  months.value = window.innerWidth >= 640 ? 2 : 1
}
onMounted(() => window.addEventListener('resize', onResize))
onBeforeUnmount(() => window.removeEventListener('resize', onResize))

function keyOf(d: Date): number {
  return d.getFullYear() * 10000 + d.getMonth() * 100 + d.getDate()
}
const startKey = computed(() => (start.value ? keyOf(start.value) : null))
const endKey = computed(() => (end.value ? keyOf(end.value) : null))

function fmt(d: Date): string {
  return d.toLocaleDateString(intlLocale())
}

function openFor(which: 'start' | 'end', event: Event) {
  active.value = which
  op.value?.show(event, wrapEl.value ?? undefined)
}

function close() {
  op.value?.hide()
}

function onPick(d: Date) {
  if (active.value === 'start') {
    start.value = d
    if (end.value && keyOf(end.value) < keyOf(d)) end.value = null
    if (end.value) close()
    else active.value = 'end'
  } else if (start.value && keyOf(d) < keyOf(start.value)) {
    // como Skyscanner: una fecha anterior al inicio reinicia el rango desde ahí
    start.value = d
    end.value = null
  } else {
    end.value = d
    if (start.value) close()
    else active.value = 'start'
  }
}

function clearStart() {
  start.value = null
  if (open.value) active.value = 'start'
}
function clearEnd() {
  end.value = null
  if (open.value) active.value = 'end'
}

// El lapso elegido se rellena como ÁREA, con la misma geometría que la franja
// del viaje (`spanClasses`): así encaja dentro de ella en vez de ser una tira
// de días sueltos, y las semanas se funden igual. Mientras falta un extremo, el
// hover rellena esa misma área a modo de previsualización. Los extremos van
// encima, en verde sólido.
function dayClass(meta: CalendarDay): string {
  if (meta.otherMonth) return ''
  const k = meta.year * 10000 + meta.month * 100 + meta.day
  let s = startKey.value
  let e = endKey.value
  let preview: 'start' | 'end' | null = null
  if (e == null && active.value === 'end' && s != null && hoverKey.value != null && hoverKey.value > s) {
    e = hoverKey.value
    preview = 'end'
  } else if (s == null && active.value === 'start' && e != null && hoverKey.value != null && hoverKey.value < e) {
    s = hoverKey.value
    preview = 'start'
  } else if (s == null && e == null && hoverKey.value != null) {
    // sin nada elegido todavía, el día bajo el ratón se previsualiza igual que
    // el segundo extremo: sin esto el calendario no responde al ratón
    s = hoverKey.value
    e = hoverKey.value
    preview = active.value
  }
  const classes: string[] = []
  // debajo de todo, la duración del viaje: el relleno de la selección va encima
  const trip = tripSpanClass(meta, props.tripStart, props.tripEnd)
  if (trip) classes.push(trip)
  // con un solo extremo, el área es de UN día: sin esto el tope se quedaría sin
  // forma (un bloque cuadrado) hasta elegir el segundo
  const selection = spanClasses(meta, s ?? e, e ?? s, 'tt-sel-day')
  if (selection) classes.push(selection)
  if (k === startKey.value) classes.push('tt-range-start')
  else if (k === endKey.value) classes.push('tt-range-end')
  else if (preview && (k === s || k === e)) classes.push('tt-range-preview')
  return classes.join(' ')
}

function onDayHover(meta: CalendarDay) {
  if (meta.otherMonth) return
  hoverKey.value = meta.year * 10000 + meta.month * 100 + meta.day
}
</script>

<template>
  <div ref="wrapEl" class="grid grid-cols-2 gap-2">
    <button
      type="button"
      class="flex items-center gap-2 px-3 py-1.5 rounded-lg border bg-surface w-full text-left transition-colors focus:outline-none border-line hover:border-line-strong"
      :class="{ '!border-emerald-500 ring-1 !ring-emerald-500': open && active === 'start' }"
      @click="openFor('start', $event)"
    >
      <span class="flex-1 min-w-0">
        <span class="block text-xs text-ink-faint">{{ startText }}</span>
        <span class="block text-sm truncate" :class="start ? 'text-ink' : 'text-ink-faint'">
          {{ start ? fmt(start) : $t('common.dateRange.pickDate') }}
        </span>
      </span>
      <i
        v-if="start && clearable"
        class="pi pi-times-circle text-ink-faint hover:text-ink-secondary shrink-0"
        @click.stop="clearStart"
      />
      <i v-else class="pi pi-calendar text-ink-faint shrink-0" />
    </button>
    <button
      type="button"
      class="flex items-center gap-2 px-3 py-1.5 rounded-lg border bg-surface w-full text-left transition-colors focus:outline-none border-line hover:border-line-strong"
      :class="{ '!border-emerald-500 ring-1 !ring-emerald-500': open && active === 'end' }"
      @click="openFor('end', $event)"
    >
      <span class="flex-1 min-w-0">
        <span class="block text-xs text-ink-faint">{{ endText }}</span>
        <span class="block text-sm truncate" :class="end ? 'text-ink' : 'text-ink-faint'">
          {{ end ? fmt(end) : $t('common.dateRange.pickDate') }}
        </span>
      </span>
      <i
        v-if="end"
        class="pi pi-times-circle text-ink-faint hover:text-ink-secondary shrink-0"
        @click.stop="clearEnd"
      />
      <i v-else class="pi pi-calendar text-ink-faint shrink-0" />
    </button>

    <Popover ref="op" @show="open = true" @hide="((open = false), (hoverKey = null))">
      <div class="tt-range-panel" @mouseleave="hoverKey = null">
        <DatePicker
          v-model="calModel"
          inline
          selectionMode="single"
          :numberOfMonths="months"
          @date-select="onPick"
        >
          <template #date="{ date }">
            <span class="tt-day-inner" :class="dayClass(date)" @mouseenter="onDayHover(date)">
              {{ date.day }}
            </span>
          </template>
        </DatePicker>
        <div class="flex items-center justify-between gap-2 pt-1">
          <span class="text-xs text-ink-faint">
            {{ active === 'start' ? $t('common.dateRange.pickStart') : $t('common.dateRange.pickEnd') }}
          </span>
          <Button :label="$t('common.actions.apply')" size="small" @click="close" />
        </div>
      </div>
    </Popover>
  </div>
</template>
