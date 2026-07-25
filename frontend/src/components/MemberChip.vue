<script setup lang="ts">
import type { Traveler } from '../api/types'
import { FALLBACK_CATEGORY_COLOR } from '../stores/categories'

defineProps<{ member: Traveler; removable?: boolean }>()
defineEmits<{ remove: [event: Event] }>()
</script>

<template>
  <span
    class="inline-flex items-center gap-1.5 px-2 py-0.5 rounded-full text-xs font-medium bg-surface-muted text-ink"
  >
    <span
      class="w-2 h-2 rounded-full"
      :style="{ background: member.color ?? FALLBACK_CATEGORY_COLOR }"
    />
    {{ member.name }}
    <button
      v-if="removable"
      type="button"
      class="flex items-center text-ink-faint hover:text-ink cursor-pointer"
      @click.stop="$emit('remove', $event)"
    >
      <i class="pi pi-times-circle text-xs" />
    </button>
  </span>
</template>
