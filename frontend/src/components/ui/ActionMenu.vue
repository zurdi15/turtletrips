<script setup lang="ts">
// Primitiva TONTA: botón de hamburguesa con las acciones secundarias de una
// barra (importar, exportar, suscribirse…) en un popover, con el mismo aspecto
// que el menú de usuario de la cabecera. Cada ítem trae su acción (`command`)
// o su enlace de descarga (`href`), así el menú no sabe nada de quién lo usa.
import { ref } from 'vue'
import Button from 'primevue/button'
import Popover from 'primevue/popover'

export interface ActionMenuItem {
  label: string
  icon: string
  /** segunda línea, más tenue: qué hace la acción si el nombre no basta */
  hint?: string
  command?: () => void
  /** enlace (descargas: CSV, .ics); se abre con `download` */
  href?: string
}

defineProps<{
  items: ActionMenuItem[]
  /** nombre accesible y tooltip del botón */
  label: string
}>()

const popover = ref<InstanceType<typeof Popover> | null>(null)

function run(item: ActionMenuItem) {
  popover.value?.hide()
  item.command?.()
}
</script>

<template>
  <Button
    icon="pi pi-bars"
    severity="secondary"
    outlined
    :aria-label="label"
    aria-haspopup="true"
    v-tooltip.bottom="label"
    class="shrink-0"
    @click="popover?.toggle($event)"
  />
  <Popover ref="popover">
    <div class="tt-stagger flex flex-col min-w-52">
      <component
        :is="item.href ? 'a' : 'button'"
        v-for="item in items"
        :key="item.label"
        v-bind="item.href ? { href: item.href, download: '' } : { type: 'button' }"
        class="flex items-start gap-2.5 px-3 py-2 text-sm text-left rounded-lg no-underline text-ink-secondary hover:bg-surface-hover hover:text-ink transition-colors cursor-pointer"
        @click="run(item)"
      >
        <i :class="item.icon" class="text-sm mt-0.5 shrink-0" />
        <span class="flex flex-col">
          {{ item.label }}
          <span v-if="item.hint" class="text-2xs leading-snug text-ink-faint max-w-56">{{ item.hint }}</span>
        </span>
      </component>
    </div>
  </Popover>
</template>
