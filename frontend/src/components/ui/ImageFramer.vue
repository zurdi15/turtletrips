<script setup lang="ts">
// Primitiva TONTA: la imagen dentro de su marco real, arrastrable para elegir
// qué parte se ve. No guarda nada — emite el encuadre y ya decide el
// consumidor cuándo persistirlo.
import { computed, onMounted, ref, watch } from 'vue'
import {
  canFrame,
  clamp01,
  coverOverflow,
  dragFocus,
  focusStyle,
  type Focus,
  type Size,
} from '../../utils/imageFocus'

const props = withDefaults(
  defineProps<{
    src: string
    /** proporción del marco, tal cual va en CSS (`16 / 9`, `1 / 1`…) */
    aspect?: string
    /** recorte redondo (avatares): solo cambia la máscara, no la mecánica */
    circle?: boolean
    /** texto de ayuda bajo el marco; sin él no se pinta nada */
    hint?: string
    disabled?: boolean
  }>(),
  { aspect: '16 / 9', circle: false, hint: '', disabled: false },
)

const focus = defineModel<Focus>({ required: true })

const frameEl = ref<HTMLElement | null>(null)
const imgEl = ref<HTMLImageElement | null>(null)
const natural = ref<Size>({ width: 0, height: 0 })
const frame = ref<Size>({ width: 0, height: 0 })
const dragging = ref(false)

const overflow = computed(() => coverOverflow(natural.value, frame.value))
// una imagen con la misma proporción que el marco no tiene nada que encuadrar:
// mejor decirlo que dejar al usuario arrastrando algo que no se mueve
const movable = computed(() => !props.disabled && canFrame(overflow.value))

const position = computed(() => focusStyle(focus.value.x, focus.value.y))

function measure() {
  const img = imgEl.value
  if (img) natural.value = { width: img.naturalWidth, height: img.naturalHeight }
  const box = frameEl.value?.getBoundingClientRect()
  if (box) frame.value = { width: box.width, height: box.height }
}

// imagen nueva en el mismo marco: hay que volver a medir (la anterior podía ser
// panorámica y la nueva un retrato)
watch(() => props.src, measure)

onMounted(() => {
  // servida de caché: el `load` pudo dispararse antes de montarse el listener
  if (imgEl.value?.complete && imgEl.value.naturalWidth > 0) measure()
})

let last: { x: number; y: number } | null = null

function onPointerDown(event: PointerEvent) {
  // medir ANTES de decidir: con la imagen servida de caché el `load` puede
  // haberse disparado antes de que este componente lo escuchase, y sin medidas
  // `movable` sale false y el arrastre no llegaría a empezar nunca
  measure()
  if (!movable.value) return
  last = { x: event.clientX, y: event.clientY }
  dragging.value = true
  // el puntero se captura para que el arrastre siga aunque te salgas del marco
  ;(event.currentTarget as HTMLElement).setPointerCapture(event.pointerId)
  event.preventDefault()
}

function onPointerMove(event: PointerEvent) {
  if (!dragging.value || !last) return
  const dx = event.clientX - last.x
  const dy = event.clientY - last.y
  last = { x: event.clientX, y: event.clientY }
  focus.value = dragFocus(focus.value, dx, dy, overflow.value)
}

function onPointerUp(event: PointerEvent) {
  if (!dragging.value) return
  dragging.value = false
  last = null
  ;(event.currentTarget as HTMLElement).releasePointerCapture?.(event.pointerId)
}

// teclado: sin esto el encuadre sería inaccesible sin ratón. Un paso del 2%
// cubre el recorrido en medio centenar de pulsaciones y afina lo suficiente
const STEP = 0.02
function onKeydown(event: KeyboardEvent) {
  if (!movable.value) return
  const dx = event.key === 'ArrowLeft' ? -1 : event.key === 'ArrowRight' ? 1 : 0
  const dy = event.key === 'ArrowUp' ? -1 : event.key === 'ArrowDown' ? 1 : 0
  if (!dx && !dy) return
  event.preventDefault()
  focus.value = {
    x: overflow.value.width > 0 ? clamp01(focus.value.x + dx * STEP) : focus.value.x,
    y: overflow.value.height > 0 ? clamp01(focus.value.y + dy * STEP) : focus.value.y,
  }
}
</script>

<template>
  <div class="flex flex-col gap-1">
    <div
      ref="frameEl"
      class="relative overflow-hidden border border-line select-none"
      :class="[
        circle ? 'rounded-full' : 'rounded-card',
        movable ? (dragging ? 'cursor-grabbing' : 'cursor-grab') : 'cursor-default',
      ]"
      :style="{ aspectRatio: aspect, touchAction: movable ? 'none' : undefined }"
      :tabindex="movable ? 0 : undefined"
      role="application"
      :aria-label="hint || undefined"
      @pointerdown="onPointerDown"
      @pointermove="onPointerMove"
      @pointerup="onPointerUp"
      @pointercancel="onPointerUp"
      @keydown="onKeydown"
    >
      <img
        ref="imgEl"
        :src="src"
        alt=""
        draggable="false"
        class="w-full h-full object-cover"
        :style="{ objectPosition: position }"
        @load="measure"
      />
      <!-- retícula de encuadre, solo mientras arrastras: fuera del arrastre
           ensuciaría la vista previa -->
      <div
        v-if="dragging"
        class="absolute inset-0 pointer-events-none grid grid-cols-3 grid-rows-3"
        aria-hidden="true"
      >
        <span
          v-for="i in 9"
          :key="i"
          class="border border-white/40"
        />
      </div>
    </div>
    <span v-if="hint && movable" class="text-xs text-ink-faint">{{ hint }}</span>
  </div>
</template>
