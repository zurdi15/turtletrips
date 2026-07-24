<script setup lang="ts">
import { useRoute } from 'vue-router'
import Toast from 'primevue/toast'
import ConfirmDialog from 'primevue/confirmdialog'
import { useTheme } from './composables/useTheme'

const route = useRoute()
const { isDark, toggle } = useTheme()

const navItems = [
  { to: '/', label: 'Viajes', icon: 'pi pi-compass', match: (p: string) => p === '/' || p.startsWith('/trips') },
  { to: '/maletas', label: 'Maletas', icon: 'pi pi-briefcase', match: (p: string) => p.startsWith('/maletas') },
  { to: '/viajeros', label: 'Viajeros', icon: 'pi pi-users', match: (p: string) => p.startsWith('/viajeros') },
]
</script>

<template>
  <div class="min-h-screen">
    <header class="bg-white border-b border-slate-200 sticky top-0 z-40">
      <div class="max-w-6xl mx-auto px-3 sm:px-4 h-14 flex items-center gap-2 sm:gap-4">
        <router-link to="/" class="flex items-center gap-2 no-underline shrink-0">
          <span class="text-2xl">🐢</span>
          <span class="font-bold text-lg text-slate-800 hidden md:inline">Turtle Trips</span>
        </router-link>
        <nav class="flex items-center gap-0.5 sm:gap-1">
          <router-link
            v-for="item in navItems"
            :key="item.to"
            :to="item.to"
            class="px-2.5 sm:px-3 py-1.5 rounded-lg text-sm font-medium no-underline transition-colors whitespace-nowrap"
            :class="
              item.match(route.path)
                ? 'bg-slate-100 text-slate-900'
                : 'text-slate-500 hover:text-slate-700 hover:bg-slate-50'
            "
          >
            <i :class="item.icon" class="text-xs sm:mr-1.5" />
            <span class="hidden sm:inline">{{ item.label }}</span>
          </router-link>
        </nav>
        <span class="flex-1" />
        <button
          class="text-slate-400 hover:text-slate-600 transition-colors"
          :title="isDark ? 'Tema claro' : 'Tema oscuro'"
          @click="toggle"
        >
          <i :class="isDark ? 'pi pi-sun' : 'pi pi-moon'" class="text-lg" />
        </button>
        <router-link
          to="/settings"
          class="transition-colors"
          :class="route.path.startsWith('/settings') ? 'text-slate-700' : 'text-slate-400 hover:text-slate-600'"
          title="Ajustes"
        >
          <i class="pi pi-cog text-lg" />
        </router-link>
      </div>
    </header>
    <main class="max-w-6xl mx-auto px-4 py-6">
      <router-view />
    </main>
    <Toast position="bottom-right" />
    <ConfirmDialog />
  </div>
</template>
