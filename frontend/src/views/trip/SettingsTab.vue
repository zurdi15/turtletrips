<script setup lang="ts">
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import Button from 'primevue/button'
import TripForm from '../../components/trips/TripForm.vue'
import type { Trip } from '../../api/types'
import { useTripsStore } from '../../stores/trips'
import { useConfirmDelete } from '../../composables/useConfirmDelete'
import { useNotify } from '../../composables/useNotify'

const props = defineProps<{ trip: Trip }>()

const router = useRouter()
const store = useTripsStore()
const notify = useNotify()
const confirmAction = useConfirmDelete()

const formRef = ref<InstanceType<typeof TripForm> | null>(null)
const saving = ref(false)

async function save() {
  const problem = formRef.value?.validate()
  if (problem) {
    notify.warn(problem)
    return
  }
  saving.value = true
  try {
    await formRef.value!.submit()
    notify.success('Viaje actualizado')
  } catch (err) {
    notify.error('Error al guardar', err)
  } finally {
    saving.value = false
  }
}

function removeTrip() {
  confirmAction({
    message: `¿Eliminar "${props.trip.name}" con todos sus datos y ficheros?`,
    header: 'Eliminar viaje',
    accept: async () => {
      await store.deleteTrip(props.trip.id)
      notify.success('Viaje eliminado')
      router.push('/')
    },
  })
}
</script>

<template>
  <div class="max-w-3xl mx-auto flex flex-col gap-6">
    <section class="bg-surface rounded-card border border-line p-4 sm:p-6">
      <h3 class="text-sm font-semibold text-ink-secondary mb-4">Datos del viaje</h3>
      <TripForm ref="formRef" :key="trip.id" :trip="trip" />
      <div class="flex justify-end mt-5">
        <Button label="Guardar cambios" icon="pi pi-check" :loading="saving" @click="save" />
      </div>
    </section>

    <!-- rojos stock: los tonos danger son invariantes al modo -->
    <section class="rounded-card border border-red-500/40 p-4 sm:p-6">
      <h3 class="text-sm font-semibold text-red-600 mb-1">Zona de peligro</h3>
      <p class="text-sm text-ink-muted mb-4">
        Eliminar el viaje borra también sus sitios, itinerario, reservas, gastos, maletas y
        ficheros. No se puede deshacer.
      </p>
      <Button
        label="Eliminar viaje"
        icon="pi pi-trash"
        severity="danger"
        outlined
        @click="removeTrip"
      />
    </section>
  </div>
</template>
