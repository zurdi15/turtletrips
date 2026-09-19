<script setup lang="ts">
import { computed, nextTick, onBeforeUnmount, onMounted, ref, watch } from 'vue'
import { useI18n } from 'vue-i18n'
import { useRoute } from 'vue-router'
import { useMediaQuery } from '../../composables/useMediaQuery'

defineProps<{ tripId: string }>()

const route = useRoute()
const { t } = useI18n()

const tabs = computed(() => [
  { name: 'trip-overview', label: t('trips.tabs.overview'), icon: 'pi pi-home' },
  { name: 'trip-places', label: t('trips.tabs.places'), icon: 'pi pi-map-marker' },
  { name: 'trip-itinerary', label: t('trips.tabs.itinerary'), icon: 'pi pi-calendar' },
  { name: 'trip-bookings', label: t('trips.tabs.bookings'), icon: 'pi pi-ticket' },
  { name: 'trip-expenses', label: t('trips.tabs.expenses'), icon: 'pi pi-wallet' },
  { name: 'trip-packing', label: t('trips.tabs.packing'), icon: 'pi pi-briefcase' },
  { name: 'trip-checklist', label: t('trips.tabs.checklist'), icon: 'pi pi-check-square' },
  { name: 'trip-links', label: t('trips.tabs.links'), icon: 'pi pi-link' },
  { name: 'trip-files', label: t('trips.tabs.files'), icon: 'pi pi-paperclip' },
  { name: 'trip-share', label: t('trips.tabs.share'), icon: 'pi pi-share-alt' },
  { name: 'trip-settings', label: t('trips.tabs.settings'), icon: 'pi pi-cog' },
])

// la tab clicada se marca activa al momento (optimista), sin esperar al router
const pendingTab = ref<string | null>(null)
const activeTab = computed(() => pendingTab.value ?? String(route.name))
watch(
  () => route.name,
  () => (pendingTab.value = null),
)

// ---- pistas de desbordamiento: en móvil la banda no cabe y hay que
// deslizarla. El borde que recorta tabs se desvanece y lleva un chevrón
// (clic = avanzar una "página"); sin nada más hacia un lado, desaparecen ----

// ancho del desvanecido, y margen que se deja al traer una tab a la vista
// para que no acabe debajo del chevrón
const EDGE_PX = 40

const trackEl = ref<HTMLElement | null>(null)
const overflowStart = ref(false)
const overflowEnd = ref(false)
const reducedMotion = useMediaQuery('(prefers-reduced-motion: reduce)')

function behavior(): ScrollBehavior {
  return reducedMotion.value ? 'auto' : 'smooth'
}

function updateOverflow() {
  const track = trackEl.value
  if (!track) return
  // 1 px de holgura: anchos fraccionarios dejan un recorrido de subpíxel que
  // mantendría encendida la pista del final estando ya al final
  const maxScroll = track.scrollWidth - track.clientWidth
  overflowStart.value = track.scrollLeft > 1
  overflowEnd.value = track.scrollLeft < maxScroll - 1
}

function reveal(el: HTMLElement | null | undefined, how: ScrollBehavior) {
  const track = trackEl.value
  if (!track || !el) return
  const start = el.offsetLeft - EDGE_PX
  const end = el.offsetLeft + el.offsetWidth + EDGE_PX - track.clientWidth
  if (start < track.scrollLeft) track.scrollTo({ left: Math.max(start, 0), behavior: how })
  else if (end > track.scrollLeft) track.scrollTo({ left: end, behavior: how })
}

function revealActive(how: ScrollBehavior) {
  reveal(trackEl.value?.querySelector<HTMLElement>('.tt-tab-active'), how)
}

// el scroll propio del foco se para en el borde, debajo del chevrón
function onFocusIn(event: FocusEvent) {
  const el = event.target as HTMLElement
  if (el.matches(':focus-visible')) reveal(el, behavior())
}

function scrollPage(direction: 1 | -1) {
  const track = trackEl.value
  if (!track) return
  track.scrollBy({ left: direction * (track.clientWidth - EDGE_PX * 2), behavior: behavior() })
}

// tocar una tab medio tapada la trae entera
watch(activeTab, () => nextTick(() => revealActive(behavior())))
// cambiar de idioma cambia el ancho de las etiquetas
watch(tabs, () => nextTick(updateOverflow))

let resizeObserver: ResizeObserver | null = null

onMounted(async () => {
  await nextTick()
  revealActive('auto')
  updateOverflow()
  const track = trackEl.value
  if (!track) return
  resizeObserver = new ResizeObserver(() => {
    // una banda más estrecha puede tapar la tab activa
    revealActive('auto')
    updateOverflow()
  })
  resizeObserver.observe(track)
})

onBeforeUnmount(() => {
  resizeObserver?.disconnect()
  resizeObserver = null
})
</script>

<template>
  <!-- el borde va en el contenedor: la máscara del desvanecido solo cae
       sobre las tabs y la línea base sigue entera -->
  <div
    class="tt-tabs relative border-b border-line mb-6 mt-4"
    :class="{ 'tt-tabs-fade-start': overflowStart, 'tt-tabs-fade-end': overflowEnd }"
    :style="{ '--tt-tabs-edge': `${EDGE_PX}px` }"
  >
    <!-- overflow-y hidden (no el auto que forzaría overflow-x): así la banda no
         es contenedor de scroll vertical y un gesto vertical que empiece en
         las tabs sigue bajando la página -->
    <nav
      ref="trackEl"
      class="tt-tabs-track flex gap-1 overflow-x-auto overflow-y-hidden overscroll-x-contain no-scrollbar"
      @scroll.passive="updateOverflow"
      @focusin="onFocusIn"
    >
      <!-- el color activo se aplica SIN transición (una transición de color se
           congela si el hilo principal está montando la tab) y el subrayado
           crece con transform, que anima en el compositor -->
      <router-link
        v-for="tab in tabs"
        :key="tab.name"
        :to="{ name: tab.name, params: { id: tripId } }"
        class="tt-tab px-3 py-2 text-sm font-medium no-underline whitespace-nowrap"
        :class="
          activeTab === tab.name
            ? 'tt-tab-active text-primary'
            : 'text-ink-muted hover:text-ink'
        "
        @click="pendingTab = tab.name"
      >
        <i :class="tab.icon" class="mr-1.5 text-xs" />{{ tab.label }}
      </router-link>
    </nav>
    <!-- atajos solo de puntero: con teclado se llega a cada tab y el foco
         ya la trae a la vista -->
    <button
      v-if="overflowStart"
      type="button"
      tabindex="-1"
      aria-hidden="true"
      class="tt-tabs-edge left-0 justify-start"
      @mousedown.prevent
      @click="scrollPage(-1)"
    >
      <i class="pi pi-chevron-left" />
    </button>
    <button
      v-if="overflowEnd"
      type="button"
      tabindex="-1"
      aria-hidden="true"
      class="tt-tabs-edge right-0 justify-end"
      @mousedown.prevent
      @click="scrollPage(1)"
    >
      <i class="pi pi-chevron-right" />
    </button>
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

/* el borde que recorta tabs se desvanece; cada lado por separado */
.tt-tabs-fade-start .tt-tabs-track {
  --tt-tabs-fade-start: var(--tt-tabs-edge);
}
.tt-tabs-fade-end .tt-tabs-track {
  --tt-tabs-fade-end: var(--tt-tabs-edge);
}
.tt-tabs-fade-start .tt-tabs-track,
.tt-tabs-fade-end .tt-tabs-track {
  mask-image: linear-gradient(
    to right,
    transparent,
    black var(--tt-tabs-fade-start, 0px),
    black calc(100% - var(--tt-tabs-fade-end, 0px)),
    transparent
  );
}

.tt-tabs-edge {
  position: absolute;
  top: 0;
  bottom: 0;
  display: flex;
  align-items: center;
  width: calc(var(--tt-tabs-edge) * 0.6);
  color: var(--tt-ink-muted);
  cursor: pointer;
}
.tt-tabs-edge:hover {
  color: var(--tt-ink);
}
</style>
