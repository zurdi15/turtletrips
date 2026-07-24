import { ref } from 'vue'

const isDark = ref(false)

function apply() {
  document.documentElement.classList.toggle('tt-dark', isDark.value)
}

/** Llamar antes de montar la app para evitar el destello de tema claro */
export function initTheme() {
  const stored = localStorage.getItem('tt-theme')
  isDark.value = stored
    ? stored === 'dark'
    : window.matchMedia('(prefers-color-scheme: dark)').matches
  apply()
}

export function useTheme() {
  function toggle() {
    isDark.value = !isDark.value
    localStorage.setItem('tt-theme', isDark.value ? 'dark' : 'light')
    apply()
  }
  return { isDark, toggle }
}
