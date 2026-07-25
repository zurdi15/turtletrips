<script setup lang="ts">
import { computed } from 'vue'
import { useRoute } from 'vue-router'
import { useI18n } from 'vue-i18n'
import BrandMark from '../BrandMark.vue'

const route = useRoute()
const { t } = useI18n()

const navItems = computed(() => [
  { to: '/', label: t('common.nav.trips'), icon: 'pi pi-compass', match: (p: string) => p === '/' || p.startsWith('/trips') },
  { to: '/map', label: t('common.nav.map'), icon: 'pi pi-globe', match: (p: string) => p.startsWith('/map') },
  { to: '/packing', label: t('common.nav.packing'), icon: 'pi pi-briefcase', match: (p: string) => p.startsWith('/packing') },
  { to: '/travelers', label: t('common.nav.travelers'), icon: 'pi pi-users', match: (p: string) => p.startsWith('/travelers') },
])
</script>

<template>
  <header class="bg-surface border-b border-line sticky top-0 z-header">
    <div class="max-w-6xl mx-auto px-3 sm:px-4 h-14 relative flex items-center gap-2 sm:gap-4">
      <router-link to="/" class="flex items-center gap-2 no-underline shrink-0">
        <BrandMark class="h-8 w-8 text-ink-heading" />
        <span class="font-bold text-lg tracking-tight text-ink-heading hidden md:inline"
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
              ? 'bg-surface-muted text-ink-strong'
              : 'text-ink-muted hover:text-ink hover:bg-surface-hover'
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
        :class="route.path.startsWith('/settings') ? 'text-ink' : 'text-ink-faint hover:text-ink-secondary'"
        :title="$t('common.nav.settings')"
      >
        <i class="pi pi-cog text-lg" />
      </router-link>
    </div>
  </header>
</template>
