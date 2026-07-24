<script setup lang="ts">
import { ref } from 'vue'
import Popover from 'primevue/popover'
import { CATEGORY_PALETTE } from '../../constants'

withDefaults(defineProps<{ colors?: string[] }>(), { colors: () => CATEGORY_PALETTE })
const emit = defineEmits<{ select: [color: string] }>()

const popover = ref()

// el padre guarda "para quién" se elige color y llama a toggle(event)
defineExpose({
  toggle: (event: Event) => popover.value?.toggle(event),
  hide: () => popover.value?.hide(),
})

function pick(color: string) {
  emit('select', color)
  popover.value?.hide()
}
</script>

<template>
  <Popover ref="popover">
    <div class="grid grid-cols-6 gap-2 p-1">
      <button
        v-for="color in colors"
        :key="color"
        class="w-6 h-6 rounded-full ring-1 ring-line hover:scale-110 transition-transform"
        :style="{ background: color }"
        @click="pick(color)"
      />
    </div>
  </Popover>
</template>
