import { ref } from 'vue'
import type { ThemePref } from '../api/types'

const themePref = ref<ThemePref>('light')
const isDark = ref(false)

/** Pura (testeable sin DOM): resuelve si toca modo oscuro. */
export function resolveDark(pref: ThemePref, systemPrefersDark: boolean): boolean {
  return pref === 'dark' || (pref === 'system' && systemPrefersDark)
}

function systemDark(): boolean {
  return window.matchMedia('(prefers-color-scheme: dark)').matches
}

function apply() {
  document.documentElement.classList.toggle('tt-dark', isDark.value)
}

/** Fija la preferencia, la aplica y la espeja a localStorage (caché anti-flash). */
export function setThemePref(pref: ThemePref) {
  themePref.value = pref
  isDark.value = resolveDark(pref, systemDark())
  localStorage.setItem('tt-theme', pref)
  apply()
}

/** Llamar antes de montar la app para evitar el destello de tema equivocado */
export function initTheme() {
  const stored = localStorage.getItem('tt-theme')
  // sin preferencia guardada el tema por defecto es el claro
  const pref: ThemePref =
    stored === 'light' || stored === 'dark' || stored === 'system' ? stored : 'light'
  themePref.value = pref
  isDark.value = resolveDark(pref, systemDark())
  apply()
}

export function useTheme() {
  return { isDark, themePref, setThemePref }
}

/**
 * Valor resuelto de un token CSS (--tt-*) para consumidores que no leen CSS
 * (canvas de Chart.js). apply() togglea la clase de tema síncronamente, así
 * que el valor leído siempre corresponde al modo actual.
 */
export function cssVar(name: string): string {
  return getComputedStyle(document.documentElement).getPropertyValue(name).trim()
}
