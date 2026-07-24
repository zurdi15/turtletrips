<script setup lang="ts">
import { computed, ref, watch } from 'vue'
import { useRoute } from 'vue-router'

defineProps<{ tripId: string }>()

const route = useRoute()

const tabs = [
  { name: 'trip-overview', label: 'Resumen', icon: 'pi pi-home' },
  { name: 'trip-places', label: 'Sitios', icon: 'pi pi-map-marker' },
  { name: 'trip-itinerary', label: 'Itinerario', icon: 'pi pi-calendar' },
  { name: 'trip-bookings', label: 'Reservas', icon: 'pi pi-ticket' },
  { name: 'trip-expenses', label: 'Gastos', icon: 'pi pi-wallet' },
  { name: 'trip-packing', label: 'Maleta', icon: 'pi pi-briefcase' },
  { name: 'trip-files', label: 'Ficheros', icon: 'pi pi-paperclip' },
]

// la tab clicada se marca activa al momento (optimista), sin esperar al router
const pendingTab = ref<string | null>(null)
const activeTab = computed(() => pendingTab.value ?? String(route.name))
watch(
  () => route.name,
  () => (pendingTab.value = null),
)
</script>

<template>
  <nav class="flex gap-1 border-b border-slate-200 mb-6 mt-4 overflow-x-auto no-scrollbar">
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
          ? 'tt-tab-active text-[var(--p-primary-color)]'
          : 'text-slate-500 hover:text-slate-700'
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
