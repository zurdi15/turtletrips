<script setup lang="ts">
import type { Traveler } from '../api/types'

defineProps<{ member: Traveler }>()
</script>

<template>
  <span
    class="inline-flex items-center gap-1.5 px-2 py-0.5 rounded-full text-xs font-medium bg-slate-100 text-slate-700"
  >
    <span
      class="w-2 h-2 rounded-full"
      :style="{ background: member.color ?? '#94a3b8' }"
    />
    {{ member.name }}
  </span>
</template>
