<script setup lang="ts">
import { useRoute } from 'vue-router'
import BrandMark from '../BrandMark.vue'

const route = useRoute()

const navItems = [
  { to: '/', label: 'Viajes', icon: 'pi pi-compass', match: (p: string) => p === '/' || p.startsWith('/trips') },
  { to: '/map', label: 'Mapa', icon: 'pi pi-globe', match: (p: string) => p.startsWith('/map') },
  { to: '/packing', label: 'Maletas', icon: 'pi pi-briefcase', match: (p: string) => p.startsWith('/packing') },
  { to: '/travelers', label: 'Viajeros', icon: 'pi pi-users', match: (p: string) => p.startsWith('/travelers') },
]
</script>

<template>
  <header class="bg-white border-b border-slate-200 sticky top-0 z-header">
    <div class="max-w-6xl mx-auto px-3 sm:px-4 h-14 relative flex items-center gap-2 sm:gap-4">
      <router-link to="/" class="flex items-center gap-2 no-underline shrink-0">
        <BrandMark class="h-8 w-8 text-slate-800" />
        <span class="font-bold text-lg tracking-tight text-slate-800 hidden md:inline"
          >turtle<span class="text-emerald-500">trips</span></span
        >
      </router-link>
      <nav class="absolute left-1/2 -translate-x-1/2 flex items-center gap-0.5 sm:gap-1">
        <router-link
          v-for="item in navItems"
          :key="item.to"
          :to="item.to"
          class="inline-flex items-center justify-center px-3 sm:px-3.5 py-2 rounded-lg text-sm font-medium no-underline transition-colors whitespace-nowrap"
          :class="
            item.match(route.path)
              ? 'bg-slate-100 text-slate-900'
              : 'text-slate-500 hover:text-slate-700 hover:bg-slate-50'
          "
        >
          <i :class="item.icon" class="text-sm sm:mr-1.5" />
          <span class="hidden sm:inline">{{ item.label }}</span>
        </router-link>
      </nav>
      <span class="flex-1" />
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
</template>
