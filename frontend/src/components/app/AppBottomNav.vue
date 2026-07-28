<script setup lang="ts">
import { useNavItems } from '../../composables/useNavItems'

// Navegación principal en móvil: barra FLOTANTE al pie (el pulgar llega, y la
// cabecera se queda solo con el logo y el avatar). En desktop no se monta: ahí
// las secciones viven en la cabecera con su guion viajero (AppNav).
const { items, activeIndex, pendingTo } = useNavItems()
</script>

<template>
  <nav class="tt-bottom-nav fixed inset-x-0 bottom-0 z-header px-3">
    <div
      class="relative mx-auto grid max-w-sm grid-flow-col auto-cols-fr items-stretch rounded-2xl border border-line bg-surface p-1.5 shadow-lift"
    >
      <!-- el verde viaja hasta la sección activa: como los segmentos son
           iguales, se mueve por índice sin medir nada (igual que ClusterBtn;
           el guion de la cabecera sí mide porque allí los anchos varían) -->
      <span
        v-if="activeIndex >= 0"
        aria-hidden="true"
        class="tt-bottom-nav-pill absolute top-1.5 bottom-1.5 left-1.5 rounded-xl bg-brand-tint-strong"
        :style="{
          width: `calc((100% - 0.75rem) / ${items.length})`,
          transform: `translateX(${activeIndex * 100}%)`,
        }"
      />
      <router-link
        v-for="(item, index) in items"
        :key="item.to"
        :to="item.to"
        class="relative flex min-w-0 flex-col items-center gap-1 rounded-xl py-1.5 text-2xs font-medium no-underline"
        :class="index === activeIndex ? 'text-brand-strong' : 'text-ink-muted'"
        @click="pendingTo = item.to"
      >
        <i :class="item.icon" class="text-base" />
        <span class="max-w-full truncate">{{ item.label }}</span>
      </router-link>
    </div>
  </nav>
</template>

<style scoped>
/* flota sobre el borde inferior, respetando la barra del sistema en iOS */
.tt-bottom-nav {
  padding-bottom: max(0.75rem, env(safe-area-inset-bottom));
}

/* reduced-motion lo cubre el guard global de style.css */
.tt-bottom-nav-pill {
  transition: transform var(--tt-dur-300) var(--tt-ease-bounce);
}
</style>
