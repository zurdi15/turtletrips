import { ref } from 'vue'
import { useI18n } from 'vue-i18n'
import { countryName, flagEmoji } from '../countries'
import { useWorldPlacesStore } from '../stores/worldPlaces'
import { useConfirmDelete } from './useConfirmDelete'
import { useNotify } from './useNotify'
import { useWorldGeometry } from './useWorldGeometry'

/** lo que la tarjeta de alta deja rellenar antes de confirmar */
export interface MarkDetails {
  visited_year?: number | null
  visited_month?: number | null
  note?: string | null
}

/**
 * Marcar y desmarcar países desde el propio mapa.
 *
 * Mientras el POST viaja, el código queda en `pending` para que el relleno se
 * pinte al instante: el store recarga el diario entero tras cada alta (el
 * backend puede arrastrar entradas), y esperar a eso se nota al tocar.
 *
 * Las altas devuelven si salieron bien: la tarjeta que las llama solo se cierra
 * con un true, para que un fallo de red no se lleve por delante el año y la
 * nota que acabas de escribir.
 */
export function useWorldMarking() {
  const store = useWorldPlacesStore()
  const notify = useNotify()
  const confirmAction = useConfirmDelete()
  const { t } = useI18n()
  const { geometry } = useWorldGeometry()

  const pending = ref<Set<string>>(new Set())

  function setPending(code: string, on: boolean) {
    const next = new Set(pending.value)
    if (on) next.add(code)
    else next.delete(code)
    pending.value = next
  }

  /** Alta de un país tocándolo en el mapa; las coordenadas salen del centroide */
  async function markCountry(code: string, details: MarkDetails = {}): Promise<boolean> {
    if (pending.value.has(code)) return false
    setPending(code, true)
    const center = geometry.value?.centerOf(code) ?? null
    try {
      await store.create({
        name: countryName(code),
        kind: 'country',
        country_code: code,
        lat: center?.[0] ?? null,
        lon: center?.[1] ?? null,
        ...details,
      })
      notify.success(t('world.toast.countryAdded', { flag: flagEmoji(code), name: countryName(code) }))
      return true
    } catch (err) {
      notify.error(t('world.toast.addError'), err)
      return false
    } finally {
      setPending(code, false)
    }
  }

  /** Alta de una región (ISO 3166-2) tocándola en el mapa */
  /** `at` = punto donde se tocó la región: sin coordenadas no se puede volar a
   *  ella desde la lista */
  async function markRegion(
    countryCode: string,
    regionCode: string,
    name: string,
    at?: [number, number] | null,
    details: MarkDetails = {},
  ): Promise<boolean> {
    if (pending.value.has(regionCode)) return false
    setPending(regionCode, true)
    try {
      await store.create({
        name,
        kind: 'region',
        country_code: countryCode,
        region_code: regionCode,
        lat: at?.[0] ?? null,
        lon: at?.[1] ?? null,
        ...details,
      })
      notify.success(t('world.toast.regionAdded', { name }))
      return true
    } catch (err) {
      notify.error(t('world.toast.addError'), err)
      return false
    } finally {
      setPending(regionCode, false)
    }
  }

  /**
   * Quitar una región. Con confirmación: dejó de ser simétrico el día en que
   * marcarla pasó a costar una tarjeta con fecha y nota — un toque en falso se
   * llevaba todo eso por delante sin preguntar.
   */
  function unmarkRegion(placeId: number, name: string) {
    confirmAction({
      message: t('world.confirmRemove.messageManual', { name }),
      header: t('world.confirmRemove.header'),
      acceptLabel: t('world.confirmRemove.accept'),
      accept: async () => {
        try {
          await store.remove(placeId)
          notify.success(t('world.toast.regionRemoved', { name }))
        } catch (err) {
          notify.error(t('world.toast.removeError'), err)
        }
      },
    })
  }

  /** Quitar el país del diario; el backend responde 409 si tiene ciudades dentro */
  function unmarkCountry(code: string, placeId: number) {
    confirmAction({
      message: t('world.confirmRemove.messageManual', { name: countryName(code) }),
      header: t('world.confirmRemove.header'),
      acceptLabel: t('world.confirmRemove.accept'),
      accept: async () => {
        try {
          await store.remove(placeId)
          notify.success(
            t('world.toast.countryRemoved', { flag: flagEmoji(code), name: countryName(code) }),
          )
        } catch (err) {
          notify.error(t('world.toast.removeError'), err)
        }
      },
    })
  }

  return { pending, markCountry, unmarkCountry, markRegion, unmarkRegion }
}
