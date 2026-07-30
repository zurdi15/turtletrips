import { defineStore } from 'pinia'
import { ref } from 'vue'
import { api } from '../api/client'

interface BagPermissions {
  revoked: number[]
  restricted_by: number[]
}

/**
 * Permisos de gestión de maletas dentro de la familia (default: permitido).
 * `revoked` = a quiénes les quitaste el permiso sobre TUS maletas (página
 * Familia); `restrictedBy` = dueños que te lo quitaron a ti (el PackingTab
 * pinta sus maletas en solo-consulta). El servidor es quien manda: esto solo
 * evita ofrecer acciones que acabarían en 403.
 */
export const useBagPermissionsStore = defineStore('bagPermissions', () => {
  const revoked = ref<Set<number>>(new Set())
  const restrictedBy = ref<Set<number>>(new Set())
  const loaded = ref(false)

  async function load(force = false) {
    if (loaded.value && !force) return
    const data = await api.get<BagPermissions>('/family/bag-permissions')
    revoked.value = new Set(data.revoked)
    restrictedBy.value = new Set(data.restricted_by)
    loaded.value = true
  }

  async function setAllowed(travelerId: number, allowed: boolean) {
    await api.put(`/family/bag-permissions/${travelerId}`, { allowed })
    const next = new Set(revoked.value)
    if (allowed) next.delete(travelerId)
    else next.add(travelerId)
    revoked.value = next
  }

  return { revoked, restrictedBy, loaded, load, setAllowed }
})
