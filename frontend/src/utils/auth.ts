/** Iniciales para el avatar sin foto: 1-2 letras de las primeras palabras. */
export function initials(name: string): string {
  const words = name.trim().split(/\s+/).filter(Boolean)
  if (!words.length) return '?'
  const letters = words.slice(0, 2).map((w) => [...w][0])
  return letters.join('').toUpperCase()
}

/** Validación de alta/cambio de contraseña; devuelve el código de error i18n o null. */
export function validatePassword(
  password: string,
  confirm: string,
): 'tooShort' | 'mismatch' | null {
  if (password.length < 8) return 'tooShort'
  if (password !== confirm) return 'mismatch'
  return null
}

/** Solo rutas internas como destino post-login (evita open redirects). */
export function safeRedirect(raw: unknown): string {
  if (typeof raw !== 'string' || !raw.startsWith('/') || raw.startsWith('//')) return '/'
  return raw
}
