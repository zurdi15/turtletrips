<script setup lang="ts">
import { ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import Toast from 'primevue/toast'
import ConfirmDialog from 'primevue/confirmdialog'
import AppNav from './components/app/AppNav.vue'

const route = useRoute()
const router = useRouter()

// tt-view = rise estándar al entrar cualquier vista (la entrada la pone el
// Transition, no una clase en el root: ver nota en style.css); tt-splash =
// transición especial al cruzar el login (entrar o salir de la app).
const transitionName = ref('tt-view')

// la nav es sticky: si apareciera al confirmarse la ruta empujaría el layout
// con el login aún despidiéndose. Se muestra justo antes de entrar la vista
// destino (before-enter, tras el out) y se oculta al instante hacia el login.
const navVisible = ref(!route.meta.bare)

router.afterEach((to, from) => {
  transitionName.value = to.name === 'login' || from.name === 'login' ? 'tt-splash' : 'tt-view'
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
    <main class="max-w-6xl mx-auto px-4 py-6">
      <!-- cada vista entra con un rise suave (appear cubre la carga inicial) -->
      <router-view v-slot="{ Component }">
        <Transition :name="transitionName" mode="out-in" appear @before-enter="onViewBeforeEnter">
          <component :is="Component" />
        </Transition>
      </router-view>
    </main>
    <Toast position="bottom-right" />
    <ConfirmDialog class="w-full max-w-md mx-4" />
  </div>
</template>
