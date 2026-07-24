<script setup lang="ts">
import { computed, onBeforeUnmount, onMounted, ref } from 'vue'
import DatePicker from 'primevue/datepicker'
import Popover from 'primevue/popover'
import Button from 'primevue/button'

interface DayMeta {
  day: number
  month: number
  year: number
  otherMonth?: boolean
}

withDefaults(defineProps<{ startLabel?: string; endLabel?: string; clearable?: boolean }>(), {
  startLabel: 'Inicio',
  endLabel: 'Fin',
})

const start = defineModel<Date | null>('start', { default: null })
const end = defineModel<Date | null>('end', { default: null })

const op = ref<InstanceType<typeof Popover> | null>(null)
const wrapEl = ref<HTMLElement | null>(null)
const active = ref<'start' | 'end'>('start')
const open = ref(false)
const hoverKey = ref<number | null>(null)

// el calendario solo refleja el inicio para abrirse en su mes; la selección la gestionamos aquí
const calModel = computed({
  get: () => start.value,
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
  return d.toLocaleDateString('es-ES')
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

// extremos en verde sólido, interior en verde claro; mientras falta un extremo,
// el hover previsualiza el lapso
function dayClass(meta: DayMeta): string {
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
  }
  if (k === startKey.value) return 'tt-range-start'
  if (k === endKey.value) return 'tt-range-end'
  if ((k === s || k === e) && preview) return 'tt-range-preview'
  if (s != null && e != null && k > s && k < e) return 'tt-in-range'
  return ''
}

function onDayHover(meta: DayMeta) {
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
        <span class="block text-xs text-ink-faint">{{ startLabel }}</span>
        <span class="block text-sm truncate" :class="start ? 'text-ink' : 'text-ink-faint'">
          {{ start ? fmt(start) : 'Elegir fecha' }}
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
        <span class="block text-xs text-ink-faint">{{ endLabel }}</span>
        <span class="block text-sm truncate" :class="end ? 'text-ink' : 'text-ink-faint'">
          {{ end ? fmt(end) : 'Elegir fecha' }}
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
            {{ active === 'start' ? 'Elige la fecha de inicio' : 'Elige la fecha de fin' }}
          </span>
          <Button label="Aplicar" size="small" @click="close" />
        </div>
      </div>
    </Popover>
  </div>
</template>
