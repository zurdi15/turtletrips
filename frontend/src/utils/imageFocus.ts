/**
 * Encuadre de una imagen recortada con `object-fit: cover`.
 *
 * El punto de encuadre son dos fracciones 0-1 que acaban en `object-position`:
 * 0,5/0,5 = centrada (lo que hace el navegador por defecto), 0 = pegada al
 * borde izquierdo/superior, 1 = al derecho/inferior.
 *
 * Arrastrar mueve la IMAGEN, no el recorte, así que el signo va cambiado: tirar
 * hacia la derecha destapa lo que había a la izquierda y el foco BAJA. Y como
 * el recorrido útil no es el ancho del marco sino lo que sobra de la imagen
 * (`overflow`), un mismo arrastre mueve mucho en una foto panorámica y poco en
 * una casi del mismo aspecto que el marco.
 */

export interface Focus {
  x: number
  y: number
}

export interface Size {
  width: number
  height: number
}

export const CENTERED: Focus = { x: 0.5, y: 0.5 }

export function clamp01(value: number): number {
  if (!Number.isFinite(value)) return 0.5
  return Math.min(1, Math.max(0, value))
}

/**
 * Píxeles de imagen que se quedan FUERA del marco en cada eje, con la escala
 * de `cover`. Un eje con 0 de sobra no se puede mover: ahí la imagen ya entra
 * justa y arrastrar no debe hacer nada.
 */
export function coverOverflow(natural: Size, frame: Size): Size {
  if (natural.width <= 0 || natural.height <= 0 || frame.width <= 0 || frame.height <= 0) {
    return { width: 0, height: 0 }
  }
  const scale = Math.max(frame.width / natural.width, frame.height / natural.height)
  return {
    width: Math.max(0, natural.width * scale - frame.width),
    height: Math.max(0, natural.height * scale - frame.height),
  }
}

/** Nuevo encuadre tras arrastrar `dx`/`dy` píxeles dentro del marco */
export function dragFocus(focus: Focus, dx: number, dy: number, overflow: Size): Focus {
  return {
    x: overflow.width > 0 ? clamp01(focus.x - dx / overflow.width) : focus.x,
    y: overflow.height > 0 ? clamp01(focus.y - dy / overflow.height) : focus.y,
  }
}

/** El valor para `object-position` (redondeado: un `50.0001%` no aporta nada) */
export function focusStyle(x: number | null | undefined, y: number | null | undefined): string {
  const px = Math.round(clamp01(x ?? 0.5) * 1000) / 10
  const py = Math.round(clamp01(y ?? 0.5) * 1000) / 10
  return `${px}% ${py}%`
}

/** ¿Hay algo que encuadrar? Si la imagen entra justa en el marco, no. */
export function canFrame(overflow: Size): boolean {
  return overflow.width > 1 || overflow.height > 1
}
