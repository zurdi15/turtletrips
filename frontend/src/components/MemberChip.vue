<script setup lang="ts">
import TravelerAvatar from './ui/TravelerAvatar.vue'

// acepta un Traveler completo o proyecciones {name, color} (saldos, CSV…)
interface MemberLike {
  id?: number
  name: string
  color: string | null
  avatar_url?: string | null
}

defineProps<{ member: MemberLike; removable?: boolean }>()
defineEmits<{ remove: [event: Event] }>()
</script>

<template>
  <span
    class="inline-flex items-center gap-1.5 px-2 py-0.5 rounded-full text-xs font-medium bg-surface-muted text-ink"
  >
    <!-- caja fija: el dot (8px) y la foto (16px) ocupan lo mismo y los chips
         quedan todos con la misma altura, tenga o no avatar el viajero.
         overflow-hidden sintetiza la baseline en el borde inferior de la caja
         (idéntica con foto o dot): sin él, los chips inline-flex con avatar
         bailan verticalmente respecto a los de solo dot -->
    <span class="w-4 h-4 grid place-items-center overflow-hidden shrink-0">
      <TravelerAvatar
        :name="member.name"
        :color="member.color"
        :avatar-url="member.avatar_url"
        size="xs"
      />
    </span>
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
