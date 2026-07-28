<script setup lang="ts">
// Primitiva TONTA: imagen con skeleton shimmer mientras carga y fade al
// aparecer. El tamaño lo pone el consumidor (clases al root por fallthrough);
// si la carga falla se queda el fondo del contenedor (sin shimmer eterno).
import { computed, onMounted, ref, watch } from 'vue'
import Skeleton from 'primevue/skeleton'
import { focusStyle } from '../../utils/imageFocus'

const props = withDefaults(
  defineProps<{
    src: string
    /** clases del <img> interno (object-cover, hover scale…) */
    imgClass?: string
    alt?: string
    lazy?: boolean
    /** encuadre elegido (0-1); sin él, centrada */
    focusX?: number | null
    focusY?: number | null
  }>(),
  { imgClass: '', alt: '', lazy: false, focusX: null, focusY: null },
)

const objectPosition = computed(() => focusStyle(props.focusX, props.focusY))

const imgEl = ref<HTMLImageElement | null>(null)
const loaded = ref(false)
const failed = ref(false)

// src nuevo (p. ej. cambiar la portada) → vuelve el shimmer
watch(
  () => props.src,
  () => {
    loaded.value = false
    failed.value = false
  },
)

onMounted(() => {
  // imagen ya en caché: el evento load pudo dispararse antes de escucharlo
  if (imgEl.value?.complete && imgEl.value.naturalWidth > 0) loaded.value = true
})
</script>

<template>
  <!-- OJO: el root NO se posiciona a sí mismo (un `relative` fijo pisaría el
       `absolute inset-0` del consumidor); el skeleton se ancla al propio root
       si viene posicionado desde fuera, o al contenedor posicionado del padre -->
  <div class="overflow-hidden">
    <img
      v-if="!failed"
      ref="imgEl"
      :src="src"
      :alt="alt"
      :loading="lazy ? 'lazy' : undefined"
      :class="[imgClass, loaded ? 'opacity-100' : 'opacity-0']"
      class="transition-opacity duration-300"
      :style="{ objectPosition }"
      @load="loaded = true"
      @error="failed = true"
    />
    <Skeleton v-if="!loaded && !failed" width="100%" height="100%" class="!absolute inset-0" />
  </div>
</template>
