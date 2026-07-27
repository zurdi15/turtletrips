<script setup lang="ts">
import { computed, ref, watch } from 'vue'
import { useI18n } from 'vue-i18n'
import { useRoute } from 'vue-router'

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
  { name: 'trip-files', label: t('trips.tabs.files'), icon: 'pi pi-paperclip' },
  { name: 'trip-settings', label: t('trips.tabs.settings'), icon: 'pi pi-cog' },
])

// la tab clicada se marca activa al momento (optimista), sin esperar al router
const pendingTab = ref<string | null>(null)
const activeTab = computed(() => pendingTab.value ?? String(route.name))
watch(
  () => route.name,
  () => (pendingTab.value = null),
)
</script>

<template>
  <nav class="flex gap-1 border-b border-line mb-6 mt-4 overflow-x-auto no-scrollbar">
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
</style>
