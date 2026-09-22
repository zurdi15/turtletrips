<script setup lang="ts">
// bajo el importe de un gasto marcado fuera de estadísticas, igual en la tabla
// y en la lista: el importe es real (presupuesto, saldos), solo no hace media
</script>

<template>
  <div
    class="inline-flex items-center gap-1 text-2xs text-ink-faint whitespace-nowrap"
    v-tooltip.top="$t('expenses.table.outOfStatsTooltip')"
  >
    <!-- .pi fija 1rem y gana a las utilidades de tamaño: que herede el del texto -->
    <i class="pi pi-eye-slash" style="font-size: inherit" />
    {{ $t('expenses.table.outOfStats') }}
  </div>
</template>
