<script setup lang="ts">
import { ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import Toast from 'primevue/toast'
import ConfirmDialog from 'primevue/confirmdialog'
import AppNav from './components/app/AppNav.vue'
import AppBottomNav from './components/app/AppBottomNav.vue'
import { useMediaQuery } from './composables/useMediaQuery'
import { AUTH_ROUTES } from './router'

const route = useRoute()
const router = useRouter()

// móvil = secciones en la barra flotante inferior; desktop = en la cabecera
const isDesktop = useMediaQuery('(min-width: 640px)')

// tt-view = rise estándar al entrar cualquier vista (la entrada la pone el
// Transition, no una clase en el root: ver nota en style.css); tt-splash =
// transición especial al cruzar el login (entrar o salir de la app).
const transitionName = ref('tt-view')
const isAuthRoute = (name: unknown) => typeof name === 'string' && AUTH_ROUTES.has(name)

// la nav es sticky: si apareciera al confirmarse la ruta empujaría el layout
// con el login aún despidiéndose. Se muestra justo antes de entrar la vista
// destino (before-enter, tras el out) y se oculta al instante hacia el login.
const navVisible = ref(!route.meta.bare)

router.afterEach((to, from) => {
  // el splash es la frontera acceso ⇄ app; entre pantallas de acceso
  // (login → recuperar contraseña) va la transición de siempre
  transitionName.value =
    isAuthRoute(to.name) !== isAuthRoute(from.name) ? 'tt-splash' : 'tt-view'
  if (to.meta.bare) navVisible.value = false
})

function onViewBeforeEnter() {
  navVisible.value = !route.meta.bare
}
</script>

<template>
  <div class="min-h-screen">
    <!-- la cabecera aparece con un fade al entrar en la app (rutas "bare" van sin ella) -->
    <Transition name="tt-fade">
      <AppNav v-if="navVisible" />
    </Transition>
    <!-- pb generoso en móvil con la barra inferior montada: el último elemento
         de la página no queda debajo de ella -->
    <main
      class="max-w-6xl mx-auto px-4 pt-6"
      :class="navVisible && !isDesktop ? 'pb-28' : 'pb-6'"
    >
      <!-- cada vista entra con un rise suave (appear cubre la carga inicial) -->
      <router-view v-slot="{ Component }">
        <Transition :name="transitionName" mode="out-in" appear @before-enter="onViewBeforeEnter">
          <component :is="Component" />
        </Transition>
      </router-view>
    </main>
    <Transition name="tt-fade">
      <AppBottomNav v-if="navVisible && !isDesktop" />
    </Transition>
    <Toast position="bottom-right" />
    <ConfirmDialog class="w-full max-w-md mx-4" />
  </div>
</template>
