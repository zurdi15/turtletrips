<script setup lang="ts">
// Primitiva TONTA: la postal ampliada, con el vuelo FLIP desde la miniatura que
// la abre. Crece desde el sitio exacto donde estaba (respetando su rotación) y
// vuelve encogiéndose al cerrar; clic fuera o Esc la cierran.
//
// El origen del vuelo lo pasa quien la abre (`openFrom`), así que la misma
// pieza sirve para una miniatura, un marco de encuadre o una ficha del mapa. El
// marco de papel blanco es a propósito: es una postal, y el blanco no sigue al
// tema oscuro.
import { nextTick, onBeforeUnmount, ref } from 'vue'

withDefaults(defineProps<{ src: string | null; alt?: string }>(), { alt: '' })

const open = ref(false)
const closing = ref(false)
// true cuando el clon está listo para pintarse: hasta entonces el overlay va
// invisible y la miniatura sigue en su sitio; el intercambio es atómico
const ready = ref(false)
// el clon conserva el aspecto EXACTO de la miniatura: así la escala del vuelo
// es uniforme (sin deformar la imagen), que es lo que lo hace fluido
const size = ref<{ width: string; height: string } | null>(null)

const backdropEl = ref<HTMLElement | null>(null)
const cardEl = ref<HTMLElement | null>(null)
const imgEl = ref<HTMLImageElement | null>(null)
let source: HTMLElement | null = null

const reducedMotion = () => window.matchMedia('(prefers-reduced-motion: reduce)').matches

/** duración (ms) de un token de motion --tt-dur-* para las animaciones WAAPI */
function durToken(name: string, fallback: number): number {
  const v = parseFloat(getComputedStyle(document.documentElement).getPropertyValue(name))
  return Number.isFinite(v) && v > 0 ? v : fallback
}

/** rotación del origen (la postal del diario va ladeada con rotate-1) */
function sourceAngle(el: HTMLElement): number {
  const t = getComputedStyle(el).transform
  if (!t || t === 'none') return 0
  const m = new DOMMatrixReadOnly(t)
  return Math.atan2(m.b, m.a) * (180 / Math.PI)
}

/** transform que superpone el clon ampliado sobre su origen */
function toSourceTransform(card: HTMLElement, from: HTMLElement): string {
  const a = from.getBoundingClientRect()
  const b = card.getBoundingClientRect()
  const dx = a.left + a.width / 2 - (b.left + b.width / 2)
  const dy = a.top + a.height / 2 - (b.top + b.height / 2)
  return `translate(${dx}px, ${dy}px) rotate(${sourceAngle(from)}deg) scale(${a.width / b.width})`
}

/**
 * Abre la postal volando desde `el`. Se le pasa el CONTENEDOR de la imagen (el
 * botón de la miniatura, el marco de encuadre, la ficha…): de ahí se sacan las
 * medidas del vuelo y él es quien se esconde mientras dura el zoom.
 */
async function openFrom(el: HTMLElement | null) {
  if (open.value || !el) return
  source = el
  // tamaño destino: la miniatura escalada (aspecto idéntico) hasta 85vw/80vh
  const thumb = source.querySelector('img')?.getBoundingClientRect()
  if (!thumb) return
  const k = Math.min(
    Math.min(window.innerWidth * 0.85, 896) / thumb.width,
    (window.innerHeight * 0.8) / thumb.height,
  )
  size.value = {
    width: `${Math.round(thumb.width * k)}px`,
    height: `${Math.round(thumb.height * k)}px`,
  }
  open.value = true
  document.body.style.overflow = 'hidden'
  window.addEventListener('keydown', onKey)
  await nextTick()
  const backdrop = backdropEl.value
  const card = cardEl.value
  const img = imgEl.value
  if (!backdrop || !card || !img) {
    ready.value = true
    return
  }
  // decodifica con el overlay aún invisible y la miniatura todavía en su sitio
  await img.decode().catch(() => {})
  // revelar y animar en el MISMO tick: el clon nace ya en el primer keyframe
  // (sobre la miniatura), sin ningún frame suelto en estado final que reinicie
  // la animación (el "crece-encoge-crece")
  ready.value = true
  // el origen se esconde DESPUÉS de revelar el clon: al revés habría un frame
  // en blanco, y así el solape ocurre justo donde los dos coinciden
  await nextTick()
  hideSource(true)
  if (reducedMotion()) return
  card.animate([{ transform: toSourceTransform(card, source) }, { transform: 'none' }], {
    duration: durToken('--tt-dur-300', 300),
    easing: 'ease',
  })
  backdrop.animate([{ opacity: 0 }, { opacity: 1 }], {
    duration: durToken('--tt-dur-200', 200),
    easing: 'ease',
  })
}

function hideSource(hidden: boolean) {
  if (source) source.style.visibility = hidden ? 'hidden' : ''
}

function close() {
  if (!open.value || closing.value) return
  const backdrop = backdropEl.value
  const card = cardEl.value
  if (!backdrop || !card || !source || reducedMotion()) {
    finish()
    return
  }
  closing.value = true
  // el rect del origen se recalcula aquí: si hubo scroll, vuelve al sitio correcto
  const flight = card.animate(
    [{ transform: 'none' }, { transform: toSourceTransform(card, source) }],
    { duration: durToken('--tt-dur-300', 300), easing: 'ease', fill: 'forwards' },
  )
  backdrop.animate([{ opacity: 1 }, { opacity: 0 }], {
    duration: durToken('--tt-dur-300', 300),
    easing: 'ease',
    fill: 'forwards',
  })
  // al aterrizar, el clon se desmonta y la miniatura reaparece en el mismo frame
  flight.finished.catch(() => {}).then(finish)
}

function finish() {
  hideSource(false)
  source = null
  open.value = false
  closing.value = false
  ready.value = false
  size.value = null
  document.body.style.overflow = ''
  window.removeEventListener('keydown', onKey)
}

function onKey(e: KeyboardEvent) {
  if (e.key === 'Escape') close()
}

// desmontar con el zoom abierto dejaría el scroll del body bloqueado
onBeforeUnmount(() => {
  if (open.value) finish()
})

defineExpose({ openFrom, close })
</script>

<template>
  <Teleport to="body">
    <div
      v-if="open"
      role="dialog"
      aria-modal="true"
      class="fixed inset-0 z-lightbox flex items-center justify-center p-6 cursor-zoom-out"
      @click="close"
    >
      <!-- el fundido es SOLO del fondo: el clon va opaco desde el primer frame -->
      <div ref="backdropEl" class="absolute inset-0 bg-black/70" :class="{ invisible: !ready }" />
      <!-- blanco stock a propósito: papel de postal, invariante al modo oscuro -->
      <div ref="cardEl" class="relative rounded bg-white p-1.5 shadow-lift" :class="{ invisible: !ready }">
        <img
          ref="imgEl"
          :src="src ?? undefined"
          :alt="alt"
          :style="size ?? undefined"
          class="tt-lightbox-img block rounded-sm object-cover"
        />
      </div>
    </div>
  </Teleport>
</template>
