import { createI18n } from 'vue-i18n'
import es from './es'
import en from './en'

export const SUPPORTED_LOCALES = ['es', 'en'] as const
export type AppLocale = (typeof SUPPORTED_LOCALES)[number]

const STORAGE_KEY = 'tt-lang'

/** Locale BCP-47 para Intl/DatePicker/InputNumber (en-GB: dd/mm/yyyy como el resto de la app) */
export const INTL_LOCALES: Record<AppLocale, string> = { es: 'es-ES', en: 'en-GB' }

function isSupported(value: string | null | undefined): value is AppLocale {
  return !!value && (SUPPORTED_LOCALES as readonly string[]).includes(value)
}

/** Preferencia guardada → idioma del navegador → español (comportamiento histórico) */
function detectLocale(): AppLocale {
  // try/catch y no typeof: Node ≥22 expone un localStorage global no funcional
  // (rompería los tests de utils que importan este módulo transitivamente)
  let stored: string | null = null
  try {
    stored = localStorage.getItem(STORAGE_KEY)
  } catch {
    stored = null
  }
  if (isSupported(stored)) return stored
  let nav: string | null = null
  try {
    nav = navigator.language?.slice(0, 2) ?? null
  } catch {
    nav = null
  }
  if (isSupported(nav)) return nav
  return 'es'
}

export const i18n = createI18n({
  legacy: false,
  globalInjection: true,
  locale: detectLocale(),
  fallbackLocale: 'es',
  messages: { es, en },
})

/** Idioma activo (no reactivo; en componentes usar useI18n().locale) */
export function currentLocale(): AppLocale {
  return i18n.global.locale.value as AppLocale
}

/**
 * Locale Intl activo, para formateadores fuera de componentes (utils puros).
 * Leerlo dentro de un computed SÍ es reactivo (i18n.global.locale es un ref).
 */
export function intlLocale(): string {
  return INTL_LOCALES[currentLocale()]
}

export function setLocale(locale: AppLocale) {
  i18n.global.locale.value = locale
  localStorage.setItem(STORAGE_KEY, locale)
  document.documentElement.lang = locale
}

/** Llamar antes de montar para que <html lang> refleje el idioma detectado */
export function initLocale() {
  document.documentElement.lang = currentLocale()
}
