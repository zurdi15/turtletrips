<script setup lang="ts">
import { computed, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useI18n } from 'vue-i18n'
import Popover from 'primevue/popover'
import BrandMark from '../BrandMark.vue'
import TravelerAvatar from '../ui/TravelerAvatar.vue'
import { useSessionStore } from '../../stores/session'

const route = useRoute()
const router = useRouter()
const { t } = useI18n()
const session = useSessionStore()

const navItems = computed(() => [
  { to: '/', label: t('common.nav.trips'), icon: 'pi pi-compass', match: (p: string) => p === '/' || p.startsWith('/trips') },
  { to: '/map', label: t('common.nav.map'), icon: 'pi pi-globe', match: (p: string) => p.startsWith('/map') },
  { to: '/packing', label: t('common.nav.packing'), icon: 'pi pi-briefcase', match: (p: string) => p.startsWith('/packing') },
  { to: '/travelers', label: t('common.nav.travelers'), icon: 'pi pi-users', match: (p: string) => p.startsWith('/travelers') },
])

const menu = ref<InstanceType<typeof Popover> | null>(null)

const menuItems = computed(() => [
  { to: '/profile', label: t('common.userMenu.profile'), icon: 'pi pi-user' },
  ...(session.isAdmin
    ? [{ to: '/admin', label: t('common.userMenu.admin'), icon: 'pi pi-shield' }]
    : []),
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
        <div class="flex flex-col min-w-44">
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
