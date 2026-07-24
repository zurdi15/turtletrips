<script setup lang="ts">
import Skeleton from 'primevue/skeleton'

withDefaults(
  defineProps<{
    variant?: 'stats' | 'table' | 'cards' | 'list'
    rows?: number
  }>(),
  { variant: 'list', rows: 5 },
)
</script>

<template>
  <!-- stats: rejilla de métricas (gastos) -->
  <div v-if="variant === 'stats'" class="grid grid-cols-2 sm:grid-cols-3 xl:grid-cols-6 gap-3">
    <div v-for="i in 6" :key="i" class="bg-white rounded-xl border border-slate-200 p-3.5">
      <Skeleton width="60%" height="0.6rem" class="mb-3" />
      <Skeleton width="80%" height="1.25rem" class="mb-2" />
      <Skeleton width="40%" height="0.6rem" />
    </div>
  </div>

  <!-- table: tarjeta con filas tipo tabla -->
  <div
    v-else-if="variant === 'table'"
    class="bg-white rounded-xl border border-slate-200 p-4 flex flex-col gap-3.5"
  >
    <div v-for="i in rows" :key="i" class="flex items-center gap-3">
      <Skeleton shape="circle" size="1.25rem" class="shrink-0" />
      <Skeleton width="5rem" height="0.9rem" class="shrink-0" />
      <Skeleton :width="i % 2 ? '40%' : '55%'" height="0.9rem" />
      <Skeleton width="4rem" height="0.9rem" class="!ml-auto shrink-0" />
    </div>
  </div>

  <!-- cards: tarjetas apiladas (reservas, sitios…) -->
  <div v-else-if="variant === 'cards'" class="flex flex-col gap-4">
    <div v-for="i in rows" :key="i" class="bg-white rounded-xl border border-slate-200 p-4">
      <div class="flex items-center gap-3 mb-3">
        <Skeleton shape="circle" size="2rem" class="shrink-0" />
        <Skeleton :width="i % 2 ? '30%' : '45%'" height="1rem" />
      </div>
      <Skeleton width="70%" height="0.75rem" class="mb-2" />
      <Skeleton width="50%" height="0.75rem" />
    </div>
  </div>

  <!-- list: líneas sueltas (maleta, ficheros…) -->
  <div v-else class="flex flex-col gap-3">
    <div v-for="i in rows" :key="i" class="flex items-center gap-3">
      <Skeleton shape="circle" size="1.1rem" class="shrink-0" />
      <Skeleton :width="i % 3 === 0 ? '35%' : i % 3 === 1 ? '55%' : '45%'" height="0.9rem" />
    </div>
  </div>
</template>
