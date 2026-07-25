<script setup lang="ts">
import Tag from 'primevue/tag'
import type { TripStatus } from '../api/types'
import { TRIP_STATUS_KEYS, TRIP_STATUS_SEVERITY } from '../constants'

defineProps<{ status: TripStatus }>()
</script>

<template>
  <Tag :value="$t(TRIP_STATUS_KEYS[status])" :severity="TRIP_STATUS_SEVERITY[status]" />
</template>
