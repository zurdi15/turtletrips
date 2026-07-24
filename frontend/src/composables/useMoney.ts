const formatters = new Map<string, Intl.NumberFormat>()

export function formatMoney(amount: number, currency: string): string {
  let fmt = formatters.get(currency)
  if (!fmt) {
    try {
      fmt = new Intl.NumberFormat('es-ES', { style: 'currency', currency })
    } catch {
      fmt = new Intl.NumberFormat('es-ES', { maximumFractionDigits: 2 })
    }
    formatters.set(currency, fmt)
  }
  return fmt.format(amount)
}

export function formatDate(iso: string | null | undefined): string {
  if (!iso) return '—'
  const d = new Date(`${iso.slice(0, 10)}T00:00:00`)
  return d.toLocaleDateString('es-ES', { day: 'numeric', month: 'short', year: 'numeric' })
}

export function formatDateTime(iso: string | null | undefined): string {
  if (!iso) return '—'
  return new Date(iso).toLocaleString('es-ES', {
    day: 'numeric',
    month: 'short',
    hour: '2-digit',
    minute: '2-digit',
  })
}

/** Fecha local en formato ISO (YYYY-MM-DD), sin sorpresas de zona horaria */
export function toIsoDate(d: Date): string {
  const y = d.getFullYear()
  const m = String(d.getMonth() + 1).padStart(2, '0')
  const day = String(d.getDate()).padStart(2, '0')
  return `${y}-${m}-${day}`
}

export function parseIsoDate(iso: string): Date {
  return new Date(`${iso.slice(0, 10)}T00:00:00`)
}
