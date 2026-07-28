<script setup lang="ts">
import { computed, nextTick, onBeforeUnmount, onMounted, ref, watch } from 'vue'
import { useRouter } from 'vue-router'
import { useI18n } from 'vue-i18n'
import Popover from 'primevue/popover'
import BrandMark from '../BrandMark.vue'
import TravelerAvatar from '../ui/TravelerAvatar.vue'
import { useMediaQuery } from '../../composables/useMediaQuery'
import { useNavItems } from '../../composables/useNavItems'
import { useSessionStore } from '../../stores/session'

const router = useRouter()
const { t, locale } = useI18n()
const session = useSessionStore()

// en móvil las secciones se van a la barra flotante inferior (AppBottomNav):
// aquí solo quedan el logo y el menú de usuario
const isDesktop = useMediaQuery('(min-width: 640px)')

const { items: navItems, activeIndex, pendingTo } = useNavItems()

// --- skeleton hasta que las fuentes de iconos estén listas ---
// Los glifos pi/mdi llegan por @font-face: hasta que cargan, los ítems se
// pintan sin icono y cambian de ancho de golpe (y el guion se mide mal).
// Mientras tanto se muestran skeletons con la silueta de los ítems.

const ICON_FONTS = ["1rem 'primeicons'", "1rem 'Material Design Icons'"] as const

function iconFontsLoaded(): boolean {
  try {
    return ICON_FONTS.every((font) => document.fonts.check(font))
  } catch {
    return true // sin Font Loading API, mejor no bloquear la nav
  }
}

// recarga en caliente con fuentes cacheadas: ni un frame de skeleton
const navReady = ref(iconFontsLoaded())

onMounted(async () => {
  if (!navReady.value) {
    try {
      await Promise.all(ICON_FONTS.map((font) => document.fonts.load(font)))
      await document.fonts.ready
    } catch {
      /* sin Font Loading API: se muestra igualmente */
    }
    navReady.value = true
  }
  await nextTick()
  placeDash(true)
  window.addEventListener('resize', onResize)
})

// --- guion viajero bajo la sección activa ---
// A diferencia de la pill de ClusterBtn (segmentos iguales, se mueve por
// índice), aquí los ítems tienen anchos variables: se mide el centro del
// activo y el guion VIAJA hasta él con el muelle del sistema.

const itemEls: (HTMLElement | null)[] = []
function setItemEl(comp: unknown, index: number) {
  itemEls[index] = (comp as { $el?: HTMLElement } | null)?.$el ?? null
}

const dashX = ref<number | null>(null)
const dashSnap = ref(false)

function placeDash(snap = false) {
  const el = itemEls[activeIndex.value]
  if (!el) {
    dashX.value = null
    return
  }
  // al (re)aparecer o recolocarse por resize/idioma no debe "volar": snap
  if (snap || dashX.value === null) {
    dashSnap.value = true
    requestAnimationFrame(() => requestAnimationFrame(() => (dashSnap.value = false)))
  }
  dashX.value = el.offsetLeft + el.offsetWidth / 2
}

watch(activeIndex, () => nextTick(() => placeDash()))
watch(locale, () => nextTick(() => placeDash(true)))
function onResize() {
  placeDash(true)
}
onBeforeUnmount(() => window.removeEventListener('resize', onResize))

// --- menú de usuario ---

const menu = ref<InstanceType<typeof Popover> | null>(null)

const menuItems = computed(() => [
  { to: '/profile', label: t('common.userMenu.profile'), icon: 'pi pi-user' },
  { to: '/settings', label: t('common.userMenu.settings'), icon: 'pi pi-cog' },
])

function go(to: string) {
  menu.value?.hide()
  router.push(to)
}

async function logout() {
  menu.value?.hide()
  await session.logout()
  router.push({ name: 'login' })
}
</script>

<template>
  <header class="bg-surface border-b border-line sticky top-0 z-header">
    <div class="max-w-6xl mx-auto px-3 sm:px-4 h-14 relative flex items-center gap-2 sm:gap-4">
      <!-- la tortuga nada al pasar el ratón por el logo -->
      <router-link to="/" class="tt-swim-hover flex items-center gap-2 no-underline shrink-0">
        <BrandMark class="tt-swim-target h-8 w-8 text-ink-heading" />
        <!-- en móvil la cabecera se queda solo con logo y avatar: cabe el nombre -->
        <span class="font-bold text-lg tracking-tight text-ink-heading"
          >turtle<span class="text-emerald-500">trips</span></span
        >
      </router-link>
      <nav v-if="isDesktop" class="absolute left-1/2 -translate-x-1/2">
        <!-- la nav no se pinta hasta que las fuentes de iconos están listas
             (evita el baile de anchos del FOUT) y entra con un fade; al estar
             centrada en absoluto, su ausencia no desplaza nada. El guion se
             coloca cuando el bloque entra de verdad en el DOM (hook enter). -->
        <Transition name="tt-fade" @enter="() => placeDash(true)">
          <div v-if="navReady" class="relative flex items-center gap-1">
            <router-link
              v-for="(item, index) in navItems"
              :key="item.to"
              :ref="(comp) => setItemEl(comp, index)"
              :to="item.to"
              class="inline-flex items-center justify-center px-3.5 py-2 rounded-lg text-sm font-medium no-underline transition-colors whitespace-nowrap"
              :class="
                index === activeIndex
                  ? 'text-ink-strong'
                  : 'text-ink-muted hover:text-ink hover:bg-surface-hover'
              "
              @click="pendingTo = item.to"
            >
              <i :class="item.icon" class="text-sm mr-1.5" />
              <span>{{ item.label }}</span>
            </router-link>
            <!-- el guion viaja hasta el centro del ítem activo (translateX -50% lo centra) -->
            <span
              v-show="activeIndex >= 0 && dashX !== null"
              class="tt-nav-dash absolute -bottom-1 left-0 h-0.5 w-8 rounded-full bg-primary"
              :class="dashSnap ? 'tt-nav-dash-snap' : ''"
              :style="{ transform: `translateX(calc(${dashX ?? 0}px - 50%))` }"
              aria-hidden="true"
            />
          </div>
        </Transition>
      </nav>
      <span class="flex-1" />
      <button
        v-if="session.me"
        type="button"
        class="rounded-full transition-shadow hover:shadow-lift shrink-0"
        :title="session.me.user.username"
        @click="menu?.toggle($event)"
      >
        <TravelerAvatar
          :name="session.me.traveler.name"
          :color="session.me.traveler.color"
          :avatar-url="session.me.traveler.avatar_url"
          size="md"
        />
      </button>
      <Popover ref="menu">
        <!-- cascada de entradas al abrir el menú -->
        <div class="tt-stagger flex flex-col min-w-44">
          <div class="px-3 py-2 border-b border-line-subtle">
            <div class="text-sm font-semibold text-ink-strong">{{ session.me?.traveler.name }}</div>
            <div class="text-2xs text-ink-muted">{{ session.me?.user.username }}</div>
          </div>
          <button
            v-for="item in menuItems"
            :key="item.to"
            type="button"
            class="flex items-center gap-2 px-3 py-2 text-sm text-left rounded-lg text-ink-secondary hover:bg-surface-hover hover:text-ink transition-colors"
            @click="go(item.to)"
          >
            <i :class="item.icon" class="text-sm" />
            {{ item.label }}
          </button>
          <div class="border-t border-line-subtle mt-1 pt-1">
            <button
              type="button"
              class="w-full flex items-center gap-2 px-3 py-2 text-sm text-left rounded-lg text-ink-secondary hover:bg-surface-hover hover:text-ink transition-colors"
              @click="logout"
            >
              <i class="pi pi-sign-out text-sm" />
              {{ t('common.userMenu.logout') }}
            </button>
          </div>
        </div>
      </Popover>
    </div>
  </header>
</template>

<style scoped>
/* reduced-motion lo cubre el guard global de style.css */
.tt-nav-dash {
  transition: transform var(--tt-dur-300) var(--tt-ease-bounce);
}
.tt-nav-dash-snap {
  transition: none;
}
</style>
